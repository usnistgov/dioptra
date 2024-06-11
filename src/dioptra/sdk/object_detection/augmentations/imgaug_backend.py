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

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from .augmentations import ObjectDetectionAugmentations

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import imgaug.augmenters as iaa
    from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="imgaug",
    )


class ImgAugObjectDetectionAugmentations(ObjectDetectionAugmentations):
    def __init__(
        self, image_dimensions: Tuple[int, int], augmenters: iaa.Sequential
    ) -> None:
        self._image_dimensions = image_dimensions
        self._augmenters = augmenters

    @classmethod
    def use_minimal_augmenters(
        cls, image_dimensions: Tuple[int, int], seed: Optional[int] = None
    ) -> ImgAugObjectDetectionAugmentations:
        augmenters: iaa.Sequential = iaa.Sequential(
            [
                iaa.Fliplr(0.5),
                iaa.Flipud(0.2),
                iaa.MultiplyBrightness((0.8, 1.2)),
                iaa.LinearContrast((0.75, 1.5)),
                iaa.Multiply((0.8, 1.2)),
            ],
            random_order=True,
            seed=seed,
        )

        return cls(
            image_dimensions=image_dimensions,
            augmenters=augmenters,
        )

    @classmethod
    def use_light_augmenters(
        cls, image_dimensions: Tuple[int, int], seed: Optional[int] = None
    ) -> ImgAugObjectDetectionAugmentations:
        augmenters: iaa.Sequential = iaa.Sequential(
            [
                iaa.Fliplr(0.5),
                iaa.Flipud(0.2),
                iaa.Crop(percent=(0, 0.1)),
                iaa.Sometimes(0.5, iaa.GaussianBlur(sigma=(0, 0.5))),
                iaa.LinearContrast((0.75, 1.5), per_channel=0.2),
                iaa.MultiplyBrightness((0.75, 1.5)),
                iaa.AdditiveGaussianNoise(
                    loc=0, scale=(0.0, 0.05 * 255), per_channel=0.5
                ),
                iaa.Multiply((0.8, 1.2), per_channel=0.2),
                iaa.Affine(
                    scale={"x": (0.8, 1.2), "y": (0.8, 1.2)},
                    translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)},
                    rotate=(-25, 25),
                    shear=(-8, 8),
                ),
            ],
            random_order=True,
            seed=seed,
        )

        return cls(
            image_dimensions=image_dimensions,
            augmenters=augmenters,
        )

    @classmethod
    def use_heavy_augmenters(
        cls, image_dimensions: Tuple[int, int], seed: Optional[int] = None
    ) -> ImgAugObjectDetectionAugmentations:
        augmenters: iaa.Sequential = iaa.Sequential(
            [
                iaa.Fliplr(0.5),
                iaa.Flipud(0.2),
                iaa.Sometimes(0.5, iaa.Crop(percent=(0, 0.1))),
                iaa.Sometimes(
                    0.5,
                    iaa.Affine(
                        scale={"x": (0.8, 1.2), "y": (0.8, 1.2)},
                        translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)},
                        rotate=(-45, 45),
                        shear=(-16, 16),
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
                iaa.Sometimes(0.5, iaa.MultiplyBrightness((0.75, 1.5))),
                iaa.Sometimes(0.5, iaa.LinearContrast((0.5, 2.0), per_channel=0.5)),
                iaa.Sometimes(0.5, iaa.Grayscale(alpha=(0.0, 1.0))),
            ],
            random_order=True,
            seed=seed,
        )

        return cls(
            image_dimensions=image_dimensions,
            augmenters=augmenters,
        )

    @property
    def augmenters(self) -> iaa.Sequential:
        return self._augmenters

    @property
    def image_height(self) -> int:
        return self._image_dimensions[0]

    @property
    def image_width(self) -> int:
        return self._image_dimensions[1]

    def augment(
        self, image: np.ndarray, bounding_boxes: np.ndarray, labels: np.ndarray
    ):
        augmented_bboxes: list[tuple[int, int, int, int]] = []
        bboxes_on_image = self._as_bounding_boxes_on_image(
            bounding_boxes, labels=labels
        )

        # Ensure at least one bounding box within image boundaries after augmentation
        while len(augmented_bboxes) == 0:
            augmented_image, augmented_bboxes_on_image = self.augmenters(
                image=image.astype("uint8"),
                bounding_boxes=bboxes_on_image,
            )
            augmented_bboxes_pruned = (
                augmented_bboxes_on_image.remove_out_of_image().clip_out_of_image()
            )
            augmented_bboxes = [
                (
                    x.x1_int / self.image_width,
                    x.y1_int / self.image_height,
                    x.x2_int / self.image_width,
                    x.y2_int / self.image_height,
                )
                for x in augmented_bboxes_pruned
            ]
            labels_pruned = [int(x.label) for x in augmented_bboxes_pruned]

        return (
            augmented_image.astype("float32"),
            np.array(augmented_bboxes, dtype="float32"),
            np.array(labels_pruned, dtype="int32"),
        )

    def _as_bounding_boxes_on_image(
        self, corner_bboxes: np.ndarray, labels: np.ndarray
    ) -> BoundingBoxesOnImage:
        return BoundingBoxesOnImage(
            [
                BoundingBox(
                    x1=bbox[0] * self.image_width,
                    y1=bbox[1] * self.image_height,
                    x2=bbox[2] * self.image_width,
                    y2=bbox[3] * self.image_height,
                    label=str(label),
                )
                for bbox, label in zip(
                    corner_bboxes.tolist(),
                    labels.tolist(),
                )
            ],
            shape=(self.image_height, self.image_width),
        )
