#!/usr/bin/env python

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

from data import create_image_dataset, download_image_archive
from log import configure_stdlib_logger, configure_structlog_logger
from models import load_model_in_registry
from tensorflow.keras.preprocessing.image import save_img
from art.defences.preprocessor import FeatureSqueezing
from typing import Dict, List

from prefect import Flow, Parameter, task
from mitre.securingai import pyplugs
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


def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))


LOGGER = structlog.get_logger()

"""
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
"""


@click.command()
@click.option(
    "--run-id", type=click.STRING, help="MLFlow Run ID of a successful fgm attack",
)
@click.option(
    "--model", type=click.STRING, help="Name of model to load from registry",
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
    "--seed", type=click.INT, help="Set the entry point rng seed", default=-1,
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
    "--model-version", type=click.STRING, default="1",
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
        """
        keras_classifier = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.registry",
            "art",
            "load_wrapped_tensorflow_keras_classifier",
            name=model,
            version=model_version,
            upstream_tasks=[init_tensorflow_results],
        )
        """
        distance_metrics_list = pyplugs.call_task(
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

        feature_squeeze = pyplugs.call_task(
            "src",
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
        """
        log_evasion_dataset_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=data_dir,
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
        """
    return flow


if __name__ == "__main__":
    log_level: str = os.getenv("AI_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("AI_JOB_LOG_AS_JSON") else False

    #   clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = feature_squeeze()
