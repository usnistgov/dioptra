#!/usr/bin/env python
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

import warnings
from pathlib import Path
from typing import Tuple

warnings.filterwarnings("ignore")


import mlflow
import numpy
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from art.attacks.evasion import FastGradientMethod
from art.attacks.inference.membership_inference.black_box import (
    MembershipInferenceBlackBox,
)
from art.estimators.classification import PyTorchClassifier
from data_pytorch import create_image_dataset
from metrics import membership_guess_accuracy
from models_pytorch import load_model_in_registry
from torch.autograd import Variable
from torch.nn import CrossEntropyLoss
from torch.optim import SGD, Adagrad, Adam, RMSprop

LOGGER = structlog.get_logger()
DISTANCE_METRICS = [
    # ("membership_guess_accuracy", membership_guess_accuracy),
]


def wrap_torch_classifier(model, loss_fn, input_shape, classes):
    torch_model = load_model_in_registry(model=model)
    return PyTorchClassifier(
        model=torch_model, loss=loss_fn, input_shape=input_shape, nb_classes=classes
    )


def init_mi(model, loss_fn, input_shape, classes, **kwargs):
    classifier = wrap_torch_classifier(model, loss_fn, input_shape, classes, **kwargs)
    attack = MembershipInferenceBlackBox(
        classifier=classifier, input_type="loss", **kwargs
    )
    return classifier, attack


def infer_membership(
    data_dir: str,
    model: str,
    adv_data_dir: Path = None,
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (1, 28, 28),
    **kwargs,
):
    classifier, attack = init_mi(
        model=model,
        loss_fn=CrossEntropyLoss(),
        input_shape=image_size,
        classes=10,
        **kwargs,
    )
    training_dir = Path(data_dir) / "training"
    testing_dir = Path(data_dir) / "testing"

    training_ds = create_image_dataset(data_dir=training_dir, batch_size=batch_size)
    testing_ds = create_image_dataset(data_dir=testing_dir, batch_size=batch_size)
    attack_train_ratio = 0.5

    x_train = next(iter(training_ds))[0].numpy()
    y_train = next(iter(training_ds))[1].numpy()

    x_test = next(iter(testing_ds))[0].numpy()
    y_test = next(iter(testing_ds))[1].numpy()

    LOGGER.info(
        "Shapes::" + str(attack.estimator.input_shape) + ":" + str(x_train.shape)
    )

    attack_train_size = int(len(x_train) * attack_train_ratio)
    attack_test_size = int(len(x_test) * attack_train_ratio)
    attack.fit(
        x_train[:attack_train_size],
        y_train[:attack_train_size],
        x_test[:attack_test_size],
        y_test[:attack_test_size],
    )

    # infer attacked feature on remainder of data
    inferred_train = attack.infer(
        x_train[attack_train_size:], y_train[attack_train_size:]
    )
    inferred_test = attack.infer(x_test[attack_test_size:], y_test[attack_test_size:])

    trainacc = (sum(inferred_train)) / len(inferred_train)
    testacc = (sum(inferred_test)) / len(inferred_test)

    accuracy = (sum(inferred_train) + sum(inferred_test)) / (
        len(inferred_train) + len(inferred_test)
    )

    LOGGER.info("Accuracy:" + str(accuracy))
    LOGGER.info(
        "Accuracy Train:" + str(trainacc) + ": Length : " + str(len(inferred_train))
    )
    LOGGER.info(
        "Accuracy Test:" + str(testacc) + ": Length : " + str(len(inferred_test))
    )
    mlflow.log_metric(key="accuracy", value=accuracy)

    return None
