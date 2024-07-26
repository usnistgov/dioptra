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
"""A task plugin module for the Fast Gradient Method evasion attack.

The Fast Gradient Method (FGM) [goodfellow2015]_ is an evasion attack that attempts to
fool a trained classifier by perturbing a test image using the gradient of the
classifier's neural network. This task plugin uses the Adversarial Robustness Toolbox's
[art2019]_ implementation of the |fgm_art|.

References:
    .. [art2019] M.-I. Nicolae et al., "Adversarial Robustness Toolbox v1.0.0,"
       Nov. 2019. [Online]. Available:
       `arXiv:1807.01069v4 [cs.LG] <http://arxiv.org/abs/1807.01069v4>`_.

    .. [goodfellow2015] I. Goodfellow, J. Shlens, and C. Szegedy. (May 2015).
       Explaining and Harnessing Adversarial Examples, Presented at the Int. Conf.
       on Learn. Represent. 2015, San Diego, California, United States. [Online].
       Available: `arXiv:1412.6572v3 [stat.ML] <http://arxiv.org/abs/1412.6572v3>`_.

.. |fgm_art| replace:: `Fast Gradient Method <https://adversarial-robustness-toolbox
   .readthedocs.io/en/latest/modules/attacks/evasion.html#fast-gradient-method-fgm>`__
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

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
    from art.attacks.evasion import FastGradientMethod
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
def create_adversarial_fgm_dataset(
    data_dir: str,
    adv_data_dir: Union[str, Path],
    keras_classifier: TensorFlowV2Classifier,
    image_size: Tuple[int, int, int],
    distance_metrics_list: Optional[List[Tuple[str, Callable[..., np.ndarray]]]] = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    eps: float = 0.3,
    eps_step: float = 0.1,
    minimal: bool = False,
    norm: Union[int, float, str] = np.inf,
) -> pd.DataFrame:
    """Generates an adversarial dataset using the Fast Gradient Method attack.

    Each generated adversarial image is saved as an image file in the directory
    specified by `adv_data_dir` and the distance metric functions passed to
    `distance_metrics_list` are used to quantify the size of the perturbation applied to
    each image.

    Args:
        data_dir: The directory containing the clean test images.
        adv_data_dir: The directory to use when saving the generated adversarial images.
        keras_classifier: A trained :py:class:`~art.estimators.classification\\
            .TensorFlowV2Classifier`.
        image_size: A tuple of integers `(height, width, channels)` used to preprocess
            the images so that they all have the same dimensions and number of color
            channels. `channels=3` means RGB color images and `channels=1` means
            grayscale images. Images with different dimensions will be resized. If
            `channels=1`, color images will be converted into grayscale.
        distance_metrics_list: A list of distance metrics to compute after generating an
            adversarial image. If `None`, then no distance metrics will be calculated.
            The default is `None`.
        rescale: The rescaling factor for the pixel vectors. If `None` or `0`, no
            rescaling is applied, otherwise multiply the data by the value provided
            (after applying all other transformations). The default is `1.0 / 255`.
        batch_size: The size of the batch on which adversarial samples are generated.
            The default is `32`.
        label_mode: Determines how the label arrays for the dataset will be returned.
            The available choices are: `"categorical"`, `"binary"`, `"sparse"`,
            `"input"`, `None`. For information on the meaning of each choice, see
            the documentation for |flow_from_directory|. The default is `"categorical"`.
        eps: The attack step size. The default is `0.3`.
        eps_step: The step size of the input variation for minimal perturbation
            computation. The default is `0.1`.
        minimal: If `True`, compute the minimal perturbation, and use `eps_step` for the
            step size and `eps` for the maximum perturbation. The default is `False`.
        norm: The norm of the adversarial perturbation. Can be `"inf"`,
            :py:data:`numpy.inf`, `1`, or `2`. The default is :py:data:`numpy.inf`.

    Returns:
        A :py:class:`~pandas.DataFrame` containing the full distribution of the
        calculated distance metrics.

    See Also:
        - |flow_from_directory|

    .. |flow_from_directory| replace:: :py:meth:`tf.keras.preprocessing.image\\
       .ImageDataGenerator.flow_from_directory`
    """
    distance_metrics_list = distance_metrics_list or []
    color_mode: str = "color" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]
    adv_data_dir = Path(adv_data_dir)

    attack = _init_fgm(
        keras_classifier=keras_classifier,
        batch_size=batch_size,
        eps=eps,
        eps_step=eps_step,
        minimal=minimal,
        norm=norm,
    )

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]

    distance_metrics_: Dict[str, List[List[float]]] = {"image": [], "label": []}
    for metric_name, _ in distance_metrics_list:
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
            batch_num * batch_size : (batch_num + 1) * batch_size  # noqa: E203
        ]

        LOGGER.info(
            "Generate adversarial image batch",
            attack="fgm",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch = attack.generate(x=x)

        _save_adv_batch(adv_batch, adv_data_dir, y_int, clean_filenames)

        _evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
            distance_metrics_list=distance_metrics_list,
        )

    LOGGER.info("Adversarial image generation complete", attack="fgm")
    _log_distance_metrics(distance_metrics_)

    return pd.DataFrame(distance_metrics_)


def _init_fgm(
    keras_classifier: TensorFlowV2Classifier, batch_size: int, **kwargs
) -> FastGradientMethod:
    """Initializes :py:class:`~art.attacks.evasion.FastGradientMethod`.

    Args:
        keras_classifier: A trained :py:class:`~art.estimators.classification\\
            .TensorFlowV2Classifier`.
        batch_size: The size of the batch on which adversarial samples are generated.

    Returns:
        A :py:class:`~art.attacks.evasion.FastGradientMethod` object.
    """
    attack: FastGradientMethod = FastGradientMethod(
        estimator=keras_classifier, batch_size=batch_size, **kwargs
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
