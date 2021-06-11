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

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from pathlib import Path

from attacks import create_adversarial_cw_dataset
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
    "--model",
    type=click.STRING,
    help="Name of model to load from registry",
)
@click.option(
    "--model-architecture",
    type=click.Choice(["shallow_net", "le_net", "alex_net"], case_sensitive=False),
    default="le_net",
    help="Model architecture",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=1,
)
@click.option(
    "--binary-search-steps",
    type=click.INT,
    help="Number of times to adjust constant with binary search (positive value).",
    default=10,
)
@click.option(
    "--max-iter",
    type=click.INT,
    help="The maximum number of iterations",
    default=10,
)
@click.option(
    "--initial-const",
    type=click.FLOAT,
    default="0.01",
    help=" The initial trade-off constant c to use to tune the relative importance of distance and confidence",
)
@click.option(
    "--learning-rate",
    type=click.FLOAT,
    default="0.01",
    help="The initial learning rate for the attack algorithm, Smaller values produce better results but are slower to converge.",
)
@click.option(
    "--confidence",
    type=click.FLOAT,
    default="0.0",
    help=" Confidence of adversarial examples",
)
@click.option(
    "--max-halving",
    type=click.INT,
    help="Maximum number of halving steps in the line search optimization",
    default=5,
)
@click.option(
    "--max-doubling",
    type=click.INT,
    help="Maximum number of doubling steps in the line search optimization",
    default=5,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
@click.option(
    "--targeted",
    type=click.BOOL,
    help="Should the attack target one specific class",
    default=False,
)
@click.option(
    "--verbose",
    type=click.BOOL,
    help="Show progress bars",
    default=True,
)
@click.option(
    "--mode",
    type=click.Choice(["inf", "L2"], case_sensitive=False),
    default="L2",
    help="Choice of distance metric",
)
def cw_attack(
    data_dir,
    model,
    mode,
    model_architecture,
    batch_size,
    confidence,
    targeted,
    learning_rate,
    binary_search_steps,
    seed,
    max_iter,
    initial_const,
    max_doubling,
    max_halving,
    verbose,
):
    norm_mapping = {"inf": np.inf, "1": 1, "2": 2}
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="cw",
        data_dir=data_dir,
        model=model,
        mode=mode,
        batch_size=batch_size,
        confidence=confidence,
        targeted=targeted,
        learning_rate=learning_rate,
        binary_search_steps=binary_search_steps,
        max_iter=max_iter,
        seed=seed,
        initial_const=initial_const,
        max_doubling=max_doubling,
        max_halving=max_halving,
        verbose=verbose,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir) / "testing"
        adv_data_dir = Path().cwd() / "adv_testing"

        adv_data_dir.mkdir(parents=True, exist_ok=True)

        image_size = (28, 28)
        if model_architecture == "alex_net":
            image_size = (224, 224)

        classifier, distance_metrics = create_adversarial_cw_dataset(
            data_dir=testing_dir,
            model=model,
            adv_data_dir=adv_data_dir.resolve(),
            batch_size=batch_size,
            confidence=confidence,
            targeted=targeted,
            learning_rate=learning_rate,
            binary_search_steps=binary_search_steps,
            max_iter=max_iter,
            initial_const=initial_const,
            max_doubling=max_doubling,
            max_halving=max_halving,
            verbose=verbose,
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
    cw_attack()
