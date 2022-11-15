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

LOGGER: BoundLogger = structlog.stdlib.get_logger()

def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))
def _coerce_comma_separated_floats(ctx, param, value):
    return tuple(float(x.strip()) for x in value.split(","))
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
    "--adv-data-dir",
    type=click.STRING,
    help="Output location for patched images",
)
@click.option(
    "--adv-patch-dir",
    type=click.STRING,
    help="Output location for patch",
)
@click.option(
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
)
@click.option(
    "--model-loc",
    type=click.STRING,
    help="Model Location",
)
@click.option(
    "--patch-shape",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the patch",
)
@click.option(
    "--patch-location",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Location of patch on image",
)
@click.option(
    "--crop-range",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Crop Range for Attack",
)
@click.option(
    "--brightness-range",
    type=click.STRING,
    callback=_coerce_comma_separated_floats,
    help="Brightness Range for Attack",
)
@click.option(
    "--rotation-weights",
    type=click.STRING,
    callback=_coerce_comma_separated_floats,
    help="Rotation Weights for Attack",
)
@click.option(
    "--sample-size",
    type=click.INT,
    help="Number of test images to consider in one iteration of attack",
    default=1,
)
@click.option(
    "--learning-rate", 
    type=click.FLOAT,
    help="Learning Rate for Attack", 
    default=0.1
)
@click.option(
    "--lr-decay-size", 
    type=click.FLOAT,
    help="Learning Rate Decay Size for Attack", 
    default=.95
)
@click.option(
    "--lr-decay-schedule", 
    type=click.FLOAT,
    help="Learning Rate Decay Schedule for Attack", 
    default=5000
)
@click.option(
    "--momentum", 
    type=click.FLOAT,
    help="Momentum for Attack", 
    default=0.9
)
@click.option(
    "--max-iter",
    type=click.INT,
    help="number of iterations to perform on patch generation",
    default=30,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use",
    default=10,
)
@click.option(
    "--targeted",
    type=click.Choice(["0", "1"]),
    help="Targeted Attack",
    callback=_coerce_int_to_bool,
    default="0"
)
@click.option(
    "--verbose",
    type=click.Choice(["0", "1"]),
    callback=_coerce_int_to_bool,
    default="1",
    help="Verbose"
)
@click.option(
    "--detection-score-cutoff", 
    type=click.FLOAT,
    help="Minimum confidence for prediction to display on the output", 
    default=0.5
)


def attack(
    data_dir,
    adv_data_dir,
    adv_patch_dir,
    image_size,
    model_loc,
    patch_shape,
    patch_location,
    crop_range,
    brightness_range,
    rotation_weights,
    sample_size,
    learning_rate,
    lr_decay_size,
    lr_decay_schedule,
    momentum,
    max_iter,
    batch_size,
    targeted,
    verbose,
    detection_score_cutoff
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="attack",
        data_dir=data_dir,
        adv_data_dir=adv_data_dir,
        adv_patch_dir=adv_patch_dir,
        image_size=image_size,
        model_loc=model_loc,
        patch_shape=patch_shape,
        patch_location=patch_location,
        crop_range=crop_range,
        brightness_range=brightness_range,
        rotation_weights=rotation_weights,
        sample_size=sample_size,
        learning_rate=learning_rate,
        lr_decay_size=lr_decay_size,
        lr_decay_schedule=lr_decay_schedule,
        momentum=momentum,
        max_iter=max_iter,
        batch_size=batch_size,
        targeted=targeted
    )


    with mlflow.start_run() as active_run:
        flow: Flow = init_attack_flow()
        state = flow.run(
            parameters=dict(
                testing_dir=Path(data_dir) / "testing",
                adv_data_dir=(Path.cwd() / adv_data_dir).resolve(),
                adv_patch_dir=(Path.cwd() / adv_patch_dir).resolve(),
                image_size=image_size,
                model_loc=model_loc,
                patch_shape=patch_shape,
                patch_location=patch_location,
                crop_range=crop_range,
                brightness_range=brightness_range,
                rotation_weights=rotation_weights,
                sample_size=sample_size,
                learning_rate=learning_rate,
                lr_decay_size=lr_decay_size,
                lr_decay_schedule=lr_decay_schedule,
                momentum=momentum,
                max_iter=max_iter,
                batch_size=batch_size,
                targeted=targeted,
                verbose=verbose,
                detection_score_cutoff=detection_score_cutoff,
            )
        )

    return state


def init_attack_flow() -> Flow:
    with Flow("Attack") as flow:
        (
            testing_dir,
            adv_data_dir,
            adv_patch_dir,
            image_size,
            model_loc,
            patch_shape,
            patch_location,
            crop_range,
            brightness_range,
            rotation_weights,
            sample_size,
            learning_rate,
            lr_decay_size,
            lr_decay_schedule,
            momentum,
            max_iter,
            batch_size,
            targeted,
            verbose,
            detection_score_cutoff,
        ) = (
            Parameter("testing_dir"),
            Parameter("adv_data_dir"),
            Parameter("adv_patch_dir"),
            Parameter("image_size"),
            Parameter("model_loc"),
            Parameter("patch_shape"),
            Parameter("patch_location"),
            Parameter("crop_range"),
            Parameter("brightness_range"),
            Parameter("rotation_weights"),
            Parameter("sample_size"),
            Parameter("learning_rate"),
            Parameter("lr_decay_size"),
            Parameter("lr_decay_schedule"),
            Parameter("momentum"),
            Parameter("max_iter"),
            Parameter("batch_size"),
            Parameter("targeted"),
            Parameter("verbose"),
            Parameter("detection_score_cutoff")
        )

        classifier = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "load_model",
            "load_model",
            model_loc=model_loc
        )
        
        dataset = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "load_dataset",
            "load_dataset",
            data_dir=testing_dir,
            image_size=image_size
        )
        
        attack = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "robust_dpatch",
            "robust_dpatch",
            frcnn=classifier,
            patch_shape=patch_shape,
            patch_location=patch_location,
            crop_range=crop_range,
            brightness_range=brightness_range,
            rotation_weights=rotation_weights,
            sample_size=sample_size,
            learning_rate=learning_rate,
            lr_decay_size=lr_decay_size,
            lr_decay_schedule=lr_decay_schedule,
            momentum=momentum,
            max_iter=max_iter,
            batch_size=batch_size,
            targeted=targeted,
            verbose=verbose
        )
        patch = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "robust_dpatch",
            "generate",
            attack=attack,
            imgs=dataset,
        )
        adv_testing_dir = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=[adv_data_dir],
        )
        adv_patch_save_dir = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=[adv_patch_dir]
        )
        patch_saved = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "robust_dpatch",
            "save_img",
            patch,
            "patch.png",
            adv_patch_dir,
            upstream_tasks=[adv_patch_save_dir]
        )
        classifier_untouched = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "load_model",
            "load_model",
            model_loc=model_loc
        )        
        patched_imgs = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "robust_dpatch",
            "apply_patches",
            attack,
            dataset,
            patch,
        )
        test_patches = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "robust_dpatch",
            "test_patches",
            classifier_untouched,
            patched_imgs,
            adv_data_dir,
            "patched",
            score_cutoff=detection_score_cutoff,
            upstream_tasks=[adv_testing_dir]
        )
        test_patches = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.rcnn",
            "robust_dpatch",
            "test_patches",
            classifier_untouched,
            dataset,
            adv_data_dir,
            "orig",
            score_cutoff=detection_score_cutoff,
            upstream_tasks=[adv_testing_dir]
        )

        log_patch_applied_dataset_result = pyplugs.call_task( 
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=adv_data_dir,
            tarball_filename="patch_applied.tar.gz",
            upstream_tasks=[test_patches],
        )
        log_patch_result = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=adv_patch_dir,
            tarball_filename="patch.tar.gz",
            upstream_tasks=[patch_saved],
        )

        LOGGER.info(patch)

    return flow


if __name__ == "__main__":
    log_level: str = os.getenv("AI_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("AI_JOB_LOG_AS_JSON") else False

    clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = attack()
