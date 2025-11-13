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
# https://creativecommons.org/licenses/by/4.0/legalcodeimport numpy as np
import keras
import numpy as np
import structlog
import tensorflow as tf
from art.attacks.evasion import (
    AdversarialPatchNumpy,
    CarliniL0Method,
    CarliniL2Method,
    CarliniLInfMethod,
    FastGradientMethod,
)
from art.estimators.classification import KerasClassifier
from keras import ops
from numpy.typing import ArrayLike

from dioptra import pyplugs

from .data import create_transformed_dataset

LOGGER = structlog.get_logger()


@pyplugs.register
def fast_gradient_method(
    model: keras.Model,
    dataset: tf.data.Dataset,
    target: int | None = None,
    norm: int | float | str = np.inf,
    eps: float = 0.3,
    eps_step: float = 0.1,
    minimal: bool = False,
    save_dataset: bool = False,
) -> tf.data.Dataset:
    """Generates an adversarial dataset using the Fast Gradient Method attack.

    Args:
        model: The classifier used to generate the attack.
        dataset: The dataset to apply the attack to.
        target: The target class index or None for an untargeted attack.
        norm: The norm of the adversarial perturbation. Can be `"inf"`,
            :py:data:`numpy.inf`, `1`, or `2`. The default is :py:data:`numpy.inf`.
        eps: The attack step size. The default is `0.3`.
        eps_step: The step size of the input variation for minimal perturbation
            computation. The default is `0.1`.
        minimal: If `True`, compute the minimal perturbation, and use `eps_step` for the
            step size and `eps` for the maximum perturbation. The default is `False`.
        save_dataset: Whether to save the dataset to disk.

    Returns:
        The transformed tf.data.Dataset.
    """
    batch_size, num_classes = next(iter(dataset))[1].shape
    clip_values = (0.0, 255.0) if ops.max(next(iter(dataset))[0]) > 1.0 else (0.0, 1.0)

    attack = FastGradientMethod(
        estimator=KerasClassifier(model, clip_values=clip_values),
        norm=norm,
        targeted=target is not None,
        eps=eps,
        eps_step=eps_step,
        batch_size=batch_size,
        minimal=minimal,
    )

    y_target = (
        None
        if target is None
        else ops.repeat([ops.one_hot(target, num_classes)], batch_size, axis=0)
    )

    @tf.numpy_function(Tout=(tf.float32, tf.float32))
    def attack_fn(x, y):
        return attack.generate(x, y=y_target), y

    return create_transformed_dataset(dataset, attack_fn, save_dataset)


@pyplugs.register
def carlini_wagner(
    model: keras.Model,
    dataset: tf.data.Dataset,
    target: int | None = None,
    norm: int | float | str = np.inf,
    confidence: float = 0.0,
    learning_rate: float = 0.01,
    max_iter: int = 10,
    initial_const: float = 0.01,
    save_dataset: bool = False,
) -> tf.data.Dataset:
    """Generates an adversarial dataset using the Carlini Wagner method

    Args:
        model: The classifier used to generate the attack.
        dataset: The dataset to apply the attack to.
        target: The target class index or None for an untargeted attack.
        norm: The norm of the adversarial perturbation. Can be `"inf"`,
            :py:data:`numpy.inf`, `1`, or `2`. The default is :py:data:`numpy.inf`.
        confidence:
        learning_rate:
        max_iter:
        initial_const:
        save_dataset: Whether to save the dataset to disk.

    Returns:
        The transformed tf.data.Dataset.
    """
    batch_size, num_classes = next(iter(dataset))[1].shape
    clip_values = (0.0, 255.0) if ops.max(next(iter(dataset))[0]) > 1.0 else (0.0, 1.0)

    method = {
        "0": CarliniL0Method,
        "2": CarliniL2Method,
        "inf": CarliniLInfMethod,
    }.get(str(norm), None)

    if method is None:
        raise ValueError("Invalid value for norm, must be one of 0, 2, inf")

    attack = method(
        classifier=KerasClassifier(model, clip_values=clip_values),
        confidence=confidence,
        targeted=target is not None,
        learning_rate=learning_rate,
        batch_size=batch_size,
        max_iter=max_iter,
        initial_const=initial_const,
        verbose=False,
    )

    y_target = (
        None
        if target is None
        else ops.repeat([ops.one_hot(target, num_classes)], batch_size, axis=0)
    )

    @tf.numpy_function(Tout=(tf.float32, tf.float32))
    def attack_fn(x, y):
        return attack.generate(x, y=y_target), y

    return create_transformed_dataset(dataset, attack_fn, save_dataset)


@pyplugs.register
def create_adversarial_patch(
    model: keras.Model,
    dataset: tf.data.Dataset,
    target: int,
    rotation_max: float = 180.0,
    scale_min: float = 0.1,
    scale_max: float = 1.0,
    learning_rate: float = 5.0,
    max_iter: int = 500,
) -> tuple[ArrayLike, ArrayLike]:
    """Optimizes an Adversarial Patch via expectation over transformation.

    Args:
        model: The classifier used to generate the patch.
        dataset: The dataset used to generate the patch.
        target: The index of target class for the patch.
        rotation_max: The max angle to rotate the patch by.
        scale_min: The min scale of the patch as a fraction of image size.
        scale_max: The max scale of the patch as a fraction of image size.
        learning_rate: The learning rate used in optimization.
        max_iter: The maximum iterations in the optimization.

    Returns:
        The trained patch and its mask.
    """
    batch_size, num_classes = next(iter(dataset))[1].shape
    clip_values = (0.0, 255.0) if ops.max(next(iter(dataset))[0]) > 1.0 else (0.0, 1.0)

    attack = AdversarialPatchNumpy(
        classifier=KerasClassifier(model, clip_values=clip_values),
        batch_size=batch_size,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
        learning_rate=learning_rate,
        max_iter=max_iter,
        verbose=False,
    )

    x, _ = next(iter(dataset))
    y_target = ops.repeat([ops.one_hot(target, num_classes)], batch_size, axis=0)

    return attack.generate(x, y=y_target)


@pyplugs.register
def apply_adversarial_patch(
    model: keras.Model,
    dataset: tf.data.Dataset,
    patch: ArrayLike,
    rotation_max: float = 180.0,
    scale: float = 0.5,
    save_dataset: bool = False,
) -> tf.data.Dataset:
    """Generates an adversarial dataset by applying an Adversarial Patch.

    Args:
        model: The keras model used for configuring AdversarialPatchNumpy.
        dataset: The dataset to transform into an adversarial dataset.
        patch: The adversarial patch to be applied to the dataset.
        rotation_max: The max angle to rotate the patch by.
        scale: The scale of the patch as a fraction of image size.
        save_dataset: Whether to save the dataset to disk.

    Returns:
        The transformed tf.data.Dataset
    """
    batch_size, num_classes = next(iter(dataset))[1].shape
    clip_values = (0.0, 255.0) if ops.max(next(iter(dataset))[0]) > 1.0 else (0.0, 1.0)

    attack = AdversarialPatchNumpy(
        classifier=KerasClassifier(model, clip_values=clip_values),
        batch_size=batch_size,
        rotation_max=rotation_max,
        verbose=False,
    )

    @tf.numpy_function(Tout=(tf.float32, tf.float32))
    def attack_fn(x, y):
        return attack.apply_patch(x, scale=scale, patch_external=patch), y

    return create_transformed_dataset(dataset, attack_fn, save_dataset)
