#!/usr/bin/env python
# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode

import warnings
from typing import Tuple
from pathlib import Path
import mlflow
import scipy.stats

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import numpy as np
import structlog
from art.attacks.evasion import PixelAttack, ThresholdAttack
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


def init_pt(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    # th=4, es=1, targeted=True, verbose=True
    attack = PixelAttack(classifier, **kwargs)
    return classifier, attack


def save_adv_batch(class_names_list, adv_batch, batch_size, batch_num, adv_data_dir, y):

    for batch_image_num, adv_image in enumerate(adv_batch):
        outfile = class_names_list[y[batch_image_num]]
        adv_image_path = (
            adv_data_dir
            / f"{outfile}"
            / f"adv{str(batch_size * batch_num + batch_image_num).zfill(5)}.png"
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


def create_adversarial_pt_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    **kwargs,
):
    classifier, attack = init_pt(model=model, batch_size=batch_size, **kwargs)

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]

    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info("Attacking data batch", batch_num=batch_num)

        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)
        save_adv_batch(
            class_names_list, adv_batch, batch_size, batch_num, adv_data_dir, y_int
        )
        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )
    LOGGER.info("Adversarial image generation complete", attack="fgm")
    log_distance_metrics(distance_metrics_)

    return classifier
