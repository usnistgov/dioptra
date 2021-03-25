#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from pathlib import Path

from data import create_image_dataset, download_image_archive
from log import configure_stdlib_logger, configure_structlog_logger
from models import load_model_in_registry


LOGGER = structlog.get_logger()


def evaluate_classification_metrics(classifier, adv_ds):
    LOGGER.info("evaluating classification metrics using adversarial images")
    result = classifier.evaluate(adv_ds, verbose=0)
    adv_metrics = dict(zip(classifier.metrics_names, result))
    LOGGER.info(
        "computation of classification metrics for adversarial images complete",
        **adv_metrics,
    )
    for metric_name, metric_value in adv_metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)


@click.command()
@click.option(
    "--run-id",
    type=click.STRING,
    help="MLFlow Run ID of a successful attack",
)
@click.option(
    "--model",
    type=click.STRING,
    help="Name of model to load from registry",
)
@click.option(
    "--model-architecture",
    type=click.Choice(
        ["shallow_net", "le_net", "mobilenet", "alex_net", "resnet50"],
        case_sensitive=False,
    ),
    default="le_net",
    help="Model architecture",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def infer_adversarial(run_id, model, model_architecture, batch_size, seed):
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="infer",
        model=model,
        model_architecture=model_architecture,
        batch_size=batch_size,
        seed=seed,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    dataset_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    LOGGER.info("Operating on files from Run ID: ", run_id=run_id)
    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:
        adv_testing_tar_name = "testing_adversarial.tar.gz"
        adv_testing_data_dir = Path.cwd() / "adv_testing"
        LOGGER.info(
            "Operating on tar name: ", adv_testing_tar_name=adv_testing_tar_name
        )
        LOGGER.info(
            "Operating on data dir: ", adv_testing_data_dir=adv_testing_data_dir
        )
        image_size = (28, 28)
        if model_architecture == "alex_net" or model_architecture == "mobilenet":
            image_size = (224, 224)

        adv_testing_tar_path = download_image_archive(
            run_id=run_id, archive_path=adv_testing_tar_name
        )

        with tarfile.open(adv_testing_tar_path, "r:gz") as f:
            f.extractall(path=Path.cwd())
        if model_architecture == "mobilenet":
            adv_ds = create_image_dataset(
                data_dir=str(adv_testing_data_dir.resolve()),
                subset=None,
                validation_split=None,
                image_size=image_size,
                seed=dataset_seed,
                color_mode="rgb",
            )

        else:
            adv_ds = create_image_dataset(
                data_dir=str(adv_testing_data_dir.resolve()),
                subset=None,
                validation_split=None,
                image_size=image_size,
                seed=dataset_seed,
            )
        classifier = load_model_in_registry(model=model)
        """
        for layer in classifier.layers:
            LOGGER.info("shape: ", shape = layer.output_shape)
        """
        LOGGER.info("model: ", model=model)
        evaluate_classification_metrics(classifier=classifier, adv_ds=adv_ds)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    infer_adversarial()
