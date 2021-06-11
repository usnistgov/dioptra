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
import pandas as pd
import os
from pathlib import Path


from mitre.securingai import pyplugs
from prefect import task
from typing import Callable, Dict, List, Optional, Tuple, Union
from data import create_image_dataset, download_image_archive
from log import configure_stdlib_logger, configure_structlog_logger
from models import load_model_in_registry
from tensorflow.keras.preprocessing.image import save_img
from mitre.securingai.sdk.utilities.decorators import require_package
from mitre.securingai.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)


try:
    from art.defences.preprocessor import FeatureSqueezing
except ImportError:
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )

LOGGER = structlog.get_logger()


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def feature_squeeze(
    data_dir,
    run_id,
    model,
    model_architecture,
    batch_size,
    seed,
    bit_depth,
    model_version,
    adv_tar_name,
    image_size,
    adv_data_dir,
    data_flow,
):
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="feature_squeeze",
        model=model,
        model_architecture=model_architecture,
        batch_size=batch_size,
        seed=seed,
        bit_depth=bit_depth,
        run_id=run_id,
    )

    batch_size = 32  # There is currently a bug preventing batch size from getting passsed in correctly
    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    dataset_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)
    defense = FeatureSqueezing(bit_depth=bit_depth, clip_values=(0.0, 1.0))
    adv_testing_tar_name = "testing_adversarial_fgm.tar.gz"
    adv_testing_data_dir = Path.cwd() / "adv_testing"
    def_testing_data_dir = Path.cwd() / "def_testing"
    adv_perturbation_tar_name = "distance_metrics.csv.gz"
    #       image_size = (28, 28)
    color_mode = "grayscale"
    LOGGER.info("adv_data_dir: ", path=adv_data_dir)
    LOGGER.info("adv_tar_name: ", path=adv_tar_name)
    if model_architecture == "alex_net" or model_architecture == "mobilenet":
        #            image_size = (224, 224)
        color_mode = "rgb"
    LOGGER.info("Downloading image archive at ", path=adv_testing_tar_name)
    """   
    adv_testing_tar_path = download_image_archive(
        run_id=run_id, archive_path=adv_testing_tar_name
    )
    
       adv_perturbation_tar_path = download_image_archive(
            run_id=run_id, archive_path=adv_data_dir  #adv_perturbation_tar_name
        )
   
    with tarfile.open(adv_testing_tar_path, "r:gz") as f:
        f.extractall(path=Path.cwd())

    adv_ds = create_image_dataset(
        data_dir=str(adv_testing_data_dir.resolve()),
        subset=None,
        validation_split=None,
        image_size=image_size,
        color_mode=color_mode,
        seed=dataset_seed,
        batch_size=batch_size,
    )
    """
    data_flow = data_flow  # dv_data_dir
    #    data_flow = adv_ds
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    num_images = int(num_images)
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
    LOGGER.info("num_images ", path=num_images)
    distance_metrics_ = {"image": [], "label": []}
    df = enumerate(data_flow)

    for batch_num, (x, y) in enumerate(data_flow):
        LOGGER.info("batch_num ", path=batch_num)

        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        y_int = np.argmax(y, axis=1)

        adv_batch = x

        adv_batch_defend, _ = defense(adv_batch)
        _save_adv_batch(
            adv_batch_defend,
            def_testing_data_dir,
            y_int,
            clean_filenames,
            class_names_list,
        )

    testing_dir = Path(data_dir) / "testing"
    adv_data_dir = Path().cwd() / "adv_testing"
    def_data_dir = Path().cwd() / "def_testing"
    adv_data_dir.mkdir(parents=True, exist_ok=True)
    adv_testing_tar = Path().cwd() / "testing_adversarial_fgm.tar.gz"
    image_perturbation_csv = Path().cwd() / "distance_metrics.csv.gz"

    #       distance_metrics = pd.DataFrame(distance_metrics_)

    image_perturbation_csv = Path(data_dir).cwd() / "distance_metrics.csv.gz"
    with tarfile.open(adv_testing_tar, "w:gz") as f:
        f.add(str(def_data_dir.resolve()), arcname=adv_data_dir.name)

    tar = tarfile.open(adv_testing_tar)
    #       LOGGER.info("Saved to : ", dir=adv_testing_tar_path)
    LOGGER.info("Log defended images", filename=adv_testing_tar.name)
    print("Base: ", str(adv_testing_tar))
    print("Name: ", str(adv_testing_tar.name))
    mlflow.log_artifact(str(adv_testing_tar.name))
    #       mlflow.log_artifact(str(adv_perturbation_tar_path))
    LOGGER.info(
        "Log distance metric distributions", filename=image_perturbation_csv.name
    )

    LOGGER.info("Finishing run ID: ", run_id=run_id)
    adv_ds_defend = create_image_dataset(
        data_dir=str(adv_testing_data_dir.resolve()),
        subset=None,
        validation_split=None,
        image_size=image_size,
        color_mode=color_mode,
        seed=dataset_seed,
        batch_size=batch_size,
    )


def _save_adv_batch(adv_batch, adv_data_dir, y, clean_filenames, class_names_list):
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


def _evaluate_classification_metrics(classifier, adv_ds):
    LOGGER.info("evaluating classification metrics using adversarial images")
    result = classifier.evaluate(adv_ds, verbose=0)
    adv_metrics = dict(zip(classifier.metrics_names, result))
    LOGGER.info(
        "computation of classification metrics for adversarial images complete",
        **adv_metrics,
    )
    for metric_name, metric_value in adv_metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)


def _log_distance_metrics(distance_metrics_: Dict[str, List[List[float]]]) -> None:
    distance_metrics_ = distance_metrics_.copy()
    del distance_metrics_["image"]
    del distance_metrics_["label"]
    for metric_name, metric_values_list in distance_metrics_.items():
        metric_values = np.array(metric_values_list)
        mlflow.log_metric(key=f"{metric_name}_mean", value=metric_values.mean())
        mlflow.log_metric(key=f"{metric_name}_median", value=np.median(metric_values))
        mlflow.log_metric(key=f"{metric_name}_stdev", value=metric_values.std())
        mlflow.log_metric(
            key=f"{metric_name}_iqr", value=scipy.stats.iqr(metric_values)
        )
        mlflow.log_metric(key=f"{metric_name}_min", value=metric_values.min())
        mlflow.log_metric(key=f"{metric_name}_max", value=metric_values.max())
        LOGGER.info("logged distance-based metric", metric_name=metric_name)


"""
        classifier = load_model_in_registry(model=model)
        evaluate_classification_metrics(classifier=classifier, adv_ds=adv_ds_defend)
"""
