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
from typing import Callable, Dict, List, Optional, Tuple, Union

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from prefect import task
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import ARTDependencyError, TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from art.attacks.evasion import AdversarialPatch
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
def create_adversarial_patches(
    data_dir: str,
    adv_data_dir: Union[str, Path],
    keras_classifier: TensorFlowV2Classifier,
    image_size: Tuple[int, int, int],
    patch_target: int,
    num_patch: int,
    num_patch_samples: int,
    rotation_max: float,
    scale_min: float,
    scale_max: float,
    learning_rate: float,
    max_iter: int,
    patch_shape: Tuple,
    rescale: float = 1.0 / 255,
    label_mode: str = "categorical",
) -> pd.DataFrame:
    color_mode: str = "rgb" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]
    adv_data_dir = Path(adv_data_dir)
    batch_size = num_patch_samples

    attack = _init_patch(
        keras_classifier=keras_classifier,
        batch_size=batch_size,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
        learning_rate=learning_rate,
        max_iter=max_iter,
        patch_shape=patch_shape,
    )

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    patch_set = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
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
            target_index = np.random.randint(0, n_classes)
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
    _save_adv_patch(patch_list, mask_list, id_list, num_patch, adv_data_dir)
    LOGGER.info("Adversarial patch generation complete", attack="patch")

    return


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_adversarial_patch_dataset(
    data_dir: str,
    adv_data_dir: Union[str, Path],
    patch_dir: str,
    patch_application_rate: float,
    keras_classifier: TensorFlowV2Classifier,
    image_size: Tuple[int, int, int],
    patch_shape: Tuple,
    distance_metrics_list: Optional[List[Tuple[str, Callable[..., np.ndarray]]]] = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    patch_deployment_method: str = "augment",
    patch_scale: float = 0.4,
    rotation_max: float = 22.5,
    scale_min: float = 0.1,
    scale_max: float = 1.0,
    label_mode: str = "categorical",
) -> pd.DataFrame:
    distance_metrics_list = distance_metrics_list or []
    color_mode: str = "rgb" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]
    adv_data_dir = Path(adv_data_dir)

    patch_list = np.load((patch_dir / "patch_list.npy").resolve())

    attack = _init_patch(
        keras_classifier=keras_classifier,
        batch_size=batch_size,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
        patch_shape=patch_shape,
    )

    if patch_application_rate <= 0 or patch_application_rate >= 1.0:
        validation_split = None
        subset = None
    else:
        validation_split = 1.0 - patch_application_rate
        subset = "training"

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
        subset=subset,
    )

    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

    distance_metrics_: Dict[str, List[List[float]]] = {"image": [], "label": []}
    for metric_name, _ in distance_metrics_list:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial images",
        attack="patch",
        num_batches=num_images // batch_size,
    )

    converted_patch_list = list(patch_list)
    # Apply patch over test set.
    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break
        LOGGER.info(
            "Generate adversarial image batch",
            attack="patch",
            batch_num=batch_num,
        )
        patch_index = np.random.randint(len(converted_patch_list))
        patch = converted_patch_list[patch_index]
        y_int = np.argmax(y, axis=1)
        if patch_scale > 0:
            adv_batch = attack.apply_patch(x, scale=patch_scale, patch_external=patch)
        else:
            adv_batch = attack.apply_patch(x, patch_external=patch)

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size
        ]

        _save_batch(
            adv_batch, adv_data_dir, y_int, clean_filenames, class_names_list, "adv"
        )

        _evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch,
            distance_metrics_list=distance_metrics_list,
        )

    if patch_deployment_method == "augment" or (
        patch_deployment_method == "corrupt" and validation_split is not None
    ):
        if patch_deployment_method == "augment":
            data_generator = ImageDataGenerator(rescale=rescale)
            data_flow = data_generator.flow_from_directory(
                directory=data_dir,
                target_size=target_size,
                color_mode=color_mode,
                class_mode=label_mode,
                batch_size=batch_size,
                shuffle=False,
            )
        elif patch_deployment_method == "corrupt" and validation_split is not None:
            data_flow = data_generator.flow_from_directory(
                directory=data_dir,
                target_size=target_size,
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
            _save_batch(
                x, adv_data_dir, y_int, clean_filenames, class_names_list, "reg"
            )

    LOGGER.info("Adversarial image generation complete", attack="patch")
    _log_distance_metrics(distance_metrics_)
    return pd.DataFrame(distance_metrics_)


def _init_patch(
    keras_classifier: TensorFlowV2Classifier, batch_size: int, **kwargs
) -> AdversarialPatch:
    attack = AdversarialPatch(
        classifier=keras_classifier, batch_size=batch_size, **kwargs
    )
    return attack


def _save_adv_patch(patch_list, mask_list, id_list, num_patch, adv_patch_dir):
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


def _save_batch(
    adv_batch, adv_data_dir, y, clean_filenames, class_names_list, type
) -> None:
    for batch_image_num, adv_image in enumerate(adv_batch):
        out_label = class_names_list[y[batch_image_num]]
        adv_image_path = (
            adv_data_dir
            / f"{out_label}"
            / f"{type}_{clean_filenames[batch_image_num].name}"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


def _evaluate_distance_metrics(
    clean_filenames, distance_metrics_, clean_batch, adv_batch, distance_metrics_list
) -> None:
    LOGGER.debug("evaluate image perturbations using distance metrics")
    distance_metrics_["image"].extend([x.name for x in clean_filenames])
    distance_metrics_["label"].extend([x.parent for x in clean_filenames])
    for metric_name, metric in distance_metrics_list:
        distance_metrics_[metric_name].extend(metric(clean_batch, adv_batch))


def _log_distance_metrics(distance_metrics_: Dict[str, List[List[float]]]) -> None:
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
