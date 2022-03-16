import argparse
import json
from pathlib import Path

# Import third-party Python packages
import numpy as np
import structlog
import tensorflow as tf
from art.attacks.evasion import RobustDPatch
from structlog.stdlib import BoundLogger
from tensorflow.keras.optimizers import Adam

from dpatch_robust import ModifiedRobustDPatch

# Import from Dioptra SDK
from mitre.securingai.sdk.utilities.logging import (
    configure_structlog,
    set_logging_level,
)
from mitre.securingai.sdk.object_detection.data import TensorflowObjectDetectionData
from mitre.securingai.sdk.object_detection.bounding_boxes.iou import (
    TensorflowBoundingBoxesBatchedGridIOU,
)
from mitre.securingai.sdk.object_detection.architectures import YOLOV1ObjectDetector, ARTYOLOV1ObjectDetector
from mitre.securingai.sdk.object_detection.losses import YOLOV1Loss
from mitre.securingai.sdk.object_detection.bounding_boxes.postprocessing import (
    TensorflowBoundingBoxesYOLOV1Confluence,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()
CHECKPOINTS_DIR = Path("checkpoints")
MODELS_DIR = Path("models") / "efficientnetb1_twoheaded"
PATCHES_DIR = Path("patches")
INPUT_IMAGE_SHAPE = (448, 448, 3)

set_logging_level("INFO")
configure_structlog()

### Functions
def append_loss_history(loss_history, output):
    for loss in ["yolov1_loss"]:
        loss_history[loss] += [output[loss]]

    return loss_history


def get_loss(model, loss_func, x, y):
    y_pred = model.predict(x)
    loss = loss_func(
        y_true=y,
        y_pred=y_pred,
    )

    return {"yolov1_loss": float(loss.numpy())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Model evaluation.")
    parser.add_argument("--batch-size", default=32, type=int)
    parser.add_argument("--confluence-threshold", default=0.85, type=float)
    parser.add_argument("--score-threshold", default=0.50, type=float)
    parser.add_argument("--min-detection-score", default=0.75, type=float)
    parser.add_argument("--pre-algorithm-threshold", default=0.25, type=float)
    parser.add_argument("--force-prediction", action="store_true")
    parser.add_argument("--finetuned", action="store_true")
    parser.add_argument("--data-dir", default="data/Road-Sign-Detection-v2-balanced-div/testing", type=str)
    parser.add_argument("--model-weights", default="roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights.hdf5", type=str)
    parser.add_argument("--patch", default="roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-robust-dpatch.npy", type=str)
    parser.add_argument("--patch-size", default=60, type=int)
    parser.add_argument("--max-iter", default=100000, type=int)
    parser.add_argument("--learning-rate", default=0.1, type=float)
    parser.add_argument("--lr-decay-size", default=0.95, type=float)
    parser.add_argument("--lr-decay-schedule", default=5000, type=int)
    parser.add_argument("--momentum", default=0.9, type=float)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--image-id", default=0, type=int)
    args = parser.parse_args()

    DATA_DIR = Path(args.data_dir).resolve()
    MODEL_WEIGHTS = MODELS_DIR / args.model_weights

    efficientnet_model = YOLOV1ObjectDetector(
        input_shape=INPUT_IMAGE_SHAPE,
        n_bounding_boxes=2,
        n_classes=4,
        backbone="efficientnetb1",
        detector="two_headed",
    )
    efficientnet_bbox_grid_iou = TensorflowBoundingBoxesBatchedGridIOU.on_grid_shape(
        efficientnet_model.output_grid_shape
    )
    efficientnet_bbox_confluence = TensorflowBoundingBoxesYOLOV1Confluence.on_grid_shape(
        efficientnet_model.output_grid_shape,
        confluence_threshold=args.confluence_threshold,
        score_threshold=args.score_threshold,
        min_detection_score=args.min_detection_score,
        pre_algorithm_threshold=args.pre_algorithm_threshold,
        force_prediction=args.force_prediction,
    )
    efficientnet_yolo_loss = YOLOV1Loss(bbox_grid_iou=efficientnet_bbox_grid_iou)

    efficientnet_data = TensorflowObjectDetectionData.create(
        image_dimensions=INPUT_IMAGE_SHAPE,
        grid_shape=efficientnet_model.output_grid_shape,
        labels=["crosswalk", "speedlimit", "stop", "trafficlight"],
        testing_directory=str(DATA_DIR),
        augmentations=None,
        batch_size=args.batch_size,
    )

    efficientnet_testing_data = efficientnet_data.testing_dataset

    ####

    efficientnet_model.build(
        (None, INPUT_IMAGE_SHAPE[0], INPUT_IMAGE_SHAPE[1], INPUT_IMAGE_SHAPE[2])
    )

    if args.finetuned:
        efficientnet_model.backbone.trainable = True

    efficientnet_model.load_weights(str(MODEL_WEIGHTS))
    efficientnet_model.compile(loss=efficientnet_yolo_loss, optimizer=Adam(3e-5))

    wrapped_model = ARTYOLOV1ObjectDetector(
        model=efficientnet_model,
        n_classes=4,
        bounding_boxes_postprocessing=efficientnet_bbox_confluence,
    )

    images = []
    pred_bboxes_cell_xywh_grid = []
    pred_bboxes_labels_grid = []
    pred_bboxes_object_mask = []
    pred_bboxes_no_object_mask = []

    for x_source, y_source in efficientnet_testing_data:
        images.append(x_source)
        _, y_pred = wrapped_model._decode_loss_gradient_input(x=x_source.numpy(), y=wrapped_model.predict(x_source.numpy(), standardise_output=False, batch_size=args.batch_size), standardise_output=False)
        pred_bboxes_cell_xywh_grid.append(y_pred[0])
        pred_bboxes_labels_grid.append(y_pred[1])
        pred_bboxes_object_mask.append(y_pred[2])
        pred_bboxes_no_object_mask.append(y_pred[3])

    images = tf.concat(images, axis=0)
    y_pred = (
        tf.concat(pred_bboxes_cell_xywh_grid, axis=0),
        tf.concat(pred_bboxes_labels_grid, axis=0),
        tf.concat(pred_bboxes_object_mask, axis=0),
        tf.concat(pred_bboxes_no_object_mask, axis=0),
    )

    dpatch_attack = ModifiedRobustDPatch(
        estimator=wrapped_model,
        brightness_range=[1.0, 1.0],
        rotation_weights=[1, 0, 0, 0],
        patch_shape=[args.patch_size, args.patch_size, 3],
        sample_size=1,
        learning_rate=args.learning_rate,
        lr_decay_size=args.lr_decay_size,
        lr_decay_schedule=args.lr_decay_schedule,
        momentum=args.momentum,
        max_iter=1,
        batch_size=1 if args.image_id >= 0 else args.batch_size,
        targeted=False,
        verbose=False,
    )

    if args.image_id >= 0:
        x = images[args.image_id:args.image_id + 1].numpy()
        y = (
            y_pred[0][args.image_id:args.image_id + 1],
            y_pred[1][args.image_id:args.image_id + 1],
            y_pred[2][args.image_id:args.image_id + 1],
            y_pred[3][args.image_id:args.image_id + 1],
        )

    else:
        x = images[0:abs(args.image_id)].numpy()
        y = (
            y_pred[0][0:abs(args.image_id)],
            y_pred[1][0:abs(args.image_id)],
            y_pred[2][0:abs(args.image_id)],
            y_pred[3][0:abs(args.image_id)],
        )

    if args.resume:
        patch = np.load(str(PATCHES_DIR / args.patch))
        dpatch_attack._patch = patch

        with (PATCHES_DIR / f"{Path(args.patch).stem}_loss_history.json").open("rt") as f:
            loss_history = json.load(f)

    else:
        loss_history = {"yolov1_loss": []}

    for i in range(args.max_iter):
        print("Iteration:", i)
        patch = dpatch_attack.generate(x)
        x_patch = dpatch_attack.apply_patch(x)

        loss = get_loss(efficientnet_model, efficientnet_yolo_loss, tf.convert_to_tensor(x_patch), y)
        print(loss)
        loss_history = append_loss_history(loss_history, loss)

        with (PATCHES_DIR / f"{Path(args.patch).stem}_loss_history.json").open("wt") as f:
            f.write(json.dumps(loss_history))

        np.save(str(PATCHES_DIR / args.patch), dpatch_attack._patch)
