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
from tensorflow.keras.callbacks import EarlyStopping
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
from tensorflow.keras.optimizers import Adam, Adagrad, RMSprop

from data import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger
from models import resnet50
from art.estimators.classification import KerasClassifier

LOGGER = structlog.get_logger()
METRICS = [
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

def get_optimizer(optimizer, learning_rate):
    optimizer_collection = {
        "rmsprop": RMSprop(learning_rate),
        "adam": Adam(learning_rate),
        "adagrad": Adagrad(learning_rate),
    }

    return optimizer_collection.get(optimizer)


def get_model(
    model_architecture: str, n_classes: int = 10,
):
    model_collection = {
        "resnet": resnet50(),
    }

    return model_collection.get(model_architecture)


def get_model_callbacks():
    early_stop = EarlyStopping(
        monitor="val_loss", min_delta=1e-2, patience=5, restore_best_weights=True
    )

    return [early_stop]

'''
#This is the init model for mnist example
def init_model(learning_rate, model_architecture: str, optimizer: str):
    model_optimizer = get_optimizer(optimizer=optimizer, learning_rate=learning_rate)
    model = get_model(model_architecture=model_architecture)
    model.compile(
        loss="categorical_crossentropy", optimizer=model_optimizer, metrics=METRICS,
    )

    return model
'''

def prepare_data(
    data_dir,
    batch_size: int,
    validation_split: float,
    model_architecture: str,
    seed: int = 8237131,
):
    training_dir = Path(data_dir) / "training"
    testing_dir = Path(data_dir) / "testing"

    image_size = (224, 224)
    

    training = create_image_dataset(
        data_dir=str(training_dir),
        subset="training",
        validation_split=validation_split,
        batch_size=batch_size,
        seed=seed,
        image_size=image_size,
    )
    validation = create_image_dataset(
        data_dir=str(training_dir),
        subset="validation",
        validation_split=validation_split,
        batch_size=batch_size,
        seed=seed,
        image_size=image_size,
    )
    testing = create_image_dataset(
        data_dir=str(testing_dir),
        subset=None,
        validation_split=None,
        batch_size=batch_size,
        seed=seed + 1,
        image_size=image_size,
    )

    return (
        training,
        validation,
        testing,
    )


def fit(model, training_ds, validation_ds, epochs):
    time_start = datetime.datetime.now()

    LOGGER.info(
        "training tensorflow model", timestamp=time_start.isoformat(),
    )

    history = model.fit(
        training_ds,
        epochs=epochs,
        validation_data=validation_ds,
        callbacks=get_model_callbacks(),
        verbose=1,
    )

    time_end = datetime.datetime.now()

    total_seconds = (time_end - time_start).total_seconds()
    total_minutes = total_seconds / 60

    mlflow.log_metric("training_time_in_minutes", total_minutes)
    LOGGER.info(
        "tensorflow model training complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )

    return history, model


# Evaluate metrics against a chosen dataset.
def evaluate_metrics(classifier, ds):
    result = classifier.model.evaluate(ds)
    metrics = dict(zip(classifier.model.metrics_names, result))
    LOGGER.info("Test dataset metrics", **metrics)
    for metric_name, metric_value in metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    default = "/nfs2/data/ImageNet-Kaggle-2017/images/ILSVRC/Data/CLS-LOC",
    help ="Root directory for ImageNet test sets. (in container",
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
        ds = create_image_dataset(
          data_dir=dataset.resolve(), subset=None, validation_split=None
        )
        classifier = KerasClassifier(model=model, clip_values=clip_values, preprocessing =([mean_b, mean_g, mean_r], 1))
        evaluate_metrics(classifier=classifier, ds=ds)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    load_and_test_model()
