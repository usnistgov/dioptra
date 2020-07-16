#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()
tf.config.threading.set_intra_op_parallelism_threads(0)
tf.config.threading.set_inter_op_parallelism_threads(0)

import click
import mlflow
import mlflow.tensorflow
import structlog
from pathlib import Path

from attacks import create_adversarial_fgm_dataset
from data import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger


LOGGER = structlog.get_logger()


def evaluate_metrics(classifier, adv_ds):
    result = classifier.model.evaluate(adv_ds)
    adv_metrics = dict(zip(classifier.model.metrics_names, result))
    LOGGER.info("adversarial dataset metrics", **adv_metrics)
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
    type=click.Choice(["le_net", "alex_net"], case_sensitive=False),
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
    "--eps",
    type=click.FLOAT,
    help="FGM attack step size (input variation)",
    default=0.3,
)
@click.option(
    "--eps-step",
    type=click.FLOAT,
    help="FGM attack step size of input variation for minimal perturbation computation",
    default=0.1,
)
@click.option(
    "--minimal",
    type=click.Choice(["0", "1"]),
    default="0",
    help="If 1, compute the minimal perturbation using eps_step for the step size and "
    "eps for the maximum perturbation.",
)
def fgm_attack(
    data_dir, model, model_architecture, batch_size, eps, eps_step, minimal,
):
    LOGGER.info(
        "Execute MLFlow entry point", entry_point="fgm_attack", data_dir=data_dir,
    )
    minimal = bool(int(minimal))

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir) / "testing"
        adv_data_dir = Path().cwd() / "adv_testing"

        adv_data_dir.mkdir(parents=True, exist_ok=True)

        image_size = (28, 28)
        if model_architecture == "alex_net":
            image_size = (224, 224)

        classifier = create_adversarial_fgm_dataset(
            data_dir=testing_dir,
            model=model,
            adv_data_dir=adv_data_dir.resolve(),
            batch_size=batch_size,
            image_size=image_size,
            eps=eps,
            eps_step=eps_step,
            minimal=minimal,
        )

        adv_ds = create_image_dataset(
            data_dir=str(adv_data_dir.resolve()), subset=None, validation_split=None
        )
        evaluate_metrics(classifier=classifier, adv_ds=adv_ds)

        adv_testing_tar = Path().cwd() / "adv_testing.tar.gz"

        with tarfile.open(adv_testing_tar, "w:gz") as f:
            f.add(str(adv_data_dir.resolve()), arcname=adv_data_dir.name)

        mlflow.log_artifact(str(adv_testing_tar))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    fgm_attack()
