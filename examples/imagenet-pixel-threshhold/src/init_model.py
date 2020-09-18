#!/usr/bin/env python

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

from data import create_image_dataset
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

# Initialize, compile, and return a Keras ResNet50 model pretrained on imagenet weights.
def init_model():
    model = tf.keras.applications.resnet50.ResNet50(weights="imagenet")
    model.compile(
        loss="categorical_crossentropy", metrics=METRICS,
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
    default = "/nfs/data/ImageNet-Kaggle-2017/images/ILSVRC/Data/CLS-LOC",
    help ="Root directory for ImageNet test sets.",
)
@click.option(
    "--dataset-name",
    type=click.STRING,
    default = "val-sorted-5000",
    help ="ImageNet test set name. Options include: " \
          "\n val-sorted-1000  : 1000 image test set " \
          "\n val-sorted-5000  : 5000 image test set " \
          "\n val-sorted-10000 : 10000 image test set " \
          "\n val-sorted       : 50000 image test set ",
)
def load_and_test_model(data_dir, dataset_name):
    image_shape = (224, 224, 3)
    clip_values = (0, 255)
    nb_classes  =1000
    batch_size = 16
    scale_min = 0.4
    scale_max = 1.0
    rotation_max = 22.5
    learning_rate = 5000.
    max_iter = 500

    mean_b = 103.939
    mean_g = 116.779
    mean_r = 123.680

    mlflow.tensorflow.autolog()

    with mlflow.start_run() as _:
        model = init_model()
        mlflow.keras.log_model(
          keras_model=model,
          artifact_path="keras-model-imagenet-resnet50",
          registered_model_name="keras-model-imagenet-resnet50"
        )
        dataset = Path(data_dir) / dataset_name
        print(dataset)
        ds = create_image_dataset(
          data_dir=dataset.resolve(), subset=None, validation_split=None
        )
        classifier = KerasClassifier(model=model, clip_values=clip_values, preprocessing =([mean_b, mean_g, mean_r], 1))
        evaluate_metrics(classifier=classifier, ds=ds)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    load_and_test_model()
