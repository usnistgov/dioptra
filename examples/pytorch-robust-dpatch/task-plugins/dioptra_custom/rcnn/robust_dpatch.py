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
from typing import Callable, Dict, List, Optional, Tuple, Union

import os
import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from structlog.stdlib import BoundLogger
from prefect import task
from art.attacks.evasion import RobustDPatch
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog
from tqdm.auto import trange
import math
import cv2
from dioptra import pyplugs
from dioptra.sdk.exceptions import (
    ARTDependencyError,
)
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

#from detectron2.engine import DefaultPredictor
#from detectron2.config import get_cfg
#from detectron2 import model_zoo
from art.estimators.object_detection import PyTorchFasterRCNN

@pyplugs.register
def robust_dpatch(
    frcnn: Any,
    patch_shape: Tuple[int,int,int] = (20,20,3),
    patch_location: Tuple[int,int] = (2, 2),
    crop_range: Tuple[int,int] = (0, 0),
    brightness_range:Tuple[float, float] = (0.1,1.9),
    rotation_weights: Tuple[float,float,float,float] = (1,0,0,0),
    sample_size: int = 1,
    learning_rate: float = 0.1,
    lr_decay_size: float = 0.95,
    lr_decay_schedule: int = 5000,
    momentum: float = 0.9,
    max_iter: int = 30,
    batch_size: int = 10,
    targeted: bool = False,
    verbose: bool = True,
) -> Any:
    """Generates an adversarial dataset using the Pixel Threshold attack.
    This attack attempts to evade a classifier by changing a set number of
    pixels below a certain threshold.
    Args:
        model_loc: The location of the model on disk to load from
        metrics: A list of metrics to be evaluated by the model during testing.
    """
    attack = RobustDPatchEdit(
        frcnn,
        patch_shape=patch_shape,
        patch_location=patch_location,
        crop_range=crop_range,
        brightness_range=brightness_range,
        rotation_weights=rotation_weights,
        sample_size=sample_size,
        learning_rate=learning_rate,
        lr_decay_size=lr_decay_size,
        lr_decay_schedule=lr_decay_schedule,
        momentum=momentum,
        max_iter=max_iter,
        batch_size=batch_size,
        targeted=targeted,
        verbose=verbose,
    )

    return attack

@pyplugs.register
def generate(
    attack: Any,
    imgs: Any,
) -> Any:
    """Generates an adversarial dataset using the Pixel Threshold attack.
    This attack attempts to evade a classifier by changing a set number of
    pixels below a certain threshold.
    Args:
        model_loc: The location of the model on disk to load from
        metrics: A list of metrics to be evaluated by the model during testing.
    """
    patch = attack.generate(x=np.stack(imgs, axis=0).astype(np.float32), y=None)

    return patch

@pyplugs.register
def apply_patches(
    attack: Any,
    imgs: Any,
    patch: Optional[Any] = None,
    patch_loc: Optional[Tuple[int,int]] = None,

):
    if patch_loc is not None:
        attack.patch_location = patch_loc 
        
    if patch is None:
        patched_imgs = attack.apply_patch(np.stack(imgs, axis=0))
    else:
        patched_imgs = attack.apply_patch(np.stack(imgs, axis=0), patch_external=patch)
    return patched_imgs

@pyplugs.register
def save_img(
    img: Any,
    img_name: str,
    img_dir: Path
):
    cv2.imwrite( str(img_dir / img_name), img)

@pyplugs.register
def test_patches(
    classifier: Any,
    patched_imgs: Any,
    img_dir: Path,
    image_name: str,
    subset: Optional[int] = None,
    score_cutoff: float = 0.5
):
    default_classes = ["stop", "crosswalk", "speedlimit", "trafficlight"]

    predictor = classifier._detectron_model
    
    try:
        for d in ["training", "testing"]:
            DatasetCatalog.register("signs_" + d, lambda d=d: get_sign_dicts(base_path + "/" + d))
            MetadataCatalog.get("signs_" + d).set(thing_classes=default_classes)
    except:
        pass
    meta = MetadataCatalog.get("signs_training")
    
    if subset is None:
        subset = len(patched_imgs)
        
    for k in range(subset):
        im2 = patched_imgs[k]
        
        outs = predictor(im2)
        v = Visualizer(im2[:, :, ::-1],
                       metadata=meta, 
                       scale=0.5)
        filtered_instances = outs['instances'][outs['instances'].scores > score_cutoff]      

        out = v.draw_instance_predictions(filtered_instances.to("cpu"))
        
        fp = str(img_dir / str( "img" + str(k) + image_name + '.png'))
        #LOGGER.info(fp)
        out.save(filepath=fp)

class RobustDPatchEdit(RobustDPatch):

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

            num_batches = math.ceil(x.shape[0] / self.batch_size)

            if i_step % self.lr_decay_schedule == 0 and self.lr_decay_size < 1.0:
                learning_rate *= self.lr_decay_size

            for e_step in range(self.sample_size):
                shuffle_idx = np.arange(num_samples, dtype="int32")
                np.random.shuffle(shuffle_idx)

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

        
    def apply_patch(self, x: np.ndarray, patch_external: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Apply the adversarial patch to images.

        :param x: Images to be patched.
        :param patch_external: External patch to apply to images `x`. If None the attacks patch will be applied.
        :return: The patched images.
        """

        x_patch = x.copy()

        if patch_external is not None:
            patch_local = patch_external.copy()
        else:
            patch_local = self._patch.copy()

        if self.estimator.channels_first:
            x_patch = np.transpose(x_patch, (0, 2, 3, 1))
            patch_local = np.transpose(patch_local, (1, 2, 0))

        # Apply patch:
        x_1, y_1 = self.patch_location
        x_2, y_2 = x_1 + patch_local.shape[0], y_1 + patch_local.shape[1]

        print(x_patch.shape)
        x_patch[:, x_1:x_2, y_1:y_2, :] = patch_local

        if self.estimator.channels_first:
            x_patch = np.transpose(x_patch, (0, 3, 1, 2))

        return x_patch
