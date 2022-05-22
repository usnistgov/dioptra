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
    default="adversarial_poison.tar.gz",
    help="Name of output tarfile artifact containing poisoned images",
)
@click.option(
    "--adv-data-dir",
    type=click.STRING,
    default="adv_poison_data",
    help="Directory for output poisoned images",
)
@click.option(
    "--target-class",
    type=click.INT,
    help=" The target class index to generate poisoned examples.",
    default=0,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help=" The number of clean sample images per poisoning batch. ",
    default=30,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
@click.option(
    "--poison-fraction",
    type=click.FLOAT,
    help="The fraction of data to be poisoned. Range 0 to 1.",
    default=1.0,
)
@click.option(
    "--label-type",
    type=click.Choice(["train", "training", "test", "testing"], case_sensitive=False),
    default="test",
    help="Sets labels either to original label (test) or poisoned label (train). Non-poisoned images keep their original label.",
)
def poison_attack(
    data_dir,
    image_size,
    adv_tar_name,
    adv_data_dir,
    batch_size,
    target_class,
    poison_fraction,
    label_type,
    seed,
):

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="gen_poison_data",
        data_dir=data_dir,
        image_size=image_size,
        adv_tar_name=adv_tar_name,
        adv_data_dir=adv_data_dir,
        batch_size=batch_size,
        target_class=target_class,
        poison_fraction=poison_fraction,
        label_type=label_type,
        seed=seed,
    )

    if image_size[2] == 3:
        rescale = 1.0
    else:
        rescale = 1.0 / 255

    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = generate_poison_data()
        state = flow.run(
            parameters=dict(
                testing_dir=Path(data_dir),
                image_size=image_size,
                rescale=rescale,
                adv_tar_name=adv_tar_name,
                adv_data_dir=(Path.cwd() / adv_data_dir),
                distance_metrics_filename="distance_metrics.csv",
                batch_size=batch_size,
                target_class=target_class,
                poison_fraction=poison_fraction,
                label_type=label_type,
                seed=seed,
            )
        )
    return state


def generate_poison_data() -> Flow:
    with Flow("Genereate Backdoor Poisoned Data") as flow:
        (
            testing_dir,
            image_size,
            rescale,
            adv_tar_name,
            adv_data_dir,
            distance_metrics_filename,
            batch_size,
            target_class,
            poison_fraction,
            label_type,
            seed,
        ) = (
            Parameter("testing_dir"),
            Parameter("image_size"),
            Parameter("rescale"),
            Parameter("adv_tar_name"),
            Parameter("adv_data_dir"),
            Parameter("distance_metrics_filename"),
            Parameter("batch_size"),
            Parameter("target_class"),
            Parameter("poison_fraction"),
            Parameter("label_type"),
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

        distance_metrics_list = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.metrics",
            "distance",
            "get_distance_metric_list",
            request=DISTANCE_METRICS,
        )

        distance_metrics = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_poisoning_plugins",
            "attacks_poison",
            "create_adversarial_poison_data",
            data_dir=testing_dir,
            distance_metrics_list=distance_metrics_list,
            adv_data_dir=adv_data_dir,
            image_size=image_size,
            rescale=rescale,
            target_class=target_class,
            poison_fraction=poison_fraction,
            label_type=label_type,
            batch_size=batch_size,
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
        _ = poison_attack()
