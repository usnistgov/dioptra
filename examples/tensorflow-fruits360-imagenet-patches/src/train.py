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

from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.resnet_v2 import ResNet50V2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam, Adagrad, RMSprop


from data import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger

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

def model_resnet50():
    return ResNet50V2(weights='imagenet', input_shape = (224, 224, 3), include_top=False)
def model_vgg16():
    return VGG16(weights='imagenet', input_shape = (224, 224, 3),  include_top=False)

def get_model(
    model_architecture: str, n_classes: int = 120,
):
    model_collection = {
        "resnet50": model_resnet50,
        "vgg16": model_vgg16
    }

    # Setup top classification layer, and freeze base model layers.
    base_model = model_collection.get(model_architecture)()
    top = base_model.output
    top = GlobalAveragePooling2D()(top)
    top = Dense(1024, activation='relu')(top)
    predictions = Dense(n_classes, activation='softmax')(top)
    model = Model(inputs=base_model.input, outputs=predictions)

    for layer in base_model.layers:
        layer.trainable = False

    return model



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
    data_dir_training,
    data_dir_testing,
    batch_size: int,
    validation_split: float,
    model_architecture: str,
    seed: int = 8237131,
):
    training_dir = Path(data_dir_training)
    testing_dir = Path(data_dir_testing)

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
    "--data-dir-training",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for Fruits360 training set.",
)
@click.option(
    "--data-dir-testing",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for Fruits360 test set.",
)
@click.option(
    "--model-architecture",
    type=click.Choice(["resnet50", "vgg16"], case_sensitive=False),
    default="vgg16",
    help="Model architecture",
)
@click.option(
    "--model-tag",
    type=click.STRING,
    default="fruits360_",
    help="Model architecture",
)
@click.option(
    "--epochs", type=click.INT, help="Number of epochs to train model", default=2,
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
    data_dir_training,
    data_dir_testing,
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
        data_dir=data_dir_training,
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
            data_dir_training=data_dir_training,
            data_dir_testing=data_dir_testing,
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
            artifact_path="fruits360-models",
            registered_model_name= model_tag + model_architecture
        )


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    train()
