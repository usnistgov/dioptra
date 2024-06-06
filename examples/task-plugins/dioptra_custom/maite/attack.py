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
import tarfile
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import importlib
import inspect
import mlflow
import numpy as np
import pandas as pd
import scipy
import structlog
import torch
from art.attacks.evasion import FastGradientMethod, ProjectedGradientDescentPyTorch, HopSkipJump, PixelAttack
from art.estimators.classification.hugging_face import HuggingFaceClassifierPyTorch
from structlog.stdlib import BoundLogger
from torch.nn import CrossEntropyLoss
from torchvision.utils import save_image

from dioptra import pyplugs
from dioptra.sdk.exceptions import ARTDependencyError
from dioptra.sdk.utilities.decorators import require_package
from dioptra.sdk.utilities.paths import set_path_ext
from heart_library.estimators.classification.pytorch import JaticPyTorchClassifier
from heart_library.attacks.attack import JaticAttack, JaticEvasionAttackOutput

warnings.filterwarnings("ignore")

LOGGER: BoundLogger = structlog.stdlib.get_logger()

def _wrap_hf_classifier(torch_model, loss_fn, input_shape, classes) -> HuggingFaceClassifierPyTorch:
    return HuggingFaceClassifierPyTorch(
        model=torch_model, loss=loss_fn, input_shape=input_shape, nb_classes=classes, clip_values=(0,1)
    )

def _wrap_jatic_classifier(model, loss_fn, input_shape, labels, classes):
  return JaticPyTorchClassifier(
    model=model, loss=loss_fn, input_shape=input_shape, nb_classes=classes, labels=labels, clip_values=(0, 1)
  )

def _construct_attack(attack_library: str, attack_name: str, model, loss_fn, input_shape, labels, classes, batch_size: int, **kwargs) -> JaticAttack:
    classifier = _wrap_hf_classifier(model, loss_fn, input_shape, classes)
    attack = lookup_class(attack_library, attack_name)
    model_param_names = check_model_parameter(attack)
    kwargs = build_parameters(model_param_names, classifier=classifier, estimator=classifier, loss=loss_fn, loss_fn=loss_fn, input_shape=input_shape, nb_classes=classes, batch_size=batch_size, **kwargs)
    attack = attack(**kwargs)
    attack = JaticAttack(attack)
    return attack

def find_function_parameter(fname):
    function_loc = fname.split('.')
    return lookup_class('.'.join(function_loc[:-1]), function_loc[-1])
def check_model_parameter(f):
    cs = get_parent_classes(f)
    parameters = []
    for c in cs:
        current_class_params = [i for i in inspect.signature(c).parameters]
        parameters += current_class_params
        if 'kwargs' not in current_class_params:
            break
    return parameters
def build_parameters(signature,**kwargs):
    function_key = '_FUNCTION'
    # convert things ending in _FUNCTION to actual functions, and remove the _FUNCTION tag
    pdict = {(m[:-len(function_key)] if m.endswith(function_key) else m):(find_function_parameter(v) if m.endswith(function_key) else v) for (m,v) in kwargs.items()}
        #TODO: log things which did not get included, for clarity
    for (m,v) in pdict.items():
        if m not in signature:
            LOGGER.warn("Filtering parameter: %s", str(m))
    pdict = {m:v for (m,v) in pdict.items() if m in signature}
    return pdict


def lookup_class(module_name, class_name):
    # grabs the class by name from the module 
    try:
        module_ = importlib.import_module(module_name)
        try:
            class_ = getattr(module_, class_name)
        except AttributeError:
            LOGGER.error('Class', class_name ,'does not exist')
    except ImportError:
        LOGGER.error('Module', module_name ,'does not exist')
    return class_ or None
def get_parent_classes(clazz):
    # gets parent classes 
    return clazz.__mro__
  
def _adv_gen(attack_library, attack_name, dataset, adv_data_dir, data_dir, loss_fn, classifier, image_size, save_original, batch_size, target_index, **kwargs):
    adv_data_dir = Path(adv_data_dir)
    data_dir = Path(data_dir)
    num_images = len(dataset)
    class_names_list = sorted(list(set([m["label"] for m in dataset])))
    classes = len(class_names_list)

    attack = _construct_attack(
        attack_library=attack_library,
        attack_name=attack_name,
        model=classifier,
        loss_fn=loss_fn,
        input_shape=image_size,
        labels = class_names_list,
        classes=classes,
        batch_size=batch_size,
        **kwargs
    )

    for batch_num in range(num_images // batch_size):
        batch_range = range(batch_num * batch_size, (batch_num + 1) * batch_size)
        batch = [dataset[min(i, len(dataset) - 1)] for i in batch_range]
        x = np.array([m["image"] for m in batch])
        y = np.array([m["label"] for m in batch])

        LOGGER.info(
            "Generate adversarial image batch",
            attack=attack_name,
            batch_num=batch_num,
        )
        if target_index >= 0:
            y_one_hot = np.zeros(classes)
            y_one_hot[target_index] = 1.0
            y_target = np.tile(y_one_hot, (x.shape[0], 1))
          
            adv_batch = [attack.run_attack(data=image, y=y_target) for image in batch]
        else:
            adv_batch = [attack.run_attack(data=image) for image in batch]

        if save_original:
            _save_batch(batch_range, x, data_dir, y, class_names_list, adv=False)
        _save_batch(batch_range, adv_batch, adv_data_dir, y, class_names_list, adv=True)
    _upload_directory_as_tarball_artifact(adv_data_dir, "fgm.tar.gz")


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
def attack_by_name(
    dataset,
    attack_name: str,
    adv_data_dir: Union[str, Path],
    data_dir: Union[str, Path],
    classifier,
    image_size: Tuple[int, int, int],
    attack_library: str = 'art.attacks.evasion',
    save_original=False,
    distance_metrics_list: Optional[List[Tuple[str, Callable[..., np.ndarray]]]] = None,
    batch_size: int = 32,
    target_index: int = -1,
    attack_kwargs: Optional[str] = None
) -> pd.DataFrame:
    _adv_gen(
      attack_library,
      attack_name,
      dataset,
      adv_data_dir,
      data_dir,
      CrossEntropyLoss(), 
      classifier.model,
      image_size,
      save_original,
      batch_size, 
      target_index=target_index,
      **attack_kwargs
    )  

def _save_batch(batch_indices, batch, data_dir, y, class_names_list, adv=False) -> None:
    for batch_image_num, image in enumerate(batch):
        image = image.adversarial_examples
        out_label = class_names_list[y[batch_image_num]]
        prefix = "adv_" if adv else ""
        image_path = (
            data_dir / f"{out_label}" / f"{prefix}{batch_indices[batch_image_num]}.png"
        )

        if not image_path.parent.exists():
            image_path.parent.mkdir(parents=True)
        save_image(tensor=torch.tensor(image), fp=str(image_path), format="png")


def _evaluate_distance_metrics(
    batch_indices,
    batch_classes,
    distance_metrics_,
    clean_batch,
    adv_batch,
    distance_metrics_list,
) -> None:
    distance_metrics_["image"].extend(batch_indices)
    distance_metrics_["label"].extend(batch_classes)
    for metric_name, metric in distance_metrics_list:
        distance_metrics_[metric_name].extend(metric(clean_batch, adv_batch))


def _log_distance_metrics(distance_metrics_: Dict[str, List[List[float]]]) -> None:
    distance_metrics_ = distance_metrics_.copy()
    del distance_metrics_["image"]
    del distance_metrics_["label"]
    for metric_name, metric_values_list in distance_metrics_.items():
        metric_values = np.array(metric_values_list)
        mlflow.log_metric(key=f"{metric_name}_mean", value=metric_values.mean())
        mlflow.log_metric(key=f"{metric_name}_median", value=np.median(metric_values))
        mlflow.log_metric(key=f"{metric_name}_stdev", value=metric_values.std())
        mlflow.log_metric(
            key=f"{metric_name}_iqr", value=scipy.stats.iqr(metric_values)
        )
        mlflow.log_metric(key=f"{metric_name}_min", value=metric_values.min())
        mlflow.log_metric(key=f"{metric_name}_max", value=metric_values.max())
        LOGGER.info("logged distance-based metric", metric_name=metric_name)


def _upload_data_frame_artifact(
    data_frame: pd.DataFrame,
    file_name: str,
    file_format: str,
    file_format_kwargs: Optional[Dict[str, Any]] = None,
    working_dir: Optional[Union[str, Path]] = None,
) -> None:
    """Uploads a :py:class:`~pandas.DataFrame` as an artifact of the active MLFlow run.

    The `file_format` argument selects the :py:class:`~pandas.DataFrame` serializer,
    which are all handled using the object's `DataFrame.to_{format}` methods. The string
    passed to `file_format` must match one of the following,

    - `csv[.bz2|.gz|.xz]` - A comma-separated values plain text file with optional
      compression.
    - `feather` - A binary feather file.
    - `json` - A plain text JSON file.
    - `pickle` - A binary pickle file.

    Args:
        data_frame: A :py:class:`~pandas.DataFrame` to be uploaded.
        file_name: The filename to use for the serialized :py:class:`~pandas.DataFrame`.
        file_format: The :py:class:`~pandas.DataFrame` file serialization format.
        file_format_kwargs: A dictionary of additional keyword arguments to pass to the
            serializer. If `None`, then no additional keyword arguments are passed. The
            default is `None`.
        working_dir: The location where the file should be saved. If `None`, then the
            current working directory is used. The default is `None`.

    Notes:
        The :py:mod:`pyarrow` package must be installed in order to serialize to the
        feather format.

    See Also:
        - :py:meth:`pandas.DataFrame.to_csv`
        - :py:meth:`pandas.DataFrame.to_feather`
        - :py:meth:`pandas.DataFrame.to_json`
        - :py:meth:`pandas.DataFrame.to_pickle`
    """

    def to_format(
        data_frame: pd.DataFrame, format: str, output_dir: Union[str, Path]
    ) -> Dict[str, Any]:
        filepath: Path = Path(output_dir) / Path(file_name).name
        format_funcs = {
            "csv": {
                "func": data_frame.to_csv,
                "filepath": set_path_ext(filepath=filepath, ext="csv"),
            },
            "csv.bz2": {
                "func": data_frame.to_csv,
                "filepath": set_path_ext(filepath=filepath, ext="csv.bz2"),
            },
            "csv.gz": {
                "func": data_frame.to_csv,
                "filepath": set_path_ext(filepath=filepath, ext="csv.gz"),
            },
            "csv.xz": {
                "func": data_frame.to_csv,
                "filepath": set_path_ext(filepath=filepath, ext="csv.xz"),
            },
            "feather": {
                "func": data_frame.to_feather,
                "filepath": set_path_ext(filepath=filepath, ext="feather"),
            },
            "json": {
                "func": data_frame.to_json,
                "filepath": set_path_ext(filepath=filepath, ext="json"),
            },
            "pickle": {
                "func": data_frame.to_pickle,
                "filepath": set_path_ext(filepath=filepath, ext="pkl"),
            },
        }

        func: Optional[Dict[str, Any]] = format_funcs.get(format)

        if func is None:
            raise Exception(
                f"Serializing data frames to the {file_format} format is not supported"
            )

        return func

    if file_format_kwargs is None:
        file_format_kwargs = {}

    if working_dir is None:
        working_dir = Path.cwd()

    working_dir = Path(working_dir)
    format_dict: Dict[str, Any] = to_format(
        data_frame=data_frame, format=file_format, output_dir=working_dir
    )

    df_to_format_func: Callable[..., None] = format_dict["func"]
    df_artifact_path: Path = format_dict["filepath"]

    df_to_format_func(df_artifact_path, **file_format_kwargs)
    LOGGER.info(
        "Data frame saved to file",
        file_name=df_artifact_path.name,
        file_format=file_format,
    )

    _upload_file_as_artifact(artifact_path=df_artifact_path)


def _upload_directory_as_tarball_artifact(
    source_dir: Union[str, Path],
    tarball_filename: str,
    tarball_write_mode: str = "w:gz",
    working_dir: Optional[Union[str, Path]] = None,
) -> None:
    """Archives a directory and uploads it as an artifact of the active MLFlow run.

    Args:
        source_dir: The directory which should be uploaded.
        tarball_filename: The filename to use for the archived directory tarball.
        tarball_write_mode: The write mode for the tarball, see :py:func:`tarfile.open`
            for the full list of compression options. The default is `"w:gz"` (gzip
            compression).
        working_dir: The location where the file should be saved. If `None`, then the
            current working directory is used. The default is `None`.

    See Also:
        - :py:func:`tarfile.open`
    """
    if working_dir is None:
        working_dir = Path.cwd()

    source_dir = Path(source_dir)
    working_dir = Path(working_dir)
    tarball_path = working_dir / tarball_filename

    with tarfile.open(tarball_path, tarball_write_mode) as f:
        f.add(source_dir, arcname=source_dir.name)

    LOGGER.info(
        "Directory added to tar archive",
        directory=source_dir,
        tarball_path=tarball_path,
    )

    _upload_file_as_artifact(artifact_path=tarball_path)


def _upload_file_as_artifact(artifact_path: Union[str, Path]) -> None:
    """Uploads a file as an artifact of the active MLFlow run.

    Args:
        artifact_path: The location of the file to be uploaded.

    See Also:
        - :py:func:`mlflow.log_artifact`
    """
    artifact_path = Path(artifact_path)
    mlflow.log_artifact(str(artifact_path))
    LOGGER.info("Artifact uploaded for current MLFlow run", filename=artifact_path.name)
