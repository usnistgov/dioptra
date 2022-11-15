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

import import_keras
import structlog
from prefect import task
from structlog.stdlib import BoundLogger

from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.callbacks import Callback
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.optimizers import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@task
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def evaluate_metrics_tensorflow(classifier, dataset) -> Dict[str, float]:
    result = classifier.evaluate(dataset, verbose=0)
    return dict(zip(classifier.metrics_names, result))


@task
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_optimizer(optimizer: str, learning_rate: float) -> Optimizer:
    return import_keras.get_optimizer(optimizer)(learning_rate)


@task
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_model_callbacks(callbacks_list: List[Dict[str, Any]]) -> List[Callback]:
    return [
        import_keras.get_callback(callback["name"])(**callback.get("parameters", {}))
        for callback in callbacks_list
    ]


@task
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_performance_metrics(
    metrics_list: List[Dict[str, Any]]
) -> List[Union[Metric, FunctionType]]:
    performance_metrics: List[Metric] = []

    for metric in metrics_list:
        new_metric: Union[Metric, FunctionType] = import_keras.get_metric(
            metric["name"]
        )
        performance_metrics.append(
            new_metric(**metric.get("parameters"))
            if not isinstance(new_metric, FunctionType) and metric.get("parameters")
            else new_metric
        )

    return performance_metrics


@task
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def feature_squeeze(
    data_dir, run_id, model, model_architecture, batch_size, seed, bit_depth
):
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="feature_squeeze",
        model=model,
        model_architecture=model_architecture,
        batch_size=batch_size,
        seed=seed,
        bit_depth=bit_depth,
    )

    tensorflow_global_seed: int = rng.integers(low=0, high=2 ** 31 - 1)
    dataset_seed: int = rng.integers(low=0, high=2 ** 31 - 1)

    tf.random.set_seed(tensorflow_global_seed)
    defense = FeatureSqueezing(bit_depth=bit_depth, clip_values=(0.0, 1.0))
    with mlflow.start_run() as _:
        adv_testing_tar_name = "testing_adversarial.tar.gz"
        adv_testing_data_dir = Path.cwd() / "adv_testing"
        def_testing_data_dir = Path.cwd() / "def_testing"
        adv_perturbation_tar_name = "distance_metrics.csv.gz"
        image_size = (28, 28)
        color_mode = "grayscale"
        if model_architecture == "alex_net" or model_architecture == "mobilenet":
            image_size = (224, 224)
            color_mode = "rgb"
        LOGGER.info("Downloading image archive at ", path=adv_testing_tar_name)
        adv_testing_tar_path = download_image_archive(
            run_id=run_id, archive_path=adv_testing_tar_name
        )
        LOGGER.info("downloading adv_perturbation_tar ", path=adv_perturbation_tar_name)
        adv_perturbation_tar_path = download_image_archive(
            run_id=run_id, archive_path=adv_perturbation_tar_name
        )

        with tarfile.open(adv_testing_tar_path, "r:gz") as f:
            f.extractall(path=Path.cwd())
        adv_ds = create_image_dataset(
            data_dir=str(adv_testing_data_dir.resolve()),
            subset=None,
            validation_split=None,
            image_size=image_size,
            color_mode=color_mode,
            seed=dataset_seed,
            batch_size=batch_size,
        )

        data_flow = adv_ds

        num_images = data_flow.n
        img_filenames = [Path(x) for x in data_flow.filenames]
        class_names_list = sorted(
            data_flow.class_indices, key=data_flow.class_indices.get
        )
        # distance_metrics_ = {"image": [], "label": []}
        for batch_num, (x, y) in enumerate(data_flow):
            if batch_num >= num_images // batch_size:
                break

            clean_filenames = img_filenames[
                batch_num * batch_size : (batch_num + 1) * batch_size
            ]

            LOGGER.info(
                "Applying Defense",
                defense="feature squeezing",
                batch_num=batch_num,
            )

            y_int = np.argmax(y, axis=1)
            adv_batch = x

            adv_batch_defend, _ = defense(adv_batch)
            save_adv_batch(
                adv_batch_defend,
                def_testing_data_dir,
                y_int,
                clean_filenames,
                class_names_list,
            )

        testing_dir = Path(data_dir) / "testing"
        adv_data_dir = Path().cwd() / "adv_testing"
        def_data_dir = Path().cwd() / "def_testing"
        adv_data_dir.mkdir(parents=True, exist_ok=True)
        adv_testing_tar = Path().cwd() / "testing_adversarial.tar.gz"
        image_perturbation_csv = Path().cwd() / "distance_metrics.csv.gz"

        #       distance_metrics = pd.DataFrame(distance_metrics_)

        image_perturbation_csv = Path(data_dir).cwd() / "distance_metrics.csv.gz"
        with tarfile.open(adv_testing_tar, "w:gz") as f:
            f.add(str(def_data_dir.resolve()), arcname=adv_data_dir.name)

        tar = tarfile.open(adv_testing_tar)
        LOGGER.info("Saved to : ", dir=adv_testing_tar_path)
        LOGGER.info("Log defended images", filename=adv_testing_tar.name)
        print("Base: ", str(adv_testing_tar))
        print("Name: ", str(adv_testing_tar.name))
        mlflow.log_artifact(str(adv_testing_tar.name))
        mlflow.log_artifact(str(adv_perturbation_tar_path))
        LOGGER.info(
            "Log distance metric distributions", filename=image_perturbation_csv.name
        )

        LOGGER.info("Finishing run ID: ", run_id=run_id)
        adv_ds_defend = create_image_dataset(
            data_dir=str(adv_testing_data_dir.resolve()),
            subset=None,
            validation_split=None,
            image_size=image_size,
            color_mode=color_mode,
            seed=dataset_seed,
            batch_size=batch_size,
        )
