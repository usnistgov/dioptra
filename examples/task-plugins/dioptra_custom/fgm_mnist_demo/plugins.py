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
from tensorflow.keras.preprocessing.image import (
    DirectoryIterator
)

from dioptra import pyplugs
from .tensorflow import get_optimizer, get_model_callbacks, get_performance_metrics, evaluate_metrics_tensorflow, predict_tensorflow
from .estimators_keras_classifiers import init_classifier
from .registry_art import load_wrapped_tensorflow_keras_classifier
from .registry_mlflow import load_tensorflow_keras_classifier
from .random_rng import init_rng
from .random_sample import draw_random_integer
from .backend_configs_tensorflow import init_tensorflow
from .tracking_mlflow import log_parameters, log_tensorflow_keras_estimator, log_metrics
from .data_tensorflow import get_n_classes_from_directory_iterator, create_image_dataset, predictions_to_df, df_to_predictions
from .estimators_methods import fit
from .mlflow import add_model_to_registry
from .artifacts_restapi import get_uri_for_model, get_uris_for_job, get_uris_for_artifacts
from .artifacts_utils import make_directories, extract_tarfile
from .metrics_distance import get_distance_metric_list
from .attacks_fgm import fgm
from .artifacts_mlflow import upload_directory_as_tarball_artifact, upload_data_frame_artifact, download_all_artifacts
from .defenses_image_preprocessing import create_defended_dataset
from .attacks_patch import create_adversarial_patches, create_adversarial_patch_dataset
from .metrics_performance import get_performance_metric_list, evaluate_metrics_generic

LOGGER: BoundLogger = structlog.stdlib.get_logger()

@pyplugs.register
def load_dataset(
    ep_seed: int = 10145783023,
    training_dir: str = "/dioptra/data/Mnist/training",
    testing_dir: str = "/dioptra/data/Mnist/testing",
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
        data_dir=training_dir,
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
        data_dir=training_dir,
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
        data_dir=testing_dir,
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
    image_size: Any = None,
    classifier_kwargs: Optional[Dict[str, Any]] = None
):
    uri = get_uri_for_model(model_name, model_version)
    if (art):
        classifier = load_wrapped_tensorflow_keras_classifier(uri, imagenet_preprocessing, image_size, classifier_kwargs)
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
    job_id: str, 
    files: List[str|Path] = None,
    extract_files: List[str|Path] = None
):
    files = [] if files is None else files
    extract_files = [] if extract_files is None else extract_files
    files += extract_files # need to download them to be able to extract

    uris = get_uris_for_job(job_id)
    paths = download_all_artifacts(uris, files)
    for extract in paths:
        for ef in extract_files:
            if (ef.endswith(str(ef))):
                extract_tarfile(extract)
    return paths

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
def attack_fgm(
    dataset: Any,
    adv_data_dir: Union[str, Path],
    classifier: Any,
    distance_metrics: List[Dict[str, str]],
    batch_size: int = 32,
    eps: float = 0.3,
    eps_step: float = 0.1,
    minimal: bool = False,
    norm: Union[int, float, str] = np.inf,
):
    '''generate fgm examples'''
    make_directories([adv_data_dir])
    distance_metrics_list = get_distance_metric_list(distance_metrics)
    fgm_dataset = fgm(
        data_flow=dataset,
        adv_data_dir=adv_data_dir,
        keras_classifier=classifier,
        distance_metrics_list=distance_metrics_list,
        batch_size=batch_size,
        eps=eps,
        eps_step=eps_step,
        minimal=minimal,
        norm=norm
    )
    return fgm_dataset

@pyplugs.register()
def attack_patch(
    data_flow: Any,
    adv_data_dir: Union[str, Path],
    model: Any,
    patch_target: int,
    num_patch: int,
    num_patch_samples: int,
    rotation_max: float,
    scale_min: float,
    scale_max: float,
    learning_rate: float,
    max_iter: int,
    patch_shape: Tuple,
):
    '''generate patches'''
    make_directories([adv_data_dir])
    create_adversarial_patches(    
        data_flow=data_flow,
        adv_data_dir=adv_data_dir,
        keras_classifier=model,
        patch_target=patch_target,
        num_patch=num_patch,
        num_patch_samples=num_patch_samples,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max,
        learning_rate=learning_rate,
        max_iter=max_iter,
        patch_shape=patch_shape,
    )

@pyplugs.register()
def augment_patch(
    data_flow: Any,
    adv_data_dir: Union[str, Path],
    patch_dir: Union[str, Path],
    model: Any,
    patch_shape: Tuple,
    distance_metrics: List[Dict[str, str]],
    batch_size: int = 32,
    patch_scale: float = 0.4,
    rotation_max: float = 22.5,
    scale_min: float = 0.1,
    scale_max: float = 1.0,
):
    '''add patches to a dataset'''
    make_directories([adv_data_dir])
    distance_metrics_list = get_distance_metric_list(distance_metrics)
    create_adversarial_patch_dataset(
        data_flow=data_flow,
        adv_data_dir=adv_data_dir,
        patch_dir=patch_dir,
        keras_classifier=model,
        patch_shape=patch_shape,
        distance_metrics_list=distance_metrics_list,
        batch_size=batch_size,
        patch_scale=patch_scale,
        rotation_max=rotation_max,
        scale_min=scale_min,
        scale_max=scale_max
    )
@pyplugs.register
def model_metrics(
    classifier: Any,
    dataset: Any
):
    metrics = evaluate_metrics_tensorflow(classifier, dataset)
    log_metrics(metrics)
    return metrics

@pyplugs.register
def prediction_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metrics_list: List[Dict[str, str]],
    func_kwargs: Dict[str, Dict[str, Any]] = None
):
    func_kwargs = {} if func_kwargs is None else func_kwargs
    callable_list = get_performance_metric_list(metrics_list)
    metrics = evaluate_metrics_generic(y_true, y_pred, callable_list, func_kwargs)
    log_metrics(metrics)
    return metrics

@pyplugs.register
def augment_data(
    dataset: Any,
    def_data_dir: Union[str, Path],
    image_size: Tuple[int, int, int],
    distance_metrics: List[Dict[str, str]],
    batch_size: int = 32,
    def_type: str = "spatial_smoothing",
    defense_kwargs: Optional[Dict[str, Any]] = None,
):
    make_directories([def_data_dir])
    distance_metrics_list = get_distance_metric_list(distance_metrics)
    defended_dataset = create_defended_dataset(
        data_flow=dataset,
        def_data_dir=def_data_dir,
        image_size=image_size,
        distance_metrics_list=distance_metrics_list,
        batch_size=batch_size,
        def_type=def_type,
        defense_kwargs=defense_kwargs,
    )
    return defended_dataset

@pyplugs.register
def predict(
    classifier: Any,
    dataset: Any,
    show_actual: bool = False,
    show_target: bool = False,
):
    predictions = predict_tensorflow(classifier, dataset)
    df = predictions_to_df( 
                            predictions, 
                            dataset, 
                            show_actual=show_actual,
                            show_target=show_target)
    return df

@pyplugs.register
def load_predictions(
    paths: List[str],
    filename: str,
    format: str = 'csv',
    dataset: DirectoryIterator = None,
    n_classes: int = -1,
):
    loc = None
    for m in paths:
        if m.endswith(filename):
            loc = m
    if (format == 'csv'):
        df = pd.read_csv(loc)
    elif (format == 'json'):
        df = pd.read_json(loc)
    y_true, y_pred = df_to_predictions(df, dataset, n_classes)
    return y_true, y_pred
    


