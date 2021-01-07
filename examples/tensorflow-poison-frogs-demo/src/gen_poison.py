#!/usr/bin/env python

import tarfile
import warnings

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import os
from pathlib import Path

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from attacks import create_poisoned_images
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


def create_class_list(imagedir):
    class_names = []
    for item in os.listdir(imagedir):
        if os.path.isdir(imagedir + "/" + item):
            class_names.append(item)
    return sorted(class_names)


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted datasets (in container)",
)
@click.option(
    "--target-image-path",
    type=click.Path(exists=True, file_okay=True, resolve_path=True, readable=True),
    help="The file path for the target image.",
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
    "--learning-rate",
    type=click.FLOAT,
    help="The learning rate of the poison frogs optimization procedure.",
    default=500 * 255.0,
)
@click.option(
    "--decay-coeff",
    type=click.FLOAT,
    help="The learning rate decay coefficient.",
    default=0.5,
)
@click.option(
    "--stopping-tol",
    type=click.FLOAT,
    help="Stop iterations after changes in attacks are less than this threshold.",
    default=1e-10,
)
@click.option(
    "--similarity-coeff",
    type=click.FLOAT,
    help="Similarity coefficient for poison frogs attack. Note, ART suggests larger values than regular Poison Frogs attack.",
    default=256.0,
)
@click.option(
    "--watermark",
    type=click.FLOAT,
    help="The opacity of the watermarked target image. "
    "Negative values will set this option to the default setting.",
    default=-1,
)
@click.option(
    "--obj-threshold",
    type=click.FLOAT,
    help="Stop iterations after changes in objective values are less than this threshold. "
    "Negative values will set this option to the default setting.",
    default=-1,
)
@click.option(
    "--num-old-obj",
    type=click.INT,
    help=" The number of old objective values to store. ",
    default=40,
)
@click.option(
    "--max-iter",
    type=click.INT,
    help=" The max number of attack iterations. ",
    default=120,
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
    "--num-poisoned-batches",
    type=click.INT,
    help=" The number of batches to poison with target image as reference. Negative values will use entire class set.",
    default=-1,
)
@click.option(
    "--feature-layer-index",
    type=click.INT,
    help=" The index of the model layer to collect feature space representations of input images. ",
    default=-1,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def poison_attack(
    data_dir,
    target_image_path,
    model,
    model_architecture,
    learning_rate,
    max_iter,
    decay_coeff,
    stopping_tol,
    similarity_coeff,
    watermark,
    obj_threshold,
    num_old_obj,
    target_class,
    batch_size,
    num_poisoned_batches,
    feature_layer_index,
    seed,
):

    if watermark < 0:
        watermark = None
    if obj_threshold < 0:
        obj_threshold = None

    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="gen_poison",
        data_dir=data_dir,
        model=model,
        model_architecture=model_architecture,
        target_image_path=target_image_path,
        batch_size=batch_size,
        num_poisoned_batches=num_poisoned_batches,
        target_class=target_class,
        feature_layer_index=feature_layer_index,
        max_iter=max_iter,
        learning_rate=learning_rate,
        decay_coeff=decay_coeff,
        obj_threshold=obj_threshold,
        num_old_obj=num_old_obj,
        stopping_tol=stopping_tol,
        similarity_coeff=similarity_coeff,
        watermark=watermark,
        seed=seed,
    )

    target_class = create_class_list(data_dir)[target_class]

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    tf.random.set_seed(tensorflow_global_seed)

    with mlflow.start_run() as _:
        testing_dir = Path(data_dir)
        adv_data_dir = Path().cwd() / "adv_poison_data"
        adv_data_dir.mkdir(parents=True, exist_ok=True)

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

        distance_metrics = create_poisoned_images(
            data_dir=testing_dir,
            adv_data_dir=adv_data_dir.resolve(),
            target_image_path=target_image_path,
            model=model,
            batch_size=batch_size,
            num_poisoned_batches=num_poisoned_batches,
            target_class=target_class,
            feature_layer_index=feature_layer_index,
            image_size=image_size,
            clip_values=clip_values,
            rescale=rescale,
            color_mode=color_mode,
            imagenet_preprocessing=imagenet_preprocessing,
            decay_coeff=decay_coeff,
            obj_threshold=obj_threshold,
            num_old_obj=num_old_obj,
            stopping_tol=stopping_tol,
            similarity_coeff=similarity_coeff,
            watermark=watermark,
            learning_rate=learning_rate,
            max_iter=max_iter,
        )

        adv_poison_tar = Path().cwd() / "adversarial_poison.tar.gz"
        image_perturbation_csv = Path().cwd() / "distance_metrics.csv.gz"

        with tarfile.open(adv_poison_tar, "w:gz") as f:
            f.add(str(adv_data_dir.resolve()), arcname=adv_data_dir.name)

        LOGGER.info("Log adversarial images", filename=adv_poison_tar.name)
        mlflow.log_artifact(str(adv_poison_tar))

        LOGGER.info(
            "Log distance metric distributions", filename=image_perturbation_csv.name
        )
        distance_metrics.to_csv(image_perturbation_csv, index=False)
        mlflow.log_artifact(str(image_perturbation_csv))


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    poison_attack()
