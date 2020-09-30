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
import numpy as np
import structlog
from pathlib import Path

from attacks import create_adversarial_fgm_dataset
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
    "--dataset-name",
    type=click.STRING,
    default = "val-sorted-5000",
    help ="ImageNet test set name. Options include: " \
          "\n val-sorted-1000  : 1000 image test set " \
          "\n val-sorted-5000  : 5000 image test set " \
          "\n val-sorted-10000 : 10000 image test set " \
          "\n val-sorted       : 50000 image test set ",
)
@click.option(
    "--model", type=click.STRING, help="Name of model to load from registry",
    default = "keras-model-imagenet-resnet50/1"
)
@click.option(
    "--model-architecture",
    type=click.Choice(["resnet50"], case_sensitive=False),
    default="resnet50",
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
@click.option(
    "--norm",
    type=click.Choice(["inf", "1", "2"]),
    help="FGM attack norm of adversarial perturbation",
    default="inf",
)
@click.option(
    "--apply-defense",
    type=click.BOOL,
    help="Toggles application of spatial smoothing defense.",
    default=False,
)
def fgm_attack(
    data_dir, dataset_name, model, model_architecture, batch_size, eps, eps_step, minimal, norm, apply_defense,
):
    norm_mapping = {"inf": np.inf, "1": 1, "2": 2}

    LOGGER.info(
        "Execute MLFlow entry point", entry_point="fgm_attack", data_dir=data_dir,
    )

    minimal = bool(int(minimal))
    norm = norm_mapping[norm]

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir) / dataset_name
        adv_data_dir = Path().cwd() / "adv_testing"

        adv_data_dir.mkdir(parents=True, exist_ok=True)

        image_size = (224, 224)
        
        classifier, distance_metrics = create_adversarial_fgm_dataset(
            data_dir=testing_dir,
            model=model,
            apply_defense=apply_defense,
            adv_data_dir=adv_data_dir.resolve(),
            batch_size=batch_size,
            image_size=image_size,
            eps=eps,
            eps_step=eps_step,
            minimal=minimal,
            norm=norm,
        )

        adv_ds = create_image_dataset(
            data_dir=str(adv_data_dir.resolve()),
            subset=None,
            validation_split=None,
            image_size=image_size,
        )
        evaluate_classification_metrics(classifier=classifier, adv_ds=adv_ds)

        adv_testing_tar = Path().cwd() / "testing_adversarial_fgm.tar.gz"
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
    fgm_attack()
