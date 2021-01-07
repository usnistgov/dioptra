#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

from pathlib import Path

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from attacks import create_adversarial_patches
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
    type=click.Choice(
        ["shallow_net", "le_net", "alex_net", "resnet50", "vgg16"], case_sensitive=False
    ),
    default="vgg16",
    help="Model architecture",
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
    "--learning-rate",
    type=click.FLOAT,
    help="The learning rate of the patch attack optimization procedure. ",
    default=5.0,
)
@click.option(
    "--max-iter",
    type=click.INT,
    help=" The number of patch optimization steps. ",
    default=500,
)
@click.option(
    "--patch-target",
    type=click.INT,
    help=" The target class index of the generated patch. Negative numbers will generate randomized id labels.",
    default=-1,
)
@click.option(
    "--num-patch",
    type=click.INT,
    help=" The number of patches generated. Each adversarial image recieves one patch. ",
    default=1,
)
@click.option(
    "--num-patch-gen-samples",
    type=click.INT,
    help=" The number of sample images used to generate each patch. ",
    default=10,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def patch_attack(
    data_dir,
    model,
    model_architecture,
    rotation_max,
    scale_min,
    scale_max,
    learning_rate,
    max_iter,
    patch_target,
    num_patch,
    num_patch_gen_samples,
    seed,
    patch_shape=None,
):

    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="patch",
        data_dir=data_dir,
        model=model,
        model_architecture=model_architecture,
        patch_target=patch_target,
        num_patch=num_patch,
        num_patch_samples=num_patch_gen_samples,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
        learning_rate=learning_rate,
        max_iter=max_iter,
        seed=seed,
    )

    batch_size = num_patch_gen_samples
    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir)
        adv_data_dir = Path().cwd() / "adv_patches"

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

        create_adversarial_patches(
            data_dir=testing_dir,
            adv_data_dir=adv_data_dir.resolve(),
            model=model,
            batch_size=batch_size,
            image_size=image_size,
            clip_values=clip_values,
            rescale=rescale,
            color_mode=color_mode,
            imagenet_preprocessing=imagenet_preprocessing,
            patch_target=patch_target,
            num_patch=num_patch,
            num_patch_samples=num_patch_gen_samples,
            rotation_max=rotation_max,
            scale_min=scale_min,
            scale_max=scale_max,
            learning_rate=learning_rate,
            max_iter=max_iter,
            patch_shape=patch_shape,
        )

        adv_patch_tar = Path().cwd() / "adversarial_patch.tar.gz"

        with tarfile.open(adv_patch_tar, "w:gz") as f:
            f.add(str(adv_data_dir.resolve()), arcname=adv_data_dir.name)

        LOGGER.info("Log adversarial patches", filename=adv_patch_tar.name)
        mlflow.log_artifact(str(adv_patch_tar))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    patch_attack()
