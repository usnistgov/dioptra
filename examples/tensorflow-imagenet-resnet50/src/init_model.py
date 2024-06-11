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
from typing import Any, Dict, List

import click
import mlflow
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

_PLUGINS_IMPORT_PATH: str = "dioptra_builtins"
_CUSTOM_PLUGINS_IMPORT_PATH: str = "dioptra_custom"
CALLBACKS: List[Dict[str, Any]] = [
    {
        "name": "EarlyStopping",
        "parameters": {
            "monitor": "val_loss",
            "min_delta": 1e-2,
            "patience": 5,
            "restore_best_weights": True,
        },
    },
]
LOGGER: BoundLogger = structlog.stdlib.get_logger()
PERFORMANCE_METRICS: List[Dict[str, Any]] = [
    {"name": "CategoricalAccuracy", "parameters": {"name": "accuracy"}},
    {"name": "Precision", "parameters": {"name": "precision"}},
    {"name": "Recall", "parameters": {"name": "recall"}},
    {"name": "AUC", "parameters": {"name": "auc"}},
]


def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))


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
    "--model-architecture",
    type=click.Choice(
        ["shallow_net", "le_net", "alex_net", "resnet50", "vgg16"], case_sensitive=False
    ),
    default="le_net",
    help="Model architecture",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use for testing",
    default=32,
)
@click.option(
    "--register-model-name",
    type=click.STRING,
    default="",
    help=(
        "Register the new model under the provided name. If an empty string, "
        "then the model will not be registered."
    ),
)
@click.option(
    "--learning-rate", type=click.FLOAT, help="Model learning rate", default=0.001
)
@click.option(
    "--optimizer",
    type=click.Choice(["Adam", "Adagrad", "RMSprop", "SGD"], case_sensitive=True),
    help="Optimizer to use to train the model",
    default="Adam",
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
def init_model(
    data_dir,
    image_size,
    model_architecture,
    batch_size,
    register_model_name,
    learning_rate,
    optimizer,
    imagenet_preprocessing,
    seed,
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="train",
        data_dir=data_dir,
        image_size=image_size,
        model_architecture=model_architecture,
        batch_size=batch_size,
        register_model_name=register_model_name,
        learning_rate=learning_rate,
        optimizer=optimizer,
        imagenet_preprocessing=imagenet_preprocessing,
        seed=seed,
    )

    with mlflow.start_run() as active_run:
        flow: Flow = init_train_flow()
        state = flow.run(
            parameters=dict(
                active_run=active_run,
                testing_dir=Path(data_dir),
                image_size=image_size,
                model_architecture=model_architecture,
                batch_size=batch_size,
                register_model_name=register_model_name,
                learning_rate=learning_rate,
                optimizer_name=optimizer,
                imagenet_preprocessing=imagenet_preprocessing,
                seed=seed,
            )
        )
    return state


def init_train_flow() -> Flow:
    with Flow("Train Model") as flow:
        (
            active_run,
            testing_dir,
            image_size,
            model_architecture,
            batch_size,
            register_model_name,
            learning_rate,
            optimizer_name,
            imagenet_preprocessing,
            seed,
        ) = (
            Parameter("active_run"),
            Parameter("testing_dir"),
            Parameter("image_size"),
            Parameter("model_architecture"),
            Parameter("batch_size"),
            Parameter("register_model_name"),
            Parameter("learning_rate"),
            Parameter("optimizer_name"),
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
        optimizer = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.evaluation",
            "tensorflow",
            "get_optimizer",
            optimizer=optimizer_name,
            learning_rate=learning_rate,
            upstream_tasks=[init_tensorflow_results],
        )
        metrics = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.evaluation",
            "tensorflow",
            "get_performance_metrics",
            metrics_list=PERFORMANCE_METRICS,
            upstream_tasks=[init_tensorflow_results],
        )
        callbacks_list = pyplugs.call_task(  # noqa: F841
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.evaluation",
            "tensorflow",
            "get_model_callbacks",
            callbacks_list=CALLBACKS,
            upstream_tasks=[init_tensorflow_results],
        )
        testing_ds = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_fgm_plugins",
            "data_tensorflow",
            "create_image_dataset",
            data_dir=testing_dir,
            subset=None,
            image_size=image_size,
            seed=dataset_seed + 1,
            rescale=rescale,
            validation_split=None,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
            imagenet_preprocessing=imagenet_preprocessing,
        )
        n_classes = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.data",
            "tensorflow",
            "get_n_classes_from_directory_iterator",
            ds=testing_ds,
        )
        classifier = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_fgm_plugins",
            "estimators_keras_classifiers",
            "init_classifier",
            model_architecture=model_architecture,
            optimizer=optimizer,
            metrics=metrics,
            input_shape=image_size,
            n_classes=n_classes,
            upstream_tasks=[init_tensorflow_results],
            training=False,
        )
        classifier_performance_metrics = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.evaluation",
            "tensorflow",
            "evaluate_metrics_tensorflow",
            classifier=classifier,
            dataset=testing_ds,
        )
        log_classifier_performance_metrics_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_metrics",
            metrics=classifier_performance_metrics,
        )
        model_storage = pyplugs.call_task(  # noqa: F841
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.custom_fgm_plugins",
            "tensorflow",
            "register_init_model",
            model=classifier,
            active_run=active_run,
            name=register_model_name,
            model_dir="model",
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
        _ = init_model()
