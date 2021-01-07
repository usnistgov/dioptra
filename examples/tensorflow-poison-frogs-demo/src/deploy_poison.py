#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import os
import shutil
from pathlib import Path

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from data import download_image_archive
from log import configure_stdlib_logger, configure_structlog_logger

LOGGER = structlog.get_logger()


def get_target_class_name(poison_dir):
    poison_dir = poison_dir.resolve()
    for item in os.listdir(poison_dir):
        if os.path.isdir(poison_dir / item):
            return item
    return "None"


def copy_poisoned_images(src, dst, num_poisoned_images):
    poison_image_list = [
        os.path.join(src, f)
        for f in os.listdir(src)
        if os.path.isfile(os.path.join(src, f))
    ]
    np.random.shuffle(poison_image_list)
    if not (num_poisoned_images < 0 or num_poisoned_images > len(poison_image_list)):
        poison_image_list = poison_image_list[:num_poisoned_images]

    for file in poison_image_list:
        shutil.copy(file, dst)


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
    help="MLFlow Run ID of a successful poison attack",
)
@click.option(
    "--poison-deployment-method",
    type=click.Choice(["replace", "add"], case_sensitive=False),
    default="add",
    help="Deployment method for creating poisoned dataset. "
    "If set to replace, poisoned images will replace their original images. "
    "If set to add, poisoned images will be added to the existing dataset. ",
)
@click.option(
    "--num-poisoned-images",
    type=click.INT,
    help="Specify number of poisoned images to add to the dataset. "
    "If number exceeds limits, then all poisoned images are added.",
    default=-1,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def deploy_poison(
    data_dir, run_id, poison_deployment_method, num_poisoned_images, seed
):

    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="deploy_poison",
        poison_deployment_method=poison_deployment_method,
        num_poisoned_images=num_poisoned_images,
        seed=seed,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:

        # Download and setup poison set.
        adv_poison_tar_name = "adversarial_poison.tar.gz"
        adv_poison_tar_path = download_image_archive(
            run_id=run_id, archive_path=adv_poison_tar_name
        )
        with tarfile.open(adv_poison_tar_path, "r:gz") as f:
            f.extractall(path=Path.cwd())

        data_dir = Path(data_dir).resolve()

        poison_images_dir = Path().cwd() / "adv_poison_data"
        target_class_name = get_target_class_name(poison_images_dir)

        adv_data_dir = Path().cwd() / "adv_poison_dataset"

        LOGGER.info("Copying original dataset.")
        if poison_deployment_method == "add":
            shutil.copytree(data_dir, adv_data_dir)
            LOGGER.info("Adding poisoned images.")
            copy_poisoned_images(
                src=poison_images_dir / target_class_name,
                dst=adv_data_dir / target_class_name,
                num_poisoned_images=num_poisoned_images,
            )
        elif poison_deployment_method == "replace":
            shutil.copytree(data_dir, adv_data_dir)
            LOGGER.info("Replacing original images with poisoned counterparts.")
            poison_class_dir = adv_data_dir / target_class_name

            for object in os.listdir(poison_class_dir):
                if os.path.isfile(poison_class_dir / object):
                    file_id = object.split("poisoned_")[-1]
                    os.remove(poison_class_dir / file_id)

            copy_poisoned_images(
                src=poison_images_dir / target_class_name,
                dst=adv_data_dir / target_class_name,
                num_poisoned_images=num_poisoned_images,
            )

        adv_dataset_tar = Path().cwd() / "adversarial_poison_dataset.tar.gz"

        with tarfile.open(adv_dataset_tar, "w:gz") as f:
            f.add(str(adv_data_dir.resolve()), arcname=adv_data_dir.name)

        LOGGER.info("Log adversarial images", filename=adv_dataset_tar.name)
        mlflow.log_artifact(str(adv_dataset_tar))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    deploy_poison()
