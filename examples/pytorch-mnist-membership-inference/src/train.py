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

import datetime
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


import click
import mlflow
import numpy as np
import structlog
import torch
from data_pytorch import create_image_dataset
from log import configure_stdlib_logger, configure_structlog_logger
from mlflow.tracking.client import MlflowClient
from models_pytorch import le_net, make_model_register
from torch.autograd import Variable
from torch.nn import CrossEntropyLoss
from torch.optim import SGD, Adagrad, Adam, RMSprop

LOGGER = structlog.get_logger()
METRICS = []


def get_optimizer(model, optimizer, learning_rate):
    optimizer_collection = {
        "rmsprop": RMSprop(model.parameters(), learning_rate),
        "adam": Adam(model.parameters(), learning_rate),
        "adagrad": Adagrad(model.parameters(), learning_rate),
        "sgd": SGD(model.parameters(), learning_rate),
    }

    return optimizer_collection.get(optimizer)


def get_model(
    model_architecture: str,
    n_classes: int = 10,
):
    model_collection = {
        "le_net": le_net(input_shape=(28, 28, 1), n_classes=n_classes),
        # "le_net": LeNet(),
    }

    return model_collection.get(model_architecture)


def init_model(learning_rate, model_architecture: str, optimizer: str):
    model = get_model(model_architecture=model_architecture)
    model_optimizer = get_optimizer(
        model=model, optimizer=optimizer, learning_rate=learning_rate
    )

    return model, model_optimizer


def prepare_data(
    data_dir,
    batch_size: int,
    validation_split: float,
    model_architecture: str,
    seed: int,
):
    training_dir = Path(data_dir) / "training"
    testing_dir = Path(data_dir) / "testing"

    image_size = (28, 28)

    training = create_image_dataset(
        data_dir=str(training_dir),
        validation_split=validation_split,
        batch_size=batch_size,
        seed=seed,
        image_size=image_size,
    )
    validation = create_image_dataset(
        data_dir=str(training_dir),
        validation_split=validation_split,
        batch_size=batch_size,
        seed=seed,
        image_size=image_size,
    )
    testing = create_image_dataset(
        data_dir=str(testing_dir),
        validation_split=None,
        batch_size=batch_size,
        seed=seed + 1,
        image_size=image_size,
    )

    return (
        training,
        validation,
        testing,
    )


def fit(model, training_ds, validation_ds, epochs, optimizer):
    time_start = datetime.datetime.now()

    LOGGER.info(
        "training pytorch model",
        timestamp=time_start.isoformat(),
    )
    loss_fn = CrossEntropyLoss()
    ave_loss = 0
    for _, (x, target) in enumerate(training_ds):
        optimizer.zero_grad()
        x, target = Variable(x), Variable(target)
        out = model(x)
        loss = loss_fn(out, target)
        ave_loss = ave_loss * 0.9 + loss.data.item() * 0.1
        loss.backward()
        optimizer.step()

    time_end = datetime.datetime.now()

    total_seconds = (time_end - time_start).total_seconds()
    total_minutes = total_seconds / 60

    mlflow.log_metric("training_time_in_minutes", total_minutes)
    LOGGER.info(
        "pytorch model training complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )
    mlflow.pytorch.log_model(model, "model")
    return model


def evaluate_metrics(model, testing_ds):
    LOGGER.info("evaluating classification metrics using testing images")
    model.eval()
    total = 0
    correct = 0

    for _, (data, target) in enumerate(testing_ds):
        t_x = Variable(data)
        t_y = Variable(target)
        outputs = model(t_x)
        _, predicted = torch.max(outputs.data, 1)
        total += t_y.size(0)
        correct += (predicted == t_y).sum().item()

    accuracy = correct / total
    LOGGER.info("Accuracy:" + str(accuracy))
    mlflow.log_metric(key="accuracy", value=accuracy)


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted datasets (in container)",
)
@click.option(
    "--model-architecture",
    type=click.Choice(["le_net"], case_sensitive=False),
    default="le_net",
    help="Model architecture",
)
@click.option(
    "--epochs",
    type=click.INT,
    help="Number of epochs to train model",
    default=30,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
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
    "--validation-split",
    type=click.FLOAT,
    help="Fraction of training dataset to use for validation",
    default=0.2,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def train(
    data_dir,
    model_architecture,
    epochs,
    batch_size,
    register_model,
    learning_rate,
    optimizer,
    validation_split,
    seed,
):
    register_model = True if register_model == "True" else False
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="train",
        data_dir=data_dir,
        model_architecture=model_architecture,
        epochs=epochs,
        batch_size=batch_size,
        register_model=register_model,
        learning_rate=learning_rate,
        optimizer=optimizer,
        validation_split=validation_split,
        seed=seed,
    )

    dataset_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    mlflow.pytorch.autolog()

    with mlflow.start_run() as active_run:
        mlflow.log_param("entry_point_seed", seed)
        mlflow.log_param("dataset_seed", dataset_seed)

        experiment_name: str = (
            MlflowClient().get_experiment(active_run.info.experiment_id).name
        )
        model_name: str = f"{experiment_name}_{model_architecture}"

        register_mnist_model = make_model_register(
            active_run=active_run,
            name=model_name,
        )

        training_ds, validation_ds, testing_ds = prepare_data(
            data_dir=data_dir,
            validation_split=validation_split,
            batch_size=batch_size,
            model_architecture=model_architecture,
            seed=dataset_seed,
        )
        model, optim = init_model(
            learning_rate=learning_rate,
            model_architecture=model_architecture,
            optimizer=optimizer,
        )
        model = fit(
            model=model,
            training_ds=training_ds,
            validation_ds=validation_ds,
            epochs=epochs,
            optimizer=optim,
        )
        evaluate_metrics(model=model, testing_ds=testing_ds)

        if register_model:
            register_mnist_model(model_dir="model")


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")

    train()
