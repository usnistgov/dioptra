#!/usr/bin/env python

import warnings
from pathlib import Path
from typing import Tuple

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from art.attacks.poisoning import (
    PoisoningAttackAdversarialEmbedding,
    PoisoningAttackBackdoor,
    PoisoningAttackCleanLabelBackdoor,
)
from art.attacks.poisoning.perturbations import add_pattern_bd
from art.estimators.classification import KerasClassifier
from art.utils import to_categorical
from metrics import (
    l_inf_norm,
    paired_cosine_similarities,
    paired_euclidean_distances,
    paired_manhattan_distances,
    paired_wasserstein_distances,
)
from models import load_model_in_registry
from PIL import Image
from tensorflow.keras.preprocessing.image import ImageDataGenerator, save_img

LOGGER = structlog.get_logger()
DISTANCE_METRICS = [
    ("l_infinity_norm", l_inf_norm),
    ("cosine_similarity", paired_cosine_similarities),
    ("euclidean_distance", paired_euclidean_distances),
    ("manhattan_distance", paired_manhattan_distances),
    ("wasserstein_distance", paired_wasserstein_distances),
]


# Load model from registry and apply imagenet_preprocessing if needed.
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


def init_poison(
    model,
    clip_values,
    imagenet_preprocessing,
    target_image_path,
    feature_layer_index,
    single_image_size,
    **kwargs,
):
    classifier = wrap_keras_classifier(model, clip_values, imagenet_preprocessing)

    # Open the image from working directory
    target_image = target_image_path
    image = Image.open(target_image).resize(
        (single_image_size[1], single_image_size[2])
    )
    image = np.asarray(image)
    image = np.reshape(image, single_image_size)
    image = image.astype(np.float32)

    # Initialize poisoning attack.
    feature_layer = classifier.layer_names[feature_layer_index]
    attack = FeatureCollisionAttack(classifier, image, feature_layer, **kwargs)

    return classifier, attack


def save_batch(class_names_list, adv_batch, adv_data_dir, y, clean_filenames, type):
    for batch_image_num, adv_image in enumerate(adv_batch):
        outfile = class_names_list[y[batch_image_num]]
        if len(type) > 0:
            adv_image_path = (
                adv_data_dir
                / f"{outfile}"
                / f"{type}_{clean_filenames[batch_image_num].name}"
            )
        else:
            adv_image_path = (
                adv_data_dir / f"{outfile}" / f"{clean_filenames[batch_image_num].name}"
            )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


def save_batch_poison(adv_batch, adv_data_dir, poison_label, clean_filenames, type):
    for batch_image_num, adv_image in enumerate(adv_batch):
        outfile = poison_label
        adv_image_path = (
            adv_data_dir
            / f"{outfile}"
            / f"{type}_{clean_filenames[batch_image_num].name}"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


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


def create_poisoned_test_images(
    data_dir: str,
    adv_data_dir: str,
    rescale: float = 1.0,
    batch_size: int = 32,
    target_class: str = "0",
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    clip_values: Tuple[float, float] = (0, 255),
    imagenet_preprocessing: bool = True,
    label_type: str = "test",
    poison_fraction: float = 1.0,
):

    validation_split = 1 - poison_fraction
    data_generator: ImageDataGenerator = ImageDataGenerator(
        rescale=rescale, validation_split=validation_split
    )

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=True,
        subset="training",
    )

    img_filenames = [Path(x) for x in data_flow.filenames]
    class_size = len(data_flow.class_indices)
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

    LOGGER.info(
        "Generate poisoned images",
        attack="backdoor poisoning",
    )

    target_index = int(target_class)
    backdoor_poisoner = PoisoningAttackBackdoor(add_pattern_bd)

    example_target = np.zeros(class_size)
    example_target[target_index] = 1

    distance_metrics_ = {"image": [], "label": []}

    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    num_images = data_flow.n

    # Apply backdoor poisoning over test set.
    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        y_int = np.argmax(y, axis=1)

        filenames = [
            img_filenames[data_flow.index_array[i]]
            for i in range(batch_num * batch_size, (batch_num + 1) * batch_size)
        ]

        poisoned_x, plabels = backdoor_poisoner.poison(
            x, y=example_target, broadcast=True
        )

        # Swap to poisoned labels if training mode is set.
        if label_type == "train" or label_type == "training":
            y_int = np.argmax(plabels, axis=1)

        save_batch(
            class_names_list, poisoned_x, adv_data_dir, y_int, filenames, "poisoned"
        )

        evaluate_distance_metrics(
            clean_filenames=filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=poisoned_x,
        )

    # Save remaining non-poisoned images.
    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=True,
        subset="validation",
    )

    img_filenames = [Path(x) for x in data_flow.filenames]
    num_images = data_flow.n

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        y_int = np.argmax(y, axis=1)
        filenames = [
            img_filenames[data_flow.index_array[i]]
            for i in range(batch_num * batch_size, (batch_num + 1) * batch_size)
        ]
        save_batch(class_names_list, x, adv_data_dir, y_int, filenames, "")

    LOGGER.info("Adversarial test image generation complete", attack="backdoor poison")
    log_distance_metrics(distance_metrics_)
    return pd.DataFrame(distance_metrics_)


def create_poisoned_clean_images(
    data_dir: str,
    adv_data_dir: str,
    model: str,
    rescale: float = 1.0,
    batch_size: int = 32,
    target_class: str = "0",
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    clip_values: Tuple[float, float] = (0, 255),
    imagenet_preprocessing: bool = True,
    label_type: str = "train",
    poison_fraction: float = 0.1,
):

    classifier = wrap_keras_classifier(model, clip_values, imagenet_preprocessing)

    validation_split = 1 - poison_fraction
    data_generator: ImageDataGenerator = ImageDataGenerator(
        rescale=rescale, validation_split=validation_split
    )

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=True,
        subset="training",
    )

    img_filenames = [Path(x) for x in data_flow.filenames]
    class_size = len(data_flow.class_indices)
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

    LOGGER.info(
        "Generate poisoned images",
        attack="backdoor poisoning",
    )

    target_index = int(target_class)

    targets = to_categorical([target_index], class_size)[0]

    example_target = np.zeros(class_size)
    example_target[target_index] = 1

    # targets = example_target

    backdoor = PoisoningAttackBackdoor(add_pattern_bd)

    backdoor_poisoner = PoisoningAttackCleanLabelBackdoor(
        backdoor=backdoor,
        proxy_classifier=classifier,
        target=targets,
        pp_poison=poison_fraction,
        norm=2,
        eps=50,
        eps_step=0.1,
        max_iter=300,
    )

    distance_metrics_ = {"image": [], "label": []}

    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    num_images = data_flow.n

    # Apply backdoor poisoning over test set.
    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        y_int = np.argmax(y, axis=1)

        filenames = [
            img_filenames[data_flow.index_array[i]]
            for i in range(batch_num * batch_size, (batch_num + 1) * batch_size)
        ]

        poisoned_x, plabels = backdoor_poisoner.poison(x, y)

        # Swap to poisoned labels if training mode is set.
        if label_type == "train" or label_type == "training":
            y_int = np.argmax(plabels, axis=1)

        save_batch(
            class_names_list, poisoned_x, adv_data_dir, y_int, filenames, "poisoned"
        )

        evaluate_distance_metrics(
            clean_filenames=filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=poisoned_x,
        )

    # Save remaining non-poisoned images.
    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=True,
        subset="validation",
    )

    img_filenames = [Path(x) for x in data_flow.filenames]
    num_images = data_flow.n

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        y_int = np.argmax(y, axis=1)
        filenames = [
            img_filenames[data_flow.index_array[i]]
            for i in range(batch_num * batch_size, (batch_num + 1) * batch_size)
        ]
        save_batch(class_names_list, x, adv_data_dir, y_int, filenames, "")

    LOGGER.info("Adversarial test image generation complete", attack="backdoor poison")
    log_distance_metrics(distance_metrics_)
    return pd.DataFrame(distance_metrics_)
