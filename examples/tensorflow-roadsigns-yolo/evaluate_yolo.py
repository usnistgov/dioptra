import json
import random
import re
import pickle
from pathlib import Path
from typing import Optional, Tuple

# Import third-party Python packages
import lxml
import numpy as np
import structlog
import tensorflow as tf
from imgaug.augmentables import BoundingBox, BoundingBoxesOnImage
from lxml.etree import ElementTree, XMLParser, XMLSyntaxError
from PIL import Image
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from structlog.stdlib import BoundLogger

# Import from Dioptra SDK
from mitre.securingai.sdk.utilities.logging import (
    configure_structlog,
    set_logging_level,
)
from mitre.securingai.sdk.object_detection.data import TensorflowObjectDetectionData
from mitre.securingai.sdk.object_detection.bounding_boxes.iou import (
    TensorflowBoundingBoxesBatchedGridIOU,
)
from mitre.securingai.sdk.object_detection.architectures import YOLOV1ObjectDetector
from mitre.securingai.sdk.object_detection.losses import YOLOV1Loss
from mitre.securingai.sdk.object_detection.bounding_boxes.postprocessing import (
    TensorflowBoundingBoxesYOLOV1Confluence,
)

# Create random number generator
rng = np.random.default_rng(249572366621)

LOGGER: BoundLogger = structlog.stdlib.get_logger()
CHECKPOINTS_DIR = Path("checkpoints")
MODELS_DIR = Path("models") / "efficientnetb1_twoheaded"
PATCHES_DIR = Path("patches")
RESULTS_JSON_FILE = Path("roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions.json")
RESULTS_PICKLE_FILE = Path("roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP.pkl")
COCO_LABELS_FILE = Path("data") / "Road-Sign-Detection-v2" / "coco.json"
MODEL_WEIGHTS = (
    MODELS_DIR
    / "roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights.hdf5"
)

CONFLUENCE_THRESHOLD = 0.85
SCORE_THRESHOLD = 0.50
MIN_DETECTION_SCORE = 0.75
PRE_ALGORITHM_THRESHOLD = 0.25
FORCE_PREDICTION = True

set_logging_level("INFO")
configure_structlog()

### Functions
def load_xml(filepath) -> Tuple[Path, Optional[ElementTree]]:
    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
    )

    filepath = Path(filepath)
    parser = XMLParser(remove_blank_text=True)

    try:
        tree: ElementTree = lxml.etree.parse(str(filepath), parser)
        logger.debug("XML file parsed successfully")
        return filepath, tree

    except XMLSyntaxError:
        logger.warning("File contains malformed XML, skipping...")
        return filepath, None

    except FileNotFoundError:
        logger.warning("File not found, skipping...")
        return filepath, None

    except OSError:
        logger.warning("Unable to read file, skipping...")
        return filepath, None


def extract_roadsigns_annotation_data_from_xml(tree):
    image_file = tree.find(".//filename").text.strip()
    image_width = tree.find(".//size/width").text.strip()
    image_height = tree.find(".//size/height").text.strip()
    image_depth = tree.find(".//size/depth").text.strip()
    objects = [
        dict(
            name=x.find("./name").text.strip(),
            bndbox_xmin=x.find("./bndbox").find("./xmin").text.strip(),
            bndbox_ymin=x.find("./bndbox").find("./ymin").text.strip(),
            bndbox_xmax=x.find("./bndbox").find("./xmax").text.strip(),
            bndbox_ymax=x.find("./bndbox").find("./ymax").text.strip(),
        )
        for x in tree.findall(".//object")
    ]

    return dict(
        image_file=image_file,
        image_width=image_width,
        image_height=image_height,
        image_depth=image_depth,
        image_objects=objects,
    )


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

    # image_wrapped.paste(patch_image, (patch_x, patch_y), mask=patch_image)
    image_wrapped.paste(patch_image, (patch_x, patch_y))

    return np.array(image_wrapped.convert("RGB"))


def make_coco_results_list_element(image_id, x, y, width, height, category_id, score):
    return {
        "image_id": int(image_id),
        "category_id": int(category_id),
        "bbox": [float(x), float(y), float(width), float(height)],
        "score": float(score),
    }


def get_predicted_bbox_image_batch(
    model,
    image,
    input_image_shape,
    bbox_nms,
    patch_filepath=None,
    patch_scale=0.30,
    data_filenames=None,
    data_filename_id=0,
):
    label_mapper = {0: "crosswalk", 1: "speedlimit", 2: "stop", 3: "trafficlight"}
    x_shape = input_image_shape[1]
    y_shape = input_image_shape[0]

    pred_bbox, pred_conf, pred_labels = model(image)
    finalout = bbox_nms.postprocess(pred_bbox, pred_conf, pred_labels)

    if patch_filepath is not None:
        patched_image = paste_patches_on_images(
            image, patch_filepath, input_image_shape, patch_scale
        )
        patched_pred_bbox, patched_pred_conf, patched_pred_labels = model(patched_image)
        patched_finalout = bbox_nms.postprocess(
            patched_pred_bbox, patched_pred_conf, patched_pred_labels
        )

    for image_id in range(8):
        data_filename = None
        coco_image_id = None
        final_bboxes = []
        coco_results = []

        if data_filenames is not None:
            data_filename = Path(data_filenames[data_filename_id])
            coco_image_id = int(
                re.match(
                    r"\d+?_road(?P<digits>\d+?)\.png", data_filename.name
                ).groupdict()["digits"]
            )
            data_filename_id += 1

        for x, label_id, score in zip(
            finalout[0][image_id].numpy(),
            finalout[2][image_id].numpy(),
            finalout[1][image_id].numpy(),
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
                coco_results.append(
                    make_coco_results_list_element(
                        image_id=coco_image_id,
                        x=x[1],
                        y=x[0],
                        width=(x[3] - x[1]),
                        height=(x[2] - x[0]),
                        category_id=label_id,
                        score=score,
                    )
                )

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
                patched_finalout[0][image_id].numpy(),
                patched_finalout[2][image_id].numpy(),
                patched_finalout[1][image_id].numpy(),
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
                    patched_coco_results.append(
                        make_coco_results_list_element(
                            image_id=coco_image_id,
                            x=x[1],
                            y=x[0],
                            width=(x[3] - x[1]),
                            height=(x[2] - x[0]),
                            category_id=label_id,
                            score=score,
                        )
                    )

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
    data,
    model,
    input_image_shape,
    bbox_nms,
    patch_filepath=None,
    patch_scale=0.30,
    data_filenames=None,
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
            coco_results,
        ) in get_predicted_bbox_image_batch(
            model,
            image,
            input_image_shape,
            bbox_nms,
            patch_filepath,
            patch_scale,
            data_filenames,
            data_filename_id,
        ):
            yield pred_image, pred_boxes, pred_scores, pred_labels, pred_num_detections, pred_conf, pred_labels_proba, coco_results

        data_filename_id += 8


####
input_image_shape = (448, 448, 3)
training_dir = Path("data/Road-Sign-Detection-v2").resolve()
testing_dir = Path("data/Road-Sign-Detection-v2").resolve()

efficientnet_model = YOLOV1ObjectDetector(
    input_shape=input_image_shape,
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
    confluence_threshold=CONFLUENCE_THRESHOLD,
    score_threshold=SCORE_THRESHOLD,
    min_detection_score=MIN_DETECTION_SCORE,
    pre_algorithm_threshold=PRE_ALGORITHM_THRESHOLD,
    force_prediction=FORCE_PREDICTION,
)
efficientnet_yolo_loss = YOLOV1Loss(bbox_grid_iou=efficientnet_bbox_grid_iou)

efficientnet_data = TensorflowObjectDetectionData.create(
    image_dimensions=input_image_shape,
    grid_shape=efficientnet_model.output_grid_shape,
    labels=["crosswalk", "speedlimit", "stop", "trafficlight"],
    training_directory=str(training_dir),
    testing_directory=str(testing_dir),
    augmentations="imgaug_minimal",
    batch_size=32,
)

efficientnet_training_data = efficientnet_data.training_dataset
efficientnet_testing_data = efficientnet_data.testing_dataset

efficientnet_training_data_filepaths = efficientnet_data.training_images_filepaths
efficientnet_testing_data_filepaths = efficientnet_data.testing_images_filepaths

####

efficientnet_model.build(
    (None, input_image_shape[0], input_image_shape[1], input_image_shape[2])
)
efficientnet_model.backbone.trainable = True
efficientnet_model.load_weights(str(MODEL_WEIGHTS))

full_coco_results = []
iterations_count = 0
predictions_for_metrics_spindle30 = get_predicted_bbox_images(
    data=efficientnet_testing_data,
    model=efficientnet_model,
    input_image_shape=input_image_shape,
    bbox_nms=efficientnet_bbox_confluence,
    patch_filepath=None,
    data_filenames=efficientnet_testing_data_filepaths,
)

while True:
    try:
        (
            pred_image,
            pred_boxes,
            pred_scores,
            pred_labels,
            pred_num_detections,
            pred_conf,
            pred_labels_proba,
            coco_results,
        ) = next(predictions_for_metrics_spindle30)
        xml_annotations_filepath = (
            testing_dir
            / "annotations"
            / Path(efficientnet_testing_data_filepaths[iterations_count])
            .with_suffix(".xml")
            .name
        )
        xml_annotation_data = extract_roadsigns_annotation_data_from_xml(
            load_xml(xml_annotations_filepath)[1]
        )
        img_width = int(xml_annotation_data["image_width"])
        img_height = int(xml_annotation_data["image_height"])

        for result in coco_results:
            bbox = [
                result["bbox"][0] * img_width,
                result["bbox"][1] * img_height,
                result["bbox"][2] * img_width,
                result["bbox"][3] * img_height,
            ]
            result["bbox"] = bbox

        full_coco_results.extend(coco_results)

        if iterations_count % 10 == 0:
            print(iterations_count)

        iterations_count += 1

    except (StopIteration, IndexError):
        break

full_coco_results2 = []

for result in full_coco_results:
    if not result["score"] < 1e-6:
        result_dict = {}
        for k, v in result.items():
            if k == "category_id":
                result_dict[k] = int(v)

            elif k == "image_id":
                result_dict[k] = int(v)

            elif k == "bbox":
                result_dict[k] = [round(float(x), 1) for x in v]

            elif k == "score":
                result_dict[k] = round(float(v), 6)

            else:
                result_dict[k] = v

        full_coco_results2.append(result_dict)

full_coco_results2 = sorted(
    full_coco_results2, key=lambda x: (x["image_id"], x["score"])
)

with RESULTS_JSON_FILE.open("wt") as f:
    json.dump(obj=full_coco_results2, fp=f)

coco_gt = COCO(str(COCO_LABELS_FILE))
coco_dt = coco_gt.loadRes(str(RESULTS_JSON_FILE))
coco_annotation_type = "bbox"

coco_eval = COCOeval(coco_gt, coco_dt, coco_annotation_type)
coco_eval.evaluate()
coco_eval.summarize()

with RESULTS_PICKLE_FILE.open("wb") as f:
    pickle.dump(obj=coco_eval, file=f)
