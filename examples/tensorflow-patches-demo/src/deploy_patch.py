#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import random
from pathlib import Path

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from art.attacks.evasion import AdversarialPatch
from art.estimators.classification import KerasClassifier
from attacks import create_adversarial_patch_dataset
from data import download_image_archive
from log import configure_stdlib_logger, configure_structlog_logger
from models import load_model_in_registry
from tensorflow.keras.preprocessing.image import save_img

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
    "--run-id",
    type=click.STRING,
    help="MLFlow Run ID of a successful patch attack",
)
@click.option(
    "--model",
    type=click.STRING,
    help="Name of model to load from registry",
)
@click.option(
    "--model-architecture",
    type=click.Choice(
        ["shallow_net", "le_net", "alex_net", "resnet50", "vgg16"], case_sensitive=False
    ),
    default="vgg16",
    help="Model architecture",
)
@click.option(
    "--patch-deployment-method",
    type=click.Choice(["corrupt", "augment"], case_sensitive=False),
    default="augment-original-images",
    help="Deployment method for creating patched dataset. "
    "If set to corrupt, patched images will replace a portion of original images. "
    "If set to augment, patched images will be created with a copy of the original dataset. ",
)
@click.option(
    "--patch-application-rate",
    type=click.FLOAT,
    help=" The fraction of images receiving an adversarial patch. "
    "Values greater than 1 or less than 0 will use the entire dataset.",
    default=1.0,
)
@click.option(
    "--patch-scale",
    type=click.FLOAT,
    help=" The scale of the patch to apply to images. ",
    default=0.4,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Image batch size to use for patch deployment.",
    default=32,
)
@click.option(
    "--rotation-max",
    type=click.FLOAT,
    help="The maximum rotation applied to random patches. \
            The value is expected to be in the range `[0, 180]` ",
    default=22.5,
)
@click.option(
    "--scale-min",
    type=click.FLOAT,
    help="The minimum scaling applied to random patches. \
            The value should be in the range `[0, 1]`, but less than `scale_max` ",
    default=0.1,
)
@click.option(
    "--scale-max",
    type=click.FLOAT,
    help="The maximum scaling applied to random patches. \
            The value should be in the range `[0, 1]`, but larger than `scale_min.` ",
    default=1.0,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def deploy_patch(
    data_dir,
    run_id,
    model,
    model_architecture,
    patch_deployment_method,
    patch_application_rate,
    patch_scale,
    batch_size,
    rotation_max,
    scale_min,
    scale_max,
    seed,
):

    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="deploy_patches",
        data_dir=data_dir,
        model=model,
        model_architecture=model_architecture,
        patch_deployment_method=patch_deployment_method,
        patch_application_rate=patch_application_rate,
        patch_scale=patch_scale,
        batch_size=batch_size,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
        seed=seed,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:

        # Download and setup patch set.
        adv_patch_tar_name = "adversarial_patch.tar.gz"
        adv_patch_tar_path = download_image_archive(
            run_id=run_id, archive_path=adv_patch_tar_name
        )
        with tarfile.open(adv_patch_tar_path, "r:gz") as f:
            f.extractall(path=Path.cwd())

        data_dir = Path(data_dir).resolve()
        patch_dir = Path().cwd() / "adv_patches"
        adv_data_dir = Path().cwd() / "adv_patch_dataset"
        adv_data_dir.mkdir(parents=True, exist_ok=True)

        image_size = (224, 224)
        clip_values = (0, 255)
        rescale = 1.0
        color_mode = "rgb"

        mnist_models = ["shallow_net", "le_net", "alex_net"]
        if model_architecture in mnist_models:
            if model_architecture != "alex_net":
                image_size = (28, 28)
            clip_values = (0, 1.0)
            rescale = 1.0 / 255
            color_mode = "grayscale"

        distance_metrics = create_adversarial_patch_dataset(
            data_dir=data_dir,
            model=model,
            adv_data_dir=adv_data_dir.resolve(),
            patch_dir=patch_dir.resolve(),
            batch_size=batch_size,
            image_size=image_size,
            clip_values=clip_values,
            rescale=rescale,
            color_mode=color_mode,
            patch_deployment_method=patch_deployment_method,
            patch_application_rate=patch_application_rate,
            patch_scale=patch_scale,
            rotation_max=rotation_max,
            scale_min=scale_min,
            scale_max=scale_max,
        )

        adv_dataset_tar = Path().cwd() / "adversarial_patch_dataset.tar.gz"
        image_perturbation_csv = Path().cwd() / "distance_metrics.csv.gz"

        with tarfile.open(adv_dataset_tar, "w:gz") as f:
            f.add(str(adv_data_dir.resolve()), arcname=adv_data_dir.name)

        LOGGER.info("Log adversarial images", filename=adv_dataset_tar.name)
        mlflow.log_artifact(str(adv_dataset_tar))

        LOGGER.info(
            "Log distance metric distributions", filename=image_perturbation_csv.name
        )
        distance_metrics.to_csv(image_perturbation_csv, index=False)
        mlflow.log_artifact(str(image_perturbation_csv))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    deploy_patch()
