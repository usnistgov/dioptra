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

import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import os
from pathlib import Path
from typing import Dict, List

import click
import mlflow
import numpy as np
import structlog
from prefect import Flow, Parameter

from dioptra import pyplugs
from dioptra.sdk.utilities.contexts import plugin_dirs
from dioptra.sdk.utilities.logging import (
    StderrLogStream,
    StdoutLogStream,
    attach_stdout_stream_handler,
    configure_structlog,
    set_logging_level,
)

_CUSTOM_PLUGINS_IMPORT_PATH: str = "dioptra_custom"
_PLUGINS_IMPORT_PATH: str = "dioptra_builtins"
DISTANCE_METRICS: List[Dict[str, str]] = [
    {"name": "l_infinity_norm", "func": "l_inf_norm"},
    {"name": "l_1_norm", "func": "l_1_norm"},
    {"name": "l_2_norm", "func": "l_2_norm"},
    {"name": "cosine_similarity", "func": "paired_cosine_similarities"},
    {"name": "euclidean_distance", "func": "paired_euclidean_distances"},
    {"name": "manhattan_distance", "func": "paired_manhattan_distances"},
    {"name": "wasserstein_distance", "func": "paired_wasserstein_distances"},
]


def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))


LOGGER = structlog.get_logger()


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
    type=click.Choice(
        ["shallow_net", "le_net", "mobilenet", "alex_net"], case_sensitive=False
    ),
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
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted datasets (in container)",
)
@click.option(
    "--adv-tar-name",
    type=click.STRING,
    default="testing_adversarial_fgm.tar.gz",
    help="Name to give to tarfile artifact containing fgm images",
)
@click.option(
    "--adv-data-dir",
    type=click.STRING,
    default="adv_testing",
    help="Directory for saving fgm images",
)
@click.option(
    "--model-version",
    type=click.STRING,
    default="1",
)
@click.option(
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
)
def feature_squeeze(
    data_dir,
    run_id,
    model,
    model_architecture,
    model_version,
    batch_size,
    seed,
    bit_depth,
    adv_data_dir,
    adv_tar_name,
    image_size,
):

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="feature_squeeze",
        model=model,
        model_architecture=model_architecture,
        batch_size=batch_size,
        seed=seed,
        bit_depth=bit_depth,
    )

    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = init_squeeze_flow()
        state = flow.run(
            parameters=dict(
                run_id=run_id,
                data_dir=data_dir,
                model=model,
                model_version=model_version,
                batch_size=batch_size,
                model_architecture=model_architecture,
                seed=seed,
                bit_depth=bit_depth,
                adv_tar_name=adv_tar_name,
                adv_data_dir=(Path.cwd() / adv_data_dir).resolve(),  # orig: data dir
                image_size=image_size,
            )
        )

    return state


def init_squeeze_flow() -> Flow:
    with Flow("Feature Squeezing") as flow:
        (
            run_id,
            data_dir,
            model,
            model_version,
            batch_size,
            model_architecture,
            seed,
            bit_depth,
            adv_tar_name,
            adv_data_dir,
            image_size,
        ) = (
            Parameter("run_id"),
            Parameter("model_architecture"),
            Parameter("data_dir"),
            Parameter("model"),
            Parameter("model_version"),
            Parameter("batch_size"),
            Parameter("seed"),
            Parameter("bit_depth"),
            Parameter("adv_tar_name"),
            Parameter("adv_data_dir"),
            Parameter("image_size"),
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
        make_directories_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=[adv_data_dir],
        )

        make_directories_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=["def_testing"],
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
        distance_metrics_list = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.metrics",
            "distance",
            "get_distance_metric_list",
            request=DISTANCE_METRICS,
        )
        adv_tar_path = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "download_all_artifacts_in_run",
            run_id=run_id,
            artifact_path=adv_tar_name,
        )
        extract_tarfile_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "extract_tarfile",
            filepath=adv_tar_path,
        )
        adv_ds = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.data",
            "tensorflow",
            "create_image_dataset",
            data_dir=adv_data_dir,  # adv_tar_name,
            subset=None,
            validation_split=None,
            image_size=image_size,
            seed=dataset_seed,
            upstream_tasks=[init_tensorflow_results, extract_tarfile_results],
        )

        feature_squeeze = pyplugs.call_task(  # noqa: F841
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.feature_squeezing",
            "squeeze_plugin",
            "feature_squeeze",
            data_dir=data_dir,
            model=model,
            model_version=model_version,
            model_architecture=model_architecture,
            batch_size=batch_size,
            seed=seed,
            bit_depth=bit_depth,
            run_id=run_id,
            adv_tar_name=adv_tar_name,
            adv_data_dir=adv_data_dir,
            data_flow=adv_ds,
            image_size=image_size,
            upstream_tasks=[make_directories_results],
        )
    return flow


if __name__ == "__main__":
    log_level: str = os.getenv("DIOPTRA_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("DIOPTRA_JOB_LOG_AS_JSON") else False

    #   clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = feature_squeeze()
