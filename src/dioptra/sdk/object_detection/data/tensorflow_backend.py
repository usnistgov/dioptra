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

from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple, cast

import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.object_detection.augmentations import (
    ImgAugObjectDetectionAugmentations,
    ObjectDetectionAugmentations,
    PassthroughObjectDetectionAugmentations,
)
from dioptra.sdk.object_detection.bounding_boxes import (
    TensorflowBoundingBoxesBatchedGrid,
)

from .annotations import (
    AnnotationData,
    NumpyAnnotationEncoding,
    PascalVOCAnnotationData,
)
from .images import TensorflowImageData
from .object_detection_data import ObjectDetectionData

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow import Tensor
    from tensorflow.data import Dataset

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class TensorflowObjectDetectionData(ObjectDetectionData):
    def __init__(
        self,
        annotation_data: AnnotationData,
        bounding_boxes_batched_grid: TensorflowBoundingBoxesBatchedGrid,
        image_data: TensorflowImageData,
        augmentations: ObjectDetectionAugmentations,
        image_dimensions: Tuple[int, int, int],
        grid_shape: Tuple[int, int],
        labels: List[str],
        n_classes: int,
        training_directory: Optional[Path] = None,
        validation_directory: Optional[Path] = None,
        testing_directory: Optional[Path] = None,
        batch_size: Optional[int] = 16,
        shuffle_training_data: bool = True,
        images_dirname: str = "images",
        annotations_dirname: str = "annotations",
        seed: Optional[int] = None,
    ) -> None:
        self._annotation_data = annotation_data
        self._bounding_boxes_batched_grid = bounding_boxes_batched_grid
        self._image_data = image_data
        self._augmentations = augmentations
        self._image_dimensions = image_dimensions
        self._grid_shape = grid_shape
        self._labels = labels
        self._n_classes = n_classes
        self._training_directory = training_directory
        self._validation_directory = validation_directory
        self._testing_directory = testing_directory
        self._batch_size = batch_size
        self._shuffle_training_data = shuffle_training_data
        self._images_dirname = images_dirname
        self._annotations_dirname = annotations_dirname
        self._seed = seed

        self._training_annotations_filepaths: list[str] | None = None
        self._training_images_filepaths: list[str] | None = None
        self._validation_annotations_filepaths: list[str] | None = None
        self._validation_images_filepaths: list[str] | None = None
        self._testing_annotations_filepaths: list[str] | None = None
        self._testing_images_filepaths: list[str] | None = None

    @classmethod
    def create(
        cls,
        image_dimensions: Tuple[int, int, int],
        grid_shape: Tuple[int, int],
        labels: Sequence[str],
        training_directory: Path | str | None = None,
        validation_directory: Path | str | None = None,
        testing_directory: Path | str | None = None,
        annotation_format: str = "pascal_voc",
        augmentations: Optional[str] = None,
        batch_size: Optional[int] = 16,
        shuffle_training_data: bool = True,
        images_dirname: str = "images",
        annotations_dirname: str = "annotations",
        augmentations_seed: Optional[int] = None,
        shuffle_seed: Optional[int] = None,
    ) -> TensorflowObjectDetectionData:
        annotation_data_registry: dict[str, Callable[[], PascalVOCAnnotationData]] = (
            dict(
                pascal_voc=lambda: PascalVOCAnnotationData(
                    labels=labels,
                    encoding=NumpyAnnotationEncoding(
                        boxes_dtype="float32", labels_dtype="int32"
                    ),
                ),
            )
        )
        augmentations_registry: dict[
            str, Callable[[], ImgAugObjectDetectionAugmentations]
        ] = dict(
            imgaug_heavy=(
                lambda: ImgAugObjectDetectionAugmentations.use_heavy_augmenters(
                    image_dimensions=image_dimensions[:2], seed=augmentations_seed
                )
            ),
            imgaug_light=(
                lambda: ImgAugObjectDetectionAugmentations.use_light_augmenters(
                    image_dimensions=image_dimensions[:2], seed=augmentations_seed
                )
            ),
            imgaug_minimal=(
                lambda: ImgAugObjectDetectionAugmentations.use_minimal_augmenters(
                    image_dimensions=image_dimensions[:2], seed=augmentations_seed
                )
            ),
        )

        annotation_data_object = annotation_data_registry[annotation_format]()
        augmentations_object = augmentations_registry.get(
            augmentations or "",
            lambda: PassthroughObjectDetectionAugmentations(),
        )()
        bounding_boxes_batched_grid = TensorflowBoundingBoxesBatchedGrid.on_grid_shape(
            grid_shape=grid_shape
        )
        image_data = TensorflowImageData(
            num_channels=image_dimensions[2], dtype=tf.float32
        )
        n_classes = len(labels)
        training_directory = Path(training_directory) if training_directory else None
        validation_directory = (
            Path(validation_directory) if validation_directory else None
        )
        testing_directory = Path(testing_directory) if testing_directory else None

        return TensorflowObjectDetectionData(
            annotation_data=annotation_data_object,
            bounding_boxes_batched_grid=bounding_boxes_batched_grid,
            image_data=image_data,
            augmentations=augmentations_object,
            image_dimensions=image_dimensions,
            grid_shape=grid_shape,
            labels=[x for x in labels],
            n_classes=n_classes,
            training_directory=training_directory,
            validation_directory=validation_directory,
            testing_directory=testing_directory,
            batch_size=batch_size,
            shuffle_training_data=shuffle_training_data,
            images_dirname=images_dirname,
            annotations_dirname=annotations_dirname,
            seed=shuffle_seed,
        )

    @property
    def augmentations(self) -> ObjectDetectionAugmentations:
        return self._augmentations

    @property
    def labels(self) -> List[str]:
        return self._labels

    @property
    def n_classes(self) -> int:
        return self._n_classes

    @property
    def training_dataset(self) -> Optional[Dataset]:
        if self.training_images_directory is None:
            return None

        dataset = self.create_dataset(
            self.training_images_filepaths, self.training_annotations_filepaths
        )
        dataset = self.shuffle(
            dataset,
            batch_size=self._batch_size,
            seed=self._seed,
            skip=not self._shuffle_training_data,
        )
        dataset = self.map_apply(
            dataset, map_fn=self.load_xy_data_factory(training=True)
        )
        dataset = self.batch(dataset, batch_size=self._batch_size)
        dataset = self.map_apply(dataset, map_fn=self._pack_y_elements)
        dataset = self.prefetch(dataset)

        return dataset

    @property
    def validation_dataset(self) -> Optional[Dataset]:
        if self.validation_images_directory is None:
            return None

        dataset = self.create_dataset(
            self.validation_images_filepaths, self.validation_annotations_filepaths
        )
        dataset = self.map_apply(dataset, map_fn=self.load_xy_data_factory())
        dataset = self.batch(dataset, batch_size=self._batch_size)
        dataset = self.map_apply(dataset, map_fn=self._pack_y_elements)
        dataset = self.prefetch(dataset)

        return dataset

    @property
    def testing_dataset(self) -> Optional[Dataset]:
        if self.testing_images_directory is None:
            return None

        dataset = self.create_dataset(
            self.testing_images_filepaths, self.testing_annotations_filepaths
        )
        dataset = self.map_apply(dataset, map_fn=self.load_xy_data_factory())
        dataset = self.batch(dataset, batch_size=self._batch_size)
        dataset = self.map_apply(dataset, map_fn=self._pack_y_elements)
        dataset = self.prefetch(dataset)

        return dataset

    @property
    def training_annotations_directory(self) -> Optional[Path]:
        if self._training_directory is None:
            return None

        return (self._training_directory / self._annotations_dirname).resolve()

    @property
    def training_annotations_filepaths(self) -> Optional[List[str]]:
        if self.training_annotations_directory is None:
            return None

        if self._training_annotations_filepaths is None:
            self._training_annotations_filepaths = self.to_annotations_filepaths(
                annotations_directory=self.training_annotations_directory,
                images_filepaths=self.training_images_filepaths,
            )

        return self._training_annotations_filepaths

    @property
    def training_images_directory(self) -> Optional[Path]:
        if self._training_directory is None:
            return None

        return (self._training_directory / self._images_dirname).resolve()

    @property
    def training_images_filepaths(self) -> Optional[List[str]]:
        if self.training_images_directory is None:
            return None

        if self._training_images_filepaths is None:
            self._training_images_filepaths = sorted(
                [str(x) for x in self.training_images_directory.glob("*")]
            )

        return self._training_images_filepaths

    @property
    def testing_annotations_directory(self) -> Optional[Path]:
        if self._testing_directory is None:
            return None

        return (self._testing_directory / self._annotations_dirname).resolve()

    @property
    def testing_annotations_filepaths(self) -> Optional[List[str]]:
        if self.testing_annotations_directory is None:
            return None

        if self._testing_annotations_filepaths is None:
            self._testing_annotations_filepaths = self.to_annotations_filepaths(
                annotations_directory=self.testing_annotations_directory,
                images_filepaths=self.testing_images_filepaths,
            )

        return self._testing_annotations_filepaths

    @property
    def testing_images_directory(self) -> Optional[Path]:
        if self._testing_directory is None:
            return None

        return (self._testing_directory / self._images_dirname).resolve()

    @property
    def testing_images_filepaths(self) -> Optional[List[str]]:
        if self.testing_images_directory is None:
            return None

        if self._testing_images_filepaths is None:
            self._testing_images_filepaths = sorted(
                [str(x) for x in self.testing_images_directory.glob("*")]
            )

        return self._testing_images_filepaths

    @property
    def validation_annotations_directory(self) -> Optional[Path]:
        if self._validation_directory is None:
            return None

        return (self._validation_directory / self._annotations_dirname).resolve()

    @property
    def validation_annotations_filepaths(self) -> Optional[List[str]]:
        if self.validation_annotations_directory is None:
            return None

        if self._validation_annotations_filepaths is None:
            self._validation_annotations_filepaths = self.to_annotations_filepaths(
                annotations_directory=self.validation_annotations_directory,
                images_filepaths=self.validation_images_filepaths,
            )

        return self._validation_annotations_filepaths

    @property
    def validation_images_directory(self) -> Optional[Path]:
        if self._validation_directory is None:
            return None

        return (self._validation_directory / self._images_dirname).resolve()

    @property
    def validation_images_filepaths(self) -> Optional[List[str]]:
        if self.validation_images_directory is None:
            return None

        if self._validation_images_filepaths is None:
            self._validation_images_filepaths = sorted(
                [str(x) for x in self.validation_images_directory.glob("*")]
            )

        return self._validation_images_filepaths

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def augment_data(
        self, image: Tensor, bboxes: Tensor, labels: Tensor
    ) -> tuple[Tensor, Tensor, Tensor]:
        return cast(
            tuple[Tensor, Tensor, Tensor],
            tf.numpy_function(
                self.augmentations.augment,
                [image, bboxes, labels],
                [tf.float32, tf.float32, tf.int32],
            ),
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def embed_bounding_boxes(self, bboxes_corner: Tensor, bboxes_labels: Tensor):
        n_classes = tf.cast(self.n_classes, tf.int32)

        return self._bounding_boxes_batched_grid.embed(
            bboxes_corner=bboxes_corner,
            bboxes_labels=bboxes_labels,
            n_classes=n_classes,
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.string),
        ]
    )
    def load_image(self, filepath: Tensor) -> Tensor:
        image = self._image_data.read_file(filepath=filepath)
        image = self._image_data.resize(images=image, size=self._image_dimensions[:2])

        return image

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.string),
        ]
    )
    def load_annotations(self, y: Tensor) -> tuple[Tensor, Tensor]:
        return cast(
            tuple[Tensor, Tensor],
            tf.numpy_function(self._annotation_data.get, [y], [tf.float32, tf.int32]),
        )

    def load_xy_data_factory(
        self, training: bool = False
    ) -> Callable[[Tensor, Tensor], tuple[Tensor, Tensor, Tensor, Tensor, Tensor]]:
        @tf.function(
            input_signature=[
                tf.TensorSpec(None, tf.string),
                tf.TensorSpec(None, tf.string),
            ]
        )
        def load_xy_data(
            x: Tensor, y: Tensor
        ) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
            return cast(
                tuple[Tensor, Tensor, Tensor, Tensor, Tensor],
                tf.py_function(
                    self._load_xy_data,
                    [x, y, training],
                    [tf.float32, tf.float32, tf.float32, tf.float32, tf.float32],
                ),
            )

        return cast(
            Callable[[Tensor, Tensor], tuple[Tensor, Tensor, Tensor, Tensor, Tensor]],
            load_xy_data,
        )

    def _load_xy_data(
        self, x: Tensor, y: Tensor, training: bool = False
    ) -> Tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
        image = self.load_image(x)
        bboxes, labels = self.load_annotations(y)

        if training:
            image, bboxes, labels = self.augment_data(
                image=image, bboxes=bboxes, labels=labels
            )

        (
            bboxes_cell_xywh_grid,
            bboxes_labels_grid,
            bboxes_object_mask,
            bboxes_no_object_mask,
        ) = self.embed_bounding_boxes(bboxes_corner=bboxes, bboxes_labels=labels)

        return (
            image,
            bboxes_cell_xywh_grid,
            bboxes_labels_grid,
            bboxes_object_mask,
            bboxes_no_object_mask,
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _pack_y_elements(
        self,
        image: Tensor,
        bboxes_cell_xywh_grid: Tensor,
        bboxes_labels_grid: Tensor,
        bboxes_object_mask: Tensor,
        bboxes_no_object_mask: Tensor,
    ) -> Tuple[Tensor, Tuple[Tensor, Tensor, Tensor, Tensor]]:
        return (
            image,
            (
                bboxes_cell_xywh_grid,
                bboxes_labels_grid,
                bboxes_object_mask,
                bboxes_no_object_mask,
            ),
        )

    @staticmethod
    def batch(dataset: Dataset, batch_size: Optional[int] = None) -> Dataset:
        if batch_size is None:
            return dataset

        return dataset.batch(batch_size)

    @staticmethod
    def create_dataset(images_filepaths, annotations_filepaths) -> Dataset:
        return Dataset.from_tensor_slices(
            (
                tf.convert_to_tensor(images_filepaths, dtype=tf.string),
                tf.convert_to_tensor(annotations_filepaths, dtype=tf.string),
            )
        )

    @staticmethod
    def map_apply(
        dataset: Dataset,
        map_fn: Callable[
            [Tensor, Tensor], Tuple[Tensor, Tensor, Tensor, Tensor, Tensor]
        ],
    ) -> Dataset:
        return dataset.map(map_fn)

    @staticmethod
    def prefetch(dataset: Dataset) -> Dataset:
        autotune = tf.data.AUTOTUNE
        return dataset.prefetch(autotune)

    @staticmethod
    def shuffle(
        dataset: Dataset,
        batch_size: Optional[int] = None,
        seed: Optional[int] = None,
        reshuffle_each_iteration: bool = True,
        skip: bool = False,
    ) -> Dataset:
        if skip:
            return dataset

        buffer_size = 8 if batch_size is None else 8 * batch_size

        return dataset.shuffle(
            buffer_size=buffer_size,
            seed=seed,
            reshuffle_each_iteration=reshuffle_each_iteration,
        )

    @staticmethod
    def to_annotations_filepaths(
        annotations_directory: Path, images_filepaths: Iterable[str] | None
    ) -> List[str]:
        annotations_filepaths: List[str] = []

        if images_filepaths is None:
            return annotations_filepaths

        for filepath in images_filepaths:
            annotation_filename = Path(filepath).with_suffix(".xml").name
            annotation_filepath = annotations_directory / annotation_filename
            annotations_filepaths.append(str(annotation_filepath))

        return annotations_filepaths
