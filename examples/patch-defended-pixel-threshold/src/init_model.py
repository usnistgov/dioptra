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

tf.compat.v1.disable_eager_execution()
tf.config.threading.set_intra_op_parallelism_threads(0)
tf.config.threading.set_inter_op_parallelism_threads(0)

import click
import mlflow
import mlflow.tensorflow
import structlog

from art.estimators.classification import KerasClassifier

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

from tensorflow import keras
from data import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger
from tensorflow.keras.layers import Input, Dense, Flatten

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

# Initialize, compile, and return a Keras ResNet50 model pretrained on imagenet weights.
def init_model():

    model = keras.models.load_model("/nfs/data/undefended_regular_model/data/model.h5")
    # model = keras.models.load_model("/nfs/data/mixed-patch-model/data/model.h5")
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
    default="/nfs/data/",
)
@click.option(
    "--dataset-name",
    type=click.STRING,
    default="regular_data",
)
def load_and_test_model(data_dir, dataset_name):
    image_shape = (224, 224, 3)
    clip_values = (0, 255)
    nb_classes = 120
    batch_size = 32
    scale_min = 0.4
    scale_max = 1.0
    learning_rate = 5000.0
    max_iter = 500

    mlflow.tensorflow.autolog()

    with mlflow.start_run() as _:
        model = init_model()
        print("HERE:" + str(model.outputs))
        mlflow.keras.log_model(
            keras_model=model,
            artifact_path="patch-defended",
            registered_model_name="patch-defended",
        )
        dataset = Path(data_dir) / dataset_name / "testing"
        ds = create_image_dataset(
            data_dir=dataset.resolve(),
            subset=None,
            validation_split=None,
            batch_size=batch_size,
        )
        classifier = KerasClassifier(
            model=model, clip_values=clip_values, use_logits=True
        )
        evaluate_metrics(classifier=classifier, ds=ds)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    load_and_test_model()
