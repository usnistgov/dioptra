#!/usr/bin/env python

import warnings
from typing import Tuple
from pathlib import Path

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow
import numpy as np
import random
import structlog
from art.attacks.evasion import AdversarialPatch
from art.estimators.classification import KerasClassifier
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import save_img

LOGGER = structlog.get_logger()

def load_model_in_registry(model: str):
    return mlflow.keras.load_model(model_uri=f"models:/{model}")

def wrap_keras_classifier(model, imagenet_preprocessing):
    keras_model = load_model_in_registry(model=model)
    clip_values = (0, 255)
    if imagenet_preprocessing:
        mean_b = 103.939
        mean_g = 116.779
        mean_r = 123.680
        return KerasClassifier(model=keras_model, clip_values=clip_values, preprocessing=([mean_b, mean_g, mean_r], 1))
    else:
        return KerasClassifier(model=keras_model, clip_values=clip_values)

def init_patch(model, batch_size, imagenet_preprocessing, **kwargs):

    classifier = wrap_keras_classifier(model,imagenet_preprocessing)

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
    imagenet_preprocessing: bool = False,
    rescale: float = 1.0,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    patch_target: int = -1,
    num_patch: int = 1,
    num_patch_samples: int = 10,
    **kwargs,
):

    classifier, attack = init_patch(model=model, batch_size=batch_size,
                                    imagenet_preprocessing=imagenet_preprocessing, **kwargs)
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
    for batch_num, (x, y) in enumerate(patch_set):

        # Generate random index from available classes.
        if (patch_target < 0):
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
    save_adv_patch(patch_list, mask_list, id_list, num_patch, adv_patch_dir)
    return classifier
