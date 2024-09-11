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
from typing import Callable, Dict, List, Optional, Tuple, Union, Any

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from .tensorflow import get_optimizer, get_model_callbacks, get_performance_metrics, evaluate_metrics_tensorflow
from .estimators_keras_classifiers import init_classifier
from .registry_art import load_wrapped_tensorflow_keras_classifier
from .random_rng import init_rng
from .random_sample import draw_random_integer
from .backend_configs_tensorflow import init_tensorflow
from .tracking_mlflow import log_parameters, log_tensorflow_keras_estimator, log_metrics
from .data_tensorflow import get_n_classes_from_directory_iterator, create_image_dataset
from .estimators_methods import fit
from .mlflow import add_model_to_registry


LOGGER: BoundLogger = structlog.stdlib.get_logger()

@pyplugs.register
def load_dataset(
    ep_seed: int = 10145783023,
    data_dir: str = "/dioptra/data/Mnist/testing",
    subset: Optional[str] = "testing",
    image_size: Tuple[int, int, int] = [28, 28, 1],
    rescale: float = 1.0 / 255,
    validation_split: Optional[float] = 0.2,
    batch_size: int = 32,
    label_mode: str = "categorical",
    shuffle: bool = False
) -> DirectoryIterator:
    seed, rng = init_rng(ep_seed)
    global_seed = draw_random_integer(rng)
    dataset_seed = draw_random_integer(rng)
    init_tensorflow(global_seed)
    if (subset == "training"):
        log_parameters(
           {'entry_point_seed': ep_seed, 
            'tensorflow_global_seed':global_seed, 
            'dataset_seed':dataset_seed})
    dataset = create_image_dataset(
        data_dir=data_dir,
        subset=subset,
        image_size=image_size,
        seed=dataset_seed,
        rescale=rescale,
        validation_split=validation_split,
        batch_size=batch_size,
        label_mode=label_mode,
        shuffle=shuffle
    )
    return dataset

@pyplugs.register
def get_model(
    dataset: DirectoryIterator = None,
    model_architecture: str = "le_net",
    input_shape: Tuple[int, int, int] = [28, 28, 1],
    loss: str = "categorical_crossentropy",
    learning_rate: float = 0.001,
    optimizer: str = "Adam", 
    metrics_list: List[Dict[str, Any]] = None,
    uri: str | None = None,
    imagenet_preprocessing: bool = False,
    classifier_kwargs: Optional[Dict[str, Any]] = None
):
    
    if uri is None:
        # create a model
        n_classes = get_n_classes_from_directory_iterator(dataset)
        optim = get_optimizer(optimizer, learning_rate)
        perf_metrics = get_performance_metrics(metrics_list)
        classifier = init_classifier(model_architecture, optim, perf_metrics, input_shape, n_classes, loss)
    else:
        # load a model
        classifier = load_wrapped_tensorflow_keras_classifier(uri, imagenet_preprocessing, classifier_kwargs)
    return classifier

@pyplugs.register
def train(
    model_name: str,
    estimator: Any,
    x: Any = None,
    y: Any = None,
    callbacks_list: List[Dict[str, Any]] = None,
    fit_kwargs: Optional[Dict[str, Any]] = None
):
    fit_kwargs = {} if fit_kwargs is None else fit_kwargs
    callbacks = get_model_callbacks(callbacks_list)
    fit_kwargs['callbacks'] = callbacks
    trained_model = fit(estimator=estimator, x=x, y=y, fit_kwargs=fit_kwargs)
    log_tensorflow_keras_estimator(estimator, "model")
    add_model_to_registry(model_name, "model")

@pyplugs.register
def attack():
    pass

@pyplugs.register
def compute_metrics(
    classifier: Any,
    dataset: Any
):
    metrics = evaluate_metrics_tensorflow(classifier, dataset)
    log_metrics(metrics)

@pyplugs.register
def augment_data():
    pass

@pyplugs.register
def predict():
    pass
