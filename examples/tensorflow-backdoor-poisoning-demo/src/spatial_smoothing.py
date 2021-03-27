#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

from pathlib import Path

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from data import create_image_dataset, download_image_archive
from defenses import create_defended_dataset
from log import configure_stdlib_logger, configure_structlog_logger

LOGGER = structlog.get_logger()


def evaluate_classification_metrics(classifier, adv_ds):
    LOGGER.info("evaluating classification metrics using adversarial images")
    result = classifier.model.evaluate(adv_ds, verbose=0)
    adv_metrics = dict(zip(classifier.model.metrics_names, result))
    LOGGER.info(
        "computation of classification metrics for adversarial images complete",
        **adv_metrics,
    )
    for metric_name, metric_value in adv_metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted datasets (in container)",
)
@click.option(
    "--model",
    type=click.STRING,
    help="Name of model to load from registry",
)
@click.option(
    "--model-architecture",
    type=click.Choice(
        ["shallow_net", "le_net", "alex_net", "resnet50", "vgg16"], case_sensitive=False
    ),
    default="vgg16",
    help="Model architecture",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--spatial-smoothing-window-size",
    type=click.INT,
    help="The size of the sliding window for spatial smoothing defense.",
    default=3,
)
@click.option(
    "--spatial-smoothing-apply-fit",
    type=click.BOOL,
    help="Spatial smoothing applied on images used for training.",
    default=False,
)
@click.option(
    "--spatial-smoothing-apply-predict",
    type=click.BOOL,
    help="Spatial smoothing applied on images used for testing.",
    default=True,
)
@click.option(
    "--load-dataset-from-mlruns",
    type=click.BOOL,
    help="If set to true, instead loads the training and test datasets from a previous poison mlruns.",
    default=False,
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
def spatial_smoothing(
    data_dir,
    model,
    model_architecture,
    batch_size,
    spatial_smoothing_window_size,
    spatial_smoothing_apply_fit,
    spatial_smoothing_apply_predict,
    load_dataset_from_mlruns,
    dataset_run_id,
    dataset_tar_name,
    dataset_name,
    seed,
):

    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="fgm",
        data_dir=data_dir,
        model=model,
        model_architecture=model_architecture,
        batch_size=batch_size,
        spatial_smoothing_window_size=spatial_smoothing_window_size,
        spatial_smoothing_apply_fit=spatial_smoothing_apply_fit,
        spatial_smoothing_apply_predict=spatial_smoothing_apply_predict,
        seed=seed,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:
        if load_dataset_from_mlruns:
            data_dir = Path.cwd() / "dataset" / dataset_name
            data_tar_name = dataset_tar_name
            data_tar_path = download_image_archive(
                run_id=dataset_run_id, archive_path=data_tar_name
            )
            with tarfile.open(data_tar_path, "r:gz") as f:
                f.extractall(path=(Path.cwd() / "dataset"))

        testing_dir = Path(data_dir)
        def_data_dir = Path().cwd() / "adv_testing"

        def_data_dir.mkdir(parents=True, exist_ok=True)
        image_size = (224, 224)
        clip_values = (0, 255)
        rescale = 1.0
        color_mode = "rgb"
        imagenet_preprocessing = True

        mnist_models = ["shallow_net", "le_net", "alex_net"]
        if model_architecture in mnist_models:
            if model_architecture != "alex_net":
                image_size = (28, 28)
            clip_values = (0, 1.0)
            rescale = 1.0 / 255
            color_mode = "grayscale"
            imagenet_preprocessing = False

        distance_metrics = create_defended_dataset(
            data_dir=testing_dir,
            model=model,
            def_data_dir=def_data_dir.resolve(),
            window_size=spatial_smoothing_window_size,
            apply_fit=spatial_smoothing_apply_fit,
            apply_predict=spatial_smoothing_apply_predict,
            batch_size=batch_size,
            image_size=image_size,
            clip_values=clip_values,
            rescale=rescale,
            color_mode=color_mode,
            imagenet_preprocessing=imagenet_preprocessing,
            def_type="spatial_smoothing",
        )

        def_testing_tar = Path().cwd() / "spatial_smoothing_dataset.tar.gz"
        image_perturbation_csv = Path().cwd() / "distance_metrics.csv.gz"

        with tarfile.open(def_testing_tar, "w:gz") as f:
            f.add(str(def_data_dir.resolve()), arcname=def_data_dir.name)

        LOGGER.info("Log spatial smoothing images", filename=def_testing_tar.name)
        mlflow.log_artifact(str(def_testing_tar))

        LOGGER.info(
            "Log distance metric distributions", filename=image_perturbation_csv.name
        )
        distance_metrics.to_csv(image_perturbation_csv, index=False)
        mlflow.log_artifact(str(image_perturbation_csv))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    spatial_smoothing()
