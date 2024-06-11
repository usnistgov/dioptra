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

import os
from pathlib import Path
from typing import Dict, List

import click
import mlflow
import numpy as np
import sklearn  # noqa: F401
import structlog
from prefect import Flow, Parameter
from prefect.utilities.logging import get_logger as get_prefect_logger
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.utilities.contexts import plugin_dirs
from dioptra.sdk.utilities.logging import (
    StderrLogStream,
    StdoutLogStream,
    attach_stdout_stream_handler,
    clear_logger_handlers,
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
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
)
@click.option(
    "--def-tar-name",
    type=click.STRING,
    default="jpeg_compression_dataset.tar.gz",
    help="Name to give to tarfile artifact containing preprocessed  images",
)
@click.option(
    "--def-data-dir",
    type=click.STRING,
    default="adv_testing",
    help="Directory for saving preprocessed images",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--jpeg-compression-quality",
    type=click.INT,
    help="The image quality, on a scale from 1 (worst) to 95 (best). Values above 95 should be avoided.",
    default=50,
)
@click.option(
    "--jpeg-compression-channels-first",
    type=click.BOOL,
    help="Set channels first or last.",
    default=False,
)
@click.option(
    "--jpeg-compression-apply-fit",
    type=click.BOOL,
    help="Defense applied on images used for training.",
    default=False,
)
@click.option(
    "--jpeg-compression-apply-predict",
    type=click.BOOL,
    help="Defense applied on images used for testing.",
    default=True,
)
@click.option(
    "--dataset-run-id",
    type=click.STRING,
    help="MLFlow Run ID of an updated dataset.",
    default="",
)
@click.option(
    "--dataset-tar-name",
    type=click.STRING,
    help="Name of dataset tarfile.",
    default="adversarial_poison.tar.gz",
)
@click.option(
    "--dataset-name",
    type=click.STRING,
    help="Name of dataset directory.",
    default="adv_poison_data",
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def jpeg_compression(
    image_size,
    def_tar_name,
    def_data_dir,
    batch_size,
    jpeg_compression_quality,
    jpeg_compression_channels_first,
    jpeg_compression_apply_fit,
    jpeg_compression_apply_predict,
    dataset_run_id,
    dataset_tar_name,
    dataset_name,
    seed,
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="jpeg_compression",
        image_size=image_size,
        def_tar_name=def_tar_name,
        def_data_dir=def_data_dir,
        batch_size=batch_size,
        jpeg_compression_quality=jpeg_compression_quality,
        jpeg_compression_channels_first=jpeg_compression_channels_first,
        jpeg_compression_apply_fit=jpeg_compression_apply_fit,
        jpeg_compression_apply_predict=jpeg_compression_apply_predict,
        seed=seed,
        dataset_run_id=dataset_run_id,
        dataset_name=dataset_name,
        dataset_tar_name=dataset_tar_name,
    )

    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = init_jpeg_compression_flow()
        state = flow.run(
            parameters=dict(
                image_size=image_size,
                def_tar_name=def_tar_name,
                def_data_dir=(Path.cwd() / def_data_dir).resolve(),
                distance_metrics_filename="distance_metrics.csv",
                batch_size=batch_size,
                jpeg_compression_quality=jpeg_compression_quality,
                jpeg_compression_channels_first=jpeg_compression_channels_first,
                jpeg_compression_apply_fit=jpeg_compression_apply_fit,
                jpeg_compression_apply_predict=jpeg_compression_apply_predict,
                seed=seed,
                dataset_run_id=dataset_run_id,
                dataset_name=dataset_name,
                dataset_tar_name=dataset_tar_name,
            )
        )

    return state


def init_jpeg_compression_flow() -> Flow:
    with Flow("Fast Gradient Method") as flow:
        (
            image_size,
            def_tar_name,
            def_data_dir,
            distance_metrics_filename,
            batch_size,
            jpeg_compression_quality,
            jpeg_compression_channels_first,
            jpeg_compression_apply_fit,
            jpeg_compression_apply_predict,
            seed,
            dataset_run_id,
            dataset_name,
            dataset_tar_name,
        ) = (
            Parameter("image_size"),
            Parameter("def_tar_name"),
            Parameter("def_data_dir"),
            Parameter("distance_metrics_filename"),
            Parameter("batch_size"),
            Parameter("jpeg_compression_quality"),
            Parameter("jpeg_compression_channels_first"),
            Parameter("jpeg_compression_apply_fit"),
            Parameter("jpeg_compression_apply_predict"),
            Parameter("seed"),
            Parameter("dataset_run_id"),
            Parameter("dataset_name"),
            Parameter("dataset_tar_name"),
        )
        data_tar_path = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "download_all_artifacts_in_run",
            run_id=dataset_run_id,
            artifact_path=dataset_tar_name,
        )

        output_dir = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "extract_tarfile_in_unique_subdir",
            filepath=data_tar_path,
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
        init_tensorflow_results = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.backend_configs",
            "tensorflow",
            "init_tensorflow",
            seed=tensorflow_global_seed,
        )
        make_directories_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=[def_data_dir],
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

        distance_metrics_list = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.metrics",
            "distance",
            "get_distance_metric_list",
            request=DISTANCE_METRICS,
        )
        distance_metrics = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_fgm_plugins",
            "defenses_image_preprocessing",
            "create_defended_dataset",
            def_type="jpeg_compression",
            data_dir=output_dir,
            dataset_name=dataset_name,
            distance_metrics_list=distance_metrics_list,
            def_data_dir=def_data_dir,
            batch_size=batch_size,
            image_size=image_size,
            quality=jpeg_compression_quality,
            channels_first=jpeg_compression_channels_first,
            apply_fit=jpeg_compression_apply_fit,
            apply_predict=jpeg_compression_apply_predict,
            upstream_tasks=[make_directories_results],
        )
        log_evasion_dataset_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=def_data_dir,
            tarball_filename=def_tar_name,
            upstream_tasks=[distance_metrics],
        )
        log_distance_metrics_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_data_frame_artifact",
            data_frame=distance_metrics,
            file_name=distance_metrics_filename,
            file_format="csv.gz",
            file_format_kwargs=dict(index=False),
        )

    return flow


if __name__ == "__main__":
    log_level: str = os.getenv("DIOPTRA_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("DIOPTRA_JOB_LOG_AS_JSON") else False

    clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = jpeg_compression()
