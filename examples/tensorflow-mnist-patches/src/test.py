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
from models import load_model_in_registry

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


def prepare_data(
    data_dir,
    batch_size: int,
    model_architecture: str,
    seed: int = 8237131,
):
    image_size = (28, 28)
    if model_architecture == "alex_net":
        image_size = (224, 224)

    testing = create_image_dataset(
        data_dir=str(data_dir),
        subset=None,
        validation_split=None,
        batch_size=batch_size,
        seed=seed + 1,
        image_size=image_size,
    )
    return testing


def evaluate_metrics(model, testing_ds):
    result = model.evaluate(testing_ds)
    testing_metrics = dict(zip(model.metrics_names, result))
    LOGGER.info("testing dataset metrics", **testing_metrics)
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
    type=click.Choice(["le_net", "alex_net"], case_sensitive=False),
    default="le_net",
    help="Model architecture",
)
@click.option(
    "--model-name",
    type=click.STRING,
    default="mnist_le_net/None",
    help="Model architecture",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
def test(
    data_dir,
    model_architecture,
    model_name,
    batch_size,
):
    model = model_name
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="test",
        data_dir=data_dir,
        model_architecture=model_architecture,
        batch_size=batch_size,
    )
    mlflow.tensorflow.autolog()

    model = load_model_in_registry(model=model)
    model.compile(
        loss="categorical_crossentropy", metrics=METRICS,
    )
    with mlflow.start_run() as _:
        testing_ds = prepare_data(
            data_dir=data_dir,
            batch_size=batch_size,
            model_architecture=model_architecture,
        )
        evaluate_metrics(model=model, testing_ds=testing_ds)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    test()