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
from typing import Union

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import ARTDependencyError, TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from art.attacks.inference.model_inversion import MIFace
    from art.estimators.classification import TensorFlowV2Classifier

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


try:
    from tensorflow.keras.preprocessing.image import save_img

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def infer_model_inversion(
    keras_classifier: TensorFlowV2Classifier,
    adv_data_dir: Union[str, Path],
    batch_size: int = 32,
    classes: int = 10,
    max_iter: int = 10000,
    window_length: int = 100,
    threshold: float = 0.99,
    learning_rate: float = 0.1,
) -> None:
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
        _save_adv_batch([attack_inferred[c]], adv_data_dir, c, f"inferred{c}.png")

    return None


def _init_miface(
    keras_classifier: TensorFlowV2Classifier, batch_size: int, **kwargs
) -> MIFace:
    # MIFace uses the classifier's input shape but does not expect None as the first
    # element representing batch size.
    keras_classifier._input_shape = keras_classifier.input_shape[1:]
    attack: MIFace = MIFace(keras_classifier, batch_size=batch_size, **kwargs)
    return attack


def _save_adv_batch(adv_batch, adv_data_dir, y, filename) -> None:
    for adv_image in adv_batch:
        adv_image_path = adv_data_dir / f"{y}" / f"adv_{filename}"
        LOGGER.warn(adv_image_path)
        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)
