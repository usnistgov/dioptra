#!/usr/bin/env python

import warnings
from typing import Tuple
from pathlib import Path

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import numpy as np
import structlog
from art.attacks.evasion import FastGradientMethod
from art.estimators.classification import KerasClassifier
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import save_img

from models import load_model_in_registry

LOGGER = structlog.get_logger()


def wrap_keras_classifier(model):
    keras_model = load_model_in_registry(model=model)
    return KerasClassifier(model=keras_model)


def init_fgm(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = FastGradientMethod(estimator=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


def save_adv_batch(adv_batch, batch_size, batch_num, adv_data_dir, y):
    for batch_image_num, adv_image in enumerate(adv_batch):
        adv_image_path = (
            adv_data_dir
            / f"{y[batch_image_num]}"
            / f"adv{str(batch_size * batch_num + batch_image_num).zfill(5)}.png"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


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

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        LOGGER.info("Attacking data batch", batch_num=batch_num)
        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)
        save_adv_batch(adv_batch, batch_size, batch_num, adv_data_dir, y_int)

    return classifier
