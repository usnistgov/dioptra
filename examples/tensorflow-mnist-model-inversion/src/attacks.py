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

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from art.attacks.inference.model_inversion import MIFace
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


def init_miface(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = MIFace(classifier, max_iter=250, batch_size=batch_size)
    return classifier, attack


def save_adv_batch(adv_batch, adv_data_dir, y, clean_filenames):
    for batch_image_num, adv_image in enumerate(adv_batch):
        adv_image_path = adv_data_dir / f"{y}" / f"adv_{clean_filenames}"

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


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


def miface_infer(
    model: str,
    adv_data_dir: Path = None,
    batch_size: int = 32,
    **kwargs,
):
    classifier, attack = init_miface(model=model, batch_size=batch_size, **kwargs)

    x_train_infer_from_zero = attack.infer(None, y=np.arange(10))
    preds = np.argmax(classifier.predict(x_train_infer_from_zero), axis=1)

    for c in np.arange(10):
        save_adv_batch(
            [x_train_infer_from_zero[c]], adv_data_dir, c, "c" + str(c) + ".png"
        )

    # print("X_TRAIN_ZERO:" + str(x_train_infer_from_zero.shape))

    return None
