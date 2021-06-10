#!/usr/bin/env python
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.

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
