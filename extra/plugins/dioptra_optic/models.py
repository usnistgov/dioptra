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
from types import ModuleType
from typing import Any, Callable

import keras
import keras.applications as kapp
import numpy as np
import pandas as pd
import structlog
import tensorflow as tf
from keras.layers import (
    BatchNormalization,
    Conv2D,
    Dense,
    Dropout,
    Flatten,
    Input,
    MaxPooling2D,
)
from keras.models import Sequential

from dioptra import pyplugs

from .data import DatasetMetadata
from .utils import DioptraMetricsLoggingCallback

LOGGER = structlog.get_logger()


@pyplugs.register
def create_model(
    model_name: str,
    dataset_meta: DatasetMetadata,
    model_options: dict[str, Any] | None = None,
    loss: str = "categorical_crossentropy",
    loss_options: dict[str, Any] | None = None,
    optimizer: str = "Adam",
    learning_rate: float = 0.001,
    optimizer_options: dict[str, Any] | None = None,
    metrics: list[str | dict[str, Any]] | None = None,
) -> keras.Model:
    """Initializes an untrained neural network image classifier for Tensorflow/Keras.

    The `model_name` argument is used to select a neural network architecture
    from the architecture registry. The string passed to `model_name` must match
    one of the following,

    - `"ShallowNet"` - A shallow neural network architecture.
    - `"LeNet"` - The LeNet-5 convolutional neural network architecture.
    - `"AlexNet"` - The AlexNet convolutional neural network architecture.
    - Any of the models available at https://keras.io/api/applications/

    Args:
        model_name: The neural network architecture to use.
        dataset_meta: A DatasetMetadata object used to get input_shape, and number of classes
        loss: A string specifying the loss function to be minimized during training. The
            string must match the name of one of the loss functions in the
            :py:mod:`keras.losses` module. The default is
            `"categorical_crossentropy"`.
        loss_options: A dictionary of options (name, value) specific to `loss`.
        optimizer: A string representing a  Keras :py:class:`~keras.optimizers.Optimizer`
            used to train the estimator, such as :py:class:`~keras.optimizers.SGD` and
            :py:class:`~keras.optimizers.Adam`. The optimzier object is constructed via
            `keras.optimizers.get(optimizer).from_config(optimizer_options)`
        learning_rate: The learning rate for `optimizer`. Overrided by optimizer_options.
        optimizer_options: A dictionary of options (name, value) specific to `optimizer`.
        metrics: A list of metrics to be evaluated by the model during training and
            testing.

    Returns:
        A compiled :py:class:`~keras.Model` object.

    See Also:
        - :py:mod:`keras.losses`
        - :py:mod:`keras.optimizers`
        - :py:mod:`keras.metrics`
        - :py:class:`keras.Model`
    """
    model_options = model_options or {}
    loss_options = loss_options or {}
    optimizer_options = optimizer_options or {"learning_rate": learning_rate}
    metrics = metrics or [
        "categorical_accuracy",
        "auc",
        "precision",
        "recall",
        {"name": "f1_score", "options": {"average": "weighted"}},
    ]

    LOGGER.info(f"initializing {model_name} model", task="create_model")
    model = KERAS_CLASSIFIERS_REGISTRY[model_name](
        input_shape=dataset_meta.image_shape,
        classes=dataset_meta.num_classes,
        **model_options,
    )

    optimizer = keras.optimizers.get(optimizer).from_config(optimizer_options)

    metrics = [
        keras.metrics.get(metric)
        if isinstance(metric, str)
        else keras.metrics.get(metric["name"]).from_config(metric.get("options", {}))
        for metric in metrics
    ]

    model.compile(loss=loss, optimizer=optimizer, metrics=metrics)

    return model


@pyplugs.register
def train_model(
    model: keras.Model,
    train_dataset: tf.data.Dataset,
    val_dataset: tf.data.Dataset | None = None,
    epochs: int = 1,
    callbacks: list[dict[str, Any]] | None = None,
    fit_options: dict[str, Any] | None = None,
) -> keras.Model:
    """Trains a keras model using model.fit.
    Registers metrics to the Dioptra Job.

    Args:
        model: The keras model to be trained.
        train_dataset: The dataset used to train the model.
        val_dataset: The dataset used to validate the model after each epoch of training.
        epochs: The number of full passes through the dataset to train the model for.
        callbacks: A list of keras callbacks.
            See https://keras.io/api/callbacks/ for the full list.
        fit_options: Additional options passed as keyword arguments to model.fit
    Returns:
        The trained keras model.
    """
    callbacks = [] if callbacks is None else callbacks
    fit_options = {} if fit_options is None else fit_options

    callbacks: list = [
        getattr(keras.callbacks, callback["name"])(**callback.get("parameters", {}))
        for callback in callbacks
    ]
    callbacks.append(DioptraMetricsLoggingCallback(LOGGER))

    LOGGER.info(f"training model for {epochs}", options=fit_options, task="train_model")
    model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=epochs,
        verbose=2,
        callbacks=callbacks,
        **fit_options,
    )
    LOGGER.info("model training complete", task="train_model")

    return model


@pyplugs.register
def evaluate_model(
    model: keras.Model,
    dataset: tf.data.Dataset,
    metrics: list[str | dict[str, Any]] | None = None,
) -> pd.DataFrame:
    """
    Evaluates the keras model by calling model.evaluate.

    Args:
        model: The keras model to evaluate.
        dataset: The dataset to use in evaluation.
        metrics: A list of metrics to be evaluated by the model.
            If None, use the metrics already compiled to the model.

    Returns:
        A DataFrame containing the computed metrics.
    """
    if metrics is not None:
        metrics = [
            keras.metrics.get(metric)
            if isinstance(metric, str)
            else keras.metrics.get(metric["name"]).from_config(
                metric.get("options", {})
            )
            for metric in metrics
        ]
        model.compile(metrics)

    LOGGER.info("begin model eval", task="evaluate_model")
    metrics = model.evaluate(
        dataset,
        callbacks=[DioptraMetricsLoggingCallback(LOGGER)],
        verbose=0,
        return_dict=True,
    )
    return pd.DataFrame(metrics, index=pd.Index([0]))


@pyplugs.register
def evaluate_predictions(
    predictions: pd.DataFrame,
    dataset: tf.data.Dataset,
    metrics: list[str | dict[str, Any]] = [
        "categorical_accuracy",
        "auc",
        "precision",
        "recall",
        {"name": "f1_score", "options": {"average": "weighted"}},
    ],
) -> pd.DataFrame:
    """
    Evaluates predictions from a model.

    Args:
        predictions: The predictions used to compute metrics.
        dataset: The dataset containing the labels.
        metrics: A list of metrics to be evaluated by the model.
            If None, use the metrics already compiled to the model.

    Returns:
        A DataFrame containing the computed metrics.
    """
    metrics_callback = DioptraMetricsLoggingCallback(LOGGER)

    metrics_fns: list[keras.Metric] = [
        keras.metrics.get(metric)
        if isinstance(metric, str)
        else keras.metrics.get(metric["name"]).from_config(metric.get("options", {}))
        for metric in metrics
    ]

    labels = np.concatenate([y for _, y in dataset])

    for metric in metrics_fns:
        metric.update_state(labels, predictions)

    metrics_results = {metric.name: metric.result().numpy() for metric in metrics_fns}

    LOGGER.info("metrics", metrics=metrics_results)
    metrics_callback.on_test_end(logs=metrics_results)

    return pd.DataFrame(metrics_results, index=pd.Index([0]))


@pyplugs.register
def model_predict(
    model: keras.Model,
    dataset: tf.data.Dataset,
) -> pd.DataFrame:
    predictions = model.predict(
        dataset, callbacks=[DioptraMetricsLoggingCallback(LOGGER)], verbose=0
    )
    return pd.DataFrame(predictions)


def shallow_net(input_shape: tuple[int, int, int], classes: int) -> Sequential:
    """Builds an untrained shallow neural network architecture for Tensorflow/Keras.

    Args:
        input_shape: A shape tuple of integers, not including the batch size, specifying
            the dimensions of the image data. The shape tuple for all classifiers in the
            architecture registry follows the convention `(height, width, channels)`.
        classes: The number of target labels in the dataset.

    Returns:
        A :py:class:`~keras.Sequential` object.

    See Also:
        - :py:class:`keras.Sequential`
    """
    model = Sequential()

    # Flatten inputs
    model.add(Flatten(input_shape=input_shape))

    # single hidden layer:
    model.add(Dense(32, activation="sigmoid"))

    # output layer:
    model.add(Dense(classes, activation="softmax"))

    return model


def le_net(input_shape: tuple[int, int, int], classes: int) -> Sequential:
    """Builds an untrained LeNet-5 neural network architecture for Tensorflow/Keras.

    Args:
        input_shape: A shape tuple of integers, not including the batch size, specifying
            the dimensions of the image data. The shape tuple for all classifiers in the
            architecture registry follows the convention `(height, width, channels)`.
        classes: The number of target labels in the dataset.

    Returns:
        A :py:class:`~keras.Sequential` object.

    See Also:
        - :py:class:`keras.Sequential`
    """
    model = Sequential()

    # input layer
    model.add(Input(shape=input_shape))

    # first convolutional layer:
    model.add(Conv2D(32, kernel_size=(3, 3), activation="relu"))

    # second conv layer, with pooling and dropout:
    model.add(Conv2D(64, kernel_size=(3, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    model.add(Flatten())

    # dense hidden layer, with dropout:
    model.add(Dense(128, activation="relu"))
    model.add(Dropout(0.5))

    # output layer:
    model.add(Dense(classes, activation="softmax"))

    return model


def alex_net(input_shape: tuple[int, int, int], classes: int) -> Sequential:
    """Builds an untrained AlexNet neural network architecture for Tensorflow/Keras.

    Args:
        input_shape: A shape tuple of integers, not including the batch size, specifying
            the dimensions of the image data. The shape tuple for all classifiers in the
            architecture registry follows the convention `(height, width, channels)`.
        classes: The number of target labels in the dataset.

    Returns:
        A :py:class:`~keras.Sequential` object.

    See Also:
        - :py:class:`keras.Sequential`
    """
    model = Sequential()

    # first conv-pool block:
    model.add(
        Conv2D(
            96,
            kernel_size=(11, 11),
            strides=(4, 4),
            activation="relu",
            input_shape=input_shape,
        )
    )
    model.add(MaxPooling2D(pool_size=(3, 3), strides=(2, 2)))
    model.add(BatchNormalization())

    # second conv-pool block:
    model.add(Conv2D(256, kernel_size=(5, 5), activation="relu"))
    model.add(MaxPooling2D(pool_size=(3, 3), strides=(2, 2)))
    model.add(BatchNormalization())

    # third conv-pool block:
    model.add(Conv2D(256, kernel_size=(3, 3), activation="relu"))
    model.add(Conv2D(384, kernel_size=(3, 3), activation="relu"))
    model.add(Conv2D(384, kernel_size=(3, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(3, 3), strides=(2, 2)))
    model.add(BatchNormalization())

    # dense layers:
    model.add(Flatten())
    model.add(Dense(4096, activation="tanh"))
    model.add(Dropout(0.5))
    model.add(Dense(4096, activation="tanh"))
    model.add(Dropout(0.5))

    # output layer:
    model.add(Dense(classes, activation="softmax"))

    return model


def _get_keras_init_fn(module: ModuleType, model_name: str) -> Callable:
    """
    Builds a Callable that initializes a `keras.applications` image classifier with preprocessing.

    Args:
        module: The Python module that has a `preprocess_input` function and `model_name` function.
        model_name: The model name matching the function name in `module` that initalizes the model.
    Returns:
        A Callable whose signature matches matches ModelFn(input_shape, classes, **model_kwargs).

    """
    model_fn = getattr(module, model_name)

    def fn(input_shape: tuple[int, int, int], classes: int, **model_kwargs):
        i = Input([None, None, 3], dtype="uint8")
        x = keras.ops.cast(i, "float32")
        x = module.preprocess_input(x)
        core = model_fn(input_shape=input_shape, classes=classes, **model_kwargs)
        x = core(x)
        model = keras.Model(inputs=[i], outputs=[x])
        return model

    return fn


KERAS_CLASSIFIERS_REGISTRY = {
    "ShallowNet": shallow_net,
    "LeNet": le_net,
    "AlexNet": alex_net,
    "ConvNeXtBase": _get_keras_init_fn(kapp.convnext, "ConvNeXtBase"),
    "ConvNeXtLarge": _get_keras_init_fn(kapp.convnext, "ConvNeXtLarge"),
    "ConvNeXtSmall": _get_keras_init_fn(kapp.convnext, "ConvNeXtSmall"),
    "ConvNeXtTiny": _get_keras_init_fn(kapp.convnext, "ConvNeXtTiny"),
    "ConvNeXtXLarge": _get_keras_init_fn(kapp.convnext, "ConvNeXtXLarge"),
    "DenseNet121": _get_keras_init_fn(kapp.densenet, "DenseNet121"),
    "DenseNet169": _get_keras_init_fn(kapp.densenet, "DenseNet169"),
    "DenseNet201": _get_keras_init_fn(kapp.densenet, "DenseNet201"),
    "EfficientNetB0": _get_keras_init_fn(kapp.efficientnet, "EfficientNetB0"),
    "EfficientNetB1": _get_keras_init_fn(kapp.efficientnet, "EfficientNetB1"),
    "EfficientNetB2": _get_keras_init_fn(kapp.efficientnet, "EfficientNetB2"),
    "EfficientNetB3": _get_keras_init_fn(kapp.efficientnet, "EfficientNetB3"),
    "EfficientNetB4": _get_keras_init_fn(kapp.efficientnet, "EfficientNetB4"),
    "EfficientNetB5": _get_keras_init_fn(kapp.efficientnet, "EfficientNetB5"),
    "EfficientNetB6": _get_keras_init_fn(kapp.efficientnet, "EfficientNetB6"),
    "EfficientNetB7": _get_keras_init_fn(kapp.efficientnet, "EfficientNetB7"),
    "EfficientNetV2B0": _get_keras_init_fn(kapp.efficientnet_v2, "EfficientNetV2B0"),
    "EfficientNetV2B1": _get_keras_init_fn(kapp.efficientnet_v2, "EfficientNetV2B1"),
    "EfficientNetV2B2": _get_keras_init_fn(kapp.efficientnet_v2, "EfficientNetV2B2"),
    "EfficientNetV2B3": _get_keras_init_fn(kapp.efficientnet_v2, "EfficientNetV2B3"),
    "EfficientNetV2L": _get_keras_init_fn(kapp.efficientnet_v2, "EfficientNetV2L"),
    "EfficientNetV2M": _get_keras_init_fn(kapp.efficientnet_v2, "EfficientNetV2M"),
    "EfficientNetV2S": _get_keras_init_fn(kapp.efficientnet_v2, "EfficientNetV2S"),
    "InceptionResNetV2": _get_keras_init_fn(
        kapp.inception_resnet_v2, "InceptionResNetV2"
    ),
    "InceptionV3": _get_keras_init_fn(kapp.inception_v3, "InceptionV3"),
    "MobileNet": _get_keras_init_fn(kapp.mobilenet, "MobileNet"),
    "MobileNetV2": _get_keras_init_fn(kapp.mobilenet_v2, "MobileNetV2"),
    # "MobileNetV3Large": _get_keras_init_fn(kapp.mobilenet_v3, "MobileNetV3Large"),
    # "MobileNetV3Small": _get_keras_init_fn(kapp.mobilenet_v3, "MobileNetV3Small"),
    "NASNetLarge": _get_keras_init_fn(kapp.nasnet, "NASNetLarge"),
    "NASNetMobile": _get_keras_init_fn(kapp.nasnet, "NASNetMobile"),
    "ResNet101": _get_keras_init_fn(kapp.resnet, "ResNet101"),
    "ResNet101V2": _get_keras_init_fn(kapp.resnet_v2, "ResNet101V2"),
    "ResNet152": _get_keras_init_fn(kapp.resnet, "ResNet152"),
    "ResNet152V2": _get_keras_init_fn(kapp.resnet_v2, "ResNet152V2"),
    "ResNet50": _get_keras_init_fn(kapp.resnet, "ResNet50"),
    "ResNet50V2": _get_keras_init_fn(kapp.resnet_v2, "ResNet50V2"),
    "VGG16": _get_keras_init_fn(kapp.vgg16, "VGG16"),
    "VGG19": _get_keras_init_fn(kapp.vgg19, "VGG19"),
    "Xception": _get_keras_init_fn(kapp.xception, "Xception"),
}
