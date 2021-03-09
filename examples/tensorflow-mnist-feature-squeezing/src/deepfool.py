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

from attacks import (
    create_adversarial_deepfool_dataset,
    create_adversarial_mnist_deepfool_dataset,
)
from data import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger


LOGGER = structlog.get_logger()


def evaluate_classification_metrics(classifier, adv_ds):
    LOGGER.info("evaluating classification metrics using adversarial images")
    result = classifier.model.evaluate(adv_ds, verbose=0)
    adv_metrics = dict(zip(classifier.model.metrics_names, result))
    LOGGER.info(
        "computation of classification metrics for adversarial images complete",
        **adv_metrics,
    )
    for metric_name, metric_value in adv_metrics.items():
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
    "--model", type=click.STRING, help="Name of model to load from registry",
)
@click.option(
    "--model-architecture",
    type=click.Choice(
        ["shallow_net", "le_net", "alex_net", "resnet50", "mobilenet"],
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
    "--max-iter", type=click.INT, help="The maximum number of iterations", default=10,
)
@click.option(
    "--nb-grads",
    type=click.INT,
    help="The number of class gradients to compute",
    default=10,
)
@click.option(
    "--epsilon", type=click.FLOAT, help="Oversoot parameter", default=0.000001,
)
@click.option(
    "--seed", type=click.INT, help="Set the entry point rng seed", default=-1,
)
@click.option(
    "--verbose", type=click.BOOL, help="Show progress bars", default=True,
)
def deepfool_attack(
    data_dir,
    model,
    model_architecture,
    batch_size,
    seed,
    max_iter,
    epsilon,
    nb_grads,
    verbose,
):
    norm_mapping = {"inf": np.inf, "1": 1, "2": 2}
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="deepfool",
        data_dir=data_dir,
        model=model,
        batch_size=batch_size,
        max_iter=max_iter,
        seed=seed,
        epsilon=epsilon,
        nb_grads=nb_grads,
        verbose=verbose,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir)  # / "testing"
        adv_data_dir = Path().cwd() / "adv_testing"

        adv_data_dir.mkdir(parents=True, exist_ok=True)
        image_size = (28, 28)
        if (
            model_architecture == "alex_net"
            or model_architecture == "resnet50"
            or model_architecture == "mobilenet"
        ):
            image_size = (224, 224)
            classifier, distance_metrics = create_adversarial_deepfool_dataset(
                data_dir=testing_dir,
                model=model,
                adv_data_dir=adv_data_dir.resolve(),
                batch_size=batch_size,
                max_iter=max_iter,
                verbose=verbose,
                epsilon=epsilon,
                nb_grads=nb_grads,
            )
        else:
            classifier, distance_metrics = create_adversarial_mnist_deepfool_dataset(
                data_dir=testing_dir,
                model=model,
                adv_data_dir=adv_data_dir.resolve(),
                batch_size=batch_size,
                max_iter=max_iter,
                verbose=verbose,
                epsilon=epsilon,
                nb_grads=nb_grads,
            )
        adv_testing_tar = Path().cwd() / "testing_adversarial.tar.gz"
        image_perturbation_csv = Path().cwd() / "distance_metrics.csv.gz"

        with tarfile.open(adv_testing_tar, "w:gz") as f:
            f.add(str(adv_data_dir.resolve()), arcname=adv_data_dir.name)

        LOGGER.info("Log adversarial images", filename=adv_testing_tar.name)
        mlflow.log_artifact(str(adv_testing_tar))

        LOGGER.info(
            "Log distance metric distributions", filename=image_perturbation_csv.name
        )
        distance_metrics.to_csv(image_perturbation_csv, index=False)
        mlflow.log_artifact(str(image_perturbation_csv))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    deepfool_attack()
