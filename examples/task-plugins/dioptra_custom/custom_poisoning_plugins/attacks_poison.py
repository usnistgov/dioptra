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
from types import FunctionType
from typing import Callable, Dict, List, Optional, Tuple, Union

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
from prefect import task
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import ARTDependencyError, TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    from art.attacks.poisoning import (
        PoisoningAttackAdversarialEmbedding,
        PoisoningAttackBackdoor,
    )
    from art.attacks.poisoning.perturbations import add_pattern_bd
    from art.estimators.classification import TensorFlowV2Classifier
    from art.utils import to_categorical
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers.legacy import Optimizer
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
def create_adv_embedding_model(
    model: Model,
    training_ds: DirectoryIterator,
    target_class_id: int,
    feature_layer_index: int,
    poison_fraction: float,
    regularization_factor: float,
    learning_rate: float,
    batch_size: int,
    epochs: int,
    discriminator_layer_1_size: int,
    discriminator_layer_2_size: int,
    optimizer: Optimizer,
    metrics: List[Union[Metric, FunctionType]],
) -> Model:

    n_classes = len(training_ds.class_indices)
    poison_model = TensorFlowV2Classifier(
        model, nb_classes=n_classes, input_shape=model.input_shape
    )

    x_train, y_train = training_ds.next()

    # Poison some percentage of all non-target-images to target-label
    targets = to_categorical([target_class_id], n_classes)[0]

    backdoor = PoisoningAttackBackdoor(add_pattern_bd)
    emb_attack = PoisoningAttackAdversarialEmbedding(
        classifier=poison_model,
        backdoor=backdoor,
        feature_layer=feature_layer_index,
        target=targets,
        regularization=regularization_factor,
        pp_poison=poison_fraction,
        discriminator_layer_1=discriminator_layer_1_size,
        discriminator_layer_2=discriminator_layer_2_size,
        learning_rate=learning_rate,
    )

    # Train and return poisoned estimator.
    classifier = emb_attack.poison_estimator(
        x_train, y_train, nb_epochs=epochs, batch_size=batch_size
    )

    model = classifier.model
    model.compile(
        loss="categorical_crossentropy",
        optimizer=optimizer,
        metrics=metrics,
    )
    return model


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_adversarial_poison_data(
    data_dir: str,
    adv_data_dir: Union[str, Path],
    image_size: Tuple[int, int, int],
    distance_metrics_list: Optional[List[Tuple[str, Callable[..., np.ndarray]]]] = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    target_class: str = "0",
    label_type: str = "test",
    poison_fraction: float = 1.0,
    label_mode: str = "categorical",
) -> pd.DataFrame:
    distance_metrics_list = distance_metrics_list or []
    color_mode: str = "rgb" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]
    adv_data_dir = Path(adv_data_dir)

    validation_split = 1 - poison_fraction

    data_generator: ImageDataGenerator = ImageDataGenerator(
        rescale=rescale, validation_split=validation_split
    )

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=True,
        subset="training",
    )

    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_size = len(data_flow.class_indices)
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

    distance_metrics_: Dict[str, List[List[float]]] = {"image": [], "label": []}
    for metric_name, _ in distance_metrics_list:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate poisoned images",
        attack="backdoor poisoning",
        num_batches=num_images // batch_size,
    )
    target_index = int(target_class)
    backdoor_poisoner = PoisoningAttackBackdoor(add_pattern_bd)

    example_target = np.zeros(class_size)
    example_target[target_index] = 1

    # Apply backdoor poisoning over test set.
    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        LOGGER.info(
            "Generate poisoned image batch",
            attack="backdoor poison",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)

        # TODO: transfer update to other attacks.
        clean_filenames = [
            img_filenames[data_flow.index_array[i]]
            for i in range(batch_num * batch_size, (batch_num + 1) * batch_size)
        ]

        poisoned_x, plabels = backdoor_poisoner.poison(
            x, y=example_target, broadcast=True
        )

        # Swap to poisoned labels if training mode is set.
        if label_type == "train" or label_type == "training":
            y_int = np.argmax(plabels, axis=1)

        _save_batch(
            poisoned_x, adv_data_dir, y_int, clean_filenames, class_names_list, "adv"
        )
        _evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=poisoned_x,
            distance_metrics_list=distance_metrics_list,
        )
    # Save remaining non-poisoned images.
    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
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
        _save_batch(x, adv_data_dir, y_int, filenames, class_names_list, "original")

    LOGGER.info("Adversarial image generation complete", attack="backdoor poison")
    _log_distance_metrics(distance_metrics_)
    return pd.DataFrame(distance_metrics_)


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_adversarial_clean_poison_dataset(
    data_dir: str,
    adv_data_dir: Union[str, Path],
    keras_classifier: TensorFlowV2Classifier,
    image_size: Tuple[int, int, int],
    distance_metrics_list: Optional[List[Tuple[str, Callable[..., np.ndarray]]]] = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    eps: float = 50,
    eps_step: float = 0.1,
    max_iter: int = 300,
    norm: float = 2,
    label_type: str = "train",
    poison_fraction: float = 0.15,
    target_index: int = 0,
) -> pd.DataFrame:

    distance_metrics_list = distance_metrics_list or []
    color_mode: str = "rgb" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]
    adv_data_dir = Path(adv_data_dir)

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=True,
        subset="training",
    )

    class_size = len(data_flow.class_indices)
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)
    targets = to_categorical([target_index], class_size)[0]

    example_target = np.zeros(class_size)
    example_target[target_index] = 1
    distance_metrics_: Dict[str, List[List[float]]] = {"image": [], "label": []}

    for metric_name, _ in distance_metrics_list:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate adversarial images",
        attack="clean label poisoning",
        num_batches=num_images // batch_size,
    )

    backdoor = PoisoningAttackBackdoor(add_pattern_bd)
    backdoor_poisoner = PoisoningAttackCleanLabelBackdoor(
        backdoor=backdoor,
        proxy_classifier=keras_classifier,
        target=targets,
        pp_poison=poison_fraction,
        norm=norm,
        eps=eps,
        eps_step=eps_step,
        max_iter=max_iter,
    )

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = [
            img_filenames[data_flow.index_array[i]]
            for i in range(batch_num * batch_size, (batch_num + 1) * batch_size)
        ]

        LOGGER.info(
            "Generate adversarial image batch",
            attack="clean label poisoning",
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)

        poisoned_x, plabels = backdoor_poisoner.poison(x, y)

        # Swap to poisoned labels if training mode is set.
        if label_type == "train" or label_type == "training":
            y_int = np.argmax(plabels, axis=1)

        _save_batch(
            poisoned_x, adv_data_dir, y_int, clean_filenames, class_names_list, "adv"
        )

        _evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=poisoned_x,
            distance_metrics_list=distance_metrics_list,
        )

    LOGGER.info("Adversarial image generation complete", attack="clean label poisoning")
    _log_distance_metrics(distance_metrics_)

    return pd.DataFrame(distance_metrics_)


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
