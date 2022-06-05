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

import structlog
from mlflow.models import Model as MLflowModel
from mlflow.models.model import MLMODEL_FILE_NAME
from mlflow.tracking.artifact_utils import _download_artifact_from_uri
from mlflow.utils.model_utils import _get_flavor_configuration
from structlog.stdlib import BoundLogger

from dioptra.sdk.object_detection.architectures import YOLOV1ObjectDetector
from dioptra.sdk.object_detection.architectures.tensorflow_layers import (
    EfficientNetBackbone,
    MobileNetV2Backbone,
    SimpleYOLOV1Detector,
    TwoHeadedYOLOV1Detector,
    YOLOV1Detector,
)

import dioptra_custom.tracking

LOGGER: BoundLogger = structlog.stdlib.get_logger()
FLAVOR_NAME: str = "yolo_v1"


def save_model(
    yolo_v1_model: YOLOV1ObjectDetector,
    path: str | Path,
    mlflow_model: MLflowModel | None = None,
):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=True)

    mlflow_mlmodel_file_path = path / MLMODEL_FILE_NAME
    model_subpath = path / "weights.hdf5"

    if mlflow_model is None:
        mlflow_model = MLflowModel()

    yolo_v1_detector_config = yolo_v1_model.detector.get_config()
    input_shape = tuple([int(x) for x in yolo_v1_model.image_input_shape])
    n_bounding_boxes = int(yolo_v1_detector_config["n_bounding_boxes"])
    n_classes = int(yolo_v1_detector_config["n_classes"])
    backbone_trainable: bool = yolo_v1_model.backbone.model.trainable

    backbone: str
    if isinstance(yolo_v1_model.backbone, MobileNetV2Backbone):
        backbone = "mobilenetv2"
    elif isinstance(yolo_v1_model.backbone, EfficientNetBackbone):
        backbone = yolo_v1_model.backbone.model.name
    else:
        raise RuntimeError("Unknown backbone for YOLO V1 object detector")

    detector: str
    if isinstance(yolo_v1_model.detector, SimpleYOLOV1Detector):
        detector = "shallow"
    elif isinstance(yolo_v1_model.detector, TwoHeadedYOLOV1Detector):
        detector = "two_headed"
    elif isinstance(yolo_v1_model.detector, YOLOV1Detector):
        detector = "original"
    else:
        raise RuntimeError("Unknown detector for YOLO V1 object detector")

    mlflow_model.add_flavor(
        FLAVOR_NAME,
        input_shape=input_shape,
        n_bounding_boxes=n_bounding_boxes,
        n_classes=n_classes,
        backbone=backbone,
        detector=detector,
        backbone_trainable=backbone_trainable,
    )
    mlflow_model.save(mlflow_mlmodel_file_path)
    yolo_v1_model.save_weights(
        filepath=str(model_subpath),
        overwrite=True,
        save_format="h5",
    )


def load_model(model_uri, dst_path=None):
    local_model_path = _download_artifact_from_uri(
        artifact_uri=model_uri, output_path=dst_path
    )
    model_weights = Path(local_model_path) / "weights.hdf5"
    yolo_v1_conf = _get_flavor_configuration(model_path=local_model_path, flavor_name=FLAVOR_NAME)
    input_shape: tuple[int, int, int] = tuple([int(x) for x in yolo_v1_conf["input_shape"]])
    backbone_trainable: bool = bool(yolo_v1_conf["backbone_trainable"])

    yolo_v1_model: YOLOV1ObjectDetector = YOLOV1ObjectDetector(
        input_shape=input_shape,
        n_bounding_boxes=yolo_v1_conf["n_bounding_boxes"],
        n_classes=yolo_v1_conf["n_classes"],
        backbone=yolo_v1_conf["backbone"],
        detector=yolo_v1_conf["detector"],
    )
    yolo_v1_model.backbone.model.trainable = backbone_trainable
    yolo_v1_model.build(
        (None, input_shape[0], input_shape[1], input_shape[2])
    )
    yolo_v1_model.load_weights(str(model_weights))

    return yolo_v1_model


def log_model(
    model: YOLOV1ObjectDetector,
    artifact_path,
    **kwargs,
):
    return MLflowModel.log(
        artifact_path=str(artifact_path),
        flavor=dioptra_custom.tracking.yolo_v1,
        yolo_v1_model=model,
        **kwargs,
    )
