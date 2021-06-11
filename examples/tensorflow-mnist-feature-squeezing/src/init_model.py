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
import os
import warnings
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import click
import mlflow
import mlflow.tensorflow
from mlflow.tracking.client import MlflowClient
import numpy as np
import structlog

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

from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.resnet import ResNet50
from tensorflow.keras.applications.mobilenet import MobileNet
from tensorflow.keras.applications.mobilenet import preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.models import Sequential
from data_res import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger
from models import make_model_register

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


def model_resnet50():
    return ResNet50(weights="imagenet", input_shape=(224, 224, 3))


def model_vgg16():
    return VGG16(weights="imagenet", input_shape=(224, 224, 3))


def model_mobilenet():
    return MobileNet(
        weights="imagenet", input_shape=(224, 224, 3), classes=1000
    )  # , classifier_activation=None)


# Evaluate metrics against a chosen dataset


def my_categorical_crossentropy(y_true, y_pred):
    return K.sparse_categorical_crossentropy(y_true, y_pred, from_logits=True)


def evaluate_metrics(model, testing_ds):
    LOGGER.info("evaluating classification metrics using testing images")
    result = model.evaluate(testing_ds, verbose=0)
    testing_metrics = dict(zip(model.metrics_names, result))
    LOGGER.info(
        "computation of classification metrics for testing images complete",
        **testing_metrics,
    )
    for metric_name, metric_value in testing_metrics.items():
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
    "--model-architecture",
    type=click.Choice(["resnet50", "vgg16", "mobilenet"], case_sensitive=False),
    default="vgg16",
    help="Model architecture",
)
@click.option(
    "--model-tag",
    type=click.STRING,
    help="Optional model tag identifier.",
    default="default_pretrained",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=10,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def load_and_test_model(data_dir, model_architecture, model_tag, batch_size, seed):

    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    dataset_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)
    mlflow.tensorflow.autolog()

    with mlflow.start_run() as active_run:
        mlflow.log_param("entry_point_seed", seed)
        mlflow.log_param("tensorflow_global_seed", tensorflow_global_seed)
        mlflow.log_param("dataset_seed", dataset_seed)

        experiment_name: str = (
            MlflowClient().get_experiment(active_run.info.experiment_id).name
        )

        if len(model_tag) > 0:
            model_name = f"{experiment_name}_{model_tag}_{model_architecture}"
        else:
            model_name = f"{experiment_name}_{model_architecture}"

        model_collection = {
            "resnet50": model_resnet50,
            "vgg16": model_vgg16,
            "mobilenet": model_mobilenet,
        }
        if model_architecture == "mobilenet":
            temp = model_collection[model_architecture]()
            newmodel = Sequential()
            for layer in temp.layers[:-1]:
                newmodel.add(layer)
            newmodel.summary()

            newmodel.compile(
                loss="categorical_crossentropy",
                metrics=METRICS,
            )

            mlflow.keras.log_model(
                keras_model=newmodel,
                artifact_path="model",
                registered_model_name=model_name + "_logits",
            )
            model = newmodel
        model = model_collection[model_architecture]()
        model.summary()
        model.compile(
            loss="categorical_crossentropy",
            metrics=METRICS,
        )
        if model_architecture != "mobilenet":
            mlflow.keras.log_model(
                keras_model=model,
                artifact_path="model",
                registered_model_name=model_name,
            )
        dataset = Path(data_dir)
        ds = create_image_dataset(
            data_dir=dataset.resolve(),
            subset=None,
            validation_split=None,
            batch_size=batch_size,
            model_architecture=model_architecture,
        )

        evaluate_metrics(model=model, testing_ds=ds)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    load_and_test_model()
