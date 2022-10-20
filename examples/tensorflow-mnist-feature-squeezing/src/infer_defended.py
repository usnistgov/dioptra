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

from data import create_image_dataset, download_image_archive
from log import configure_stdlib_logger, configure_structlog_logger
from models import load_model_in_registry
from tensorflow.keras.preprocessing.image import save_img
from art.defences.preprocessor import FeatureSqueezing


LOGGER = structlog.get_logger()


def save_adv_batch(adv_batch, adv_data_dir, y, clean_filenames, class_names_list):
    for batch_image_num, adv_image in enumerate(adv_batch):
        out_label = class_names_list[y[batch_image_num]]
        adv_image_path = (
            adv_data_dir
            / f"{out_label}"
            / f"adv_{clean_filenames[batch_image_num].name}"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


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
    help="MLFlow Run ID of a successful fgm attack",
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
    default=32,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
@click.option(
    "--bit-depth",
    type=click.INT,
    help="Color Depth squeezing in bits. Default 8. 1 = monochrome",
    default=8,
)
def infer_adversarial(run_id, model, model_architecture, batch_size, seed, bit_depth):
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
        bit_depth=bit_depth,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    dataset_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)
    defense = FeatureSqueezing(bit_depth=bit_depth, clip_values=(0.0, 1.0))
    with mlflow.start_run() as _:
        adv_testing_tar_name = "testing_adversarial_fgm.tar.gz"
        adv_testing_data_dir = Path.cwd() / "adv_testing"

        image_size = (28, 28)
        if model_architecture == "alex_net":
            image_size = (224, 224)

        adv_testing_tar_path = download_image_archive(
            run_id=run_id, archive_path=adv_testing_tar_name
        )

        with tarfile.open(adv_testing_tar_path, "r:gz") as f:
            
            import os
            
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(f, path=Path.cwd())

        adv_ds = create_image_dataset(
            data_dir=str(adv_testing_data_dir.resolve()),
            subset=None,
            validation_split=None,
            image_size=image_size,
            seed=dataset_seed,
        )

    data_flow = adv_ds

    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
    distance_metrics_ = {"image": [], "label": []}
    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Applying Defense",
            attack="fgm",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch = x

        adv_batch_defend, _ = defense(adv_batch)
        save_adv_batch(
            adv_batch_defend,
            adv_testing_data_dir,
            y_int,
            clean_filenames,
            class_names_list,
        )

    adv_ds_defend = create_image_dataset(
        data_dir=str(adv_testing_data_dir.resolve()),
        subset=None,
        validation_split=None,
        image_size=image_size,
        seed=dataset_seed,
    )

    classifier = load_model_in_registry(model=model)
    evaluate_classification_metrics(classifier=classifier, adv_ds=adv_ds_defend)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    infer_adversarial()
