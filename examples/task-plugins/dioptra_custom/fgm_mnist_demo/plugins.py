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
from .registry_mlflow import load_tensorflow_keras_classifier
from .random_rng import init_rng
from .random_sample import draw_random_integer
from .backend_configs_tensorflow import init_tensorflow
from .tracking_mlflow import log_parameters, log_tensorflow_keras_estimator, log_metrics
from .data_tensorflow import get_n_classes_from_directory_iterator, create_image_dataset
from .estimators_methods import fit
from .mlflow import add_model_to_registry
from .artifacts_restapi import get_uri_for_model, get_uris_for_job, get_uris_for_artifacts
from .artifacts_utils import make_directories, extract_tarfile
from .metrics_distance import get_distance_metric_list
from .attacks_fgm import fgm
from .artifacts_mlflow import upload_directory_as_tarball_artifact, upload_data_frame_artifact, download_all_artifacts

LOGGER: BoundLogger = structlog.stdlib.get_logger()

@pyplugs.register
def load_dataset(
    ep_seed: int = 10145783023,
    data_dir: str = "/dioptra/data/Mnist/testing",
    subsets: List[str] = ['testing'],
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
    log_parameters(
       {'entry_point_seed': ep_seed, 
        'tensorflow_global_seed':global_seed, 
        'dataset_seed':dataset_seed})
    training_dataset = None if "training" not in subsets else create_image_dataset(
        data_dir=data_dir,
        subset="training",
        image_size=image_size,
        seed=dataset_seed,
        rescale=rescale,
        validation_split=validation_split,
        batch_size=batch_size,
        label_mode=label_mode,
        shuffle=shuffle
    )
   
    validation_dataset = None if "validation" not in subsets else create_image_dataset(
        data_dir=data_dir,
        subset="validation",
        image_size=image_size,
        seed=dataset_seed,
        rescale=rescale,
        validation_split=validation_split,
        batch_size=batch_size,
        label_mode=label_mode,
        shuffle=shuffle
    )
    testing_dataset = None if "testing" not in subsets else create_image_dataset(
        data_dir=data_dir,
        subset=None,
        image_size=image_size,
        seed=dataset_seed,
        rescale=rescale,
        validation_split=validation_split,
        batch_size=batch_size,
        label_mode=label_mode,
        shuffle=shuffle
    )
    return training_dataset, validation_dataset, testing_dataset

@pyplugs.register
def create_model(
    dataset: DirectoryIterator = None,
    model_architecture: str = "le_net",
    input_shape: Tuple[int, int, int] = [28, 28, 1],
    loss: str = "categorical_crossentropy",
    learning_rate: float = 0.001,
    optimizer: str = "Adam", 
    metrics_list: List[Dict[str, Any]] = None,
):
    n_classes = get_n_classes_from_directory_iterator(dataset)
    optim = get_optimizer(optimizer, learning_rate)
    perf_metrics = get_performance_metrics(metrics_list)
    classifier = init_classifier(model_architecture, optim, perf_metrics, input_shape, n_classes, loss)
    return classifier

@pyplugs.register
def load_model(
    model_name: str | None = None,
    model_version: int | None = None,
    imagenet_preprocessing: bool = False,
    art: bool = False,
    classifier_kwargs: Optional[Dict[str, Any]] = None
):
    uri = get_uri_for_model(model_name, model_version)
    if (art):
        classifier = load_wrapped_tensorflow_keras_classifier(uri, imagenet_preprocessing, classifier_kwargs)
    else:
        classifier = load_tensorflow_keras_classifier(uri)
    return classifier

@pyplugs.register
def train(
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
    return estimator

@pyplugs.register    
def save_artifacts_and_models(
    artifacts: List[Dict[str, Any]] = None,
    models: List[Dict[str, Any]] = None
):
    artifacts = [] if artifacts is None else artifacts
    models = [] if models is None else models

    for model in models:
        log_tensorflow_keras_estimator(model['model'], "model")
        add_model_to_registry(model['name'], "model")
    for artifact in artifacts:
        if (artifact['type'] == 'tarball'):
            upload_directory_as_tarball_artifact(
                source_dir=artifact['adv_data_dir'],
                tarball_filename=artifact['adv_tar_name']
            )
        if (artifact['type'] == 'dataframe'):
            upload_data_frame_artifact(
                data_frame=artifact['data_frame'],
                file_name=artifact['file_name'],
                file_format=artifact['file_format'],
                file_format_kwargs=artifact['file_format_kwargs']
            )
@pyplugs.register
def load_artifacts_for_job(
    job_id: str, extract_files: List[str|Path] = None
):
    extract_files = [] if extract_files is None else extract_files
    uris = get_uris_for_job(job_id)
    paths = download_all_artifacts(uris, extract_files)
    for extract in paths:
        extract_tarfile(extract)

@pyplugs.register
def load_artifacts(
    artifact_ids: List[int] = None, extract_files: List[str|Path] = None
):
    extract_files = [] if extract_files is None else extract_files
    artifact_ids = [] if artifact_ids is not None else artifact_ids
    uris = get_uris_for_artifacts(artifact_ids)
    paths = download_all_artifacts(uris, extract_files)
    for extract in paths:
        extract_tarfile(extract)

@pyplugs.register
def attack(
    dataset: Any,
    data_dir: str,
    adv_data_dir: Union[str, Path],
    classifier: Any,
    image_size: Tuple[int, int, int],
    distance_metrics: List[Dict[str, str]],
    rescale: float = 1.0 / 255,
    batch_size: int = 32,
    label_mode: str = "categorical",
    eps: float = 0.3,
    eps_step: float = 0.1,
    minimal: bool = False,
    norm: Union[int, float, str] = np.inf,
):
    make_directories(adv_data_dir)
    distance_metrics_list = get_distance_metric_list(distance_metrics)
    fgm_dataset = fgm(
        data_flow=dataset,
        data_dir=data_dir,
        adv_data_dir=adv_data_dir,
        keras_classifier=classifier,
        image_size=image_size,
        distance_metrics_list=distance_metrics_list,
        rescale=rescale,
        batch_size=batch_size,
        label_mode=label_mode,
        eps=eps,
        eps_step=eps_step,
        minimal=minimal,
        norm=norm
    )
    return fgm_dataset

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
