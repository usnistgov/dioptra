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
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
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
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--eps",
    type=click.FLOAT,
    help="FGM attack step size (input variation)",
    default=0.3,
)
@click.option(
    "--eps-step",
    type=click.FLOAT,
    help="FGM attack step size of input variation for minimal perturbation computation",
    default=0.1,
)
@click.option(
    "--minimal",
    type=click.Choice(["0", "1"]),
    callback=_coerce_int_to_bool,
    help="If 1, compute the minimal perturbation using eps_step for the step size and "
    "eps for the maximum perturbation.",
    default="0",
)
@click.option(
    "--norm",
    type=click.Choice(["inf", "1", "2"]),
    default="inf",
    callback=_map_norm,
    help="FGM attack norm of adversarial perturbation",
)
@click.option(
    "--imagenet-preprocessing",
    type=click.BOOL,
    help="If true, initializes model with Imagenet image preprocessing settings.",
    default=False,
)
@click.option(
    "--target-index",
    type=click.INT,
    help="Class index for targeted attack. If set to a negative value, the fgm attack will be untargeted.",
    default="-1",
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def fgm_attack(
    data_dir,
    image_size,
    adv_tar_name,
    adv_data_dir,
    model_name,
    model_version,
    batch_size,
    eps,
    eps_step,
    minimal,
    norm,
    imagenet_preprocessing,
    target_index,
    seed,
):
    targeted = False
    if target_index >= 0:
        targeted = True
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="fgm",
        data_dir=data_dir,
        image_size=image_size,
        adv_tar_name=adv_tar_name,
        adv_data_dir=adv_data_dir,
        model_name=model_name,
        model_version=model_version,
        batch_size=batch_size,
        eps=eps,
        eps_step=eps_step,
        minimal=minimal,
        targeted=targeted,
        target_index=target_index,
        imagenet_preprocessing=imagenet_preprocessing,
        norm=norm,
        seed=seed,
    )

    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = init_fgm_flow()
        state = flow.run(
            parameters=dict(
                testing_dir=Path(data_dir),
                image_size=image_size,
                adv_tar_name=adv_tar_name,
                adv_data_dir=(Path.cwd() / adv_data_dir).resolve(),
                distance_metrics_filename="distance_metrics.csv",
                model_name=model_name,
                model_version=model_version,
                batch_size=batch_size,
                eps=eps,
                eps_step=eps_step,
                minimal=minimal,
                norm=norm,
                targeted=targeted,
                target_index=target_index,
                imagenet_preprocessing=imagenet_preprocessing,
                seed=seed,
            )
        )

    return state


def init_fgm_flow() -> Flow:
    with Flow("Fast Gradient Method") as flow:
        (
            testing_dir,
            image_size,
            adv_tar_name,
            adv_data_dir,
            distance_metrics_filename,
            model_name,
            model_version,
            batch_size,
            eps,
            eps_step,
            minimal,
            norm,
            targeted,
            target_index,
            imagenet_preprocessing,
            seed,
        ) = (
            Parameter("testing_dir"),
            Parameter("image_size"),
            Parameter("adv_tar_name"),
            Parameter("adv_data_dir"),
            Parameter("distance_metrics_filename"),
            Parameter("model_name"),
            Parameter("model_version"),
            Parameter("batch_size"),
            Parameter("eps"),
            Parameter("eps_step"),
            Parameter("minimal"),
            Parameter("norm"),
            Parameter("targeted"),
            Parameter("target_index"),
            Parameter("imagenet_preprocessing"),
            Parameter("seed"),
        )
        rescale = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_fgm_plugins",
            "data_tensorflow",
            "rescale",
            imagenet_preprocessing=imagenet_preprocessing,
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

        keras_classifier = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.registry",
            "art",
            "load_wrapped_tensorflow_keras_classifier",
            name=model_name,
            version=model_version,
            imagenet_preprocessing=imagenet_preprocessing,
            upstream_tasks=[init_tensorflow_results],
        )

        distance_metrics_list = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.metrics",
            "distance",
            "get_distance_metric_list",
            request=DISTANCE_METRICS,
        )

        distance_metrics = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_fgm_plugins",
            "attacks_fgm",
            "create_adversarial_fgm_dataset",
            data_dir=testing_dir,
            keras_classifier=keras_classifier,
            distance_metrics_list=distance_metrics_list,
            adv_data_dir=adv_data_dir,
            batch_size=batch_size,
            image_size=image_size,
            rescale=rescale,
            eps=eps,
            eps_step=eps_step,
            minimal=minimal,
            norm=norm,
            targeted=targeted,
            target_index=target_index,
            upstream_tasks=[make_directories_results],
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
        _ = fgm_attack()
