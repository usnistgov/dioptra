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
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
)
@click.option(
    "--adv-tar-name",
    type=click.STRING,
    default="adversarial_patch.tar.gz",
    help="Name to give to tarfile artifact containing patches",
)
@click.option(
    "--adv-data-dir",
    type=click.STRING,
    default="adv_patches",
    help="Directory for saving adversarial patches",
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
def patch_attack(
    data_dir,
    image_size,
    adv_tar_name,
    adv_data_dir,
    rotation_max,
    scale_min,
    scale_max,
    learning_rate,
    max_iter,
    patch_target,
    num_patch,
    num_patch_gen_samples,
    model_name,
    model_version,
    imagenet_preprocessing,
    seed,
    patch_shape=None,
):

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="gen_patch",
        data_dir=data_dir,
        image_size=image_size,
        adv_tar_name=adv_tar_name,
        adv_data_dir=adv_data_dir,
        model_name=model_name,
        model_version=model_version,
        patch_target=patch_target,
        num_patch=num_patch,
        num_patch_gen_samples=num_patch_gen_samples,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
        learning_rate=learning_rate,
        max_iter=max_iter,
        imagenet_preprocessing=imagenet_preprocessing,
        seed=seed,
    )

    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = init_gen_patch_flow()
        state = flow.run(
            parameters=dict(
                testing_dir=Path(data_dir),
                image_size=image_size,
                adv_tar_name=adv_tar_name,
                adv_data_dir=(Path.cwd() / adv_data_dir).resolve(),
                model_name=model_name,
                model_version=model_version,
                patch_target=patch_target,
                num_patch=num_patch,
                num_patch_gen_samples=num_patch_gen_samples,
                rotation_max=rotation_max,
                scale_min=scale_min,
                scale_max=scale_max,
                learning_rate=learning_rate,
                max_iter=max_iter,
                patch_shape=patch_shape,
                imagenet_preprocessing=imagenet_preprocessing,
                seed=seed,
            )
        )
    return state


def init_gen_patch_flow() -> Flow:
    with Flow("Fast Gradient Method") as flow:
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
            learning_rate,
            max_iter,
            patch_target,
            num_patch,
            num_patch_gen_samples,
            imagenet_preprocessing,
            patch_shape,
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
            Parameter("learning_rate"),
            Parameter("max_iter"),
            Parameter("patch_target"),
            Parameter("num_patch"),
            Parameter("num_patch_gen_samples"),
            Parameter("imagenet_preprocessing"),
            Parameter("patch_shape"),
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
        make_directories_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=[adv_data_dir],
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
            f"{_PLUGINS_IMPORT_PATH}.registry",
            "art",
            "load_wrapped_tensorflow_keras_classifier",
            name=model_name,
            version=model_version,
            clip_values=clip_values,
            imagenet_preprocessing=imagenet_preprocessing,
            upstream_tasks=[init_tensorflow_results],
        )
        patch_dir = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_patch_plugins",
            "attacks_patch",
            "create_adversarial_patches",
            data_dir=testing_dir,
            keras_classifier=keras_classifier,
            adv_data_dir=adv_data_dir,
            image_size=image_size,
            rescale=rescale,
            patch_target=patch_target,
            num_patch=num_patch,
            num_patch_samples=num_patch_gen_samples,
            rotation_max=rotation_max,
            scale_min=scale_min,
            scale_max=scale_max,
            learning_rate=learning_rate,
            max_iter=max_iter,
            patch_shape=patch_shape,
            upstream_tasks=[make_directories_results],
        )
        log_evasion_dataset_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=adv_data_dir,
            tarball_filename=adv_tar_name,
            upstream_tasks=[patch_dir],
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
        _ = patch_attack()
