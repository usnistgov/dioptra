#!/usr/bin/env python

import warnings
from pathlib import Path
from typing import Tuple

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import random

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from art.attacks.evasion import AdversarialPatch
from art.estimators.classification import KerasClassifier
from metrics import (
    l_inf_norm,
    paired_cosine_similarities,
    paired_euclidean_distances,
    paired_manhattan_distances,
    paired_wasserstein_distances,
)
from models import load_model_in_registry
from tensorflow.keras.preprocessing.image import ImageDataGenerator, save_img

LOGGER = structlog.get_logger()
DISTANCE_METRICS = [
    ("l_infinity_norm", l_inf_norm),
    ("cosine_similarity", paired_cosine_similarities),
    ("euclidean_distance", paired_euclidean_distances),
    ("manhattan_distance", paired_manhattan_distances),
    ("wasserstein_distance", paired_wasserstein_distances),
]


def wrap_keras_classifier(model, clip_values, imagenet_preprocessing):
    keras_model = load_model_in_registry(model=model)
    if imagenet_preprocessing:
        mean_b = 103.939
        mean_g = 116.779
        mean_r = 123.680
        return KerasClassifier(
            model=keras_model,
            clip_values=clip_values,
            preprocessing=([mean_b, mean_g, mean_r], 1),
        )
    else:
        return KerasClassifier(model=keras_model, clip_values=clip_values)


def init_patch(model, batch_size, clip_values, imagenet_preprocessing, **kwargs):
    classifier = wrap_keras_classifier(model, clip_values, imagenet_preprocessing)
    attack = AdversarialPatch(classifier=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


def save_batch(class_names_list, adv_batch, adv_data_dir, y, clean_filenames, type):
    for batch_image_num, adv_image in enumerate(adv_batch):
        outfile = class_names_list[y[batch_image_num]]
        adv_image_path = (
            adv_data_dir
            / f"{outfile}"
            / f"{type}_{clean_filenames[batch_image_num].name}"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


def save_adv_patch(patch_list, mask_list, id_list, num_patch, adv_patch_dir):
    patch_list = np.array(patch_list)
    mask_list = np.array(mask_list)
    id_list = np.array(id_list)

    np.save(str(adv_patch_dir) + "/patch_list", patch_list)
    np.save(str(adv_patch_dir) + "/patch_mask_list", mask_list)
    np.save(str(adv_patch_dir) + "/patch_id_list", id_list)

    for patch_id in range(num_patch):
        patch = patch_list[patch_id]
        mask = mask_list[patch_id]

        # Combine patch with mask.
        masked_patch = patch * mask

        # Save masked patch as image.
        adv_patch_path = adv_patch_dir / f"Patch_{patch_id}.png"

        if not adv_patch_path.parent.exists():
            adv_patch_path.parent.mkdir(parents=True)

        save_img(path=str(adv_patch_path), x=masked_patch)


def evaluate_distance_metrics(
    clean_filenames, distance_metrics_, clean_batch, adv_batch
):
    LOGGER.debug("evaluate image perturbations using distance metrics")
    distance_metrics_["image"].extend([x.name for x in clean_filenames])
    distance_metrics_["label"].extend([x.parent for x in clean_filenames])
    for metric_name, metric in DISTANCE_METRICS:
        distance_metrics_[metric_name].extend(metric(clean_batch, adv_batch))


def log_distance_metrics(distance_metrics_):
    distance_metrics_ = distance_metrics_.copy()
    del distance_metrics_["image"]
    del distance_metrics_["label"]
    for metric_name, metric_values_list in distance_metrics_.items():
        metric_values = np.array(metric_values_list)
        mlflow.log_metric(key=f"{metric_name}_mean", value=metric_values.mean())
        mlflow.log_metric(key=f"{metric_name}_median", value=np.median(metric_values))
        mlflow.log_metric(key=f"{metric_name}_stdev", value=metric_values.std())
        mlflow.log_metric(
            key=f"{metric_name}_iqr", value=scipy.stats.iqr(metric_values)
        )
        mlflow.log_metric(key=f"{metric_name}_min", value=metric_values.min())
        mlflow.log_metric(key=f"{metric_name}_max", value=metric_values.max())
        LOGGER.info("logged distance-based metric", metric_name=metric_name)


def create_adversarial_patches(
    data_dir: str,
    adv_data_dir: str,
    model: str,
    rescale: float = 1.0,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    clip_values: Tuple[float, float] = (0, 255),
    patch_target: int = -1,
    num_patch: int = 1,
    num_patch_samples: int = 10,
    imagenet_preprocessing: bool = True,
    **kwargs,
):

    classifier, attack = init_patch(
        model=model,
        batch_size=batch_size,
        clip_values=clip_values,
        imagenet_preprocessing=imagenet_preprocessing,
        **kwargs,
    )

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    patch_set = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=num_patch_samples,
        shuffle=True,
    )
    # Start by generating adversarial patches.
    target_index = patch_target
    patch_list = []
    mask_list = []
    id_list = []
    n_classes = len(patch_set.class_indices)

    LOGGER.info(
        "Generate adversarial patches",
        attack="patch",
        num_patches=num_patch,
    )

    for batch_num, (x, y) in enumerate(patch_set):
        # Generate random index from available classes.
        if patch_target < 0:
            target_index = random.randint(0, n_classes - 1)
        id_list.append(target_index)
        y_one_hot = np.zeros(n_classes)
        y_one_hot[target_index] = 1.0
        y_target = np.tile(y_one_hot, (x.shape[0], 1))

        if batch_num >= num_patch:
            break

        patch, patch_mask = attack.generate(x=x, y=y_target)
        patch_list.append(patch)
        mask_list.append(patch_mask)

    # Save adversarial patches.
    save_adv_patch(patch_list, mask_list, id_list, num_patch, adv_data_dir)
    LOGGER.info("Adversarial patch generation complete", attack="patch")

    return


def create_adversarial_patch_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: str,
    patch_dir: str,
    patch_application_rate: float,
    rescale: float = 1.0,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    clip_values: Tuple[float, float] = (0, 255),
    patch_deployment_method: str = "augment",
    patch_scale: float = 0.4,
    rotation_max: float = 22.5,
    scale_min: float = 0.1,
    scale_max: float = 1.0,
):
    patch_list = np.load((patch_dir / "patch_list.npy").resolve())

    keras_model = load_model_in_registry(model=model)
    classifier = KerasClassifier(model=keras_model, clip_values=clip_values)
    attack = AdversarialPatch(
        classifier=classifier,
        batch_size=batch_size,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
    )

    if patch_application_rate <= 0 or patch_application_rate >= 1.0:
        validation_split = None
        subset = None
    else:
        validation_split = 1.0 - patch_application_rate
        subset = "training"

    data_generator = ImageDataGenerator(
        rescale=rescale, validation_split=validation_split
    )

    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
        subset=subset,
    )

    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

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

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]
        save_batch(
            class_names_list, adv_batch, adv_data_dir, y_int, clean_filenames, "adv"
        )
        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )

    if patch_deployment_method == "augment" or (
        patch_deployment_method == "corrupt" and validation_split is not None
    ):
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
                subset="validation",
            )
        class_names_list = sorted(
            data_flow.class_indices, key=data_flow.class_indices.get
        )
        img_filenames = [Path(x) for x in data_flow.filenames]
        num_images = data_flow.n

        # Apply patch over test set.
        for batch_num, (x, y) in enumerate(data_flow):
            y_int = np.argmax(y, axis=1)
            if batch_num >= num_images // batch_size:
                break
            LOGGER.info("Saving regular image batch", batch_num=batch_num)
            clean_filenames = img_filenames[
                batch_num * batch_size : (batch_num + 1) * batch_size
            ]
            save_batch(class_names_list, x, adv_data_dir, y_int, clean_filenames, "reg")

    LOGGER.info("Adversarial image generation complete", attack="patch")
    log_distance_metrics(distance_metrics_)

    return pd.DataFrame(distance_metrics_)
