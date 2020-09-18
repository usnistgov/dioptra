#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()
tf.config.threading.set_intra_op_parallelism_threads(0)
tf.config.threading.set_inter_op_parallelism_threads(0)

import click
import mlflow
import mlflow.tensorflow
import structlog
from pathlib import Path

from attacks import create_adversarial_patch_dataset
from data import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger


LOGGER = structlog.get_logger()


def evaluate_metrics(classifier, adv_ds):
    result = classifier.model.evaluate(adv_ds)
    adv_metrics = dict(zip(classifier.model.metrics_names, result))
    LOGGER.info("adversarial dataset metrics", **adv_metrics)
    for metric_name, metric_value in adv_metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help ="Root directory for ImageNet test sets.",
    default = "/nfs/data/ImageNet-Kaggle-2017/images/ILSVRC/Data/CLS-LOC",
)
@click.option(
    "--dataset-name",
    type=click.STRING,
    default = "val-sorted-5000",
    help ="ImageNet test set name. Options include: " \
          "\n val-sorted-1000  : 1000 image test set " \
          "\n val-sorted-5000  : 5000 image test set " \
          "\n val-sorted-10000 : 10000 image test set " \
          "\n val-sorted       : 50000 image test set ",
)
@click.option(
    "--model", type=click.STRING, help="Name of model to load from registry",
    default = "keras-model-imagenet-resnet50/1"
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=20,
)
@click.option(
    "--rotation-max",
    type=click.FLOAT,
    help = "The maximum rotation applied to random patches. \
            The value is expected to be in the range `[0, 180]` ",
    default=22.5,
)
@click.option(
    "--scale-min",
    type=click.FLOAT,
    help = "The minimum scaling applied to random patches. \
            The value should be in the range `[0, 1]`, but less than `scale_max` ",
    default=0.1,
)
@click.option(
    "--scale-max",
    type=click.FLOAT,
    help = "The maximum scaling applied to random patches. \
            The value should be in the range `[0, 1]`, but larger than `scale_min.` ",
    default=1.0,
)
@click.option(
    "--scale-patch",
    type=click.FLOAT,
    help = "Fixed scaling applied to random patches. \
            If set to a negative value, random scaling is used instead. ",
    default=0.4,
)
@click.option(
    "--learning-rate",
    type=click.FLOAT,
    help = "The learning rate of the patch attack optimization procedure. ",
    default=5.0,
)
@click.option(
    "--max-iter",
    type=click.INT,
    help = " The number of patch optimization steps. ",
    default=500,
)
@click.option(
    "--patch-target",
    type=click.INT,
    help = " The target class index of the generated patch. Negative numbers will generate randomized id labels.",
    default=-1,
)
@click.option(
    "--num-patch",
    type=click.INT,
    help = " The number of patches generated. Each adversarial image recieves one patch. ",
    default=1,
)
@click.option(
    "--num-patch-gen-samples",
    type=click.INT,
    help = " The number of sample images used to generate each patch. ",
    default=10,
)
@click.option(
    "--max-iter",
    type=click.INT,
    help = " The number of patch optimization steps. ",
    default=500,
)
#@click.option(
#    "--patch-shape",
#    type=click.Tuple([int, int, int]),
#    help = " Shape of adversarial patch. Matches input if set to None.",
#    default=None,
#)
def patch_attack(
    data_dir, dataset_name, model, batch_size, rotation_max, scale_min, scale_max, scale_patch, learning_rate, max_iter, patch_target, num_patch, num_patch_gen_samples, patch_shape = None,
):
    LOGGER.info(
        "Execute MLFlow entry point", entry_point="patch_attack", data_dir=data_dir,
    )

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir) / dataset_name

        adv_data_dir = Path().cwd() / "adv_testing"
        adv_data_dir.mkdir(parents=True, exist_ok=True)

        adv_patch_dir = Path().cwd() / "adv_patches"
        adv_patch_dir.mkdir(parents=True, exist_ok=True)

        image_size = (224, 224)

        classifier = create_adversarial_patch_dataset(
            data_dir=testing_dir,
            model=model,
            adv_data_dir=adv_data_dir.resolve(),
            adv_patch_dir=adv_patch_dir.resolve(),
            batch_size=batch_size,
            image_size=image_size,
            patch_target = patch_target,
            num_patch = num_patch,
            num_patch_samples = num_patch_gen_samples,
            scale_patch=scale_patch,
            rotation_max=rotation_max,
            scale_min=scale_min,
            scale_max=scale_max,
            learning_rate=learning_rate,
            max_iter=max_iter,
            patch_shape=patch_shape
        )

        adv_ds = create_image_dataset(
            data_dir=str(adv_data_dir.resolve()), subset=None, validation_split=None
        )
        evaluate_metrics(classifier=classifier, adv_ds=adv_ds)

        # Save adversarial dataset.
        adv_testing_tar = Path().cwd() / "adv_testing.tar.gz"

        with tarfile.open(adv_testing_tar, "w:gz") as f:
            f.add(str(adv_data_dir.resolve()), arcname=adv_data_dir.name)

        mlflow.log_artifact(str(adv_testing_tar))

        # Save patch set.
        adv_patch_tar = Path().cwd() / "adv_patch.tar.gz"

        with tarfile.open(adv_patch_tar , "w:gz") as f:
            f.add(str(adv_patch_dir.resolve()), arcname=adv_patch_dir.name)

        mlflow.log_artifact(str(adv_patch_tar))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    patch_attack()
