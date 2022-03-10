import random
import re
from pathlib import Path

import numpy as np
import tensorflow as tf
from imgaug.augmentables import BoundingBox, BoundingBoxesOnImage
from PIL import Image
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
from mitre.securingai.sdk.object_detection.losses import YOLOV1Loss
from mitre.securingai.sdk.object_detection.bounding_boxes.nms import (
    TensorflowBoundingBoxesYOLOV1NMS,
)


def prepare_callbacks(logfile_name, checkpoint_prefix):
    return [
        ModelCheckpoint(
            filepath=str(Path.cwd() / "checkpoints")
            # filepath=str(Path.cwd() / "checkpoints-speedlimit-stop-only")
            + "/" + checkpoint_prefix + "-weights.{epoch:03d}-{loss:.3f}.hdf5",
            monitor="loss",
            save_weights_only=True,
        ),
        CSVLogger(logfile_name, append=True),
        TerminateOnNaN(),
    ]


def paste_patches_on_images(image_batch, patch_filepath, image_shape, patch_scale=0.30):
    patched_image_batch = []
    for image in image_batch.numpy():
        patched_image = paste_patch_on_image(
            image.astype("uint8"), patch_filepath, image_shape, patch_scale
        )
        patched_image_batch.append(np.expand_dims(patched_image, axis=0))

    patched_image_batch = np.concatenate(patched_image_batch, axis=0)

    return tf.convert_to_tensor(patched_image_batch.astype("float32"))


def paste_patch_on_image(image, patch_filepath, image_shape, patch_scale=0.30):
    image_height = image_shape[0]
    image_width = image_shape[1]

    patch_image = Image.open(str(patch_filepath)).resize(
        (int(image_width * patch_scale), int(image_height * patch_scale))
    )
    image_wrapped = Image.fromarray(image).copy().convert("RGBA")

    patch_x = random.randint(0, int(image_width * (1 - patch_scale)))
    patch_y = random.randint(0, int(image_height * (1 - patch_scale)))

    image_wrapped.paste(patch_image, (patch_x, patch_y), mask=patch_image)

    return np.array(image_wrapped.convert("RGB"))


def make_coco_results_list_element(image_id, x, y, width, height, category_id, score):
    return {"image_id": int(image_id), "category_id": int(category_id), "bbox": [float(x), float(y), float(width), float(height)], "score": float(score)}


def get_predicted_bbox_image_batch(
    model, image, input_image_shape, bbox_nms, patch_filepath=None, patch_scale=0.30, data_filenames=None, data_filename_id=0
):
    label_mapper = {0: "crosswalk", 1: "speedlimit", 2: "stop", 3: "trafficlight"}
    # label_mapper = {0: "speedlimit", 1: "stop"}
    x_shape = input_image_shape[1]
    y_shape = input_image_shape[0]

    pred_bbox, pred_conf, pred_labels = model(image)
    finalout = bbox_nms.combined_non_max_suppression(pred_bbox, pred_conf, pred_labels)

    if patch_filepath is not None:
        patched_image = paste_patches_on_images(
            image, patch_filepath, input_image_shape, patch_scale
        )
        patched_pred_bbox, patched_pred_conf, patched_pred_labels = model(patched_image)
        patched_finalout = bbox_nms.combined_non_max_suppression(
            patched_pred_bbox, patched_pred_conf, patched_pred_labels
        )

    for image_id in range(8):
        data_filename = None
        coco_image_id = None
        final_bboxes = []
        coco_results = []

        if data_filenames is not None:
            data_filename = Path(data_filenames[data_filename_id])
            coco_image_id = int(re.match(r"\d+?_road(?P<digits>\d+?)\.png", data_filename.name).groupdict()["digits"])
            data_filename_id += 1


        for x, label_id, score in zip(
            finalout[0][image_id].numpy(), finalout[2][image_id].numpy(), finalout[1][image_id].numpy()
        ):
            final_bboxes.append(
                BoundingBox(
                    x1=x[1] * x_shape,
                    y1=x[0] * y_shape,
                    x2=x[3] * x_shape,
                    y2=x[2] * y_shape,
                    label=label_mapper.get(label_id, str(label_id)),
                )
            )

            if image_id is not None:
                coco_results.append(make_coco_results_list_element(image_id=coco_image_id, x=x[1], y=x[0], width=(x[3] - x[1]), height=(x[2] - x[0]), category_id=label_id, score=score))

        final_bboxes_image = BoundingBoxesOnImage(final_bboxes, shape=input_image_shape)

        yield final_bboxes_image.clip_out_of_image().draw_on_image(
            image=image[image_id].numpy().astype("uint8")
        ), finalout[0][image_id], finalout[1][image_id], finalout[2][
            image_id
        ], finalout[
            3
        ][
            image_id
        ], pred_conf[
            image_id
        ], pred_labels[
            image_id
        ], coco_results

        if patch_filepath is not None:
            patched_final_bboxes = []
            patched_coco_results = []

            for x, label_id, score in zip(
                patched_finalout[0][image_id].numpy(), patched_finalout[2][image_id].numpy(), patched_finalout[1][image_id].numpy()
            ):
                patched_final_bboxes.append(
                    BoundingBox(
                        x1=x[1] * x_shape,
                        y1=x[0] * y_shape,
                        x2=x[3] * x_shape,
                        y2=x[2] * y_shape,
                        label=label_mapper.get(label_id, str(label_id)),
                    )
                )

                if image_id is not None:
                    patched_coco_results.append(make_coco_results_list_element(image_id=coco_image_id, x=x[1], y=x[0], width=(x[3] - x[1]), height=(x[2] - x[0]), category_id=label_id, score=score))

            patched_final_bboxes_image = BoundingBoxesOnImage(
                patched_final_bboxes, shape=input_image_shape
            )

            yield patched_final_bboxes_image.clip_out_of_image().draw_on_image(
                image=patched_image[image_id].numpy().astype("uint8")
            ), patched_finalout[0][image_id], patched_finalout[1][
                image_id
            ], patched_finalout[
                2
            ][
                image_id
            ], patched_finalout[
                3
            ][
                image_id
            ], patched_pred_conf[
                image_id
            ], patched_pred_labels[
                image_id
            ], patched_coco_results


def get_predicted_bbox_images(
    data, model, input_image_shape, bbox_nms, patch_filepath=None, patch_scale=0.30, data_filenames=None
):
    data_filename_id = 0
    for image, _ in data:
        for (
            pred_image,
            pred_boxes,
            pred_scores,
            pred_labels,
            pred_num_detections,
            pred_conf,
            pred_labels_proba,
            coco_results
        ) in get_predicted_bbox_image_batch(
            model, image, input_image_shape, bbox_nms, patch_filepath, patch_scale, data_filenames, data_filename_id
        ):
            yield pred_image, pred_boxes, pred_scores, pred_labels, pred_num_detections, pred_conf, pred_labels_proba, coco_results

        data_filename_id += 8

def finetune(
    train_data,
    val_data,
    model,
    loss,
    epochs,
    logfile_name,
    checkpoint_prefix,
    learning_rate=1e-5,
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
    train_data,
    val_data,
    model,
    loss,
    epochs,
    logfile_name,
    checkpoint_prefix,
    learning_rate=3e-5,
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


# input_image_shape = (448, 448, 3)
input_image_shape = (224, 224, 3)
# training_dir = Path("data/speedlimit_stop/training").resolve()
# validation_dir = Path("data/speedlimit_stop/validation").resolve()
# testing_dir = Path("data/speedlimit_stop/testing").resolve()
training_dir = Path("data/Road-Sign-Detection-v2").resolve()
validation_dir = None
testing_dir = Path("data/Road-Sign-Detection-v2").resolve()

# efficientnet_model = EfficientNetTwoHeadedYOLOV1Detector(
#     flavor="B0", input_shape=input_image_shape, n_bounding_boxes=2, n_classes=2
# )
efficientnet_model = EfficientNetTwoHeadedYOLOV1Detector(
    flavor="B1", input_shape=input_image_shape, n_bounding_boxes=2, n_classes=4
)
efficientnet_bbox_grid_iou = TensorflowBoundingBoxesBatchedGridIOU.on_grid_shape(
    efficientnet_model.output_grid_shape
)
efficientnet_bbox_nms = TensorflowBoundingBoxesYOLOV1NMS.on_grid_shape(
    efficientnet_model.output_grid_shape,
    max_output_size_per_class=10,
    iou_threshold=0.2,
    score_threshold=0.6,
)
efficientnet_testing_bbox_nms = TensorflowBoundingBoxesYOLOV1NMS.on_grid_shape(
    efficientnet_model.output_grid_shape,
    max_output_size_per_class=10,
    iou_threshold=0.2,
    score_threshold=0.6,
)
efficientnet_yolo_loss = YOLOV1Loss(bbox_grid_iou=efficientnet_bbox_grid_iou)
# mobilenetv2_model = MobileNetV2TwoHeadedYOLOV1Detector(
#     input_shape=input_image_shape, n_bounding_boxes=2, n_classes=2
# )
mobilenetv2_model = MobileNetV2TwoHeadedYOLOV1Detector(
    input_shape=input_image_shape, n_bounding_boxes=2, n_classes=4
)
# mobilenetv2_model = MobileNetV2TwoHeadedYOLOV1Detector(
#     input_shape=input_image_shape, n_bounding_boxes=2, n_classes=2
# )
mobilenetv2_bbox_grid_iou = TensorflowBoundingBoxesBatchedGridIOU.on_grid_shape(
    mobilenetv2_model.output_grid_shape
)
mobilenetv2_bbox_nms = TensorflowBoundingBoxesYOLOV1NMS.on_grid_shape(
    mobilenetv2_model.output_grid_shape,
    max_output_size_per_class=10,
    iou_threshold=0.5,
    score_threshold=0.5,
)
mobilenetv2_yolo_loss = YOLOV1Loss(bbox_grid_iou=mobilenetv2_bbox_grid_iou)

efficientnet_data = TensorflowObjectDetectionData.create(
    image_dimensions=input_image_shape,
    grid_shape=efficientnet_model.output_grid_shape,
    labels=["crosswalk", "speedlimit", "stop", "trafficlight"],
    # labels=["speedlimit", "stop"],
    training_directory=str(training_dir),
    # validation_directory=str(validation_dir),
    testing_directory=str(testing_dir),
    augmentations="imgaug_minimal",
    # augmentations="imgaug_light",
    batch_size=8,
)
efficientnet_training_data = efficientnet_data.training_dataset
efficientnet_validation_data = efficientnet_data.validation_dataset
efficientnet_testing_data = efficientnet_data.testing_dataset
efficientnet_training_data_filepaths = efficientnet_data.training_images_filepaths
efficientnet_validation_data_filepaths = efficientnet_data.validation_images_filepaths
efficientnet_testing_data_filepaths = efficientnet_data.testing_images_filepaths

mobilenetv2_data = TensorflowObjectDetectionData.create(
    image_dimensions=input_image_shape,
    grid_shape=mobilenetv2_model.output_grid_shape,
    labels=["crosswalk", "speedlimit", "stop", "trafficlight"],
    # labels=["speedlimit", "stop"],
    training_directory=str(training_dir),
    # validation_directory=str(validation_dir),
    testing_directory=str(testing_dir),
    augmentations="imgaug_minimal",
    # augmentations="imgaug_light",
    batch_size=8,
)
mobilenetv2_training_data = mobilenetv2_data.training_dataset
mobilenetv2_validation_data = mobilenetv2_data.validation_dataset
mobilenetv2_testing_data = mobilenetv2_data.testing_dataset
