# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import warnings
from typing import Optional, Tuple

warnings.filterwarnings("ignore")

import tensorflow as tf

from tensorflow.keras.applications.resnet50 import preprocess_input

tf.compat.v1.disable_eager_execution()

import structlog
from mlflow.tracking import MlflowClient
from tensorflow.keras.preprocessing.image import ImageDataGenerator


LOGGER = structlog.get_logger()


def download_image_archive(
    run_id: str, archive_path: str, destination_path: Optional[str] = None
) -> str:
    client: MlflowClient = MlflowClient()
    image_archive_path: str = client.download_artifacts(
        run_id=run_id, path=archive_path, dst_path=destination_path
    )
    LOGGER.info(
        "Image archive downloaded",
        run_id=run_id,
        storage_path=archive_path,
        dst_path=image_archive_path,
    )
    return image_archive_path


def create_image_dataset(
    data_dir: str,
    subset: str,
    rescale: float = 1.0,
    validation_split: float = 0.2,
    batch_size: int = 32,
    seed: int = 8237131,
    label_mode: str = "categorical",
    color_mode: str = "rgb",
    image_size: Tuple[int, int] = (224, 224),
    model_architecture: str = "resnet50",
):
    if model_architecture == "mobilenet":
        from tensorflow.keras.applications.mobilenet import preprocess_input

    data_generator: ImageDataGenerator = ImageDataGenerator(
        rescale=rescale,
        validation_split=validation_split,
        preprocessing_function=preprocess_input,
    )

    return data_generator.flow_from_directory(
        directory=data_dir,
        target_size=image_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        seed=seed,
        subset=subset,
    )
