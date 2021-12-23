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

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import cv2

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/frontend.py
class BoundBox:
    def __init__(self, xmin, ymin, xmax, ymax, c=None, classes=None):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

        self.c = c
        self.classes = classes

        self.label = -1
        self.score = -1

    def get_label(self):
        if self.label == -1:
            self.label = np.argmax(self.classes)

        return self.label

    def get_score(self):
        if self.score == -1:
            self.score = self.classes[self.get_label()]

        return self.score


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/frontend.py
def evaluate(
    generator,
    model,
    input_size,
    max_box_per_image,
    anchors,
    nb_class,
    iou_threshold=0.3,
    score_threshold=0.3,
    max_detections=100,
    save_path=None,
):
    """Evaluate a given dataset using a given model.
    code originally from https://github.com/fizyr/keras-retinanet
    # Arguments
        generator       : The generator that represents the dataset to evaluate.
        model           : The model to evaluate.
        iou_threshold   : The threshold used to consider when a detection is positive or negative.
        score_threshold : The score confidence threshold to use for detections.
        max_detections  : The maximum number of detections to use per image.
        save_path       : The path to save images with visualized detections to.
    # Returns
        A dict mapping class names to mAP scores.
    """
    # gather all detections and annotations
    all_detections = [
        [None for i in range(generator.num_classes())] for j in range(generator.size())
    ]
    all_annotations = [
        [None for i in range(generator.num_classes())] for j in range(generator.size())
    ]

    for i in range(generator.size()):
        raw_image = generator.load_image(i)
        raw_height, raw_width, raw_channels = raw_image.shape

        # make the boxes and the labels
        pred_boxes = detector_predict(
            model=model,
            image=raw_image,
            input_size=input_size,
            max_box_per_image=max_box_per_image,
            anchors=anchors,
            nb_class=nb_class,
        )

        score = np.array([box.score for box in pred_boxes])
        pred_labels = np.array([box.label for box in pred_boxes])

        if len(pred_boxes) > 0:
            pred_boxes = np.array(
                [
                    [
                        box.xmin * raw_width,
                        box.ymin * raw_height,
                        box.xmax * raw_width,
                        box.ymax * raw_height,
                        box.score,
                    ]
                    for box in pred_boxes
                ]
            )
        else:
            pred_boxes = np.array([[]])

        # sort the boxes and the labels according to scores
        score_sort = np.argsort(-score)
        pred_labels = pred_labels[score_sort]
        pred_boxes = pred_boxes[score_sort]

        # copy detections to all_detections
        for label in range(generator.num_classes()):
            all_detections[i][label] = pred_boxes[pred_labels == label, :]

        annotations = generator.load_annotation(i)

        # copy detections to all_annotations
        for label in range(generator.num_classes()):
            all_annotations[i][label] = annotations[
                annotations[:, 4] == label, :4
            ].copy()

    # compute mAP by comparing all detections and all annotations
    average_precisions = {}

    for label in range(generator.num_classes()):
        false_positives = np.zeros((0,))
        true_positives = np.zeros((0,))
        scores = np.zeros((0,))
        num_annotations = 0.0

        for i in range(generator.size()):
            detections = all_detections[i][label]
            annotations = all_annotations[i][label]
            num_annotations += annotations.shape[0]
            detected_annotations = []

            for d in detections:
                scores = np.append(scores, d[4])

                if annotations.shape[0] == 0:
                    false_positives = np.append(false_positives, 1)
                    true_positives = np.append(true_positives, 0)
                    continue

                overlaps = compute_overlap(np.expand_dims(d, axis=0), annotations)
                assigned_annotation = np.argmax(overlaps, axis=1)
                max_overlap = overlaps[0, assigned_annotation]

                if (
                    max_overlap >= iou_threshold
                    and assigned_annotation not in detected_annotations
                ):
                    false_positives = np.append(false_positives, 0)
                    true_positives = np.append(true_positives, 1)
                    detected_annotations.append(assigned_annotation)
                else:
                    false_positives = np.append(false_positives, 1)
                    true_positives = np.append(true_positives, 0)

        # no annotations -> AP for this class is 0 (is this correct?)
        if num_annotations == 0:
            average_precisions[label] = 0
            continue

        # sort by score
        indices = np.argsort(-scores)
        false_positives = false_positives[indices]
        true_positives = true_positives[indices]

        # compute false positives and true positives
        false_positives = np.cumsum(false_positives)
        true_positives = np.cumsum(true_positives)

        # compute recall and precision
        recall = true_positives / num_annotations
        precision = true_positives / np.maximum(
            true_positives + false_positives, np.finfo(np.float64).eps
        )

        # compute average precision
        average_precision = compute_ap(recall, precision)
        average_precisions[label] = average_precision

    return average_precisions


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/frontend.py
def detector_predict(model, image, input_size, max_box_per_image, anchors, nb_class):
    image_h, image_w, _ = image.shape
    image = cv2.resize(image, (input_size, input_size))

    input_image = image[:, :, ::-1]
    input_image = np.expand_dims(input_image, 0)
    dummy_array = np.zeros((1, 1, 1, 1, max_box_per_image, 4))

    netout = model.predict([input_image, dummy_array])[0]
    boxes = decode_netout(netout, anchors, nb_class)

    return boxes


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/utils.py
def compute_overlap(a, b):
    """
    Code originally from https://github.com/rbgirshick/py-faster-rcnn.
    Parameters
    ----------
    a: (N, 4) ndarray of float
    b: (K, 4) ndarray of float
    Returns
    -------
    overlaps: (N, K) ndarray of overlap between boxes and query_boxes
    """
    area = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])

    iw = np.minimum(np.expand_dims(a[:, 2], axis=1), b[:, 2]) - np.maximum(
        np.expand_dims(a[:, 0], 1), b[:, 0]
    )
    ih = np.minimum(np.expand_dims(a[:, 3], axis=1), b[:, 3]) - np.maximum(
        np.expand_dims(a[:, 1], 1), b[:, 1]
    )

    iw = np.maximum(iw, 0)
    ih = np.maximum(ih, 0)

    ua = (
        np.expand_dims((a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1]), axis=1)
        + area
        - iw * ih
    )

    ua = np.maximum(ua, np.finfo(float).eps)

    intersection = iw * ih

    return intersection / ua


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/utils.py
def bbox_iou(box1, box2):
    intersect_w = _interval_overlap([box1.xmin, box1.xmax], [box2.xmin, box2.xmax])
    intersect_h = _interval_overlap([box1.ymin, box1.ymax], [box2.ymin, box2.ymax])

    intersect = intersect_w * intersect_h

    w1, h1 = box1.xmax - box1.xmin, box1.ymax - box1.ymin
    w2, h2 = box2.xmax - box2.xmin, box2.ymax - box2.ymin

    union = w1 * h1 + w2 * h2 - intersect

    return float(intersect) / union


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/utils.py
def decode_netout(netout, anchors, nb_class, obj_threshold=0.3, nms_threshold=0.3):
    grid_h, grid_w, nb_box = netout.shape[:3]

    boxes = []

    # decode the output by the network
    netout[..., 4] = _sigmoid(netout[..., 4])
    netout[..., 5:] = netout[..., 4][..., np.newaxis] * _softmax(netout[..., 5:])
    netout[..., 5:] *= netout[..., 5:] > obj_threshold

    for row in range(grid_h):
        for col in range(grid_w):
            for b in range(nb_box):
                # from 4th element onwards are confidence and class classes
                classes = netout[row, col, b, 5:]

                if np.sum(classes) > 0:
                    # first 4 elements are x, y, w, and h
                    x, y, w, h = netout[row, col, b, :4]

                    x = (
                        col + _sigmoid(x)
                    ) / grid_w  # center position, unit: image width
                    y = (
                        row + _sigmoid(y)
                    ) / grid_h  # center position, unit: image height
                    w = anchors[2 * b + 0] * np.exp(w) / grid_w  # unit: image width
                    h = anchors[2 * b + 1] * np.exp(h) / grid_h  # unit: image height
                    confidence = netout[row, col, b, 4]

                    box = BoundBox(
                        x - w / 2, y - h / 2, x + w / 2, y + h / 2, confidence, classes
                    )

                    boxes.append(box)

    # suppress non-maximal boxes
    for c in range(nb_class):
        sorted_indices = list(reversed(np.argsort([box.classes[c] for box in boxes])))

        for i in range(len(sorted_indices)):
            index_i = sorted_indices[i]

            if boxes[index_i].classes[c] == 0:
                continue
            else:
                for j in range(i + 1, len(sorted_indices)):
                    index_j = sorted_indices[j]

                    if bbox_iou(boxes[index_i], boxes[index_j]) >= nms_threshold:
                        boxes[index_j].classes[c] = 0

    # remove the boxes which are less likely than a obj_threshold
    boxes = [box for box in boxes if box.get_score() > obj_threshold]

    return boxes


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/utils.py
def compute_ap(recall, precision):
    """Compute the average precision, given the recall and precision curves.
    Code originally from https://github.com/rbgirshick/py-faster-rcnn.
    # Arguments
        recall:    The recall curve (list).
        precision: The precision curve (list).
    # Returns
        The average precision as computed in py-faster-rcnn.
    """
    # correct AP calculation
    # first append sentinel values at the end
    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.concatenate(([0.0], precision, [0.0]))

    # compute the precision envelope
    for i in range(mpre.size - 1, 0, -1):
        mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])

    # to calculate area under PR curve, look for points
    # where X axis (recall) changes value
    i = np.where(mrec[1:] != mrec[:-1])[0]

    # and sum (\Delta recall) * prec
    ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
    return ap


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/utils.py
def _interval_overlap(interval_a, interval_b):
    x1, x2 = interval_a
    x3, x4 = interval_b

    if x3 < x1:
        if x4 < x1:
            return 0
        else:
            return min(x2, x4) - x1
    else:
        if x2 < x3:
            return 0
        else:
            return min(x2, x4) - x3


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/utils.py
def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# https://github.com/experiencor/keras-yolo2/blob/8bc3fcdc123a5d6b9624ed4188e07b876b79dac5/utils.py
def _softmax(x, axis=-1, t=-100.0):
    x = x - np.max(x)

    if np.min(x) < t:
        x = x / np.min(x) * t

    e_x = np.exp(x)

    return e_x / e_x.sum(axis, keepdims=True)
