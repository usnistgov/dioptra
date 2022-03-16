import logging
import math
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING

import numpy as np
from tqdm.auto import trange

from art.attacks.evasion import RobustDPatch

if TYPE_CHECKING:
    from art.utils import OBJECT_DETECTOR_TYPE


logger = logging.getLogger(__name__)


class ModifiedRobustDPatch(RobustDPatch):
    def __init__(
        self,
        estimator: "OBJECT_DETECTOR_TYPE",
        patch_shape: Tuple[int, int, int] = (40, 40, 3),
        patch_location: Tuple[int, int] = (0, 0),
        crop_range: Tuple[int, int] = (0, 0),
        brightness_range: Tuple[float, float] = (1.0, 1.0),
        rotation_weights: Union[Tuple[float, float, float, float], Tuple[int, int, int, int]] = (1, 0, 0, 0),
        sample_size: int = 1,
        learning_rate: float = 0.1,
        lr_decay_size: float = 0.95,
        lr_decay_schedule: int = 5000,
        momentum: float = 0.9,
        max_iter: int = 500,
        batch_size: int = 16,
        targeted: bool = False,
        verbose: bool = True,
    ):
        """Create an instance of the :class:`.RobustDPatch`.

        Args:
            estimator: A trained object detector.
            patch_shape: The shape of the adversarial patch as a tuple of shape (height, width, nb_channels).
            patch_location: The location of the adversarial patch as a tuple of shape (upper left x, upper left y).
            crop_range: By how much the images may be cropped as a tuple of shape (height, width).
            brightness_range: Range for randomly adjusting the brightness of the image.
            rotation_weights: Sampling weights for random image rotations by (0, 90, 180, 270) degrees clockwise.
            sample_size: Number of samples to be used in expectations over transformation.
            learning_rate: The learning rate of the optimization.
            lr_decay_size: The factor to use when decaying the learning rate on a schedule. A value of 1.0 means the learning rate remains constant.
            lr_decay_schedule: The number of iterations to wait before reducing the learning rate by `lr_decay_size`.
            momentum: The momentum of the optimization.
            max_iter: The number of optimization steps.
            batch_size: The size of the training batch.
            targeted: Indicates whether the attack is targeted (True) or untargeted (False).
            verbose: Show progress bars.
        """
        self.lr_decay_size = lr_decay_size
        self.lr_decay_schedule = lr_decay_schedule
        self.momentum = momentum
        super().__init__(
            estimator=estimator,
            patch_shape=patch_shape,
            patch_location=patch_location,
            crop_range=crop_range,
            brightness_range=brightness_range,
            rotation_weights=rotation_weights,
            sample_size=sample_size,
            learning_rate=learning_rate,
            max_iter=max_iter,
            batch_size=batch_size,
            targeted=targeted,
            verbose=verbose,
        )

    def generate(
        self, x: np.ndarray, y: Optional[List[Dict[str, np.ndarray]]] = None, **kwargs
    ) -> np.ndarray:
        """Generate RobustDPatch.

        Args:
            x: Sample images.
            y: Target labels for object detector.

        Returns:
            Adversarial patch.
        """
        channel_index = 1 if self.estimator.channels_first else x.ndim - 1

        if x.shape[channel_index] != self.patch_shape[channel_index - 1]:
            raise ValueError(
                "The color channel index of the images and the patch have to be identical."
            )

        if y is None and self.targeted:
            raise ValueError(
                "The targeted version of RobustDPatch attack requires target labels provided to `y`."
            )

        if y is not None and not self.targeted:
            raise ValueError("The RobustDPatch attack does not use target labels.")

        if x.ndim != 4:  # pragma: no cover
            raise ValueError("The adversarial patch can only be applied to images.")

        # Check whether patch fits into the cropped images:
        if self.estimator.channels_first:
            image_height, image_width = x.shape[2:4]

        else:
            image_height, image_width = x.shape[1:3]

        if not self.estimator.native_label_is_pytorch_format and y is not None:
            from art.estimators.object_detection.utils import convert_tf_to_pt

            y = convert_tf_to_pt(y=y, height=x.shape[1], width=x.shape[2])

        if y is not None:
            for i_image in range(x.shape[0]):
                y_i = y[i_image]["boxes"]

                for i_box in range(y_i.shape[0]):
                    x_1, y_1, x_2, y_2 = y_i[i_box]

                    if (
                        x_1 < self.crop_range[1]
                        or y_1 < self.crop_range[0]
                        or x_2 > image_width - self.crop_range[1] + 1
                        or y_2 > image_height - self.crop_range[0] + 1
                    ):
                        raise ValueError(
                            "Cropping is intersecting with at least one box, reduce `crop_range`."
                        )

        if (
            self.patch_location[0] + self.patch_shape[0]
            > image_height - self.crop_range[0]
            or self.patch_location[1] + self.patch_shape[1]
            > image_width - self.crop_range[1]
        ):
            raise ValueError("The patch (partially) lies outside the cropped image.")

        learning_rate = self.learning_rate
        patch_change = 0.0

        for i_step in trange(
            self.max_iter, desc="RobustDPatch iteration", disable=not self.verbose
        ):
            if i_step == 0 or (i_step + 1) % 100 == 0:
                logger.info("Training Step: %i", i_step + 1)

            num_batches = math.ceil(x.shape[0] / self.batch_size)
            patch_gradients_old = np.zeros_like(self._patch)

            if i_step % self.lr_decay_schedule == 0 and self.lr_decay_size < 1.0:
                learning_rate *= self.lr_decay_size
                logger.info("Updated Learning Rate: %s", str(learning_rate))

            for e_step in range(self.sample_size):
                if e_step == 0 or (e_step + 1) % 100 == 0:
                    logger.info("EOT Step: %i", e_step + 1)

                for i_batch in range(num_batches):
                    i_batch_start = i_batch * self.batch_size
                    i_batch_end = min((i_batch + 1) * self.batch_size, x.shape[0])

                    if y is None:
                        y_batch = y
                    else:
                        y_batch = y[i_batch_start:i_batch_end]

                    # Sample and apply the random transformations:
                    (
                        patched_images,
                        patch_target,
                        transforms,
                    ) = self._augment_images_with_patch(
                        x[i_batch_start:i_batch_end],
                        y_batch,
                        self._patch,
                        channels_first=self.estimator.channels_first,
                    )

                    gradients = self.estimator.loss_gradient(
                        x=patched_images,
                        y=patch_target,
                        standardise_output=True,
                    )

                    gradients = self._untransform_gradients(
                        gradients,
                        transforms,
                        channels_first=self.estimator.channels_first,
                    )

                    patch_gradients = patch_gradients_old + np.sum(gradients, axis=0)
                    logger.debug(
                        "Gradient percentage diff: %f)",
                        np.mean(
                            np.sign(patch_gradients) != np.sign(patch_gradients_old)
                        ),
                    )

                    patch_gradients_old = patch_gradients

            new_patch_change = (
                np.sign(patch_gradients)
                * (1 - 2 * int(self.targeted))
                * learning_rate
                + self.momentum * patch_change
            )

            self._patch = self._patch + new_patch_change

            patch_change = new_patch_change

            if self.estimator.clip_values is not None:
                self._patch = np.clip(
                    self._patch,
                    a_min=self.estimator.clip_values[0],
                    a_max=self.estimator.clip_values[1],
                )

        return self._patch

    def _check_params(self) -> None:
        super()._check_params()

        if not isinstance(self.momentum, float):
            raise ValueError("The momentum must be of type float.")

        if self.momentum < 0.0:
            raise ValueError("The momentum must be greater than or equal to 0.0.")

        if not isinstance(self.lr_decay_size, float):
            raise ValueError("The decay schedule must be of type float.")

        if self.lr_decay_size <= 0.0:
            raise ValueError("The decay size must be greater than 0.0.")

        if self.lr_decay_size > 1.0:
            raise ValueError("The decay size cannot be larger than 1.0.")

        if not isinstance(self.lr_decay_schedule, int):
            raise ValueError("The decay schedule must be of type int.")

        if self.lr_decay_schedule <= 0:
            raise ValueError("The decay schedule must be greater than 0.")


class SGDRobustDPatch(RobustDPatch):
    def __init__(
        self,
        estimator: "OBJECT_DETECTOR_TYPE",
        patch_shape: Tuple[int, int, int] = (40, 40, 3),
        patch_location: Tuple[int, int] = (0, 0),
        crop_range: Tuple[int, int] = (0, 0),
        brightness_range: Tuple[float, float] = (1.0, 1.0),
        rotation_weights: Union[Tuple[float, float, float, float], Tuple[int, int, int, int]] = (1, 0, 0, 0),
        sample_size: int = 1,
        learning_rate: float = 0.1,
        lr_decay_size: float = 0.95,
        lr_decay_schedule: int = 5000,
        momentum: float = 0.9,
        max_iter: int = 500,
        batch_size: int = 16,
        targeted: bool = False,
        verbose: bool = True,
    ):
        """Create an instance of the :class:`.RobustDPatch`.

        Args:
            estimator: A trained object detector.
            patch_shape: The shape of the adversarial patch as a tuple of shape (height, width, nb_channels).
            patch_location: The location of the adversarial patch as a tuple of shape (upper left x, upper left y).
            crop_range: By how much the images may be cropped as a tuple of shape (height, width).
            brightness_range: Range for randomly adjusting the brightness of the image.
            rotation_weights: Sampling weights for random image rotations by (0, 90, 180, 270) degrees clockwise.
            sample_size: Number of samples to be used in expectations over transformation.
            learning_rate: The learning rate of the optimization.
            lr_decay_size: The factor to use when decaying the learning rate on a schedule. A value of 1.0 means the learning rate remains constant.
            lr_decay_schedule: The number of iterations to wait before reducing the learning rate by `lr_decay_size`.
            momentum: The momentum of the optimization.
            max_iter: The number of optimization steps.
            batch_size: The size of the training batch.
            targeted: Indicates whether the attack is targeted (True) or untargeted (False).
            verbose: Show progress bars.
        """
        self.lr_decay_size = lr_decay_size
        self.lr_decay_schedule = lr_decay_schedule
        self.momentum = momentum
        super().__init__(
            estimator=estimator,
            patch_shape=patch_shape,
            patch_location=patch_location,
            crop_range=crop_range,
            brightness_range=brightness_range,
            rotation_weights=rotation_weights,
            sample_size=sample_size,
            learning_rate=learning_rate,
            max_iter=max_iter,
            batch_size=batch_size,
            targeted=targeted,
            verbose=verbose,
        )

    def generate(
        self, x: np.ndarray, y: Optional[List[Dict[str, np.ndarray]]] = None, **kwargs
    ) -> np.ndarray:
        """Generate RobustDPatch.

        Args:
            x: Sample images.
            y: Target labels for object detector.

        Returns:
            Adversarial patch.
        """
        channel_index = 1 if self.estimator.channels_first else x.ndim - 1

        if x.shape[channel_index] != self.patch_shape[channel_index - 1]:
            raise ValueError(
                "The color channel index of the images and the patch have to be identical."
            )

        if y is None and self.targeted:
            raise ValueError(
                "The targeted version of RobustDPatch attack requires target labels provided to `y`."
            )

        if y is not None and not self.targeted:
            raise ValueError("The RobustDPatch attack does not use target labels.")

        if x.ndim != 4:  # pragma: no cover
            raise ValueError("The adversarial patch can only be applied to images.")

        # Check whether patch fits into the cropped images:
        if self.estimator.channels_first:
            image_height, image_width = x.shape[2:4]

        else:
            image_height, image_width = x.shape[1:3]

        if not self.estimator.native_label_is_pytorch_format and y is not None:
            from art.estimators.object_detection.utils import convert_tf_to_pt

            y = convert_tf_to_pt(y=y, height=x.shape[1], width=x.shape[2])

        if y is not None:
            for i_image in range(x.shape[0]):
                y_i = y[i_image]["boxes"]

                for i_box in range(y_i.shape[0]):
                    x_1, y_1, x_2, y_2 = y_i[i_box]

                    if (
                        x_1 < self.crop_range[1]
                        or y_1 < self.crop_range[0]
                        or x_2 > image_width - self.crop_range[1] + 1
                        or y_2 > image_height - self.crop_range[0] + 1
                    ):
                        raise ValueError(
                            "Cropping is intersecting with at least one box, reduce `crop_range`."
                        )

        if (
            self.patch_location[0] + self.patch_shape[0]
            > image_height - self.crop_range[0]
            or self.patch_location[1] + self.patch_shape[1]
            > image_width - self.crop_range[1]
        ):
            raise ValueError("The patch (partially) lies outside the cropped image.")

        learning_rate = self.learning_rate
        patch_change = 0.0
        num_samples = x.shape[0]

        for i_step in trange(
            self.max_iter, desc="RobustDPatch iteration", disable=not self.verbose
        ):
            if i_step == 0 or (i_step + 1) % 100 == 0:
                logger.info("Training Step: %i", i_step + 1)

            num_batches = math.ceil(x.shape[0] / self.batch_size)

            if i_step % self.lr_decay_schedule == 0 and self.lr_decay_size < 1.0:
                learning_rate *= self.lr_decay_size
                logger.info("Updated Learning Rate: %s", str(learning_rate))

            for e_step in range(self.sample_size):
                shuffle_idx = np.arange(num_samples, dtype="int32")
                np.random.shuffle(shuffle_idx)

                if e_step == 0 or (e_step + 1) % 100 == 0:
                    logger.info("EOT Step: %i", e_step + 1)

                for i_batch in range(num_batches):
                    i_batch_start = i_batch * self.batch_size
                    i_batch_end = min((i_batch + 1) * self.batch_size, x.shape[0])

                    if y is None:
                        y_batch = y

                    else:
                        y_batch = [y[int(i)] for i in shuffle_idx.tolist()][i_batch_start:i_batch_end]

                    # Sample and apply the random transformations:
                    (
                        patched_images,
                        patch_target,
                        transforms,
                    ) = self._augment_images_with_patch(
                        x[shuffle_idx][i_batch_start:i_batch_end],
                        y_batch,
                        self._patch,
                        channels_first=self.estimator.channels_first,
                    )

                    gradients = self.estimator.loss_gradient(
                        x=patched_images,
                        y=patch_target,
                        standardise_output=True,
                    )

                    gradients = self._untransform_gradients(
                        gradients,
                        transforms,
                        channels_first=self.estimator.channels_first,
                    )

                    patch_gradients = np.sum(gradients, axis=0)

                    new_patch_change = (
                        np.sign(patch_gradients)
                        * (1 - 2 * int(self.targeted))
                        * learning_rate
                        + self.momentum * patch_change
                    )

                    self._patch = self._patch + new_patch_change

                    patch_change = new_patch_change

                    if self.estimator.clip_values is not None:
                        self._patch = np.clip(
                            self._patch,
                            a_min=self.estimator.clip_values[0],
                            a_max=self.estimator.clip_values[1],
                        )

        return self._patch

    def _check_params(self) -> None:
        super()._check_params()

        if not isinstance(self.momentum, float):
            raise ValueError("The momentum must be of type float.")

        if self.momentum < 0.0:
            raise ValueError("The momentum must be greater than or equal to 0.0.")

        if not isinstance(self.lr_decay_size, float):
            raise ValueError("The decay schedule must be of type float.")

        if self.lr_decay_size <= 0.0:
            raise ValueError("The decay size must be greater than 0.0.")

        if self.lr_decay_size > 1.0:
            raise ValueError("The decay size cannot be larger than 1.0.")

        if not isinstance(self.lr_decay_schedule, int):
            raise ValueError("The decay schedule must be of type int.")

        if self.lr_decay_schedule <= 0:
            raise ValueError("The decay schedule must be greater than 0.")
