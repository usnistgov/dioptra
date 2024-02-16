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
from __future__ import annotations

from typing import Tuple

import mlflow
import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import ARTDependencyError, TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from art.estimators.classification import KerasClassifier

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


try:
    from tensorflow.keras.models import Sequential

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def load_wrapped_tensorflow_keras_classifier(
    name: str,
    version: int,
    clip_values: Tuple = None,
    imagenet_preprocessing: bool = False,
) -> KerasClassifier:
    uri = f"models:/{name}/{version}"
    LOGGER.info("Load Keras classifier from model registry", uri=uri)
    keras_classifier = mlflow.tensorflow.load_model(uri)
    if imagenet_preprocessing:
        mean_b = 103.939
        mean_g = 116.779
        mean_r = 123.680

        wrapped_keras_classifier = KerasClassifier(
            model=keras_classifier,
            clip_values=clip_values,
            preprocessing=(
                np.array([mean_b, mean_g, mean_r]),
                np.array([1.0, 1.0, 1.0]),
            ),
        )
    else:
        wrapped_keras_classifier = KerasClassifier(
            model=keras_classifier, clip_values=clip_values
        )
    LOGGER.info(
        "Wrap Keras classifier for compatibility with Adversarial Robustness Toolbox"
    )

    return wrapped_keras_classifier


def get_target_class_name(poison_dir):
    poison_dir = poison_dir.resolve()
    for item in os.listdir(poison_dir):
        if os.path.isdir(poison_dir / item):
            return item
    return "None"


def copy_poisoned_images(src, dst, num_poisoned_images):
    poison_image_list = [
        os.path.join(src, f)
        for f in os.listdir(src)
        if os.path.isfile(os.path.join(src, f))
    ]
    np.random.shuffle(poison_image_list)
    if not (num_poisoned_images < 0 or num_poisoned_images > len(poison_image_list)):
        poison_image_list = poison_image_list[:num_poisoned_images]

    for file in poison_image_list:
        shutil.copy(file, dst)


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def deploy_poison_images(
    data_dir: str,
    adv_data_dir: Union[str, Path],
    poison_deployment_method: str,
    num_poisoned_images: int,
) -> str:
    LOGGER.info("Copying original dataset.")
    if poison_deployment_method == "add":
        shutil.copytree(data_dir, adv_data_dir)
        LOGGER.info("Adding poisoned images.")
        copy_poisoned_images(
            src=poison_images_dir / target_class_name,
            dst=adv_data_dir / target_class_name,
            num_poisoned_images=num_poisoned_images,
        )
    elif poison_deployment_method == "replace":
        shutil.copytree(data_dir, adv_data_dir)
        LOGGER.info("Replacing original images with poisoned counterparts.")
        poison_class_dir = adv_data_dir / target_class_name

        for object in os.listdir(poison_class_dir):
            if os.path.isfile(poison_class_dir / object):
                file_id = object.split("poisoned_")[-1]
                os.remove(poison_class_dir / file_id)

        copy_poisoned_images(
            src=poison_images_dir / target_class_name,
            dst=adv_data_dir / target_class_name,
            num_poisoned_images=num_poisoned_images,
        )
    return adv_data_dir
