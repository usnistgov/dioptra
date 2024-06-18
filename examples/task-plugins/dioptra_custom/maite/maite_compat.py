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

import random
from typing import Any, Dict, Tuple

import mlflow
import structlog
from maite import evaluate, load_dataset, load_metric, load_model
from maite._internals.interop.torchvision.datasets import TorchVisionDataset
from structlog.stdlib import BoundLogger
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torchvision.transforms import InterpolationMode
from torchvision.transforms.functional import to_tensor

from dioptra import pyplugs

LOGGER: BoundLogger = structlog.stdlib.get_logger()

@pyplugs.register
def get_dataset_in_maite_format(local: bool = False, dataset_kwargs: Dict[str, Any] = {}):
    if (not local):
      return get_dataset_from_maite(**dataset_kwargs)
    else:
      return get_dataset_from_local(**dataset_kwargs)

@pyplugs.register
def get_dataset_from_maite(provider_name: str, dataset_name: str, task: str, split: str) -> Any:
    dataset = load_dataset(
        provider=provider_name, dataset_name=dataset_name, task=task, split=split
    )
    return dataset


@pyplugs.register
def transform_tensor(
    dataset: Any, shape: Tuple[int, int], totensor: bool = False, subset: int = 0
) -> Any:
    dataset.set_transform(
        lambda x: {
            "image": (
                to_tensor(x["image"].resize(shape))
                if totensor
                else x["image"].reshape(shape)
            ),
            "label": x["label"],
        }
    )
    if subset > 0:
        dataset = [dataset[i] for i in random.sample(range(0, len(dataset)), subset)]
    return dataset

@pyplugs.register
def get_model(local: bool = False, model_kwargs: Dict[str, Any] = {}) -> Any:
    if not local:
        return get_model_from_maite(**model_kwargs)
    else:
        return get_model_from_registry(**model_kwargs)

@pyplugs.register
def get_model_from_maite(
    provider_name: str,
    model_name: str,
    task: str,
    register_model_name: str = "loaded_model",
) -> Any:
    model = load_model(provider=provider_name, model_name=model_name, task=task)
    _register_init_model(register_model_name, "model", model)
    return model


@pyplugs.register
def get_model_from_registry(name: str, version: int) -> Sequential:
    uri: str = f"models:/{name}/{version}"
    LOGGER.info("Load Pytorch classifier from model registry", uri=uri)
    return load_pytorch_model(model_uri=uri)

@pyplugs.register
def get_metric(provider_name: str, metric_name: str, task: str, classes: int) -> Any:
    metric = load_metric(
        provider=provider_name, metric_name=metric_name, task=task, num_classes=classes
    )
    return metric


@pyplugs.register
def compute_metric(
    dataset: Any, model: Any, metric: Any, task: str, batch_size: int
) -> Any:
    evaluator = evaluate(task)
    output = evaluator(
        model,
        dataset,
        metric=dict(accuracy=metric),
        batch_size=batch_size,
    )
    _log_metrics(output)
    return output


def _register_init_model(name, model_dir, model) -> Any:
    mlflow.pytorch.log_model(
        pytorch_model=model, artifact_path=model_dir, registered_model_name=name
    )
    return model


@pyplugs.register
@pyplugs.task_nout(3)
def get_dataset_from_local(
    data_dir: str,
    image_size,
    new_size: int = 0,
    validation_split=0.2,
    batch_size: int = 32,
    label_mode: str = "categorical",
) -> Tuple[Any, Any]:
    """Creates an image dataset from a directory, assuming the
    subdirectories of the directory correspond to the classes of
    the data.

    Args:
        data_dir: A string representing the directory the class
            directories are located in.

        image_size:  The size in pixels of each image in the dataset.

        batch_size: Size of the batches of data.

        validation_split: A float value representing the split between
            training and validation data, if desired.

        label_mode: One of 'int', 'categorical', or 'binary' depending on how the
            classes are organized.

    Returns:
        One or two DataLoader object(s) which can be used to iterate over
        images in the dataset. This will return two DataLoaders if
        validation_split is set, otherwise it will return one.
    """
    color_mode: str = "color" if image_size[2] == 3 else "grayscale"

    transform_list = [transforms.ToTensor()]

    if color_mode == "grayscale":
        transform_list += [transforms.Grayscale()]
    if new_size > 0:
        transform_list += [
            transforms.Resize(
                new_size,
                interpolation=InterpolationMode.BILINEAR,
                max_size=None,
                antialias=True,
            )
        ]
    transform = transforms.Compose(transform_list)

    dataset = ImageFolder(root=data_dir, transform=transform)
    classes = list(dataset.class_to_idx.keys())

    if validation_split is not None:
        train_size = (int)(validation_split * len(dataset))
        val_size = len(dataset) - (int)(validation_split * len(dataset))

        train, val = random_split(dataset, [train_size, val_size])

        train_gen = DataLoader(train, batch_size=batch_size, shuffle=True)
        val_gen = DataLoader(val, batch_size=batch_size, shuffle=True)

        train_gen.dataset.classes = classes
        val_gen.dataset.classes = classes
        return (
            TorchVisionDataset(train_gen.dataset),
            TorchVisionDataset(val_gen.dataset),
        )
    else:
        data_generator = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        data_generator.dataset.classes = classes
        return (TorchVisionDataset(data_generator.dataset), None)


def _log_metrics(metrics: Dict[str, float]) -> None:
    """Logs metrics to the MLFlow Tracking service for the current run.

    Args:
        metrics: A dictionary with the metrics to be logged. The keys are the metric
            names and the values are the metric values.

    See Also:
        - :py:func:`mlflow.log_metric`
    """
    for metric_name, metric_value in metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)
        LOGGER.info(
            "Log metric to MLFlow Tracking server",
            metric_name=metric_name,
            metric_value=metric_value,
        )
