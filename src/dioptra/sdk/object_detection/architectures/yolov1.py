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

import math
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.object_detection.architectures.tensorflow_layers.backbones import (  # noqa: B950
    EfficientNetBackbone,
)
from dioptra.sdk.object_detection.bounding_boxes.postprocessing import (
    BoundingBoxesYOLOV1PostProcessing,
)

from .tensorflow_layers import (
    MobileNetV2Backbone,
    SimpleYOLOV1Detector,
    TwoHeadedYOLOV1Detector,
    YOLOV1Detector,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    import tensorflow as tf
    from tensorflow import GradientTape, Tensor
    from tensorflow.keras import Model
    from tensorflow.keras.layers import Layer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


try:
    from art.defences.preprocessor.preprocessor import Preprocessor
    from art.estimators.object_detection.object_detector import (
        ObjectDetector as ARTObjectDetector,
    )
    from art.estimators.object_detection.utils import convert_pt_to_tf, convert_tf_to_pt
    from art.utils import CLIP_VALUES_TYPE

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


class YOLOV1ObjectDetector(Model):
    def __init__(
        self,
        input_shape: tuple[int, int, int],
        n_bounding_boxes: int,
        n_classes: int,
        backbone: str = "efficientnetb4",
        detector: str = "two_headed",
        name: str = "yolo_v1_object_detector",
    ) -> None:
        super().__init__(name=name)
        self.backbone = self._set_backbone(backbone=backbone, input_shape=input_shape)
        self.detector = self._set_detector(
            detector=detector,
            grid_shape=self.backbone.output_grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            n_classes=n_classes,
        )
        self.loss_tracker = tf.keras.metrics.Mean(name="loss")
        self.val_loss_tracker = tf.keras.metrics.Mean(name="loss")
        self._image_input_shape = input_shape

    @property
    def image_input_shape(self) -> tuple[int, int, int]:
        return self._image_input_shape

    @property
    def output_grid_shape(self):
        return self.backbone.output_grid_shape

    @property
    def metrics(self):
        return [self.loss_tracker, self.val_loss_tracker]

    def call(self, inputs, training=None):
        x = self.backbone(inputs)

        return self.detector(x, training=training)

    def train_step(self, data):
        x, y = data

        with GradientTape() as tape:
            y_pred = self(x, training=True)
            loss = self.loss(y, y_pred)

        trainable_vars = self.trainable_variables
        gradients = tape.gradient(loss, trainable_vars)

        self.optimizer.apply_gradients(zip(gradients, trainable_vars))
        self.loss_tracker.update_state(loss)

        return {"loss": self.loss_tracker.result()}

    def test_step(self, data):
        x, y = data

        y_pred = self(x, training=False)
        loss = self.loss(y, y_pred)

        self.val_loss_tracker.update_state(loss)

        return {"loss": self.val_loss_tracker.result()}

    @staticmethod
    def _set_backbone(
        backbone: str, input_shape: Optional[Tuple[int, int, int]]
    ) -> Model:
        backbone_registry: dict[str, Callable[[], EfficientNetBackbone]] = dict(
            efficientnetb0=lambda: EfficientNetBackbone(
                flavor="b0", input_shape=input_shape
            ),
            efficientnetb1=lambda: EfficientNetBackbone(
                flavor="b1", input_shape=input_shape
            ),
            efficientnetb2=lambda: EfficientNetBackbone(
                flavor="b2", input_shape=input_shape
            ),
            efficientnetb3=lambda: EfficientNetBackbone(
                flavor="b3", input_shape=input_shape
            ),
            efficientnetb4=lambda: EfficientNetBackbone(
                flavor="b4", input_shape=input_shape
            ),
            efficientnetb5=lambda: EfficientNetBackbone(
                flavor="b5", input_shape=input_shape
            ),
            efficientnetb6=lambda: EfficientNetBackbone(
                flavor="b6", input_shape=input_shape
            ),
            efficientnetb7=lambda: EfficientNetBackbone(
                flavor="b7", input_shape=input_shape
            ),
            mobilenetv2=lambda: MobileNetV2Backbone(input_shape=input_shape),
        )

        return backbone_registry[backbone.strip().lower()]()

    @staticmethod
    def _set_detector(
        detector: str,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        n_classes: int,
    ) -> Layer:
        detector_registry: dict[str, Callable[[], Layer]] = dict(
            original=lambda: YOLOV1Detector(
                grid_shape=grid_shape,
                n_bounding_boxes=n_bounding_boxes,
                n_classes=n_classes,
            ),
            shallow=lambda: SimpleYOLOV1Detector(
                grid_shape=grid_shape,
                n_bounding_boxes=n_bounding_boxes,
                n_classes=n_classes,
            ),
            two_headed=lambda: TwoHeadedYOLOV1Detector(
                grid_shape=grid_shape,
                n_bounding_boxes=n_bounding_boxes,
                n_classes=n_classes,
            ),
        )

        return detector_registry[detector.strip().lower()]()


class ARTYOLOV1ObjectDetector(ARTObjectDetector):
    def __init__(
        self,
        model: YOLOV1ObjectDetector,
        n_classes: int,
        bounding_boxes_postprocessing: BoundingBoxesYOLOV1PostProcessing,
        clip_values: Optional[CLIP_VALUES_TYPE] = (0, 255),
        preprocessing_defences: Union[Preprocessor, List[Preprocessor], None] = None,
        **kwargs,
    ) -> None:
        self._bounding_boxes_postprocessing = bounding_boxes_postprocessing
        self._channels_first = False
        self._n_classes = n_classes
        super().__init__(
            model=model,
            clip_values=clip_values,
            preprocessing_defences=preprocessing_defences,
            **kwargs,
        )

    @property
    def channels_first(self) -> bool:
        """Boolean to indicate index of the color channels in the sample `x`."""
        return self._channels_first

    @property
    def input_shape(self) -> tuple[int, int, int]:
        """Return the shape of one input sample.

        Returns:
            Shape of one input sample.
        """
        return cast(YOLOV1ObjectDetector, self._model).image_input_shape

    @property
    def native_label_is_pytorch_format(self) -> bool:
        return False

    def fit(self, x, y, **kwargs) -> None:
        raise NotImplementedError

    def predict(
        self,
        x: np.ndarray,
        batch_size: int = 16,
        standardise_output: bool = False,
        **kwargs,
    ) -> Any:
        """Perform prediction for a batch of inputs.

        Args:
            x: Samples of shape (nb_samples, height, width, nb_channels).
            batch_size: Batch size.
            standardise_output: True if output should be standardised to PyTorch format.
                Box coordinates will be scaled from [0, 1] to image dimensions, label
                index will be increased by 1 to adhere to COCO categories and the boxes
                will be changed to [x1, y1, x2, y2] format, with 0 <= x1 < x2 <= W and
                0 <= y1 < y2 <= H.

        Returns:
            Predictions of format `List[Dict[str, np.ndarray]]`, one for each input
            image. The fields of the Dict are as follows:
            - boxes [N, 4]: the boxes in [y1, x1, y2, x2] format, with 0 <= x1 < x2 <= W
                and 0 <= y1 < y2 <= H. Can be changed to PyTorch format with
                `standardise_output=True`.
            - labels [N]: the labels for each image in TensorFlow format. Can be changed
                to PyTorch format with `standardise_output=True`.
            - scores [N]: the scores or each prediction.
        """
        # Apply preprocessing
        x, _ = self._apply_preprocessing(x, y=None, fit=False)

        num_batches = math.ceil(x.shape[0] / batch_size)

        bbox_coordinates = []
        bbox_confidences = []
        class_probabilities = []

        for i_batch in range(num_batches):
            i_batch_start = i_batch * batch_size
            i_batch_end = min((i_batch + 1) * batch_size, x.shape[0])
            coord, conf, prob = self._model.predict(
                x=tf.convert_to_tensor(x[i_batch_start:i_batch_end]),
                **kwargs,
            )

            bbox_coordinates.append(coord)
            bbox_confidences.append(conf)
            class_probabilities.append(prob)

        predictions = self._bounding_boxes_postprocessing.postprocess(
            bboxes_cell_xywh=tf.concat(bbox_coordinates, axis=0),
            bboxes_conf=tf.concat(bbox_confidences, axis=0),
            bboxes_labels=tf.concat(class_probabilities, axis=0),
        )

        return self._encode_predict_output(
            predictions=predictions, standardise_output=standardise_output
        )

    def loss_gradient(
        self,
        x: np.ndarray,
        y: List[Dict[str, np.ndarray]],
        standardise_output: bool = False,
        **kwargs,
    ):
        """Compute the gradient of the loss function w.r.t. `x`.

        Args:
            x: Samples of shape (nb_samples, height, width, nb_channels).
            y: Targets of format `List[Dict[str, np.ndarray]]`, one for each input
                image. The fields of the Dict are as follows:
                - boxes [N, 4]: the boxes in [y1, x1, y2, x2] in scale [0, 1]
                    (`standardise_output=False`) or [x1, y1, x2, y2] in image scale
                    (`standardise_output=True`) format, with 0 <= x1 < x2 <= W and
                    0 <= y1 < y2 <= H.
                - labels [N]: the labels for each image in TensorFlow
                    (`standardise_output=False`) or PyTorch (`standardise_output=True`)
                    format
            standardise_output: True if `y` is provided in standardised PyTorch format.
                Box coordinates will be scaled back to [0, 1], label index will be
                decreased by 1 and the boxes will be changed from [x1, y1, x2, y2] to
                [y1, x1, y2, x2] format, with 0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H.

        Returns:
            Loss gradients of the same shape as `x`.
        """
        # Apply preprocessing
        x_preprocessed, _ = self._apply_preprocessing(x, y=None, fit=False)

        x_tensor, y_tensor = self._decode_loss_gradient_input(
            x=x_preprocessed, y=y, standardise_output=standardise_output
        )
        input_var = tf.Variable(x_tensor)

        with GradientTape() as tape:
            tape.watch(input_var)
            y_pred = self._model(input_var, training=False)
            loss = self._model.loss(y_tensor, y_pred)

        grads = tape.gradient(loss, input_var).numpy()
        grads = self._apply_preprocessing_gradient(x, grads)

        return grads

    def _decode_loss_gradient_input(
        self, x: np.ndarray, y: List[Dict[str, np.ndarray]], standardise_output: bool
    ) -> Tuple[Tensor, Tuple[Tensor, Tensor, Tensor, Tensor]]:
        # Necessary to make copies of underlying numpy arrays, otherwise y mutates each
        # time this function is called with strandardise_output = True
        y = [{k: v.copy() for k, v in y_dict.items()} for y_dict in y]

        if standardise_output:
            y = convert_pt_to_tf(
                y=y, height=self.input_shape[0], width=self.input_shape[1]
            )

        bboxes_cell_xywh_grid = []
        bboxes_labels_grid = []
        bboxes_object_mask = []
        bboxes_no_object_mask = []

        for element in y:
            nonzero_scores_mask = element["scores"] > 0
            boxes = element["boxes"][..., [1, 0, 3, 2]][nonzero_scores_mask]
            labels = element["labels"][nonzero_scores_mask].astype("int32")

            y_embedded = self._bounding_boxes_postprocessing.embed(
                bboxes_corner=tf.convert_to_tensor(boxes, dtype=tf.float32),
                bboxes_labels=tf.convert_to_tensor(labels, dtype=tf.int32),
                n_classes=tf.convert_to_tensor(self._n_classes, dtype=tf.int32),
            )

            bboxes_cell_xywh_grid.append(y_embedded[0])
            bboxes_labels_grid.append(y_embedded[1])
            bboxes_object_mask.append(y_embedded[2])
            bboxes_no_object_mask.append(y_embedded[3])

        x_tensor = tf.convert_to_tensor(x)
        y_tensor = (
            tf.stack(bboxes_cell_xywh_grid, axis=0),
            tf.stack(bboxes_labels_grid, axis=0),
            tf.stack(bboxes_object_mask, axis=0),
            tf.stack(bboxes_no_object_mask, axis=0),
        )

        return x_tensor, y_tensor

    def _encode_predict_output(
        self,
        predictions: Tuple[Tensor, Tensor, Tensor, Tensor],
        standardise_output: bool,
    ) -> List[Dict[str, np.ndarray]]:
        batched_predictions = zip(
            predictions[0].numpy(),
            predictions[1].numpy(),
            predictions[2].numpy(),
        )
        results = [
            {"boxes": boxes.copy(), "labels": labels.copy(), "scores": scores.copy()}
            for boxes, scores, labels in batched_predictions
        ]

        if standardise_output:
            results = convert_tf_to_pt(
                y=results, height=self.input_shape[0], width=self.input_shape[1]
            )

        return results
