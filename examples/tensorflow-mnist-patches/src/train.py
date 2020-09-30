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
from models import le_net, alex_net

LOGGER = structlog.get_logger()
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
        loss="categorical_crossentropy", optimizer=model_optimizer, metrics=METRICS,
    )

    return model


def prepare_data(
    data_dir_train,
    data_dir_test,
    batch_size: int,
    validation_split: float,
    model_architecture: str,
    seed: int = 8237131,
):
    training_dir = Path(data_dir_train)
    testing_dir = Path(data_dir_test)

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

    mlflow.log_param("time_minutes", str(total_minutes))
    LOGGER.info(
        "tensorflow model training complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )

    return history, model


def evaluate_metrics(model, testing_ds):
    result = model.evaluate(testing_ds)
    testing_metrics = dict(zip(model.metrics_names, result))
    LOGGER.info("testing dataset metrics", **testing_metrics)
    for metric_name, metric_value in testing_metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)


@click.command()
@click.option(
    "--data-dir-train",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted training dataset (in container)",
)
@click.option(
    "--data-dir-test",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted training dataset (in container)",
)
@click.option(
    "--model-architecture",
    type=click.Choice(["le_net", "alex_net"], case_sensitive=False),
    default="le_net",
    help="Model architecture",
)
@click.option(
    "--model-tag", type=click.STRING, help="Model tag label", default = "mnist_",
)
@click.option(
    "--epochs", type=click.INT, help="Number of epochs to train model", default=30,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--learning-rate", type=click.FLOAT, help="Model learning rate", default=0.001
)
@click.option(
    "--optimizer",
    type=click.STRING,
    help="Optimizer to use to train the model",
    default="adam",
)
@click.option(
    "--validation-split",
    type=click.FLOAT,
    help="Fraction of training dataset to use for validation",
    default=0.2,
)
def train(
    data_dir_train,
    data_dir_test,
    model_architecture,
    model_tag,
    epochs,
    batch_size,
    learning_rate,
    optimizer,
    validation_split,
):

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="train",
        data_dir_train=data_dir_train,
        data_dir_test=data_dir_test,
        model_architecture=model_architecture,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        optimizer=optimizer,
        validation_split=validation_split,
    )
    mlflow.tensorflow.autolog()

    with mlflow.start_run() as _:
        training_ds, validation_ds, testing_ds = prepare_data(
            data_dir_train=data_dir_train,
            data_dir_test=data_dir_test,
            validation_split=validation_split,
            batch_size=batch_size,
            model_architecture=model_architecture,
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

        # Register model
        mlflow.keras.log_model(
            keras_model=model,
            artifact_path="mnist-models",
            registered_model_name=model_tag + model_architecture
        )


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    train()
