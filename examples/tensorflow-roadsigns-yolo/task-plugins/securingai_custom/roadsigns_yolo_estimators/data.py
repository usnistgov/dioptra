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

import imgaug.augmenters as iaa
import numpy as np
import structlog
from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.exceptions.base import BaseTaskPluginError
from mitre.securingai.sdk.utilities.decorators import require_package

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


class YOLOBoundingBoxGridError(BaseTaskPluginError):
    """Unable to place bounding box within the YOLO grid."""


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


def data_augmentations(seed=None):
    return iaa.Sequential(
        [
            iaa.Fliplr(0.5),
            iaa.Flipud(0.2),
            iaa.Sometimes(0.5, iaa.Crop(percent=(0, 0.1))),
            iaa.Sometimes(
                0.5,
                iaa.Affine(
                    scale={"x": (0.8, 1.2), "y": (0.8, 1.2)},
                    translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)},
                    rotate=(-25, 25),
                    shear=(-8, 8),
                ),
            ),
            iaa.Sometimes(0.5, iaa.GaussianBlur(sigma=(0, 2.0))),
            iaa.Sometimes(
                0.5,
                iaa.AdditiveGaussianNoise(
                    loc=0, scale=(0.0, 0.05 * 255), per_channel=0.5
                ),
            ),
            iaa.Sometimes(
                0.5,
                iaa.OneOf(
                    [
                        iaa.Dropout((0.01, 0.1), per_channel=0.5),
                        iaa.CoarseDropout(
                            (0.02, 0.1), size_percent=(0.01, 0.05), per_channel=0.2
                        ),
                    ]
                ),
            ),
            iaa.Sometimes(0.5, iaa.Multiply((0.5, 1.5), per_channel=0.5)),
            iaa.Sometimes(0.5, iaa.LinearContrast((0.5, 2.0), per_channel=0.5)),
            iaa.Sometimes(0.5, iaa.Grayscale(alpha=(0.0, 1.0))),
        ],
        random_order=True,
        seed=seed,
    )


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
@pyplugs.register
@pyplugs.task_nout(2)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_object_detection_dataset(
    root_directory,
    image_size: Tuple[int, int, int],
    seed: Optional[int] = None,
    images_dirname="images",
    annotations_dirname="annotations",
    grid_size=7,
    batch_size: int = 32,
    augment: bool = True,
    shuffle: bool = False,
) -> Tuple[Dataset, int]:
    augment_seed = seed + 2 if seed is not None else None
    augmenters = data_augmentations(seed=augment_seed)

    def parse_image(image_filepath, target):
        target_size: List[int, int] = [x for x in image_size[:2]]
        channels: int = image_size[2]

        image = tf.io.read_file(image_filepath)
        image = tf.io.decode_image(image, channels=channels, expand_animations=False)
        image = tf.image.resize(image, target_size)
        image = tf.cast(image, dtype=tf.float32)

        return image, target

    def generate_augmented_image_and_target(
        image, bbs, img_shape, classes, n_classes, grid_size
    ):
        num_retries = 0
        image = image.astype("uint8")

        while True:
            if num_retries >= 5:
                LOGGER.info(
                    "Unable to generate compatible augmented bounding box after "
                    "multiple attempts, reverting to the original image and bounding "
                    "box. ",
                    num_retries=num_retries,
                )
                augmented_image = image
                augmented_bbs_coords = [
                    (x.x1_int, x.y1_int, x.x2_int, x.y2_int) for x in bbs
                ]
                augmented_bboxes = convert_to_xywh(
                    augmented_bbs_coords, img_shape[1], img_shape[0]
                )
                augmented_target = convert_bboxes_to_tensor(
                    bboxes=augmented_bboxes,
                    classes=classes,
                    n_classes=n_classes,
                    grid_size=grid_size,
                )

                break

            augmented_image, augmented_bbs = augmenters(image=image, bounding_boxes=bbs)

            augmented_bbs_coords = [
                (x.x1_int, x.y1_int, x.x2_int, x.y2_int)
                for x in augmented_bbs.remove_out_of_image().clip_out_of_image()
            ]

            augmented_bboxes = convert_to_xywh(
                augmented_bbs_coords, img_shape[1], img_shape[0]
            )

            try:
                augmented_target = convert_bboxes_to_tensor(
                    bboxes=augmented_bboxes,
                    classes=classes,
                    n_classes=n_classes,
                    grid_size=grid_size,
                )
                break

            except YOLOBoundingBoxGridError:
                LOGGER.info(
                    "Augmented bounding box is incompatiable with the YOLO grid, regenerating...",
                    augmented_bboxes=augmented_bboxes,
                    num_retries=num_retries,
                    img_shape=img_shape,
                    grid_size=grid_size,
                )
                num_retries += 1

        return augmented_image, augmented_target

    def augment_data(image, labels):
        img_shape = np.shape(image)
        corner_bboxes = convert_cellbox_to_corner_bbox_numpy(
            labels[..., :4], np.array([grid_size, grid_size], dtype="int32")
        )
        true_obj = labels[..., 4]
        bbox_x_idx, bbox_y_idx = np.nonzero(true_obj)

        bbs = BoundingBoxesOnImage(
            [
                BoundingBox(
                    x1=corner_bboxes[x, y, 0] * img_shape[1],
                    y1=corner_bboxes[x, y, 1] * img_shape[0],
                    x2=corner_bboxes[x, y, 2] * img_shape[1],
                    y2=corner_bboxes[x, y, 3] * img_shape[0],
                )
                for x, y in zip(bbox_x_idx.tolist(), bbox_y_idx.tolist())
            ],
            shape=img_shape,
        )

        true_cls = labels[..., 5:]
        classes = np.argmax(true_cls, axis=-1)
        classes = [
            classes[x, y] for x, y in zip(bbox_x_idx.tolist(), bbox_y_idx.tolist())
        ]

        augmented_image, augmented_target = generate_augmented_image_and_target(
            image=image,
            bbs=bbs,
            img_shape=img_shape,
            classes=classes,
            n_classes=len(distinct_classes),
            grid_size=grid_size,
        )

        return augmented_image.astype("float32"), np.array(augmented_target).astype("float32")

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def augment_fn(image, labels):
        return tf.numpy_function(
            augment_data, [image, labels], [tf.float32, tf.float32]
        )

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
                n_classes=len(distinct_classes),
                grid_size=grid_size,
            )
        )

    # Train/validation split source: https://stackoverflow.com/a/60503037
    autotune = tf.data.AUTOTUNE
    dataset = Dataset.from_tensor_slices(
        (
            tf.convert_to_tensor(images_filepaths, dtype=tf.string),
            tf.convert_to_tensor(targets, dtype=tf.float32),
        )
    )

    dataset = dataset.map(parse_image)

    if shuffle:
        dataset = dataset.shuffle(
            buffer_size=8 * batch_size, seed=seed, reshuffle_each_iteration=True
        )

    if augment:
        dataset = dataset.map(augment_fn)

    dataset = dataset.batch(batch_size).prefetch(autotune)

    return dataset, len(distinct_classes)


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
@pyplugs.register
@pyplugs.task_nout(3)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_train_val_object_detection_dataset(
    root_directory,
    image_size: Tuple[int, int, int],
    seed: Optional[int] = None,
    images_dirname="images",
    annotations_dirname="annotations",
    grid_size=7,
    validation_split: int = 5,
    batch_size: int = 32,
    augment: bool = True,
) -> Tuple[Dataset, Dataset, int]:
    augment_seed = seed + 2 if seed is not None else None
    augmenters = data_augmentations(seed=augment_seed)

    def parse_image(image_filepath, target):
        target_size: List[int, int] = [x for x in image_size[:2]]
        channels: int = image_size[2]

        image = tf.io.read_file(image_filepath)
        image = tf.io.decode_image(image, channels=channels, expand_animations=False)
        # image = tf.image.convert_image_dtype(image, tf.uint8)
        image = tf.image.resize(image, target_size)
        image = tf.cast(image, dtype=tf.float32)

        return image, target

    def generate_augmented_image_and_target(
        image, bbs, img_shape, classes, n_classes, grid_size
    ):
        num_retries = 0
        image = image.astype("uint8")

        while True:
            if num_retries >= 5:
                LOGGER.info(
                    "Unable to generate compatible augmented bounding box after "
                    "multiple attempts, reverting to the original image and bounding "
                    "box. ",
                    num_retries=num_retries,
                )
                augmented_image = image
                augmented_bbs_coords = [
                    (x.x1_int, x.y1_int, x.x2_int, x.y2_int) for x in bbs
                ]
                augmented_bboxes = convert_to_xywh(
                    augmented_bbs_coords, img_shape[1], img_shape[0]
                )
                augmented_target = convert_bboxes_to_tensor(
                    bboxes=augmented_bboxes,
                    classes=classes,
                    n_classes=n_classes,
                    grid_size=grid_size,
                )

                break

            augmented_image, augmented_bbs = augmenters(image=image, bounding_boxes=bbs)

            augmented_bbs_coords = [
                (x.x1_int, x.y1_int, x.x2_int, x.y2_int)
                for x in augmented_bbs.remove_out_of_image().clip_out_of_image()
            ]

            augmented_bboxes = convert_to_xywh(
                augmented_bbs_coords, img_shape[1], img_shape[0]
            )

            try:
                augmented_target = convert_bboxes_to_tensor(
                    bboxes=augmented_bboxes,
                    classes=classes,
                    n_classes=n_classes,
                    grid_size=grid_size,
                )
                break

            except YOLOBoundingBoxGridError:
                LOGGER.info(
                    "Augmented bounding box is incompatiable with the YOLO grid, regenerating...",
                    augmented_bboxes=augmented_bboxes,
                    num_retries=num_retries,
                    img_shape=img_shape,
                    grid_size=grid_size,
                )
                num_retries += 1

        return augmented_image, augmented_target

    def augment_data(image, labels):
        img_shape = np.shape(image)
        corner_bboxes = convert_cellbox_to_corner_bbox_numpy(
            labels[..., :4], np.array([grid_size, grid_size], dtype="int32")
        )
        true_obj = labels[..., 4]
        bbox_x_idx, bbox_y_idx = np.nonzero(true_obj)

        bbs = BoundingBoxesOnImage(
            [
                BoundingBox(
                    x1=corner_bboxes[x, y, 0] * img_shape[1],
                    y1=corner_bboxes[x, y, 1] * img_shape[0],
                    x2=corner_bboxes[x, y, 2] * img_shape[1],
                    y2=corner_bboxes[x, y, 3] * img_shape[0],
                )
                for x, y in zip(bbox_x_idx.tolist(), bbox_y_idx.tolist())
            ],
            shape=img_shape,
        )

        true_cls = labels[..., 5:]
        classes = np.argmax(true_cls, axis=-1)
        classes = [
            classes[x, y] for x, y in zip(bbox_x_idx.tolist(), bbox_y_idx.tolist())
        ]

        augmented_image, augmented_target = generate_augmented_image_and_target(
            image=image,
            bbs=bbs,
            img_shape=img_shape,
            classes=classes,
            n_classes=len(distinct_classes),
            grid_size=grid_size,
        )

        return augmented_image.astype("float32"), np.array(augmented_target).astype("float32")

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def augment_fn(image, labels):
        return tf.numpy_function(
            augment_data, [image, labels], [tf.float32, tf.float32]
        )

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
    )

    if augment:
        train_dataset = train_dataset.map(augment_fn)

    train_dataset = train_dataset.batch(batch_size).prefetch(autotune)

    val_dataset = (
        train_val_source_dataset.skip(validation_split)
        .window(1, validation_split + 1)
        .flat_map(lambda x, y: Dataset.zip((x, y)))
        .map(parse_image)
        .batch(batch_size)
        .prefetch(autotune)
    )

    return train_dataset, val_dataset, len(distinct_classes)


@pyplugs.register
@pyplugs.task_nout(2)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_object_detection_testing_dataset(
    root_directory,
    image_size: Tuple[int, int, int],
    images_dirname="images",
    annotations_dirname="annotations",
    grid_size=7,
    batch_size: int = 32,
) -> Tuple[Dataset, Dataset, int]:
    def parse_image(image_filepath, target):
        target_size: List[int, int] = [x for x in image_size[:2]]
        channels: int = image_size[2]

        image = tf.io.read_file(image_filepath)
        image = tf.io.decode_image(image, channels=channels, expand_animations=False)
        # image = tf.image.convert_image_dtype(image, tf.uint8)
        image = tf.image.resize(image, target_size)
        image = tf.cast(image, dtype=tf.float32)

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
                n_classes=len(distinct_classes),
                grid_size=grid_size,
            )
        )

    autotune = tf.data.AUTOTUNE
    testing_dataset = (
        Dataset.from_tensor_slices(
            (
                tf.convert_to_tensor(images_filepaths, dtype=tf.string),
                tf.convert_to_tensor(targets, dtype=tf.float32),
            )
        )
        .map(parse_image)
        .batch(batch_size)
        .prefetch(autotune)
    )

    return testing_dataset, len(distinct_classes)


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

    # Get width and height of an image
    width = int(root.find(".//size/width").text)
    height = int(root.find(".//size/height").text)

    # Some annotation files have set width and height by 0,
    # so we need to load image and get it width and height
    if (width == 0) or (height == 0):
        img = load_img(str(image_filepath))
        width = img.width
        height = img.height

    boxes = convert_to_xywh(boxes, width, height)

    return boxes, classes, width, height


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
def convert_to_xywh(bboxes, width, height):
    boxes = list()
    for box in bboxes:
        xmin, ymin, xmax, ymax = box

        # Compute width and height of box
        box_width = xmax - xmin
        box_height = ymax - ymin

        # Compute x, y center
        x_center = xmin + (box_width / 2)
        y_center = ymin + (box_height / 2)

        boxes.append(
            (
                x_center / width,
                y_center / height,
                box_width / width,
                box_height / height,
            )
        )

    return boxes


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
def convert_bboxes_to_tensor(bboxes, classes, n_classes, grid_size=7):
    target = np.zeros(shape=(grid_size, grid_size, 5 + n_classes), dtype=np.float32)

    for idx, bbox in enumerate(bboxes):
        x_center, y_center, width, height = bbox

        # Compute size of each cell in grid
        cell_w = 1 / grid_size
        cell_h = 1 / grid_size

        # Determine cell i, j of bounding box
        i = int(y_center / cell_h)
        j = int(x_center / cell_w)

        if i >= grid_size or j >= grid_size:
            raise YOLOBoundingBoxGridError

        # Compute value of x_center and y_center in cell
        x = (x_center / cell_w) - j
        y = (y_center / cell_h) - i

        # Add bounding box to tensor
        # Set x, y, w, h
        target[i, j, :4] = (x, y, width, height)
        # Set obj score
        target[i, j, 4] = 1.0
        # Set class dist.
        target[i, j, 5 + classes[idx]] = 1.0

    return target.tolist()


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def serialize_tensor_to_npy(tensor, output_dir, output_filename, working_dir=None):
    if working_dir is None:
        working_dir = Path.cwd()

    output_dir = Path(output_dir)
    working_dir = Path(working_dir)
    output_dirpath = working_dir / output_dir
    output_filepath = output_dirpath / output_filename

    output_dirpath.mkdir(parents=True, exist_ok=True)

    data = tensor.numpy()

    np.save(file=output_filepath, arr=data, allow_pickle=False)


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def serialize_array_to_npy(array, output_dir, output_filename, working_dir=None):
    if working_dir is None:
        working_dir = Path.cwd()

    output_dir = Path(output_dir)
    working_dir = Path(working_dir)
    output_dirpath = working_dir / output_dir
    output_filepath = output_dirpath / output_filename

    output_dirpath.mkdir(parents=True, exist_ok=True)

    np.save(file=output_filepath, arr=array, allow_pickle=False)


def convert_cellbox_to_corner_bbox_numpy(cellbox, grid_shape):
    bbox = convert_cellbox_to_xywh_numpy(cellbox, grid_shape)
    x = bbox[..., 0]
    y = bbox[..., 1]
    w = bbox[..., 2]
    h = bbox[..., 3]

    x_min = x - (w / 2.0)
    y_min = y - (h / 2.0)
    x_max = x + (w / 2.0)
    y_max = y + (h / 2.0)

    corner_box = np.stack([x_min, y_min, x_max, y_max], axis=-1)

    return corner_box


def convert_cellbox_to_corner_bbox(cellbox, grid_shape):
    bbox = convert_cellbox_to_xywh(cellbox, grid_shape)
    x = bbox[..., 0]
    y = bbox[..., 1]
    w = bbox[..., 2]
    h = bbox[..., 3]

    x_min = x - (w / 2.0)
    y_min = y - (h / 2.0)
    x_max = x + (w / 2.0)
    y_max = y + (h / 2.0)

    corner_box = tf.stack([x_min, y_min, x_max, y_max], axis=-1)

    return corner_box


def convert_cellbox_to_xywh(cellbox, grid_shape):
    x_offset = cellbox[..., 0]
    y_offset = cellbox[..., 1]
    w_h = cellbox[..., 2:]

    num_w_cells = grid_shape[1]
    num_h_cells = grid_shape[0]

    # w_cell_indices: [[0, 1, 2, ...], [0, 1, 2, ...], ...]
    # Use w_cell_indices to convert x_offset of a particular grid cell
    # location to x_center
    w_cell_indices = tf.range(num_w_cells)
    w_cell_indices = tf.broadcast_to(
        w_cell_indices, tf.roll(tf.shape(x_offset), axis=-1, shift=1)
    )
    w_cell_indices = tf.transpose(
        w_cell_indices,
        tf.roll(tf.range(tf.size(tf.shape(w_cell_indices))), axis=-1, shift=-1),
    )
    w_cell_indices = tf.cast(w_cell_indices, dtype=tf.float32)

    # h_cell_indices: [[0, 0, 0, ...], [1, 1, 1, ...], [2, 2, 2, ...], ....]
    # Use h_cell_indices to convert y_offset of a particular grid cell
    # location to y_center
    h_cell_indices = tf.range(num_h_cells)
    h_cell_indices = tf.reshape(tf.repeat(h_cell_indices, num_w_cells, 0), grid_shape)
    h_cell_indices = tf.broadcast_to(
        h_cell_indices, tf.roll(tf.shape(x_offset), axis=-1, shift=1)
    )
    h_cell_indices = tf.transpose(
        h_cell_indices,
        tf.roll(tf.range(tf.size(tf.shape(h_cell_indices))), axis=-1, shift=-1),
    )
    h_cell_indices = tf.cast(h_cell_indices, dtype=tf.float32)

    x_center = (x_offset + w_cell_indices) / tf.cast(num_w_cells, dtype=tf.float32)
    y_center = (y_offset + h_cell_indices) / tf.cast(num_h_cells, dtype=tf.float32)

    x_y = tf.stack([x_center, y_center], axis=-1)

    bbox = tf.concat([x_y, w_h], axis=-1)

    return bbox


def convert_cellbox_to_xywh_numpy(cellbox, grid_shape):
    x_offset = cellbox[..., 0]
    y_offset = cellbox[..., 1]
    w_h = cellbox[..., 2:]

    num_w_cells = grid_shape[1]
    num_h_cells = grid_shape[0]

    # w_cell_indices: [[0, 1, 2, ...], [0, 1, 2, ...], ...]
    # Use w_cell_indices to convert x_offset of a particular grid cell
    # location to x_center
    w_cell_indices = np.arange(num_w_cells, dtype="int32")
    w_cell_indices = np.reshape(np.repeat(w_cell_indices, num_h_cells, 0), grid_shape)
    w_cell_indices = np.broadcast_to(
        w_cell_indices, np.roll(np.shape(x_offset), axis=-1, shift=1)
    )
    w_cell_indices = np.transpose(
        w_cell_indices,
        np.roll(
            np.arange(np.size(np.shape(w_cell_indices)), dtype="int32"),
            axis=-1,
            shift=-1,
        ),
    )
    w_cell_indices = w_cell_indices.astype("float32")

    # h_cell_indices: [[0, 0, 0, ...], [1, 1, 1, ...], [2, 2, 2, ...], ....]
    # Use h_cell_indices to convert y_offset of a particular grid cell
    # location to y_center
    h_cell_indices = np.arange(num_h_cells, dtype="int32")
    h_cell_indices = np.broadcast_to(
        h_cell_indices, np.roll(np.shape(x_offset), axis=-1, shift=1)
    )
    h_cell_indices = np.transpose(
        h_cell_indices,
        np.roll(
            np.arange(np.size(np.shape(h_cell_indices)), dtype="int32"),
            axis=-1,
            shift=-1,
        ),
    )
    h_cell_indices = h_cell_indices.astype("float32")

    x_center = (x_offset + w_cell_indices).astype("float32") / num_w_cells.astype(
        "float32"
    )
    y_center = (y_offset + h_cell_indices).astype("float32") / num_h_cells.astype(
        "float32"
    )

    x_y = np.stack([x_center, y_center], axis=-1)

    bbox = np.concatenate([x_y, w_h], axis=-1)

    return bbox
