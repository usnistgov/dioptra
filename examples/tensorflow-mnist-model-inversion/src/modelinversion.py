from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from prefect import task
from mitre.securingai.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from art.attacks.inference.model_inversion import MIFace
    from art.estimators.classification import KerasClassifier

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

#@pyplugs.register
@task
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def infer_model_inversion(
    data_dir: str,
    adv_data_dir: Union[str, Path],
    keras_classifier: KerasClassifier,
    image_size: Tuple[int, int, int],
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    classes: int = 10,
    max_iter: int = 10000,
    window_length: int = 100,
    threshold: float = 0.99,
    learning_rate: float = 0.1,
) -> None:
    color_mode: str = "color" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]
    adv_data_dir = Path(adv_data_dir)

    attack = _init_miface(
        keras_classifier=keras_classifier,
        batch_size=batch_size,
        max_iter=max_iter,
        window_length=window_length,
        threshold=threshold,
        learning_rate=learning_rate,
    )
    
    attack_inferred = attack.infer(None, y=np.arange(classes))
    
    for c in np.arange(classes):
        _save_adv_batch([attack_inferred[c]], adv_data_dir, c, 'inferred' + str(c) + '.png')

    return None


def _init_miface(
    keras_classifier: KerasClassifier, batch_size: int, **kwargs
) -> MIFace:
    attack: MIFace = MIFace(
        keras_classifier, batch_size=batch_size, **kwargs
    )
    return attack


def _save_adv_batch(adv_batch, adv_data_dir, y, filename) -> None:
    for batch_image_num, adv_image in enumerate(adv_batch):
        adv_image_path = (
            adv_data_dir
            / f"{y}"
            / f"adv_{filename}"
        )
        LOGGER.warn(adv_image_path)
        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)




