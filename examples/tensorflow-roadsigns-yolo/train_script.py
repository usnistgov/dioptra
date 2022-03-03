from pathlib import Path

from imgaug.augmentables import BoundingBox, BoundingBoxesOnImage
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import CSVLogger, ModelCheckpoint, TerminateOnNaN

from mitre.securingai.sdk.object_detection.data import TensorflowObjectDetectionData
from mitre.securingai.sdk.object_detection.bounding_boxes.iou import (
    TensorflowBoundingBoxesBatchedGridIOU,
)
from mitre.securingai.sdk.object_detection.architectures import (
    EfficientNetTwoHeadedYOLOV1Detector,
    MobileNetV2TwoHeadedYOLOV1Detector,
)
from mitre.securingai.sdk.object_detection.losses import ModifiedYOLOV1Loss
from mitre.securingai.sdk.object_detection.bounding_boxes.nms import (
    TensorflowBoundingBoxesYOLOV1NMS,
)


def prepare_callbacks(logfile_name, checkpoint_prefix):
    return [
        ModelCheckpoint(
            # filepath=str(Path.cwd() / "checkpoints")
            filepath=str(Path.cwd() / "checkpoints-speedlimit-stop-only")
            + "/"
            + checkpoint_prefix
            + "-weights.{epoch:03d}-{loss:.3f}.hdf5",
            monitor="loss",
            save_weights_only=True,
        ),
        CSVLogger(logfile_name, append=True),
        TerminateOnNaN(),
    ]


def get_predicted_bbox_image_batch(model, image, input_image_shape, bbox_nms):
    # label_mapper = {0: "crosswalk", 1: "speedlimit", 2: "stop", 3: "trafficlight"}
    label_mapper = {0: "speedlimit", 1: "stop"}
    x_shape = input_image_shape[1]
    y_shape = input_image_shape[0]

    pred_bbox, pred_conf, pred_labels = model(image)
    finalout = bbox_nms.combined_non_max_suppression(pred_bbox, pred_conf, pred_labels)
    for image_id in range(8):
        final_bboxes = [
            BoundingBox(
                x1=x[1] * x_shape,
                y1=x[0] * y_shape,
                x2=x[3] * x_shape,
                y2=x[2] * y_shape,
                label=label_mapper.get(label_id, str(label_id)),
            )
            for x, label_id in zip(
                finalout[0][image_id].numpy(), finalout[2][image_id].numpy()
            )
        ]
        final_bboxes_image = BoundingBoxesOnImage(final_bboxes, shape=input_image_shape)

        yield final_bboxes_image.clip_out_of_image().draw_on_image(
            image=image[image_id].numpy().astype("uint8")
        ), finalout[0][image_id], finalout[1][image_id], finalout[2][image_id], finalout[3][image_id], pred_conf[image_id], pred_labels[image_id]


def get_predicted_bbox_images(data, model, input_image_shape, bbox_nms):
    for image, _ in data:
        for pred_image, pred_boxes, pred_scores, pred_labels, pred_num_detections, pred_conf, pred_labels_proba in get_predicted_bbox_image_batch(
            model, image, input_image_shape, bbox_nms
        ):
            yield pred_image, pred_boxes, pred_scores, pred_labels, pred_num_detections, pred_conf, pred_labels_proba


def finetune(
    train_data, val_data, model, loss, epochs, logfile_name, checkpoint_prefix, learning_rate=1e-5
):
    model.backbone.model.trainable = True
    optimizer = Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss=loss)

    return model.fit(
        x=train_data,
        validation_data=val_data,
        epochs=epochs,
        callbacks=prepare_callbacks(logfile_name, checkpoint_prefix),
    )


def train(
    train_data, val_data, model, loss, epochs, logfile_name, checkpoint_prefix, learning_rate=3e-5
):
    model.backbone.model.trainable = False
    optimizer = Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss=loss)

    return model.fit(
        x=train_data,
        validation_data=val_data,
        epochs=epochs,
        callbacks=prepare_callbacks(logfile_name, checkpoint_prefix),
    )


input_image_shape = (448, 448, 3)
# input_image_shape = (224, 224, 3)
training_dir = Path("data/speedlimit_stop/training").resolve()
validation_dir = Path("data/speedlimit_stop/validation").resolve()
testing_dir = Path("data/speedlimit_stop/testing").resolve()
# training_dir = Path("data/Road-Sign-Detection-v2").resolve()
# validation_dir = None
# testing_dir = Path("data/Road-Sign-Detection-v2").resolve()

efficientnet_model = EfficientNetTwoHeadedYOLOV1Detector(
    flavor="B0", input_shape=input_image_shape, n_bounding_boxes=2, n_classes=2
)
# efficientnet_model = EfficientNetTwoHeadedYOLOV1Detector(
#     flavor="B1", input_shape=input_image_shape, n_bounding_boxes=2, n_classes=4
# )
efficientnet_bbox_grid_iou = TensorflowBoundingBoxesBatchedGridIOU.on_grid_shape(
    efficientnet_model.output_grid_shape
)
efficientnet_bbox_nms = TensorflowBoundingBoxesYOLOV1NMS.on_grid_shape(
    efficientnet_model.output_grid_shape,
    max_output_size_per_class=10,
    iou_threshold=0.2,
    score_threshold=0.6,
)
efficientnet_yolo_loss = ModifiedYOLOV1Loss(bbox_grid_iou=efficientnet_bbox_grid_iou, coord_weight=5)
# mobilenetv2_model = MobileNetV2TwoHeadedYOLOV1Detector(
#     input_shape=input_image_shape, n_bounding_boxes=2, n_classes=2
# )
# mobilenetv2_model = MobileNetV2TwoHeadedYOLOV1Detector(
#     input_shape=input_image_shape, n_bounding_boxes=2, n_classes=4
# )
mobilenetv2_model = MobileNetV2TwoHeadedYOLOV1Detector(
    input_shape=input_image_shape, n_bounding_boxes=2, n_classes=2
)
mobilenetv2_bbox_grid_iou = TensorflowBoundingBoxesBatchedGridIOU.on_grid_shape(
    mobilenetv2_model.output_grid_shape
)
mobilenetv2_bbox_nms = TensorflowBoundingBoxesYOLOV1NMS.on_grid_shape(
    mobilenetv2_model.output_grid_shape,
    max_output_size_per_class=10,
    iou_threshold=0.5,
    score_threshold=0.5,
)
mobilenetv2_yolo_loss = ModifiedYOLOV1Loss(bbox_grid_iou=mobilenetv2_bbox_grid_iou, coord_weight=5)

efficientnet_data = TensorflowObjectDetectionData.create(
    image_dimensions=input_image_shape,
    grid_shape=efficientnet_model.output_grid_shape,
    # labels=["crosswalk", "speedlimit", "stop", "trafficlight"],
    labels=["speedlimit", "stop"],
    training_directory=str(training_dir),
    validation_directory=str(validation_dir),
    testing_directory=str(testing_dir),
    augmentations="imgaug_minimal",
    # augmentations="imgaug_light",
    batch_size=8,
)
efficientnet_training_data = efficientnet_data.training_dataset
efficientnet_validation_data = efficientnet_data.validation_dataset
efficientnet_testing_data = efficientnet_data.testing_dataset

mobilenetv2_data = TensorflowObjectDetectionData.create(
    image_dimensions=input_image_shape,
    grid_shape=mobilenetv2_model.output_grid_shape,
    # labels=["crosswalk", "speedlimit", "stop", "trafficlight"],
    labels=["speedlimit", "stop"],
    training_directory=str(training_dir),
    validation_directory=str(validation_dir),
    testing_directory=str(testing_dir),
    augmentations="imgaug_minimal",
    # augmentations="imgaug_light",
    batch_size=8,
)
mobilenetv2_training_data = mobilenetv2_data.training_dataset
mobilenetv2_validation_data = mobilenetv2_data.validation_dataset
mobilenetv2_testing_data = mobilenetv2_data.testing_dataset
