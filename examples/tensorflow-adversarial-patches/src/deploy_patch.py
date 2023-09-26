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
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
)
@click.option(
    "--adv-tar-name",
    type=click.STRING,
    default="adversarial_patch_dataset.tar.gz",
    help="Name of output tarfile artifact containing patched images",
)
@click.option(
    "--adv-data-dir",
    type=click.STRING,
    default="adv_testing",
    help="Directory for output patched images",
)
@click.option(
    "--adv-patch-tar-name",
    type=click.STRING,
    default="adversarial_patch.tar.gz",
    help="Name of input tarfile artifact containing adversarial patches",
)
@click.option(
    "--adv-patch-dir",
    type=click.STRING,
    default="adv_patches",
    help="Directory for input adversarial patches",
)
@click.option(
    "--model-name",
    type=click.STRING,
    help="Name of model to load from registry",
)
@click.option(
    "--model-version",
    type=click.STRING,
    help="Version of model to load from registry",
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
    "--imagenet-preprocessing",
    type=click.BOOL,
    help="If true, initializes model with Imagenet image preprocessing settings.",
    default=False,
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
    image_size,
    adv_tar_name,
    adv_data_dir,
    adv_patch_tar_name,
    adv_patch_dir,
    patch_deployment_method,
    patch_application_rate,
    patch_scale,
    batch_size,
    rotation_max,
    scale_min,
    scale_max,
    model_name,
    model_version,
    imagenet_preprocessing,
    seed,
    patch_shape=None,
):

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="deploy_patch",
        run_id=run_id,
        data_dir=data_dir,
        image_size=image_size,
        adv_tar_name=adv_tar_name,
        adv_data_dir=adv_data_dir,
        adv_patch_tar_name=adv_patch_tar_name,
        adv_patch_dir=adv_patch_dir,
        model_name=model_name,
        model_version=model_version,
        patch_deployment_method=patch_deployment_method,
        patch_application_rate=patch_application_rate,
        patch_scale=patch_scale,
        batch_size=batch_size,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
        imagenet_preprocessing=imagenet_preprocessing,
        seed=seed,
    )

    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = deploy_adversarial_patch()
        state = flow.run(
            parameters=dict(
                testing_dir=Path(data_dir),
                image_size=image_size,
                adv_tar_name=adv_tar_name,
                adv_data_dir=(Path.cwd() / adv_data_dir),
                distance_metrics_filename="distance_metrics.csv",
                model_name=model_name,
                model_version=model_version,
                rotation_max=rotation_max,
                scale_min=scale_min,
                scale_max=scale_max,
                patch_shape=patch_shape,
                seed=seed,
                run_id=run_id,
                adv_patch_tar_name=adv_patch_tar_name,
                adv_patch_dir=(Path.cwd() / adv_patch_dir),
                patch_deployment_method=patch_deployment_method,
                patch_application_rate=patch_application_rate,
                patch_scale=patch_scale,
                batch_size=batch_size,
                imagenet_preprocessing=imagenet_preprocessing,
            )
        )

    return state


def deploy_adversarial_patch() -> Flow:
    with Flow("Deploy Adversarial Patches") as flow:
        (
            testing_dir,
            image_size,
            adv_tar_name,
            adv_data_dir,
            model_name,
            model_version,
            rotation_max,
            scale_min,
            scale_max,
            patch_shape,
            run_id,
            adv_patch_tar_name,
            adv_patch_dir,
            distance_metrics_filename,
            patch_deployment_method,
            patch_application_rate,
            patch_scale,
            batch_size,
            imagenet_preprocessing,
            seed,
        ) = (
            Parameter("testing_dir"),
            Parameter("image_size"),
            Parameter("adv_tar_name"),
            Parameter("adv_data_dir"),
            Parameter("model_name"),
            Parameter("model_version"),
            Parameter("rotation_max"),
            Parameter("scale_min"),
            Parameter("scale_max"),
            Parameter("patch_shape"),
            Parameter("run_id"),
            Parameter("adv_patch_tar_name"),
            Parameter("adv_patch_dir"),
            Parameter("distance_metrics_filename"),
            Parameter("patch_deployment_method"),
            Parameter("patch_application_rate"),
            Parameter("patch_scale"),
            Parameter("batch_size"),
            Parameter("imagenet_preprocessing"),
            Parameter("seed"),
        )
        seed, rng = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH }.random", "rng", "init_rng", seed=seed
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
            dirs=[adv_patch_dir],
        )

        adv_tar_path = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "download_all_artifacts_in_run",
            run_id=run_id,
            artifact_path=adv_patch_tar_name,
        )

        extract_tarfile_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "extract_tarfile",
            filepath=adv_tar_path,
        )

        rescale = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_poisoning_plugins",
            "datasetup",
            "select_rescale_value",
            imagenet_preprocessing=imagenet_preprocessing,
        )

        clip_values = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_poisoning_plugins",
            "datasetup",
            "select_clip_values",
            image_size=image_size,
        )

        log_mlflow_params_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_parameters",
            parameters=dict(
                entry_point_seed=seed,
                tensorflow_global_seed=tensorflow_global_seed,
                dataset_seed=dataset_seed,
                rescale=rescale,
                clip_values=clip_values,
            ),
        )

        keras_classifier = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_patch_plugins",
            "registry_art",
            "load_wrapped_tensorflow_keras_classifier",
            name=model_name,
            version=model_version,
            clip_values=clip_values,
            upstream_tasks=[init_tensorflow_results],
            imagenet_preprocessing=imagenet_preprocessing,
        )

        distance_metrics_list = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.metrics",
            "distance",
            "get_distance_metric_list",
            request=DISTANCE_METRICS,
        )

        distance_metrics = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_patch_plugins",
            "attacks_patch",
            "create_adversarial_patch_dataset",
            data_dir=testing_dir,
            keras_classifier=keras_classifier,
            distance_metrics_list=distance_metrics_list,
            adv_data_dir=adv_data_dir,
            patch_dir=adv_patch_dir,
            image_size=image_size,
            rescale=rescale,
            rotation_max=rotation_max,
            scale_min=scale_min,
            scale_max=scale_max,
            patch_shape=patch_shape,
            batch_size=batch_size,
            patch_deployment_method=patch_deployment_method,
            patch_application_rate=patch_application_rate,
            patch_scale=patch_scale,
            upstream_tasks=[make_directories_results, extract_tarfile_results],
        )
        log_evasion_dataset_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=adv_data_dir,
            tarball_filename=adv_tar_name,
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
        _ = deploy_patch()
