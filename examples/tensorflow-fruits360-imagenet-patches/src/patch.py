#!/usr/bin/env python

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
    help ="Root directory for Fruits360 test sets.",
    default = "/nfs/data/Fruits360-Kaggle-2019/fruits-360/Test",
)
@click.option(
    "--out-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help ="Root directory for storing patch results.",
    default = "/out/data",
)
@click.option(
    "--model", type=click.STRING, help="Name of model to load from registry",
    default = "fruits360_vgg16/None"
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
    help = " The number of patches generated. Each adversarial image receives one patch. ",
    default=1,
)
@click.option(
    "--num-patch-gen-samples",
    type=click.INT,
    help = " The number of sample images used to generate each patch. ",
    default=10,
)
@click.option(
    "--imagenet-preprocessing",
    type=click.BOOL,
    help = "Specifies whether to include ImageNet image preprocessing. ",
    default=False,
)
def patch_attack(
    data_dir, out_dir, model, rotation_max, scale_min, scale_max,
    learning_rate, max_iter, patch_target, num_patch, num_patch_gen_samples, imagenet_preprocessing,
):
    patch_shape = None
    LOGGER.info(
        "Execute MLFlow entry point", entry_point="patch_attack", data_dir=data_dir,
    )

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir)
        batch_size = num_patch_gen_samples
        adv_patch_dir = Path(out_dir)/ "adv_patches"
        adv_patch_dir.mkdir(parents=True, exist_ok=True)

        image_size = (224, 224)

        classifier = create_adversarial_patch_dataset(
            data_dir=testing_dir,
            model=model,
            adv_patch_dir=adv_patch_dir.resolve(),
            imagenet_preprocessing=imagenet_preprocessing,
            batch_size=batch_size,
            image_size=image_size,
            patch_target = patch_target,
            num_patch = num_patch,
            num_patch_samples = num_patch_gen_samples,
            rotation_max=rotation_max,
            scale_min=scale_min,
            scale_max=scale_max,
            learning_rate=learning_rate,
            max_iter=max_iter,
            patch_shape=patch_shape
        )

if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    patch_attack()
