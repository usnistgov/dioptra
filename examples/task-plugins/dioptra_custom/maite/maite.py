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

from types import FunctionType
from typing import Any, Dict, List, Union

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

from maite import load_dataset
from maite import load_model
from maite import load_metric
from maite import evaluate
from torchvision.transforms.functional import to_tensor

@pyplugs.register
def get_dataset(provider_name: str, dataset_name: str, task: str, split: str) -> Any:
    dataset = load_dataset(
        provider=provider_name,
        dataset_name=dataset_name,
        task=task,
        split=split
    )
    return dataset
@pyplugs.register
def transform_tensor(dataset: Any, shape: Tuple[int, int], subset: int = 0) -> Any:
    dataset.set_transform(
        lambda x: {
            "image": to_tensor(x["image"].resize(shape)),
            "label": x["label"]
        }
    )
    if (subset > 0):
        dataset = [dataset[i] for i in range(subset)]
    print(type(dataset))
    print(dataset[0])
    return dataset
@pyplugs.register
def get_model(provider_name: str, model_name: str, task: str) -> Any:
    model = load_model(
        provider=provider_name,
        model_name=model_name,
        task=task
    )
    return model
@pyplugs.register
def get_metric(provider_name: str, metric_name: str, task: str, classes: int) -> Any:
    metric = load_metric(
        provider=provider_name,
        metric_name=metric_name,
        task=task,
        num_classes=classes
    )
    return metric
@pyplugs.register
def compute_metric(dataset: Any, model: Any, metric: Any, task: string, batch_size: int) -> Any: 
    evaluator = evaluate(task)
    output = evaluator(
      model,
      dataset,
      metric=dict(accuracy=metric),
      batch_size=batch_size,
    )
    print(output)
    return output
@pyplugs.register
def register_init_model(name, model_dir, model) -> Model:
    mlflow.pytorch.log_model(
        pytorch_model=model, artifact_path=model_dir, registered_model_name=name
    )
    return model
