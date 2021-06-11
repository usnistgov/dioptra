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

import datetime
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import tensorflow as tf
from typing import Tuple

tf.compat.v1.disable_eager_execution()
tf.config.threading.set_intra_op_parallelism_threads(0)
tf.config.threading.set_inter_op_parallelism_threads(0)

import click
import mlflow
import mlflow.tensorflow
import structlog

from art.estimators.classification import KerasClassifier

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.metrics import (
    TruePositives,
    FalsePositives,
    TrueNegatives,
    FalseNegatives,
    CategoricalAccuracy,
    Precision,
    Recall,
    AUC,
)

from log import configure_stdlib_logger, configure_structlog_logger

LOGGER = structlog.get_logger()

# List of Keras model metrics.
METRICS = [
    TruePositives(name="tp"),
    FalsePositives(name="fp"),
    TrueNegatives(name="tn"),
    FalseNegatives(name="fn"),
    CategoricalAccuracy(name="accuracy"),
    Precision(name="precision"),
    Recall(name="recall"),
    AUC(name="auc"),
]


def create_image_dataset(
    data_dir: str,
    subset: str,
    rescale: float = 1.0,
    validation_split: float = 0.2,
    batch_size: int = 20,
    seed: int = 8237131,
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
):
    data_generator = ImageDataGenerator(
        rescale=rescale,
        validation_split=validation_split,
    )

    return data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        seed=seed,
        subset=subset,
    )


# Initialize, compile, and return a Keras ResNet50 model pretrained on imagenet weights.
def init_model():
    model = tf.keras.applications.resnet50.ResNet50(weights="imagenet")
    model.compile(
        loss="categorical_crossentropy",
        metrics=METRICS,
    )
    return model


# Evaluate metrics against a chosen dataset.
def evaluate_metrics(classifier, ds):
    result = classifier.model.evaluate(ds)
    metrics = dict(zip(classifier.model.metrics_names, result))
    LOGGER.info("Test dataset metrics", **metrics)
    for metric_name, metric_value in metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)


# Load pretrained model and test against input dataset.
@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    default="/nfs/data/ImageNet-Kaggle-2017/images/ILSVRC/Data/CLS-LOC",
    help="Root directory for ImageNet test sets.",
)
@click.option(
    "--dataset-name",
    type=click.STRING,
    default="val-sorted-5000",
    help="ImageNet test set name. Options include: "
    "\n val-sorted-1000  : 1000 image test set "
    "\n val-sorted-5000  : 5000 image test set "
    "\n val-sorted-10000 : 10000 image test set "
    "\n val-sorted       : 50000 image test set ",
)
def load_and_test_model(data_dir, dataset_name):

    clip_values = (0, 255)

    mean_b = 103.939
    mean_g = 116.779
    mean_r = 123.680

    mlflow.tensorflow.autolog()

    with mlflow.start_run() as _:
        model = init_model()
        mlflow.keras.log_model(
            keras_model=model,
            artifact_path="keras-model-imagenet-resnet50",
            registered_model_name="keras-model-imagenet-resnet50",
        )
        dataset = Path(data_dir) / dataset_name
        ds = create_image_dataset(
            data_dir=dataset.resolve(), subset=None, validation_split=None
        )
        classifier = KerasClassifier(
            model=model,
            clip_values=clip_values,
            preprocessing=([mean_b, mean_g, mean_r], 1),
        )
        evaluate_metrics(classifier=classifier, ds=ds)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    load_and_test_model()
