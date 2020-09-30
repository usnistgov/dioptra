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
import numpy as np
import random
from log import configure_stdlib_logger, configure_structlog_logger
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from art.attacks.evasion import AdversarialPatch
from art.estimators.classification import KerasClassifier
from models import load_model_in_registry
from tensorflow.keras.preprocessing.image import save_img


LOGGER = structlog.get_logger()


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted datasets (in container)",
)
@click.option(
    "--patch-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for patch dataset.",
)
@click.option(
    "--out-dir",
    type=click.Path(
        exists=False
    ),
    help ="Root directory for storing patched image results.",
    default = "/out/data",
)
@click.option(
    "--model", type=click.STRING, help="Name of model to load from registry",
)
@click.option(
     "--patch-deployment-method",
     type=click.Choice(["corrupt", "augment", "patches-only"], case_sensitive=False),
     default="augment-original-images",
     help="Deployment method for creating patched dataset. " 
          "If set to corrupt, patched images will replace a portion of original images. " 
          "If set to augment, patched images will be created with a copy of the original dataset. "
          "If set to patches only, no original images will be included.",
 )
@click.option(
    "--patch-application-rate",
    type=click.FLOAT,
    help=" The fraction of images receiving an adversarial patch. "
         "Values greater than 1 or less than 0 will use the entire dataset.",
    default=1.0,
)
@click.option(
    "--patch-scale",
    type=click.FLOAT,
    help = " The scale of the patch to apply to images. ",
    default=0.4,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Image batch size to use for patch deployment.",
    default=32,
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
def deploy_patches(data_dir, patch_dir, out_dir, model, patch_deployment_method,
                   patch_application_rate, patch_scale, batch_size, rotation_max, scale_min, scale_max):
    # MNIST data parameters.
    image_size = (28, 28)
    color_mode = 'grayscale'
    label_mode = 'categorical'
    rescale = 1.0/255.0

    LOGGER.info(
        "Execute MLFlow entry point", entry_point="deploy_patches", data_dir=data_dir,
    )
    model = "mnist_le_net/1"

    with mlflow.start_run() as _:
        data_dir = Path(data_dir).resolve()
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        adv_data_dir = Path(out_dir).resolve()
        patch_dir = Path(patch_dir)
        patch_list = np.load((patch_dir / "patch_list.npy").resolve())
        keras_model = load_model_in_registry(model=model)
        classifier = KerasClassifier(model=keras_model, clip_values=(0.0, 1.0))
        attack = AdversarialPatch(classifier=classifier, batch_size=batch_size,
                                  rotation_max=rotation_max, scale_min=scale_min, scale_max=scale_max)

        if patch_application_rate <= 0 or patch_application_rate >= 1.0:
            validation_split = None
            subset = None
        else:
            validation_split = 1.0 - patch_application_rate
            subset = 'training'

        data_generator = ImageDataGenerator(rescale=rescale, validation_split=validation_split)

        data_flow = data_generator.flow_from_directory(
                directory=data_dir,
                target_size=image_size,
                color_mode=color_mode,
                class_mode=label_mode,
                batch_size=batch_size,
                shuffle=False,
                subset=subset
        )

        class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
        num_images = data_flow.n

        # Apply patch over test set.
        for batch_num, (x, y) in enumerate(data_flow):
            if batch_num >= num_images // batch_size:
                break
            LOGGER.info("Attacking data batch", batch_num=batch_num)
            patch = random.sample(list(patch_list), 1)[0]
            y_int = np.argmax(y, axis=1)
            if patch_scale > 0:
                adv_batch = attack.apply_patch(x, scale=patch_scale, patch_external=patch)
            else:
                adv_batch = attack.apply_patch(x, patch_external=patch)
            save_adv_batch(class_names_list, adv_batch, batch_size, batch_num, adv_data_dir, y_int)

        if (patch_deployment_method == "augment" or
           (patch_deployment_method == "corrupt" and validation_split is not None)):
            if patch_deployment_method == "augment":
                data_generator = ImageDataGenerator(rescale=rescale)
                data_flow = data_generator.flow_from_directory(
                    directory=data_dir,
                    target_size=image_size,
                    color_mode=color_mode,
                    class_mode=label_mode,
                    batch_size=batch_size,
                    shuffle=False,
                )
            if patch_deployment_method == "corrupt" and validation_split is not None:
                data_flow = data_generator.flow_from_directory(
                    directory=data_dir,
                    target_size=image_size,
                    color_mode=color_mode,
                    class_mode=label_mode,
                    batch_size=batch_size,
                    shuffle=False,
                    subset='validation'
                )
            class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
            num_images = data_flow.n
            # Apply patch over test set.
            for batch_num, (x, y) in enumerate(data_flow):
                y_int = np.argmax(y, axis=1)
                if batch_num >= num_images // batch_size:
                    break
                LOGGER.info("Saving regular image batch", batch_num=batch_num)
                save_reg_batch(class_names_list, x, batch_size, batch_num, adv_data_dir, y_int)


def save_adv_batch(class_names_list, adv_batch, batch_size, batch_num, adv_data_dir, y):
    for batch_image_num, adv_image in enumerate(adv_batch):
        outfile = class_names_list[y[batch_image_num]]
        adv_image_path = (
            adv_data_dir
            / f"{outfile}"
            / f"adv{str(batch_size * batch_num + batch_image_num).zfill(5)}.png"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


def save_reg_batch(class_names_list, adv_batch, batch_size, batch_num, adv_data_dir, y):
    for batch_image_num, adv_image in enumerate(adv_batch):
        outfile = class_names_list[y[batch_image_num]]
        adv_image_path = (
            adv_data_dir
            / f"{outfile}"
            / f"reg{str(batch_size * batch_num + batch_image_num).zfill(5)}.png"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    deploy_patches()
