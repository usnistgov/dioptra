#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import os
from pathlib import Path

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from attacks import create_poisoned_test_images
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
    "--model-architecture",
    type=click.Choice(
        ["shallow_net", "le_net", "alex_net", "resnet50", "vgg16"], case_sensitive=False
    ),
    default="vgg16",
    help="Model architecture",
)
@click.option(
    "--target-class",
    type=click.INT,
    help=" The target class index to generate poisoned examples.",
    default=0,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help=" The number of clean sample images per poisoning batch. ",
    default=30,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
@click.option(
    "--poison-fraction",
    type=click.FLOAT,
    help="The fraction of data to be poisoned. Range 0 to 1.",
    default=1.0,
)
@click.option(
    "--label-type",
    type=click.Choice(["train", "training", "test", "testing"], case_sensitive=False),
    default="test",
    help="Sets labels either to original label (test) or poisoned label (train). Non-poisoned images keep their original label.",
)
def poison_attack(
    data_dir,
    model_architecture,
    target_class,
    batch_size,
    poison_fraction,
    label_type,
    seed,
):

    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="gen_poison_test_data",
        data_dir=data_dir,
        model_architecture=model_architecture,
        batch_size=batch_size,
        target_class=target_class,
        seed=seed,
        poison_fraction=poison_fraction,
        label_type=label_type,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir)
        adv_data_dir = Path().cwd() / "adv_poison_data"
        adv_data_dir.mkdir(parents=True, exist_ok=True)

        image_size = (224, 224)
        clip_values = (0, 255)
        rescale = 1.0
        color_mode = "rgb"
        imagenet_preprocessing = True

        mnist_models = ["shallow_net", "le_net", "alex_net"]
        if model_architecture in mnist_models:
            if model_architecture != "alex_net":
                image_size = (28, 28)
            clip_values = (0, 1.0)
            rescale = 1.0 / 255
            color_mode = "grayscale"
            imagenet_preprocessing = False

        distance_metrics = create_poisoned_test_images(
            data_dir=testing_dir,
            adv_data_dir=adv_data_dir.resolve(),
            batch_size=batch_size,
            target_class=target_class,
            image_size=image_size,
            clip_values=clip_values,
            rescale=rescale,
            color_mode=color_mode,
            imagenet_preprocessing=imagenet_preprocessing,
            label_type=label_type,
            poison_fraction=poison_fraction,
        )

        adv_poison_tar = Path().cwd() / "adversarial_poison.tar.gz"
        image_perturbation_csv = Path().cwd() / "distance_metrics.csv.gz"

        with tarfile.open(adv_poison_tar, "w:gz") as f:
            f.add(str(adv_data_dir.resolve()), arcname=adv_data_dir.name)

        LOGGER.info("Log adversarial images", filename=adv_poison_tar.name)
        mlflow.log_artifact(str(adv_poison_tar))

        LOGGER.info(
            "Log distance metric distributions", filename=image_perturbation_csv.name
        )
        distance_metrics.to_csv(image_perturbation_csv, index=False)
        mlflow.log_artifact(str(image_perturbation_csv))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    poison_attack()
