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
#
# This is an adaptation of the work
# https://github.com/ashep29/confluence/blob/748c71e848b8a397df6ab0d6173ba890d8b585e2/confluence.py  # noqa: B950
# See copyright below.
#
# Copyright (c) 2021 ashep29
# Distributed under the terms of the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

from collections import defaultdict
from typing import cast

import numpy as np
import numpy.typing as npt
import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.object_detection.bounding_boxes.coordinates import (
    TensorflowBoundingBoxesBatchedGrid,
)
from dioptra.sdk.object_detection.bounding_boxes.postprocessing.bounding_boxes_postprocessing import (  # noqa: B950
    BoundingBoxesYOLOV1PostProcessing,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow import Tensor

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class TensorflowBoundingBoxesYOLOV1Confluence(BoundingBoxesYOLOV1PostProcessing):
    def __init__(
        self,
        bounding_boxes_batched_grid: TensorflowBoundingBoxesBatchedGrid,
        confluence_threshold: float = 0.8,
        score_threshold: float = 0.5,
        min_detection_score: float = 0.5,
        pre_algorithm_threshold: float = 0.05,
        gaussian: bool = False,
        sigma: float = 0.5,
        force_prediction: bool = False,
    ) -> None:
        """
        Args:
            confluence_threshold: value between 0 and 2, with optimum from 0.5-0.8
            score_threshold: class confidence score
            gaussian: boolean switch to turn gaussian decaying of suboptimal bounding
                box confidence scores (setting to False results in suppression of
                suboptimal boxes)
            sigma: used in gaussian decaying. A smaller value causes harsher decaying.

        Returns:
            A dictionary mapping class identity to final retained boxes (and
            corresponding confidence scores)
        """
        self._bbox_batched_grid = bounding_boxes_batched_grid
        self._confluence_threshold = confluence_threshold
        self._score_threshold = score_threshold
        self._min_detection_score = min_detection_score
        self._pre_algorithm_threshold = pre_algorithm_threshold
        self._gaussian = gaussian
        self._sigma = sigma
        self._force_prediction = force_prediction

    @classmethod
    def on_grid_shape(
        cls,
        grid_shape: tuple[int, int],
        confluence_threshold: float = 0.80,
        score_threshold: float = 0.5,
        min_detection_score: float = 0.5,
        pre_algorithm_threshold: float = 0.05,
        gaussian: bool = False,
        sigma: float = 0.5,
        force_prediction: bool = False,
    ) -> TensorflowBoundingBoxesYOLOV1Confluence:
        return cls(
            bounding_boxes_batched_grid=(
                TensorflowBoundingBoxesBatchedGrid.on_grid_shape(grid_shape=grid_shape)
            ),
            confluence_threshold=confluence_threshold,
            score_threshold=score_threshold,
            min_detection_score=min_detection_score,
            pre_algorithm_threshold=pre_algorithm_threshold,
            gaussian=gaussian,
            sigma=sigma,
            force_prediction=force_prediction,
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def postprocess(
        self, bboxes_cell_xywh: Tensor, bboxes_conf: Tensor, bboxes_labels: Tensor
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        batch_size = tf.cast(tf.shape(bboxes_cell_xywh)[0], tf.int32)
        num_boxes = tf.cast(tf.reduce_prod(tf.shape(bboxes_cell_xywh)[1:4]), tf.int32)
        num_labels = tf.cast(tf.shape(bboxes_labels)[-1], tf.int32)

        boxes = tf.reshape(
            self._from_cell_xywh_to_corner(bboxes_cell_xywh=bboxes_cell_xywh),
            shape=(batch_size, num_boxes, 4),
        )

        all_scores = tf.reshape(
            self._calculate_prediction_scores(
                bboxes_conf=bboxes_conf, bboxes_labels=bboxes_labels
            ),
            shape=(batch_size, num_boxes, num_labels),
        )
        top_scores = tf.math.top_k(all_scores, k=1)
        scores = tf.cast(
            tf.reshape(top_scores.values, shape=(batch_size, num_boxes)), tf.float32
        )
        labels = tf.cast(
            tf.reshape(top_scores.indices, shape=(batch_size, num_boxes)), tf.int32
        )

        final_boxes, final_scores, final_labels, final_detections = tf.numpy_function(
            self.confluence,
            [boxes, scores, labels],
            [tf.float32, tf.float32, tf.int32, tf.int32],
        )

        return (
            tf.gather(final_boxes, indices=[1, 0, 3, 2], axis=-1),
            final_scores,
            final_labels,
            final_detections,
        )

    def confluence(
        self,
        boxes: npt.NDArray,
        scores: npt.NDArray,
        labels: npt.NDArray,
    ):
        """
        Args:
            bounding_boxes: list of bounding boxes (x1,y1,x2,y2)
            classes: list of class identifiers (int value, e.g. 1 = person)
            scores: list of class confidence scores (0.0-1.0)

        Returns:
            A dictionary mapping class identity to final retained boxes (and
            corresponding confidence scores)
        """
        batch_size = boxes.shape[0]
        retained_boxes = []
        retained_scores = []
        retained_labels = []

        for batch_idx in range(batch_size):
            class_mapping: dict[int, list[npt.NDArray]] = self.assign_boxes_to_classes(
                boxes[batch_idx], labels[batch_idx], scores[batch_idx]
            )
            output = {}

            for each_class in class_mapping:
                dets = np.array(class_mapping[each_class])
                retain = []

                while dets.size > 0:
                    confluence_scores: list[npt.NDArray] = []
                    proximities = []

                    while len(confluence_scores) < np.size(dets, 0):
                        current_box = len(confluence_scores)
                        x1 = dets[current_box, 0]
                        y1 = dets[current_box, 1]
                        x2 = dets[current_box, 2]
                        y2 = dets[current_box, 3]
                        confidence_score = dets[current_box, 4]

                        xx1 = dets[np.arange(len(dets)) != current_box, 0]
                        yy1 = dets[np.arange(len(dets)) != current_box, 1]
                        xx2 = dets[np.arange(len(dets)) != current_box, 2]
                        yy2 = dets[np.arange(len(dets)) != current_box, 3]
                        cconf = dets[np.arange(len(dets)) != current_box, 4]

                        min_x: npt.NDArray = np.minimum(x1, xx1)
                        min_y: npt.NDArray = np.minimum(y1, yy1)
                        max_x: npt.NDArray = np.maximum(x2, xx2)
                        max_y: npt.NDArray = np.maximum(y2, yy2)

                        x1, y1, x2, y2 = self.normalise_coordinates(
                            x1,
                            y1,
                            x2,
                            y2,
                            min_x,
                            max_x,
                            min_y,
                            max_y,
                        )
                        xx1, yy1, xx2, yy2 = self.normalise_coordinates(
                            xx1,
                            yy1,
                            xx2,
                            yy2,
                            min_x,
                            max_x,
                            min_y,
                            max_y,
                        )

                        hd_x1, hd_x2, vd_y1, vd_y2 = (
                            abs(x1 - xx1),
                            abs(x2 - xx2),
                            abs(y1 - yy1),
                            abs(y2 - yy2),
                        )
                        proximity = hd_x1 + hd_x2 + vd_y1 + vd_y2
                        all_proximities = np.ones_like(proximity)
                        cconf_scores = np.zeros_like(cconf)

                        all_proximities[proximity <= self._confluence_threshold] = (
                            proximity[proximity <= self._confluence_threshold]
                        )
                        cconf_scores[proximity <= self._confluence_threshold] = cconf[
                            proximity <= self._confluence_threshold
                        ]

                        if cconf_scores.size > 0:
                            confluence_score = np.amax(cconf_scores)

                        else:
                            confluence_score = confidence_score

                        if all_proximities.size > 0:
                            proximity = (
                                sum(all_proximities) / all_proximities.size
                            ) * (1 - confidence_score)

                        else:
                            proximity = sum(all_proximities) * (1 - confidence_score)

                        confluence_scores.append(confluence_score)
                        proximities.append(proximity)

                    conf = np.array(confluence_scores)
                    prox = np.array(proximities)

                    dets_temp = np.concatenate((dets, prox[:, None]), axis=1)
                    dets_temp = np.concatenate((dets_temp, conf[:, None]), axis=1)
                    min_idx = np.argmin(dets_temp[:, 5], axis=0)
                    dets[[0, min_idx], :] = dets[[min_idx, 0], :]
                    dets_temp[[0, min_idx], :] = dets_temp[[min_idx, 0], :]
                    dets[0, 4] = dets_temp[0, 6]
                    retain.append(dets[0, :])

                    x1, y1, x2, y2 = dets[0, 0], dets[0, 1], dets[0, 2], dets[0, 3]
                    min_x = np.minimum(x1, dets[1:, 0])
                    min_y = np.minimum(y1, dets[1:, 1])
                    max_x = np.maximum(x2, dets[1:, 2])
                    max_y = np.maximum(y2, dets[1:, 3])

                    x1, y1, x2, y2 = self.normalise_coordinates(
                        x1,
                        y1,
                        x2,
                        y2,
                        min_x,
                        max_x,
                        min_y,
                        max_y,
                    )
                    xx1, yy1, xx2, yy2 = self.normalise_coordinates(
                        dets[1:, 0],
                        dets[1:, 1],
                        dets[1:, 2],
                        dets[1:, 3],
                        min_x,
                        max_x,
                        min_y,
                        max_y,
                    )
                    md_x1, md_x2, md_y1, md_y2 = (
                        abs(x1 - xx1),
                        abs(x2 - xx2),
                        abs(y1 - yy1),
                        abs(y2 - yy2),
                    )
                    manhattan_distance = md_x1 + md_x2 + md_y1 + md_y2
                    weights = np.ones_like(manhattan_distance)

                    if self._gaussian:
                        gaussian_weights = np.exp(
                            -((1 - manhattan_distance) * (1 - manhattan_distance))
                            / self._sigma
                        )
                        weights[manhattan_distance <= self._confluence_threshold] = (
                            gaussian_weights[
                                manhattan_distance <= self._confluence_threshold
                            ]
                        )

                    else:
                        weights[manhattan_distance <= self._confluence_threshold] = (
                            manhattan_distance[
                                manhattan_distance <= self._confluence_threshold
                            ]
                        )

                    dets[1:, 4] *= weights
                    to_reprocess = np.where(dets[1:, 4] >= self._score_threshold)[0]
                    dets = dets[to_reprocess + 1, :]

                output[each_class] = retain

            batch_boxes, batch_scores, batch_labels = self.from_mapping_to_arrays(
                output
            )

            retained_boxes.append(batch_boxes)
            retained_scores.append(batch_scores)
            retained_labels.append(batch_labels)

        return self.pad_retained_arrays(
            boxes=retained_boxes,
            scores=retained_scores,
            labels=retained_labels,
            batch_size=batch_size,
        )

    def assign_boxes_to_classes(
        self, bounding_boxes: npt.NDArray, classes: npt.NDArray, scores: npt.NDArray
    ) -> dict[int, list[npt.NDArray]]:
        """
        Args:
            bounding_boxes: list of bounding boxes (x1,y1,x2,y2)
            classes: list of class identifiers (int value, e.g. 1 = person)
            scores: list of class confidence scores (0.0-1.0)

        Returns:
            defaultdict(list) containing mapping to bounding boxes and confidence scores
            to class
        """
        boxes_to_classes = defaultdict(list)
        for each_box, each_class, each_score in zip(
            bounding_boxes.tolist(), classes.tolist(), scores.tolist()
        ):
            if each_score >= self._pre_algorithm_threshold:
                boxes_to_classes[each_class].append(
                    np.array(
                        [each_box[0], each_box[1], each_box[2], each_box[3], each_score]
                    )
                )

        return boxes_to_classes

    def normalise_coordinates(
        self,
        x1: npt.NDArray,
        y1: npt.NDArray,
        x2: npt.NDArray,
        y2: npt.NDArray,
        min_x: npt.NDArray,
        max_x: npt.NDArray,
        min_y: npt.NDArray,
        max_y: npt.NDArray,
    ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]:
        """
        Args:
            x1: bounding box coordinate x1
            y1: bounding box coordinate y1
            x2: bounding box coordinate x2
            y2: bounding box coordinate y2
            min_x: minimum bounding box value along x
            max_x: maximum bounding box value along x
            min_y: minimum bounding box value along y
            max_y: maximum bounding box value along y

        Returns:
            Normalised bounding box coordinates (scaled between 0 and 1)
        """
        x1, y1, x2, y2 = (
            (x1 - min_x) / (max_x - min_x),
            (y1 - min_y) / (max_y - min_y),
            (x2 - min_x) / (max_x - min_x),
            (y2 - min_y) / (max_y - min_y),
        )
        return x1, y1, x2, y2

    def from_mapping_to_arrays(
        self, retained
    ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray]:
        boxes = []
        scores = []
        labels = []

        for label_id, label_boxes in retained.items():
            num_label_boxes = len(label_boxes)
            boxes.extend([x[0:4] for x in label_boxes])
            scores.extend([x[4] for x in label_boxes])
            labels.extend(num_label_boxes * [label_id])

        boxes_array = np.array(boxes).astype("float32")
        scores_array = np.array(scores).astype("float32")
        labels_array = np.array(labels).astype("int32")

        # If no boxes remain after confluence calculation, then return empty arrays
        if scores_array.shape[0] == 0:
            return (
                np.zeros((1, 4)).astype("float32"),
                np.zeros(1).astype("float32"),
                np.zeros(1).astype("int32"),
            )

        # If one or more boxes remain after confluence calculation, then drop all below
        # min detection score
        scores_threshold_mask = scores_array >= self._min_detection_score
        num_retained = np.sum(scores_threshold_mask)

        if num_retained > 0:
            return (
                boxes_array[scores_threshold_mask],
                scores_array[scores_threshold_mask],
                labels_array[scores_threshold_mask],
            )

        # If the min detection score threshold drops all the remaining boxes, then check
        # if force prediction option is enabled If force prediction is disabled, then
        # just return empty arrays
        if not self._force_prediction:
            return (
                np.zeros((1, 4)).astype("float32"),
                np.zeros(1).astype("float32"),
                np.zeros(1).astype("int32"),
            )

        # If force prediction is enabled, then keep the best prediction and drop the
        # rest
        idx = int(np.argmax(scores_array))
        return (
            boxes_array[idx : idx + 1],
            scores_array[idx : idx + 1],
            labels_array[idx : idx + 1],
        )

    def pad_retained_arrays(
        self, boxes, scores, labels, batch_size
    ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]:
        padded_boxes: npt.NDArray = np.zeros(
            (batch_size, max(max([x.shape[0] for x in boxes]), 1), 4), dtype="float32"
        )
        padded_scores: npt.NDArray = np.zeros(
            (batch_size, max(max([x.shape[0] for x in scores]), 1)), dtype="float32"
        )
        padded_labels: npt.NDArray = np.zeros(
            (batch_size, max(max([x.shape[0] for x in labels]), 1)), dtype="int32"
        )
        padded_detections: npt.NDArray = np.zeros(batch_size, dtype="int32")

        for batch_idx, (batch_boxes, batch_scores, batch_labels) in enumerate(
            zip(boxes, scores, labels)
        ):
            if len(batch_boxes) > 0:
                padded_boxes[batch_idx, 0 : batch_boxes.shape[0]] = batch_boxes.astype(
                    "float32"
                )

            if len(batch_scores) > 0:
                padded_scores[batch_idx, 0 : batch_scores.shape[0]] = (
                    batch_scores.astype("float32")
                )

            if len(batch_labels) > 0:
                padded_labels[batch_idx, 0 : batch_labels.shape[0]] = (
                    batch_labels.astype("int32")
                )

            padded_detections[batch_idx] = len(batch_scores)

        return padded_boxes, padded_scores, padded_labels, padded_detections

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def embed(
        self, bboxes_corner: Tensor, bboxes_labels: Tensor, n_classes: Tensor
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        return cast(
            tuple[Tensor, Tensor, Tensor, Tensor],
            self._bbox_batched_grid.embed(
                bboxes_corner=bboxes_corner,
                bboxes_labels=bboxes_labels,
                n_classes=n_classes,
            ),
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _from_cell_xywh_to_corner(self, bboxes_cell_xywh: Tensor) -> Tensor:
        n_bounding_boxes = tf.cast(tf.shape(bboxes_cell_xywh)[-2], tf.int32)

        return self._bbox_batched_grid.from_cell_xywh_to_corner(
            bboxes_cell_xywh=bboxes_cell_xywh,
            n_bounding_boxes=n_bounding_boxes,
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _calculate_prediction_scores(
        self, bboxes_conf: Tensor, bboxes_labels: Tensor
    ) -> Tensor:
        n_bounding_boxes = tf.cast(tf.shape(bboxes_conf)[-1], tf.int32)
        bboxes_labels = tf.tile(
            tf.expand_dims(bboxes_labels, axis=-2),
            multiples=(1, 1, 1, n_bounding_boxes, 1),
        )

        return tf.expand_dims(bboxes_conf, axis=-1) * bboxes_labels
