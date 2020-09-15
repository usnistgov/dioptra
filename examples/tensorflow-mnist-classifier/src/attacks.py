#!/usr/bin/env python

import warnings
from typing import Tuple
from pathlib import Path

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from art.attacks.evasion import FastGradientMethod
from art.estimators.classification import KerasClassifier
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import save_img

from models import load_model_in_registry
from metrics import (
    l_inf_norm,
    paired_cosine_similarities,
    paired_euclidean_distances,
    paired_manhattan_distances,
    paired_wasserstein_distances,
)

LOGGER = structlog.get_logger()
DISTANCE_METRICS = [
    ("l_infinity_norm", l_inf_norm),
    ("cosine_similarity", paired_cosine_similarities),
    ("euclidean_distance", paired_euclidean_distances),
    ("manhattan_distance", paired_manhattan_distances),
    ("wasserstein_distance", paired_wasserstein_distances),
]


def wrap_keras_classifier(model):
    keras_model = load_model_in_registry(model=model)
    return KerasClassifier(model=keras_model)


def init_fgm(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = FastGradientMethod(estimator=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


def save_adv_batch(adv_batch, adv_data_dir, y, clean_filenames):
    for batch_image_num, adv_image in enumerate(adv_batch):
        adv_image_path = (
            adv_data_dir
            / f"{y[batch_image_num]}"
            / f"adv_{clean_filenames[batch_image_num].name}"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


def np_norm(im, im2, order):
    im_diff = im - im2
    batch_size = im_diff.shape[0]
    flatten_size = np.prod(im_diff.shape[1:])
    im_diff_norm = np.linalg.norm(
        im_diff.reshape((batch_size, flatten_size)), axis=1, ord=order
    )
    return im_diff_norm.tolist()


def evaluate_distance_metrics(
    clean_filenames, distance_metrics_, clean_batch, adv_batch
):
    LOGGER.debug("evaluate image perturbations using distance metrics")
    distance_metrics_["image"].extend([x.name for x in clean_filenames])
    distance_metrics_["label"].extend([x.parent for x in clean_filenames])
    for metric_name, metric in DISTANCE_METRICS:
        distance_metrics_[metric_name].extend(metric(clean_batch, adv_batch))


def log_distance_metrics(distance_metrics_):
    distance_metrics_ = distance_metrics_.copy()
    del distance_metrics_["image"]
    del distance_metrics_["label"]
    for metric_name, metric_values_list in distance_metrics_.items():
        metric_values = np.array(metric_values_list)
        mlflow.log_metric(key=f"{metric_name}_mean", value=metric_values.mean())
        mlflow.log_metric(key=f"{metric_name}_median", value=np.median(metric_values))
        mlflow.log_metric(key=f"{metric_name}_stdev", value=metric_values.std())
        mlflow.log_metric(
            key=f"{metric_name}_iqr", value=scipy.stats.iqr(metric_values)
        )
        mlflow.log_metric(key=f"{metric_name}_min", value=metric_values.min())
        mlflow.log_metric(key=f"{metric_name}_max", value=metric_values.max())
        LOGGER.info("logged distance-based metric", metric_name=metric_name)


def create_adversarial_fgm_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
    **kwargs,
):
    classifier, attack = init_fgm(model=model, batch_size=batch_size, **kwargs)

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]

    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial images",
        attack="fgm",
        num_batches=num_images // batch_size,
    )

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Generate adversarial image batch", attack="fgm", batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)

        save_adv_batch(adv_batch, adv_data_dir, y_int, clean_filenames)

        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )

    LOGGER.info("Adversarial image generation complete", attack="fgm")
    log_distance_metrics(distance_metrics_)

    return pd.DataFrame(distance_metrics_)
