#!/usr/bin/env python

import warnings
from typing import Tuple
from pathlib import Path
import tensorflow as tf

warnings.filterwarnings("ignore")

tf.compat.v1.disable_eager_execution()

import numpy as np
import random
import structlog
from art.attacks.evasion import AdversarialPatch
from art.estimators.classification import KerasClassifier
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import save_img

from models import load_model_in_registry

LOGGER = structlog.get_logger()


def wrap_keras_classifier(model):
    keras_model = load_model_in_registry(model=model)
    return KerasClassifier(model=keras_model, clip_values=(0.0, 1.0))


def init_patch(model, batch_size, **kwargs):
    classifier = wrap_keras_classifier(model)
    attack = AdversarialPatch(classifier=classifier, batch_size=batch_size, **kwargs)
    return classifier, attack


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
        masked_patch = patch*mask

        # Save masked patch as image.
        adv_patch_path = (
            adv_patch_dir
            / f"Patch_{patch_id}.png"
        )

        if not adv_patch_path.parent.exists():
            adv_patch_path.parent.mkdir(parents=True)

        save_img(path=str(adv_patch_path), x=masked_patch)


def create_adversarial_patch_dataset(
    data_dir: str,
    model: str,
    adv_patch_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
    patch_target: int = -1,
    num_patch: int = 1,
    num_patch_samples: int = 10,
    **kwargs,
):

    classifier, attack = init_patch(model=model, batch_size=batch_size, **kwargs)
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

    for batch_num, (x, y) in enumerate(patch_set):

        # Generate random index from 10 classes.
        if patch_target < 0:
            target_index = random.randint(0, 9)
        id_list.append(target_index)
        y_one_hot = np.zeros(10)
        y_one_hot[target_index] = 1.0
        y_target = np.tile(y_one_hot, (x.shape[0], 1))

        if batch_num >= num_patch:
            break

        patch, patch_mask = attack.generate(x=x, y=y_target)

        patch_list.append(patch)
        mask_list.append(patch_mask)

    # Save adversarial patches.
    save_adv_patch(patch_list, mask_list, id_list, num_patch, adv_patch_dir)
    return classifier
