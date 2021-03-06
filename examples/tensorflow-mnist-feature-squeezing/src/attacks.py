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

import warnings
from typing import Tuple
from pathlib import Path

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
import random
from art.estimators.classification import KerasClassifier
from art.attacks.evasion import FastGradientMethod
from art.attacks.evasion import CarliniL2Method
from art.attacks.evasion import CarliniLInfMethod
from art.attacks.evasion import DeepFool
from art.attacks.evasion import SaliencyMapMethod as jsma
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import save_img

from models import load_model_in_registry
from metrics import (
    l_inf_norm,
    paired_cosine_similarities,
    paired_euclidean_distances,
    paired_manhattan_distances,
    paired_wasserstein_distances,
)

LOGGER = structlog.get_logger()
DISTANCE_METRICS = [
    ("l_infinity_norm", l_inf_norm),
    ("cosine_similarity", paired_cosine_similarities),
    ("euclidean_distance", paired_euclidean_distances),
    ("manhattan_distance", paired_manhattan_distances),
    ("wasserstein_distance", paired_wasserstein_distances),
]


def wrap_keras_classifier(model):
    keras_model = load_model_in_registry(model=model)
    return KerasClassifier(model=keras_model)


def init_fgm(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = FastGradientMethod(estimator=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


def init_cw(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = CarliniL2Method(classifier=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


def init_cw_inf(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = CarliniLInfMethod(classifier=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


def init_deepfool(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = DeepFool(classifier=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


def init_jsma(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = jsma(classifier=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


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


def np_norm(im, im2, order):
    im_diff = im - im2
    batch_size = im_diff.shape[0]
    flatten_size = np.prod(im_diff.shape[1:])
    im_diff_norm = np.linalg.norm(
        im_diff.reshape((batch_size, flatten_size)), axis=1, ord=order
    )
    return im_diff_norm.tolist()


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


def create_adversarial_cw_inf_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
    **kwargs,
):

    classifier, attack = init_cw_inf(model=model, batch_size=batch_size, **kwargs)

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial images",
        attack="cw_inf",
        num_batches=num_images // batch_size,
    )
    # Here
    n_classes = len(class_names_list)
    # End
    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Generate adversarial image batch",
            attack="cw_inf",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        target_index = random.randint(0, n_classes - 1)
        y_one_hot = np.zeros(n_classes)
        #       y_one_hot[target_index] = 1.0
        y_one_hot[1] = 1.0
        y_target = np.tile(y_one_hot, (x.shape[0], 1))
        adv_batch = attack.generate(x=x)  # ,y=y_target)
        save_adv_batch(
            adv_batch, adv_data_dir, y_int, clean_filenames, class_names_list
        )

        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )

    LOGGER.info("Adversarial Carlini-Wagner image generation complete", attack="cw_inf")
    log_distance_metrics(distance_metrics_)

    return classifier, pd.DataFrame(distance_metrics_)


def create_adversarial_cw_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
    **kwargs,
):
    classifier, attack = init_cw(model=model, batch_size=batch_size, **kwargs)

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial images",
        attack="cw",
        num_batches=num_images // batch_size,
    )
    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Generate adversarial image batch",
            attack="cw",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)
        save_adv_batch(
            adv_batch, adv_data_dir, y_int, clean_filenames, class_names_list
        )

        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )

    LOGGER.info("Adversarial Carlini-Wagner image generation complete", attack="cw")
    log_distance_metrics(distance_metrics_)

    return classifier, pd.DataFrame(distance_metrics_)


def create_adversarial_fgm_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
    **kwargs,
):
    classifier, attack = init_fgm(model=model, batch_size=batch_size, **kwargs)

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial images",
        attack="fgm",
        num_batches=num_images // batch_size,
    )

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Generate adversarial image batch",
            attack="fgm",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)
        save_adv_batch(
            adv_batch, adv_data_dir, y_int, clean_filenames, class_names_list
        )

        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )

    LOGGER.info("Adversarial image generation complete", attack="fgm")
    log_distance_metrics(distance_metrics_)

    return classifier, pd.DataFrame(distance_metrics_)


def create_adversarial_mnist_deepfool_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
    **kwargs,
):

    classifier, attack = init_deepfool(model=model, batch_size=batch_size, **kwargs)
    LOGGER.info("Deepfool Batch Size: ", batch_size=batch_size)
    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)
    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

    LOGGER.info("Class names len: ", classes=len(class_names_list))

    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial mnist images",
        attack="deepfool",
        num_batches=num_images // batch_size,
    )

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Generate adversarial mnist image batch",
            attack="deepfool",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)
        save_adv_batch(
            adv_batch, adv_data_dir, y_int, clean_filenames, class_names_list
        )

        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )

    LOGGER.info("Adversarial image generation complete", attack="deepfool")
    log_distance_metrics(distance_metrics_)

    return classifier, pd.DataFrame(distance_metrics_)


def create_adversarial_deepfool_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0,
    batch_size: int = 40,
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    **kwargs,
):
    classifier, attack = init_deepfool(model=model, batch_size=batch_size, **kwargs)
    LOGGER.info("Deepfool Batch Size: ", batch_size=batch_size)
    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)
    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

    LOGGER.info("Class names len: ", classes=len(class_names_list))

    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial images",
        attack="deepfool",
        num_batches=num_images // batch_size,
    )

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Generate adversarial image batch",
            attack="deepfool",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)
        save_adv_batch(
            adv_batch, adv_data_dir, y_int, clean_filenames, class_names_list
        )

        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )

    LOGGER.info("Adversarial image generation complete", attack="deepfool")
    log_distance_metrics(distance_metrics_)

    return classifier, pd.DataFrame(distance_metrics_)


def create_adversarial_jsma_dataset(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
    **kwargs,
):
    classifier, attack = init_jsma(model=model, batch_size=batch_size, **kwargs)

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
    distance_metrics_ = {"image": [], "label": []}
    for metric_name, _ in DISTANCE_METRICS:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial images",
        attack="deepfool",
        num_batches=num_images // batch_size,
    )

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        LOGGER.info(
            "Generate adversarial image batch",
            attack="jsma",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)
        save_adv_batch(
            adv_batch, adv_data_dir, y_int, clean_filenames, class_names_list
        )

        evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
        )

    LOGGER.info("Adversarial image generation complete", attack="deepfool")
    log_distance_metrics(distance_metrics_)

    return classifier, pd.DataFrame(distance_metrics_)
