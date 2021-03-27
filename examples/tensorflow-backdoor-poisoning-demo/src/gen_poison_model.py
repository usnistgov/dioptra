#!/usr/bin/env python

import datetime
import os
import warnings
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import tarfile

import click
import mlflow
import mlflow.tensorflow
import numpy as np
import structlog
from art.attacks.poisoning import (
    PoisoningAttackAdversarialEmbedding,
    PoisoningAttackBackdoor,
)
from art.attacks.poisoning.perturbations import add_pattern_bd
from art.estimators.classification import KerasClassifier
from art.utils import load_mnist, preprocess, to_categorical
from data import create_image_dataset, download_image_archive
from log import configure_stdlib_logger, configure_structlog_logger
from mlflow.tracking.client import MlflowClient
from models import alex_net, le_net, make_model_register, shallow_net
from tensorflow.keras.applications.resnet_v2 import ResNet50V2
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
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
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import SGD, Adagrad, Adam, RMSprop

LOGGER = structlog.get_logger()
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


def get_optimizer(optimizer, learning_rate):
    optimizer_collection = {
        "rmsprop": RMSprop(learning_rate),
        "adam": Adam(learning_rate),
        "adagrad": Adagrad(learning_rate),
        "sgd": SGD(learning_rate),
    }

    return optimizer_collection.get(optimizer)


def model_resnet50():
    return ResNet50V2(weights="imagenet", input_shape=(224, 224, 3), include_top=False)


def model_vgg16():
    return VGG16(weights="imagenet", input_shape=(224, 224, 3), include_top=False)


def get_model(
    model_architecture: str,
    n_classes: int,
):
    model_collection = {
        "shallow_net": shallow_net(input_shape=(28, 28, 1), n_classes=n_classes),
        "le_net": le_net(input_shape=(28, 28, 1), n_classes=n_classes),
        "alex_net": alex_net(input_shape=(224, 224, 1), n_classes=n_classes),
        "resnet50": ResNet50V2(
            weights="imagenet", input_shape=(224, 224, 3), include_top=False
        ),
        "vgg16": VGG16(
            weights="imagenet", input_shape=(224, 224, 3), include_top=False
        ),
    }

    keras_models = ["resnet50", "vgg16"]

    if model_architecture in keras_models:
        # Setup top classification layer, and freeze base model layers.
        base_model = model_collection.get(model_architecture)
        top = base_model.output
        top = GlobalAveragePooling2D()(top)
        top = Dense(1024, activation="relu")(top)
        predictions = Dense(n_classes, activation="softmax")(top)
        model = Model(inputs=base_model.input, outputs=predictions)

        for layer in base_model.layers:
            layer.trainable = False
    else:
        model = model_collection.get(model_architecture)
    return model


def get_model_callbacks():
    early_stop = EarlyStopping(
        monitor="val_loss", min_delta=1e-2, patience=5, restore_best_weights=True
    )

    return [early_stop]


def init_model(learning_rate, model_architecture: str, n_classes: int, optimizer: str):
    model_optimizer = get_optimizer(optimizer=optimizer, learning_rate=learning_rate)
    model = get_model(model_architecture=model_architecture, n_classes=n_classes)
    model.compile(
        loss="categorical_crossentropy",
        optimizer=model_optimizer,
        metrics=METRICS,
    )

    return model


def prepare_data_training(
    data_dir_train,
    batch_size: int,
    validation_split: float,
    model_architecture: str,
    seed: int,
):
    training_dir = Path(data_dir_train)

    image_size = (224, 224)
    rescale = 1.0
    imagenet_preprocessing = True
    color_mode = "rgb"
    mnist_models = ["shallow_net", "le_net", "alex_net"]

    if model_architecture in mnist_models:
        if model_architecture != "alex_net":
            image_size = (28, 28)
        rescale = 1.0 / 255
        color_mode = "grayscale"
        imagenet_preprocessing = False

    training = create_image_dataset(
        data_dir=str(training_dir),
        subset="training",
        validation_split=validation_split,
        batch_size=batch_size,
        seed=seed,
        image_size=image_size,
        rescale=rescale,
        color_mode=color_mode,
        imagenet_preprocessing=imagenet_preprocessing,
    )
    return training


def prepare_data(
    data_dir_train,
    data_dir_test,
    batch_size: int,
    validation_split: float,
    model_architecture: str,
    seed: int,
):
    training_dir = Path(data_dir_train)
    testing_dir = Path(data_dir_test)

    image_size = (224, 224)
    rescale = 1.0
    imagenet_preprocessing = True
    color_mode = "rgb"
    mnist_models = ["shallow_net", "le_net", "alex_net"]

    if model_architecture in mnist_models:
        if model_architecture != "alex_net":
            image_size = (28, 28)
        rescale = 1.0 / 255
        color_mode = "grayscale"
        imagenet_preprocessing = False

    training = create_image_dataset(
        data_dir=str(training_dir),
        subset="training",
        validation_split=validation_split,
        batch_size=batch_size,
        seed=seed,
        image_size=image_size,
        rescale=rescale,
        color_mode=color_mode,
        imagenet_preprocessing=imagenet_preprocessing,
    )
    validation = create_image_dataset(
        data_dir=str(training_dir),
        subset="validation",
        validation_split=validation_split,
        batch_size=batch_size,
        seed=seed,
        image_size=image_size,
        rescale=rescale,
        color_mode=color_mode,
        imagenet_preprocessing=imagenet_preprocessing,
    )
    testing = create_image_dataset(
        data_dir=str(testing_dir),
        subset=None,
        validation_split=None,
        batch_size=batch_size,
        seed=seed + 1,
        image_size=image_size,
        rescale=rescale,
        color_mode=color_mode,
        imagenet_preprocessing=imagenet_preprocessing,
    )

    return (
        training,
        validation,
        testing,
    )


def fit(model, training_ds, validation_ds, epochs):
    time_start = datetime.datetime.now()

    LOGGER.info(
        "training tensorflow model",
        timestamp=time_start.isoformat(),
    )

    history = model.fit(
        training_ds,
        epochs=epochs,
        validation_data=validation_ds,
        callbacks=get_model_callbacks(),
        verbose=1,
    )

    time_end = datetime.datetime.now()

    total_seconds = (time_end - time_start).total_seconds()
    total_minutes = total_seconds / 60

    mlflow.log_metric("training_time_in_minutes", total_minutes)
    LOGGER.info(
        "tensorflow model training complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )

    return history, model


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


@click.command()
@click.option(
    "--data-dir-train",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted training dataset (in container)",
)
@click.option(
    "--data-dir-test",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted training dataset (in container)",
)
@click.option(
    "--model-architecture",
    type=click.Choice(
        ["shallow_net", "le_net", "alex_net", "resnet50", "vgg16"], case_sensitive=False
    ),
    default="vgg16",
    help="Model architecture",
)
@click.option(
    "--epochs",
    type=click.INT,
    help="Number of epochs to train model",
    default=10,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch.",
    default=32,
)
@click.option(
    "--register-model",
    type=click.Choice(["True", "False"], case_sensitive=True),
    default="False",
    help="Add trained model to registry",
)
@click.option(
    "--learning-rate", type=click.FLOAT, help="Model learning rate", default=0.001
)
@click.option(
    "--optimizer",
    type=click.Choice(["adam", "adagrad", "rmsprop", "sgd"], case_sensitive=False),
    help="Optimizer to use to train the model",
    default="adam",
)
@click.option(
    "--training-split",
    type=click.FLOAT,
    help="Fraction of training dataset to use for embedding attack. ART attack takes in training data as a single numpy array which limits dataset sizes.",
    default=1.0,
)
@click.option(
    "--model-tag",
    type=click.STRING,
    help="Optional model tag identifier.",
    default="",
)
@click.option(
    "--load-dataset-from-mlruns",
    type=click.BOOL,
    help="If set to true, instead loads the training and test datasets from a previous poison mlruns.",
    default=False,
)
@click.option(
    "--training-dataset-run-id",
    type=click.STRING,
    help="MLFlow Run ID of a successful poison attack on a training dataset.",
    default="None",
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
@click.option(
    "--target-class-id",
    type=click.INT,
    help="Index of target class for backdoor poison.",
    default=1,
)
@click.option(
    "--feature-layer-index",
    type=click.INT,
    help="Index of feature layer for backdoor poisoning.",
    default=6,
)
@click.option(
    "--discriminator-layer-1-size",
    type=click.INT,
    help="The size of the first discriminator layer.",
    default=256,
)
@click.option(
    "--discriminator-layer-2-size",
    type=click.INT,
    help="The size of the second discriminator layer.",
    default=128,
)
@click.option(
    "--regularization-factor",
    type=click.FLOAT,
    help="The regularization constant for the backdoor recognition part of the loss function.",
    default=30.0,
)
@click.option(
    "--poison-fraction",
    type=click.FLOAT,
    help="The fraction of training data to be poisoned. Range 0 to 1.",
    default=0.10,
)
def train(
    data_dir_train,
    data_dir_test,
    model_architecture,
    model_tag,
    epochs,
    batch_size,
    register_model,
    learning_rate,
    optimizer,
    training_split,
    load_dataset_from_mlruns,
    training_dataset_run_id,
    seed,
    target_class_id,
    feature_layer_index,
    discriminator_layer_1_size,
    discriminator_layer_2_size,
    regularization_factor,
    poison_fraction,
):
    validation_split = 1 - training_split
    register_model = True if register_model == "True" else False
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="train_poison",
        data_dir_train=data_dir_train,
        data_dir_test=data_dir_test,
        model_architecture=model_architecture,
        epochs=epochs,
        batch_size=batch_size,
        register_model=register_model,
        learning_rate=learning_rate,
        optimizer=optimizer,
        validation_split=validation_split,
        seed=seed,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    dataset_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)

    mlflow.tensorflow.autolog()

    with mlflow.start_run() as active_run:
        mlflow.log_param("entry_point_seed", seed)
        mlflow.log_param("tensorflow_global_seed", tensorflow_global_seed)
        mlflow.log_param("dataset_seed", dataset_seed)

        experiment_name: str = (
            MlflowClient().get_experiment(active_run.info.experiment_id).name
        )

        if len(model_tag) > 0:
            model_name = f"{experiment_name}_{model_tag}_{model_architecture}"
        else:
            model_name = f"{experiment_name}_{model_architecture}"

        if load_dataset_from_mlruns:
            data_dir_train = Path.cwd() / "training" / "adv_poison_dataset"
            data_train_tar_name = "adversarial_poison_dataset.tar.gz"
            adv_training_tar_path = download_image_archive(
                run_id=training_dataset_run_id, archive_path=data_train_tar_name
            )
            with tarfile.open(adv_training_tar_path, "r:gz") as f:
                f.extractall(path=(Path.cwd() / "training"))

        register_mnist_model = make_model_register(
            active_run=active_run,
            name=model_name,
        )

        training_ds, validation_ds, testing_ds = prepare_data(
            data_dir_train=data_dir_train,
            data_dir_test=data_dir_test,
            validation_split=validation_split,
            batch_size=batch_size,
            model_architecture=model_architecture,
            seed=dataset_seed,
        )

        n_classes = len(training_ds.class_indices)
        model = init_model(
            learning_rate=learning_rate,
            model_architecture=model_architecture,
            n_classes=n_classes,
            optimizer=optimizer,
        )

        # TODO: Double check model register saves intended poisoned model
        # if register_model:
        #     register_mnist_model(model_dir="model")

        poison_model = KerasClassifier(model)

        # x_train, y_train = training_ds.next()

        # batch_index = 1

        # while batch_index <= training_ds.batch_index:
        #    x,y = training_ds.next()
        #    x_train = x_train + x
        #    y_train = y_train + y
        #    batch_index = batch_index + 1

        training_ds_full = prepare_data_training(
            data_dir_train=data_dir_train,
            validation_split=validation_split,
            batch_size=training_ds.n,
            model_architecture=model_architecture,
            seed=dataset_seed,
        )

        x_train, y_train = training_ds_full.next()

        # Poison some percentage of all non-target-images to target-label

        targets = to_categorical([target_class_id], n_classes)[0]

        # emb_attack = PoisoningAttackAdversarialEmbedding(classifier=poison_model, backdoor=backdoor, feature_layer=5,
        #                                                 target=targets, regularization=30.0, pp_poison=percent_poison,
        #                                                 discriminator_layer_1=256, discriminator_layer_2=128,
        #                                                 learning_rate=1e-4)

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
            optimizer=get_optimizer(optimizer=optimizer, learning_rate=learning_rate),
            metrics=METRICS,
        )

        mlflow.keras.log_model(
            keras_model=model, artifact_path="model", registered_model_name=model_name
        )

        # history, model = fit(
        #    model=model,
        #    training_ds=training_ds,
        #    validation_ds=validation_ds,
        #    epochs=epochs,
        # )

        evaluate_metrics(model=model, testing_ds=testing_ds)


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    train()
