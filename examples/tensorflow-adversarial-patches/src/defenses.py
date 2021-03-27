#!/usr/bin/env python

import warnings
from pathlib import Path
from typing import Tuple

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from art.attacks.evasion import FastGradientMethod
from art.defences.preprocessor import (
    GaussianAugmentation,
    JpegCompression,
    SpatialSmoothing,
)
from art.estimators.classification import KerasClassifier
from metrics import (
    l_inf_norm,
    paired_cosine_similarities,
    paired_euclidean_distances,
    paired_manhattan_distances,
    paired_wasserstein_distances,
)
from models import load_model_in_registry
from tensorflow.keras.preprocessing.image import ImageDataGenerator, save_img

LOGGER = structlog.get_logger()
DISTANCE_METRICS = [
    ("l_infinity_norm", l_inf_norm),
    ("cosine_similarity", paired_cosine_similarities),
    ("euclidean_distance", paired_euclidean_distances),
    ("manhattan_distance", paired_manhattan_distances),
    ("wasserstein_distance", paired_wasserstein_distances),
]

DEFENSE_LIST = {
    "spatial_smoothing": SpatialSmoothing,
    "jpeg_compression": JpegCompression,
    "gaussian_augmentation": GaussianAugmentation,
}


def get_optimizer(optimizer, learning_rate):
    optimizer_collection = {
        "rmsprop": RMSprop(learning_rate),
        "adam": Adam(learning_rate),
        "adagrad": Adagrad(learning_rate),
        "sgd": SGD(learning_rate),
    }

    return optimizer_collection.get(optimizer)


# Load model from registry and apply imagenet_preprocessing if needed.
def wrap_keras_classifier(model, clip_values, imagenet_preprocessing):
    keras_model = load_model_in_registry(model=model)
    if imagenet_preprocessing:
        mean_b = 103.939
        mean_g = 116.779
        mean_r = 123.680
        return KerasClassifier(
            model=keras_model,
            clip_values=clip_values,
            preprocessing=([mean_b, mean_g, mean_r], 1),
        )
    else:
        return KerasClassifier(model=keras_model, clip_values=clip_values)


def init_defense(
    model, batch_size, clip_values, imagenet_preprocessing, def_type, **kwargs
):
    classifier = wrap_keras_classifier(model, clip_values, imagenet_preprocessing)

    defense = DEFENSE_LIST[def_type](
        clip_values=clip_values,
        **kwargs,
    )

    return classifier, defense


def save_def_batch(def_batch, def_data_dir, y, clean_filenames, class_names_list):
    for batch_image_num, def_image in enumerate(def_batch):
        out_label = class_names_list[y[batch_image_num]]
        def_image_path = (
            def_data_dir
            / f"{out_label}"
            / f"def_{clean_filenames[batch_image_num].name}"
        )

        if not def_image_path.parent.exists():
            def_image_path.parent.mkdir(parents=True)

        save_img(path=str(def_image_path), x=def_image)


def evaluate_distance_metrics(
    clean_filenames, distance_metrics_, clean_batch, def_batch
):
    LOGGER.debug("evaluate image perturbations using distance metrics")
    distance_metrics_["image"].extend([x.name for x in clean_filenames])
    distance_metrics_["label"].extend([x.parent for x in clean_filenames])
    for metric_name, metric in DISTANCE_METRICS:
        distance_metrics_[metric_name].extend(metric(clean_batch, def_batch))


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


def create_defended_dataset(
    data_dir: str,
    model: str,
    def_data_dir: Path = None,
    rescale: float = 1.0,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    clip_values: Tuple[float, float] = (0, 255),
    imagenet_preprocessing: bool = True,
    def_type: str = "spatial_smoothing",
    **kwargs,
):

    classifier, defense = init_defense(
        model=model,
        batch_size=batch_size,
        clip_values=clip_values,
        def_type=def_type,
        imagenet_preprocessing=imagenet_preprocessing,
        **kwargs,
    )

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
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate defended images",
        defense=def_type,
        num_batches=num_images // batch_size,
    )

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Generate defended image batch",
            defense=def_type,
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)

        adv_batch_defend, _ = defense(x)
        save_def_batch(
            adv_batch_defend, def_data_dir, y_int, clean_filenames, class_names_list
        )

        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            def_batch=adv_batch_defend,
        )

    LOGGER.info("Defended image generation complete", defense=def_type)
    log_distance_metrics(distance_metrics_)

    return pd.DataFrame(distance_metrics_)
