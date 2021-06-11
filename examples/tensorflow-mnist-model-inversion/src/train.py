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
import numpy as np
import structlog
from mlflow.tracking.client import MlflowClient
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.metrics import (
    CategoricalAccuracy,
    Precision,
    Recall,
    AUC,
)
from tensorflow.keras.optimizers import Adam, Adagrad, RMSprop, SGD

from data import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger
from models import shallow_net, le_net, alex_net, make_model_register

LOGGER = structlog.get_logger()
METRICS = [
    CategoricalAccuracy(name="accuracy"),
    Precision(name="precision"),
    Recall(name="recall"),
    AUC(name="auc"),
]


def get_optimizer(optimizer, learning_rate):
    optimizer_collection = {
        "rmsprop": RMSprop(learning_rate),
        "adam": Adam(learning_rate),
        "adagrad": Adagrad(learning_rate),
        "sgd": SGD(learning_rate),
    }

    return optimizer_collection.get(optimizer)


def get_model(
    model_architecture: str,
    n_classes: int = 10,
):
    model_collection = {
        "shallow_net": shallow_net(input_shape=(28, 28, 1), n_classes=n_classes),
        "le_net": le_net(input_shape=(28, 28, 1), n_classes=n_classes),
        "alex_net": alex_net(input_shape=(224, 224, 1), n_classes=n_classes),
    }

    return model_collection.get(model_architecture)


def get_model_callbacks():
    early_stop = EarlyStopping(
        monitor="val_loss", min_delta=1e-2, patience=5, restore_best_weights=True
    )

    return [early_stop]


def init_model(learning_rate, model_architecture: str, optimizer: str):
    model_optimizer = get_optimizer(optimizer=optimizer, learning_rate=learning_rate)
    model = get_model(model_architecture=model_architecture)
    model.compile(
        loss="categorical_crossentropy",
        optimizer=model_optimizer,
        metrics=METRICS,
    )

    return model


def prepare_data(
    data_dir,
    batch_size: int,
    validation_split: float,
    model_architecture: str,
    seed: int,
):
    training_dir = Path(data_dir) / "training"
    testing_dir = Path(data_dir) / "testing"

    image_size = (28, 28)
    if model_architecture == "alex_net":
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
        "training tensorflow model",
        timestamp=time_start.isoformat(),
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


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted datasets (in container)",
)
@click.option(
    "--model-architecture",
    type=click.Choice(["shallow_net", "le_net", "alex_net"], case_sensitive=False),
    default="le_net",
    help="Model architecture",
)
@click.option(
    "--epochs",
    type=click.INT,
    help="Number of epochs to train model",
    default=30,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--register-model",
    type=click.Choice(["True", "False"], case_sensitive=True),
    default="False",
    help="Add trained model to registry",
)
@click.option(
    "--learning-rate", type=click.FLOAT, help="Model learning rate", default=0.001
)
@click.option(
    "--optimizer",
    type=click.Choice(["adam", "adagrad", "rmsprop", "sgd"], case_sensitive=False),
    help="Optimizer to use to train the model",
    default="adam",
)
@click.option(
    "--validation-split",
    type=click.FLOAT,
    help="Fraction of training dataset to use for validation",
    default=0.2,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def train(
    data_dir,
    model_architecture,
    epochs,
    batch_size,
    register_model,
    learning_rate,
    optimizer,
    validation_split,
    seed,
):
    register_model = True if register_model == "True" else False
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="train",
        data_dir=data_dir,
        model_architecture=model_architecture,
        epochs=epochs,
        batch_size=batch_size,
        register_model=register_model,
        learning_rate=learning_rate,
        optimizer=optimizer,
        validation_split=validation_split,
        seed=seed,
    )

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
        model_name: str = f"{experiment_name}_{model_architecture}"

        register_mnist_model = make_model_register(
            active_run=active_run,
            name=model_name,
        )

        training_ds, validation_ds, testing_ds = prepare_data(
            data_dir=data_dir,
            validation_split=validation_split,
            batch_size=batch_size,
            model_architecture=model_architecture,
            seed=dataset_seed,
        )
        model = init_model(
            learning_rate=learning_rate,
            model_architecture=model_architecture,
            optimizer=optimizer,
        )
        history, model = fit(
            model=model,
            training_ds=training_ds,
            validation_ds=validation_ds,
            epochs=epochs,
        )
        evaluate_metrics(model=model, testing_ds=testing_ds)

        if register_model:
            register_mnist_model(model_dir="model")


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    train()
