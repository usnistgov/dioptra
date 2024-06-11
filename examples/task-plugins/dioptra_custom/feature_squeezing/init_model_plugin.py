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

import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
import tensorflow as tf
from tensorflow.keras.applications.mobilenet import MobileNet
from tensorflow.keras.applications.resnet import ResNet50
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.metrics import (
    AUC,
    CategoricalAccuracy,
    FalseNegatives,
    FalsePositives,
    Precision,
    Recall,
    TrueNegatives,
    TruePositives,
)
from tensorflow.keras.models import Sequential

from dioptra import pyplugs
from dioptra.sdk.exceptions import ARTDependencyError, TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

tf.compat.v1.disable_eager_execution()
warnings.filterwarnings("ignore")

LOGGER = structlog.get_logger()

# List of Keras model metrics.
METRICS = [
    TruePositives(name="tp"),
    FalsePositives(name="fp"),
    TrueNegatives(name="tn"),
    FalseNegatives(name="fn"),
    CategoricalAccuracy(name="accuracy"),
    Precision(name="precision"),
    Recall(name="recall"),
    AUC(name="auc"),
]


def model_resnet50():
    return ResNet50(weights="imagenet", input_shape=(224, 224, 3))


def model_vgg16():
    return VGG16(weights="imagenet", input_shape=(224, 224, 3))


def model_mobilenet():
    return MobileNet(
        weights="imagenet", input_shape=(224, 224, 3), classes=1000
    )  # , classifier_activation=None)


def evaluate_metrics(model, testing_ds):
    LOGGER.info("evaluating classification metrics using testing images")
    result = model.evaluate(testing_ds, verbose=0)
    testing_metrics = dict(zip(model.metrics_names, result))
    LOGGER.info(
        "computation of classification metrics for testing images complete",
        **testing_metrics,
    )
    for metric_name, metric_value in testing_metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)


# Load pretrained model and test against input dataset.


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def load_and_test_model(
    data_dir, model_architecture, batch_size, seed, register_model_name
):
    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    tensorflow_global_seed: int = rng.integers(low=0, high=2**31 - 1)
    dataset_seed: int = rng.integers(low=0, high=2**31 - 1)

    tf.random.set_seed(tensorflow_global_seed)
    mlflow.tensorflow.autolog()
    """
    with mlflow.start_run() as active_run:
    """
    mlflow.log_param("entry_point_seed", seed)
    mlflow.log_param("tensorflow_global_seed", tensorflow_global_seed)
    mlflow.log_param("dataset_seed", dataset_seed)

    model_name = f"{register_model_name}"

    LOGGER.info(
        "Loading Pretrained Model",
        model_name=model_name,
        model_architecture=model_architecture,
    )

    model_collection = {
        "resnet50": model_resnet50,
        "vgg16": model_vgg16,
        "mobilenet": model_mobilenet,
    }
    if model_architecture == "mobilenet":
        temp = model_collection[model_architecture]()
        newmodel = Sequential()
        for layer in temp.layers[:-1]:
            newmodel.add(layer)
        newmodel.summary()

        newmodel.compile(
            loss="categorical_crossentropy",
            metrics=METRICS,
        )

        mlflow.tensorflow.log_model(
            model=newmodel,
            artifact_path="model",
            registered_model_name=model_name + "_logits",
        )
        model = newmodel
    model = model_collection[model_architecture]()
    model.summary()
    model.compile(
        loss="categorical_crossentropy",
        metrics=METRICS,
    )
    if model_architecture != "mobilenet":
        mlflow.tensorflow.log_model(
            model=model,
            artifact_path="model",
            registered_model_name=model_name,
        )

    return model
