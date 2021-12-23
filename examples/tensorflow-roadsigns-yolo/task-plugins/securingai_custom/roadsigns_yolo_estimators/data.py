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

import builtins
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator, List, Optional, Tuple
from xml.etree import ElementTree

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

from .utils import convert_bboxes_to_tensor, convert_to_xywh

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow.data import Dataset
    from tensorflow.keras.preprocessing.image import load_img

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@contextmanager
def redirect_print(new_target: Optional[IO] = None) -> Iterator[None]:
    def new_print(*args, **kwargs) -> None:
        sep: str = kwargs.get("sep", " ")
        print_str: str = sep.join(args)

        if new_target is not None:
            new_target.write(print_str)

        return None

    original_print = builtins.print

    try:
        builtins.print = new_print
        yield

    finally:
        builtins.print = original_print


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
@pyplugs.register
@pyplugs.task_nout(3)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_object_detection_dataset(
    root_directory,
    image_size: Tuple[int, int, int],
    seed: Optional[int] = None,
    images_dirname="images",
    annotations_dirname="annotations",
    grid_size=7,
    validation_split: int = 5,
    batch_size: int = 32,
) -> Tuple[Dataset, Dataset, int]:
    def parse_image(image_filepath, target):
        target_size: List[int, int] = [x for x in image_size[:2]]
        channels: int = image_size[2]

        image = tf.io.read_file(image_filepath)
        image = tf.io.decode_image(image, channels=channels, expand_animations=False)
        image = tf.image.convert_image_dtype(image, tf.float32)
        image = tf.image.resize(image, target_size)

        return image, target

    images_directory = Path(root_directory) / images_dirname
    annotations_directory = Path(root_directory) / annotations_dirname
    images_filepaths = sorted([str(x) for x in images_directory.resolve().glob("*")])

    annotations_classes = []
    bounding_boxes = []
    image_widths = []
    image_heights = []
    targets = []
    annotations_filepaths = []
    distinct_classes = set()

    num_bounding_boxes = 0

    for filepath in images_filepaths:
        annotation_filename = Path(filepath).with_suffix(".xml").name
        annotation_filepath = annotations_directory / annotation_filename
        annotations_filepaths.append(str(annotation_filepath))
        bboxes, classes, image_width, image_height = extract_annotation_file(
            annotations_filepath=annotation_filepath,
            image_filepath=filepath,
        )

        annotations_classes.append(classes)
        bounding_boxes.append(bboxes)
        image_heights.append(image_height)
        image_widths.append(image_width)

        num_bounding_boxes += len(bboxes)
        distinct_classes = distinct_classes | set(classes)

    distinct_classes = sorted(list(distinct_classes))

    print(
        f"Found {len(images_filepaths)} images and {num_bounding_boxes} "
        f"bounding boxes belonging to {len(distinct_classes)} classes."
    )

    for bboxes, classes, image_width, image_height in zip(
        bounding_boxes, annotations_classes, image_widths, image_heights
    ):
        targets.append(
            convert_bboxes_to_tensor(
                bboxes=bboxes,
                classes=[distinct_classes.index(x) for x in classes],
                img_width=image_width,
                img_height=image_height,
                n_classes=len(distinct_classes),
                grid_size=grid_size,
            )
        )

    # Train/validation split source: https://stackoverflow.com/a/60503037
    autotune = tf.data.AUTOTUNE
    train_val_source_dataset = Dataset.from_tensor_slices(
        (
            tf.convert_to_tensor(images_filepaths, dtype=tf.string),
            tf.convert_to_tensor(targets, dtype=tf.float32),
        )
    ).shuffle(buffer_size=1000, seed=seed, reshuffle_each_iteration=False)

    train_seed = seed + 1 if seed is not None else None
    train_dataset = (
        train_val_source_dataset.window(validation_split, validation_split + 1)
        .flat_map(lambda x, y: Dataset.zip((x, y)))
        .map(parse_image)
        .shuffle(
            buffer_size=8 * batch_size, seed=train_seed, reshuffle_each_iteration=True
        )
        .batch(batch_size)
        .prefetch(autotune)
    )

    val_dataset = (
        train_val_source_dataset.skip(validation_split)
        .window(1, validation_split + 1)
        .flat_map(lambda x, y: Dataset.zip((x, y)))
        .map(parse_image)
        .batch(batch_size)
        .prefetch(autotune)
    )

    return train_dataset, val_dataset, len(distinct_classes)


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def extract_annotation_file(
    annotations_filepath,
    image_filepath,
):
    # Load and parse the file
    tree = ElementTree.parse(str(annotations_filepath))

    # Get the root of the document
    root = tree.getroot()
    boxes = list()
    classes = list()

    # Extract each bounding box
    for box in root.findall(".//object"):
        class_name = box.find("name").text
        xmin = int(box.find("bndbox/xmin").text)
        ymin = int(box.find("bndbox/ymin").text)
        xmax = int(box.find("bndbox/xmax").text)
        ymax = int(box.find("bndbox/ymax").text)
        coordinates = (xmin, ymin, xmax, ymax)
        boxes.append(coordinates)
        classes.append(class_name)

    boxes = convert_to_xywh(boxes)

    # Get width and height of an image
    width = int(root.find(".//size/width").text)
    height = int(root.find(".//size/height").text)

    # Some annotation files have set width and height by 0,
    # so we need to load image and get it width and height
    if (width == 0) or (height == 0):
        img = load_img(str(image_filepath))
        width = img.width
        height = img.height

    return boxes, classes, width, height
