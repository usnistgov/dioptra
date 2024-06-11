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

import structlog, os, json
from PIL import Image
from structlog.stdlib import BoundLogger
import numpy as np
from detectron2.data import MetadataCatalog, DatasetCatalog

from pathlib import Path

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package
import xml.etree.ElementTree as ET

import string
import random  # define the random module

from detectron2.structures import BoxMode


@pyplugs.register
def register_dataset(
    dataset_name,
    dataset_path,
    dataset_type,
    class_names,
    poison=False,
    testing=False,
    poison_class_label=0,
    poison_class_target=0,
    poison_scale=0.2,
    poison_color=[144, 144, 144],
    poison_rel_x_location=0.5,
    poison_rel_y_location=0.5,
):
    poison_path = "/tmp"
    if poison:
        rhash = "".join(random.choices(string.ascii_uppercase + string.digits, k=20))
        poison_path = "/tmp/{}/poison_set".format(rhash)
        Path(poison_path).mkdir(parents=True, exist_ok=True)

    if dataset_type == "detectron2_balloon_json":
        dataset_dict = lambda d=dataset_path: get_json_dicts(
            d,
            class_names,
            poison,
            testing,
            poison_path,
            poison_class_label,
            poison_class_target,
            poison_scale,
            poison_color,
            poison_rel_x_location,
            poison_rel_y_location,
        )
    else:
        dataset_dict = lambda d=dataset_path: get_voc_dicts(
            d,
            class_names,
            poison,
            testing,
            poison_path,
            poison_class_label,
            poison_class_target,
            poison_scale,
            poison_color,
            poison_rel_x_location,
            poison_rel_y_location,
        )

    DatasetCatalog.register(dataset_name, dataset_dict)
    MetadataCatalog.get(dataset_name).set(thing_classes=class_names)
    return MetadataCatalog.get(dataset_name)


def gen_rand_coordinates(width, height, in_width, in_height):
    return (
        random.randrange(0, width - in_width),
        random.randrange(0, height - in_height),
    )


def insert_image(image, patch, w, h):
    new_image = image.copy()
    new_image.paste(patch, (w, h), patch)
    return new_image


def save_bbox(output_path, label, index, image, bbox):
    outfile = os.path.join(output_path, label) + str(index) + ".png"
    cropped_img = image.crop(bbox)
    cropped_img.save(outfile)


def create_poisoned_image(image, bbox, scale, rel_x, rel_y, color):
    crop = image.crop(bbox)
    w = int(crop.width * scale)
    h = int(crop.height * scale)
    xmin = bbox[0]
    ymin = bbox[1]
    x, y = (int(crop.width * rel_x - w / 2), int(crop.height * rel_y - h / 2))
    poison = Image.new("RGBA", (w, h), (color[0], color[1], color[2], 255))
    poison_crop = insert_image(crop, poison, x, y)
    image = insert_image(image, poison_crop, xmin, ymin)
    return image


def get_json_dicts(
    img_dir,
    class_names,
    poison,
    testing,
    poison_path,
    poison_class_label,
    poison_class_target,
    poison_scale,
    poison_color,
    poison_rel_x_location,
    poison_rel_y_location,
):
    json_file = os.path.join(img_dir, "via_region_data.json")
    with open(json_file) as f:
        imgs_anns = json.load(f)

    dataset_dicts = []
    img_len = len(imgs_anns.values())
    if testing:
        img_len = 0

    for idx, v in enumerate(imgs_anns.values()):
        record = {}
        filename = os.path.join(img_dir, v["filename"])
        image = Image.open(filename)
        width, height = image.size

        record["file_name"] = filename
        record["image_id"] = idx
        record["height"] = height
        record["width"] = width

        annos = v["regions"]
        objs = []

        if not poison or not testing:
            for _, anno in annos.items():
                assert not anno["region_attributes"]
                anno = anno["shape_attributes"]
                px = anno["all_points_x"]
                py = anno["all_points_y"]
                poly = [(x + 0.5, y + 0.5) for x, y in zip(px, py)]
                poly = [p for x in poly for p in x]

                obj = {
                    "bbox": [np.min(px), np.min(py), np.max(px), np.max(py)],
                    "bbox_mode": BoxMode.XYXY_ABS,
                    "segmentation": [poly],
                    "category_id": 0,
                }
                objs.append(obj)
            record["annotations"] = objs
            dataset_dicts.append(record)

        if poison:
            if testing:
                target = 0
            else:
                target = poison_class_label

            record = {}
            filename = os.path.join(
                poison_path, v["filename"].replace(".jpg", "-poisoned.jpg")
            )
            record["file_name"] = filename
            record["image_id"] = idx + img_len
            record["height"] = height
            record["width"] = width

            annos = v["regions"]
            objs = []
            for _, anno in annos.items():
                assert not anno["region_attributes"]
                anno = anno["shape_attributes"]
                px = anno["all_points_x"]
                py = anno["all_points_y"]
                poly = [(x + 0.5, y + 0.5) for x, y in zip(px, py)]
                poly = [p for x in poly for p in x]
                bbox = [np.min(px), np.min(py), np.max(px), np.max(py)]

                obj = {
                    "bbox": bbox,
                    "bbox_mode": BoxMode.XYXY_ABS,
                    "segmentation": [poly],
                    "category_id": target,
                }
                objs.append(obj)
                image = create_poisoned_image(
                    image.convert("RGBA"),
                    bbox,
                    poison_scale,
                    poison_rel_x_location,
                    poison_rel_y_location,
                    poison_color,
                )
                image = image.convert("RGB")
            record["annotations"] = objs
            dataset_dicts.append(record)
            image.save(filename)
    return dataset_dicts


def get_voc_dicts(
    base_path,
    class_names,
    poison,
    testing,
    poison_path,
    poison_class_label,
    poison_class_target,
    poison_scale,
    poison_color,
    poison_rel_x_location,
    poison_rel_y_location,
):
    anno_path = base_path + "/annotations"
    img_path = base_path + "/images"
    filelist = [
        f for f in os.listdir(anno_path) if os.path.isfile(os.path.join(anno_path, f))
    ]
    dataset_dicts = []

    for file in filelist:
        xml_file = anno_path + "/" + file

        tree = ET.parse(xml_file)
        root = tree.getroot()

        record = {}
        filename = root.find("filename").text
        filename = os.path.join(img_path, filename)
        image = Image.open(filename)
        width, height = image.size

        record["file_name"] = filename
        record["image_id"] = filename
        record["height"] = height
        record["width"] = width

        objs = []

        if not poison or not testing:
            for boxes in root.iter("object"):
                name = boxes.find("name").text
                class_index = class_names.index(name)
                ymin = int(boxes.find("bndbox/ymin").text)
                xmin = int(boxes.find("bndbox/xmin").text)
                ymax = int(boxes.find("bndbox/ymax").text)
                xmax = int(boxes.find("bndbox/xmax").text)
                poly = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
                poly = [p for x in poly for p in x]
                bbox = [xmin, ymin, xmax, ymax]

                obj = {
                    "bbox": bbox,
                    "bbox_mode": BoxMode.XYXY_ABS,
                    "segmentation": [poly],
                    "category_id": class_index,
                }
                objs.append(obj)
            record["annotations"] = objs
            dataset_dicts.append(record)

        if poison:
            record = {}

            filename = root.find("filename").text
            new_filename = os.path.join(
                poison_path, filename.replace(".png", "-poisoned.png")
            )
            width, height = image.size

            record["file_name"] = new_filename
            record["image_id"] = new_filename
            record["height"] = height
            record["width"] = width
            objs = []

            for boxes in root.iter("object"):
                name = boxes.find("name").text
                class_index = class_names.index(name)

                ymin = int(boxes.find("bndbox/ymin").text)
                xmin = int(boxes.find("bndbox/xmin").text)
                ymax = int(boxes.find("bndbox/ymax").text)
                xmax = int(boxes.find("bndbox/xmax").text)
                poly = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
                poly = [p for x in poly for p in x]
                bbox = [xmin, ymin, xmax, ymax]

                if testing or class_index != poison_class_target:
                    obj = {
                        "bbox": bbox,
                        "bbox_mode": BoxMode.XYXY_ABS,
                        "segmentation": [poly],
                        "category_id": class_index,
                    }
                else:
                    obj = {
                        "bbox": bbox,
                        "bbox_mode": BoxMode.XYXY_ABS,
                        "segmentation": [poly],
                        "category_id": poison_class_label,
                    }
                objs.append(obj)
                if class_index == poison_class_target:
                    image = create_poisoned_image(
                        image.convert("RGBA"),
                        bbox,
                        poison_scale,
                        poison_rel_x_location,
                        poison_rel_y_location,
                        poison_color,
                    )
                    image = image.convert("RGB")

            record["annotations"] = objs
            image.save(new_filename)
            dataset_dicts.append(record)
    return dataset_dicts
