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

from typing import Optional, Tuple

import structlog
from structlog.stdlib import BoundLogger

from .conv2dbatchnorm import Conv2DBatchNormalization

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    import tensorflow as tf
    from tensorflow.keras.initializers import Constant, RandomNormal
    from tensorflow.keras.layers import (
        Activation,
        Concatenate,
        Conv2D,
        Dense,
        Dropout,
        Flatten,
        Layer,
        LeakyReLU,
        Reshape,
        Softmax,
    )

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class YOLOV1BoundingBoxCoordinates(Layer):
    def __init__(
        self,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        confidence_indices = [5 * x + 4 for x in range(n_bounding_boxes)]
        self.bounding_box_indices = [
            x for x in range(5 * n_bounding_boxes) if x not in confidence_indices
        ]
        self.logits_reshape = Reshape(
            target_shape=(
                grid_shape[0],
                grid_shape[1],
                n_bounding_boxes,
                4,
            ),
            name=f"{name}_reshape",
        )
        self.concatenate = Concatenate(axis=-1)
        self.xy_activation = Activation(
            "sigmoid",
            name=f"{name}_xy_activation",
        )
        self.wh_activation = Activation(
            "exponential",
            name=f"{name}_wh_activation",
        )

    def call(self, inputs):
        x = tf.gather(inputs, indices=self.bounding_box_indices, axis=-1)
        x = self.logits_reshape(x)
        x_xy = self.xy_activation(x[..., :2])
        x_wh = self.wh_activation(x[..., 2:4])

        return self.concatenate([x_xy, x_wh])

    def get_config(self):
        grid_shape = self.logits_reshape.target_shape[:2]
        n_bounding_boxes = self.logits_reshape.target_shape[2]

        config = super().get_config()
        config.update({"grid_shape": grid_shape, "n_bounding_boxes": n_bounding_boxes})

        return config


class YOLOV1BoundingBoxConfidences(Layer):
    def __init__(
        self,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.confidence_indices = [5 * x + 4 for x in range(n_bounding_boxes)]
        self.logits_reshape = Reshape(
            target_shape=(
                grid_shape[0],
                grid_shape[1],
                n_bounding_boxes,
            ),
            name=f"{name}_reshape",
        )
        self.activation = Activation(
            "sigmoid",
            name=f"{name}_activation",
        )

    def call(self, inputs):
        x = tf.gather(inputs, indices=self.confidence_indices, axis=-1)
        x = self.logits_reshape(x)

        return self.activation(x)

    def get_config(self):
        grid_shape = self.logits_reshape.target_shape[:2]
        n_bounding_boxes = self.logits_reshape.target_shape[2]

        config = super().get_config()
        config.update({"grid_shape": grid_shape, "n_bounding_boxes": n_bounding_boxes})

        return config


class YOLOV1ClassProbabilities(Layer):
    def __init__(
        self,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        n_classes: int,
        name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.index_begin = 5 * n_bounding_boxes
        self.logits_reshape = Reshape(
            target_shape=(
                grid_shape[0],
                grid_shape[1],
                n_classes,
            ),
            name=f"{name}_reshape",
        )
        self.activation = Activation(
            Softmax(),
            name=f"{name}_activation",
        )

    def call(self, inputs):
        x = inputs[..., self.index_begin :]  # noqa: E203
        x = self.logits_reshape(x)

        return self.activation(x)

    def get_config(self):
        grid_shape = self.logits_reshape.target_shape[:2]
        n_bounding_boxes = self.index_begin // 5
        n_classes = self.logits_reshape.target_shape[2]

        config = super().get_config()
        config.update(
            {
                "grid_shape": grid_shape,
                "n_bounding_boxes": n_bounding_boxes,
                "n_classes": n_classes,
            }
        )

        return config


class YOLOV1Detector(Layer):
    def __init__(
        self,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        n_classes: int,
        init_final_bias_confidence: float = 0.01,
        name: str = "yolo_v1_detector",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        final_bias_init = tf.cast(
            tf.math.log((1 - init_final_bias_confidence) / init_final_bias_confidence),
            tf.float32,
        )
        self.conv_1 = Conv2DBatchNormalization(
            filters=1024,
            kernel_size=(3, 3),
            strides=(1, 1),
            padding="same",
            name=f"{name}_conv_1",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.conv_2 = Conv2DBatchNormalization(
            filters=1024,
            kernel_size=(3, 3),
            strides=(1, 1),
            padding="same",
            name=f"{name}_conv_2",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.conv_3 = Conv2DBatchNormalization(
            filters=1024,
            kernel_size=(3, 3),
            strides=(1, 1),
            padding="same",
            name=f"{name}_conv_3",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.conv_4 = Conv2DBatchNormalization(
            filters=1024,
            kernel_size=(3, 3),
            strides=(1, 1),
            padding="same",
            name=f"{name}_conv_4",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.flatten = Flatten(name=f"{name}_flatten")
        self.dense_1 = Dense(
            units=4096,
            name=f"{name}_dense_1",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.dense_1_activation = Activation(
            LeakyReLU(alpha=0.1), name=f"{name}_dense_1_activation"
        )
        self.dense_1_dropout = Dropout(0.5, name=f"{name}_dense_1_dropout")
        self.dense_2 = Dense(
            units=grid_shape[0] * grid_shape[1] * (5 * n_bounding_boxes + n_classes),
            name=f"{name}_dense_2",
            kernel_initializer=RandomNormal(stddev=0.01),
            bias_initializer=Constant(final_bias_init),
        )
        self.dense_2_reshape = Reshape(
            target_shape=(
                grid_shape[0],
                grid_shape[1],
                5 * n_bounding_boxes + n_classes,
            ),
            name=f"{name}_dense_2_reshape",
        )
        self.bbox_coordinates = YOLOV1BoundingBoxCoordinates(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            name=f"{name}_bbox_coordinates",
        )
        self.bbox_confidences = YOLOV1BoundingBoxConfidences(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            name=f"{name}_bbox_confidences",
        )
        self.class_probabilities = YOLOV1ClassProbabilities(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            n_classes=n_classes,
            name=f"{name}_class_probabilities",
        )

    def call(self, inputs, training=None):
        x = self.conv_1(inputs, training=training)
        x = self.conv_2(x, training=training)
        x = self.conv_3(x, training=training)
        x = self.conv_4(x, training=training)
        x = self.flatten(x)
        x = self.dense_1(x)
        x = self.dense_1_activation(x)
        x = self.dense_1_dropout(x, training=training)
        x = self.dense_2(x)
        x = self.dense_2_reshape(x)

        bbox_coordinates = self.bbox_coordinates(x)
        bbox_confidences = self.bbox_confidences(x)
        class_probabilities = self.class_probabilities(x)

        return bbox_coordinates, bbox_confidences, class_probabilities

    def get_config(self):
        grid_shape = self.dense_2_reshape.target_shape[:2]
        n_bounding_boxes = self.bbox_coordinates.logits_reshape.target_shape[2]
        n_classes = self.class_probabilities.logits_reshape.target_shape[2]

        config = super().get_config()
        config.update(
            {
                "grid_shape": grid_shape,
                "n_bounding_boxes": n_bounding_boxes,
                "n_classes": n_classes,
            }
        )

        return config


class SimpleYOLOV1Detector(Layer):
    def __init__(
        self,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        n_classes: int,
        init_final_bias_confidence: float = 0.01,
        name: str = "simple_yolo_v1_detector",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        final_bias_init = tf.cast(
            tf.math.log((1 - init_final_bias_confidence) / init_final_bias_confidence),
            tf.float32,
        )
        self.conv_1 = Conv2D(
            filters=5 * n_bounding_boxes + n_classes,
            kernel_size=(1, 1),
            strides=(1, 1),
            padding="same",
            name=f"{name}_conv_1",
            kernel_initializer=RandomNormal(stddev=0.01),
            bias_initializer=Constant(final_bias_init),
        )
        self.bbox_coordinates = YOLOV1BoundingBoxCoordinates(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            name=f"{name}_bbox_coordinates",
        )
        self.bbox_confidences = YOLOV1BoundingBoxConfidences(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            name=f"{name}_bbox_confidences",
        )
        self.class_probabilities = YOLOV1ClassProbabilities(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            n_classes=n_classes,
            name=f"{name}_class_probabilities",
        )

        self._grid_shape = grid_shape
        self._n_bounding_boxes = n_bounding_boxes
        self._n_classes = n_classes

    def call(self, inputs):
        x = self.conv_1(inputs)

        bbox_coordinates = self.bbox_coordinates(x)
        bbox_confidences = self.bbox_confidences(x)
        class_probabilities = self.class_probabilities(x)

        return bbox_coordinates, bbox_confidences, class_probabilities

    def get_config(self):
        grid_shape = self._grid_shape
        n_classes = self._n_bounding_boxes
        n_bounding_boxes = self._n_classes

        config = super().get_config()
        config.update(
            {
                "grid_shape": grid_shape,
                "n_bounding_boxes": n_bounding_boxes,
                "n_classes": n_classes,
            }
        )

        return config


class BoundingBoxRegressorYOLOV1Head(Layer):
    def __init__(
        self,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        name: str = "bbox_regressor_yolo_v1_head",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.bbox_conv_1 = Conv2DBatchNormalization(
            filters=1024,
            kernel_size=(1, 1),
            strides=(1, 1),
            padding="valid",
            use_bias=False,
            name=f"{name}_conv_1",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.bbox_conv_1_dropout = Dropout(0.5, name=f"{name}_conv_1_dropout")
        self.bbox_conv_2 = Conv2DBatchNormalization(
            filters=512,
            kernel_size=(1, 1),
            strides=(1, 1),
            padding="valid",
            use_bias=False,
            name=f"{name}_conv_2",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.bbox_conv_2_dropout = Dropout(0.5, name=f"{name}_conv_2_dropout")
        self.bbox_conv_3 = Conv2D(
            filters=5 * n_bounding_boxes,
            kernel_size=(1, 1),
            strides=(1, 1),
            padding="valid",
            use_bias=True,
            name=f"{name}_conv_3",
            kernel_initializer=RandomNormal(stddev=0.01),
        )

        self._grid_shape = grid_shape
        self._n_bounding_boxes = n_bounding_boxes

    def call(self, inputs, training=None):
        x = self.bbox_conv_1(inputs, training=training)
        x = self.bbox_conv_1_dropout(x, training=training)
        x = self.bbox_conv_2(x, training=training)
        x = self.bbox_conv_2_dropout(x, training=training)

        return self.bbox_conv_3(x, training=training)

    def get_config(self):
        grid_shape = self._grid_shape
        n_bounding_boxes = self._n_bounding_boxes

        config = super().get_config()
        config.update({"grid_shape": grid_shape, "n_bounding_boxes": n_bounding_boxes})

        return config


class ObjectClassifierYOLOV1Head(Layer):
    def __init__(
        self,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        n_classes: int,
        init_final_bias_confidence: float = 0.01,
        name: str = "object_classifier_yolo_v1_head",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        final_bias_init = tf.cast(
            tf.math.log((1 - init_final_bias_confidence) / init_final_bias_confidence),
            tf.float32,
        )
        self.classifier_conv_1 = Conv2DBatchNormalization(
            filters=1024,
            kernel_size=(1, 1),
            strides=(1, 1),
            padding="valid",
            use_bias=False,
            name=f"{name}_conv_1",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.classifier_conv_1_dropout = Dropout(0.5, name=f"{name}_conv_1_dropout")
        self.classifier_conv_2 = Conv2DBatchNormalization(
            filters=512,
            kernel_size=(1, 1),
            strides=(1, 1),
            padding="valid",
            use_bias=False,
            name=f"{name}_conv_2",
            kernel_initializer=RandomNormal(stddev=0.01),
        )
        self.classifier_conv_2_dropout = Dropout(0.5, name=f"{name}_conv_2_dropout")
        self.classifier_conv_3 = Conv2D(
            filters=n_classes,
            kernel_size=(1, 1),
            strides=(1, 1),
            padding="valid",
            use_bias=True,
            name=f"{name}_conv_3",
            kernel_initializer=RandomNormal(stddev=0.01),
            bias_initializer=Constant(final_bias_init),
        )

        self._grid_shape = grid_shape
        self._n_bounding_boxes = n_bounding_boxes
        self._n_classes = n_classes

    def call(self, inputs, training=None):
        x = self.classifier_conv_1(inputs, training=training)
        x = self.classifier_conv_1_dropout(x, training=training)
        x = self.classifier_conv_2(x, training=training)
        x = self.classifier_conv_2_dropout(x, training=training)

        return self.classifier_conv_3(x, training=training)

    def get_config(self):
        grid_shape = self._grid_shape
        n_bounding_boxes = self._n_bounding_boxes
        n_classes = self._n_classes

        config = super().get_config()
        config.update(
            {
                "grid_shape": grid_shape,
                "n_bounding_boxes": n_bounding_boxes,
                "n_classes": n_classes,
            }
        )

        return config


class TwoHeadedYOLOV1Detector(Layer):
    def __init__(
        self,
        grid_shape: Tuple[int, int],
        n_bounding_boxes: int,
        n_classes: int,
        init_final_bias_confidence: float = 0.01,
        name: str = "two_headed_yolo_v1_detector",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.bbox_regressor = BoundingBoxRegressorYOLOV1Head(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            name=f"{name}_bbox_regressor_head",
        )
        self.object_classifier = ObjectClassifierYOLOV1Head(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            n_classes=n_classes,
            init_final_bias_confidence=init_final_bias_confidence,
            name=f"{name}_obj_classifier_head",
        )
        self.concatenate = Concatenate(axis=-1)
        self.bbox_coordinates = YOLOV1BoundingBoxCoordinates(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            name=f"{name}_bbox_coordinates",
        )
        self.bbox_confidences = YOLOV1BoundingBoxConfidences(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            name=f"{name}_bbox_confidences",
        )
        self.class_probabilities = YOLOV1ClassProbabilities(
            grid_shape=grid_shape,
            n_bounding_boxes=n_bounding_boxes,
            n_classes=n_classes,
            name=f"{name}_class_probabilities",
        )

    def call(self, inputs):
        logits_bbox_regressor = self.bbox_regressor(inputs)
        logits_obj_classifier = self.object_classifier(inputs)
        x = self.concatenate([logits_bbox_regressor, logits_obj_classifier])

        bbox_coordinates = self.bbox_coordinates(x)
        bbox_confidences = self.bbox_confidences(x)
        class_probabilities = self.class_probabilities(x)

        return bbox_coordinates, bbox_confidences, class_probabilities

    def get_config(self):
        object_classifier_config = self.object_classifier.get_config()
        grid_shape = object_classifier_config["grid_shape"]
        n_bounding_boxes = object_classifier_config["n_bounding_boxes"]
        n_classes = object_classifier_config["n_classes"]

        config = super().get_config()
        config.update(
            {
                "grid_shape": grid_shape,
                "n_bounding_boxes": n_bounding_boxes,
                "n_classes": n_classes,
            }
        )

        return config
