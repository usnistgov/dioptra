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

from attacks import create_adversarial_pt_dataset
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
    "--model",
    type=click.STRING,
    help="Name of model to load from registry",
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
    "--th",
    type=click.INT,
    help="Pixel Attack Threshold",
    default=10,
)
@click.option(
    "--es",
    type=click.INT,
    help="Pixel Attack Evolution Algorithm",
    default=0,
)
def pt_attack(data_dir, model, model_architecture, batch_size, th, es):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="pt_attack",
        data_dir=data_dir,
    )

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir) / "regular_data/testing"
        adv_data_dir = Path().cwd() / "adv_testing_pt"

        adv_data_dir.mkdir(parents=True, exist_ok=True)

        image_size = (224, 224)
        classifier = create_adversarial_pt_dataset(
            data_dir=testing_dir,
            model=model,
            adv_data_dir=adv_data_dir.resolve(),
            batch_size=batch_size,
            image_size=image_size,
            th=th,
            es=es,
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

    pt_attack()
