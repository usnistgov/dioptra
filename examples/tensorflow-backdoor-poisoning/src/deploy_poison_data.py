#!/usr/bin/env python
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.

import os
from pathlib import Path
from typing import Dict, List

import click
import mlflow
import numpy as np
import structlog
from attacks_poison_updated import create_adversarial_poison_data
from prefect import Flow, Parameter, task
from prefect.utilities.logging import get_logger as get_prefect_logger
from registry_art_updated import load_wrapped_tensorflow_keras_classifier
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)
from mitre.securingai.sdk.utilities.contexts import plugin_dirs
from mitre.securingai.sdk.utilities.logging import (
    StderrLogStream,
    StdoutLogStream,
    attach_stdout_stream_handler,
    clear_logger_handlers,
    configure_structlog,
    set_logging_level,
)

_PLUGINS_IMPORT_PATH: str = "securingai_builtins"
DISTANCE_METRICS: List[Dict[str, str]] = [
    {"name": "l_infinity_norm", "func": "l_inf_norm"},
    {"name": "l_1_norm", "func": "l_1_norm"},
    {"name": "l_2_norm", "func": "l_2_norm"},
    {"name": "cosine_similarity", "func": "paired_cosine_similarities"},
    {"name": "euclidean_distance", "func": "paired_euclidean_distances"},
    {"name": "manhattan_distance", "func": "paired_manhattan_distances"},
    {"name": "wasserstein_distance", "func": "paired_wasserstein_distances"},
]

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def _map_norm(ctx, param, value):
    norm_mapping: Dict[str, float] = {"inf": np.inf, "1": 1, "2": 2}
    processed_norm: float = norm_mapping[value]

    return processed_norm


def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))


def _coerce_int_to_bool(ctx, param, value):
    return bool(int(value))


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
    "--poison-tar-name",
    type=click.STRING,
    default="adversarial_poison.tar.gz",
    help="Name of input tarfile artifact containing poisoned images.",
)
@click.option(
    "--poison-data-dir",
    type=click.STRING,
    default="adv_poison_data",
    help="Directory for input poisoned images.",
)
@click.option(
    "--adv-tar-name",
    type=click.STRING,
    default="adversarial_poison_dataset.tar.gz",
    help="Name of output tarfile artifact containing poisoned images.",
)
@click.option(
    "--adv-data-dir",
    type=click.STRING,
    default="adv_poison_dataset",
    help="Directory for output poisoned images.",
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def deploy_poison(
    data_dir,
    run_id,
    poison_deployment_method,
    num_poisoned_images,
    poison_tar_name,
    poison_data_dir,
    adv_tar_name,
    adv_data_dir,
    seed,
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="deploy_poison",
        run_id=run_id,
        data_dir=data_dir,
        poison_deployment_method=poison_deployment_method,
        num_poisoned_images=num_poisoned_images,
        poison_tar_name=poison_tar_name,
        poison_data_dir=poison_data_dir,
        adv_tar_name=adv_tar_name,
        adv_data_dir=adv_data_dir,
        seed=seed,
    )

    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = deploy_poison_data()
        state = flow.run(
            parameters=dict(
                run_id=run_id,
                testing_dir=Path(data_dir),
                poison_deployment_method=poison_deployment_method,
                num_poisoned_images=num_poisoned_images,
                poison_tar_name=poison_tar_name,
                poison_data_dir=poison_data_dir,
                adv_tar_name=adv_tar_name,
                adv_data_dir=adv_data_dir,
                seed=seed,
            )
        )
    return state


def deploy_poison_data() -> Flow:
    with Flow("Deploy Adversarial Patches") as flow:
        (
            run_id,
            testing_dir,
            poison_deployment_method,
            num_poisoned_images,
            poison_tar_name,
            poison_data_dir,
            adv_tar_name,
            adv_data_dir,
            seed,
        ) = (
            Parameter("run_id"),
            Parameter("testing_dir"),
            Parameter("poison_deployment_method"),
            Parameter("num_poisoned_images"),
            Parameter("poison_tar_name"),
            Parameter("poison_data_dir"),
            Parameter("adv_tar_name"),
            Parameter("adv_data_dir"),
            Parameter("seed"),
        )
        seed, rng = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "rng", "init_rng", seed=seed
        )
        tensorflow_global_seed = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "sample", "draw_random_integer", rng=rng
        )
        dataset_seed = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "sample", "draw_random_integer", rng=rng
        )
        init_tensorflow_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.backend_configs",
            "tensorflow",
            "init_tensorflow",
            seed=tensorflow_global_seed,
        )

        log_mlflow_params_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_parameters",
            parameters=dict(
                entry_point_seed=seed,
                tensorflow_global_seed=tensorflow_global_seed,
                dataset_seed=dataset_seed,
            ),
        )

        make_directories_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=[adv_data_dir],
        )

        poison_tar_path = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "download_all_artifacts_in_run",
            run_id=run_id,
            artifact_path=poison_tar_name,
        )
        extract_tarfile_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "extract_tarfile",
            filepath=poison_tar_path,
        )

        # TODO: Transfer to load_tensorflow_keras_classifier
        adv_dataset = deploy_poison_images(
            data_dir=testing_dir,
            adv_data_dir=adv_data_dir,
            poison_deployment_method=poison_deployment_method,
            num_poisoned_images=num_poisoned_images,
            upstream_tasks=[make_directories_results, extract_tarfile_results],
        )
        log_dataset_result = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=adv_data_dir,
            tarball_filename=adv_tar_name,
            upstream_tasks=[adv_dataset],
        )
    return flow


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


@task
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def deploy_poison_images(
    data_dir: str,
    adv_data_dir: Union[str, Path],
    poison_deployment_method: str,
    num_poisoned_images: int,
) -> str:
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
    return adv_data_dir


if __name__ == "__main__":
    log_level: str = os.getenv("AI_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("AI_JOB_LOG_AS_JSON") else False

    clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = deploy_poison()
