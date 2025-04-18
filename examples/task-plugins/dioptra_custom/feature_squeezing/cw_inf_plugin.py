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

from pathlib import Path
from typing import Dict, List, Tuple

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import ARTDependencyError, TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from art.attacks.evasion import CarliniLInfMethod
    from art.estimators.classification import TensorFlowV2Classifier

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


try:
    from tensorflow.keras.preprocessing.image import ImageDataGenerator, save_img

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_adversarial_cw_inf_dataset(
    data_dir: str,
    model_name: str,
    model_version: int,
    learning_rate: float,
    max_iter: int,
    verbose: str,
    # eps: float,
    keras_classifier: TensorFlowV2Classifier,
    adv_data_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
    confidence: float = 0.0,
    **kwargs,
):
    model_name = model_name + "/" + str(model_version)
    LOGGER.info("Model Selected: ", model_name=model_name)
    color_mode: str = "color" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]
    adv_data_dir = Path(adv_data_dir)
    LOGGER.info("initiating classifier: ", keras_classifier=keras_classifier)
    attack = _init_cw_inf(
        keras_classifier=keras_classifier,
        batch_size=batch_size,
        confidence=confidence,
        learning_rate=learning_rate,  # placeholder
        max_iter=max_iter,
        verbose=verbose,
    )

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=True,  # false,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    distance_metrics_list = []  # distance_metrics_list or []
    distance_metrics_: Dict[str, List[List[float]]] = {"image": [], "label": []}
    for metric_name, _ in distance_metrics_list:
        distance_metrics_[metric_name] = []
    LOGGER.info(
        "Generate adversarial images",
        attack="cw_inf",
        model_version=model_version,
        num_batches=num_images // batch_size,
        confidence=confidence,
        learning_rate=learning_rate,
        max_iter=max_iter,
    )
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
            attack_object=attack,
        )

        y_int = np.argmax(y, axis=1)

        adv_batch = attack.generate(x=x, y=y)
        LOGGER.info(
            "Saving adversarial image batch",
            attack="cw_inf",
            batch_num=batch_num,
        )
        _save_adv_batch(
            adv_batch, adv_data_dir, y_int, clean_filenames  # ,class_names_list
        )

        _evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
            distance_metrics_list=distance_metrics_list,
        )

    LOGGER.info("Adversarial Carlini-Wagner image generation complete", attack="cw_inf")
    _log_distance_metrics(distance_metrics_)

    return pd.DataFrame(distance_metrics_)


def _init_cw_inf(
    keras_classifier: TensorFlowV2Classifier, batch_size: int, **kwargs
) -> CarliniLInfMethod:
    """Initializes :py:class:`~art.attacks.evasionCarliniLInfMethod`.

    Args:
        keras_classifier: A trained :py:class:`~art.estimators.classification\\
            .TensorFlowV2Classifier`.
        batch_size: The size of the batch on which adversarial samples are generated.

    Returns:
        A :py:class:`~art.attacks.evasion.CarliniLInfMethod` object.
    """
    attack: CarliniLInfMethod = CarliniLInfMethod(
        classifier=keras_classifier, batch_size=batch_size, **kwargs
    )
    return attack


def _save_adv_batch(adv_batch, adv_data_dir, y, clean_filenames) -> None:
    """Saves a batch of adversarial images to disk.

    Args:
        adv_batch: A generated batch of adversarial images.
        adv_data_dir: The directory to use when saving the generated adversarial images.
        y: An array containing the target labels of the original images.
        clean_filenames: A list containing the filenames of the original images.
    """
    for batch_image_num, adv_image in enumerate(adv_batch):
        adv_image_path = (
            adv_data_dir
            / f"{y[batch_image_num]}"
            / f"adv_{clean_filenames[batch_image_num].name}"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


def _evaluate_distance_metrics(
    clean_filenames, distance_metrics_, clean_batch, adv_batch, distance_metrics_list
) -> None:
    """Calculates distance metrics for a batch of clean/adversarial image pairs.

    Args:
        clean_filenames: A list containing the filenames of the original images.
        distance_metrics_: A dictionary used to record the values of the distance
            metrics computed for the clean/adversarial image pairs.
        clean_batch: The clean images used to generate the adversarial images in
            `adv_batch`.
        adv_batch: A generated batch of adversarial images.
        distance_metrics_list: A list of distance metrics to compute after generating an
            adversarial image.
    """
    LOGGER.debug("evaluate image perturbations using distance metrics")
    distance_metrics_["image"].extend([x.name for x in clean_filenames])
    distance_metrics_["label"].extend([x.parent for x in clean_filenames])
    for metric_name, metric in distance_metrics_list:
        distance_metrics_[metric_name].extend(metric(clean_batch, adv_batch))


def _log_distance_metrics(distance_metrics_: Dict[str, List[List[float]]]) -> None:
    """Logs the distance metrics summary statistics to the MLFlow Tracking service.

    The following summary statistics are calculated and logged to the MLFlow Tracking
    service for each of the distributions recorded in the `distance_metrics_`
    dictionary:

    - mean
    - median
    - standard deviation
    - interquartile range
    - minimum
    - maximum

    Args:
        distance_metrics_: A dictionary used to record the values of the distance
            metrics computed for the clean/adversarial image pairs.
    """
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
