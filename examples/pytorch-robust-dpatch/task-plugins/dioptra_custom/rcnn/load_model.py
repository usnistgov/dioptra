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

from dioptra import pyplugs
from dioptra.sdk.exceptions import (
    ARTDependencyError,
)
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo
from art.estimators.object_detection import PyTorchFasterRCNN


from art.attacks.attack import EvasionAttack
from art.estimators.estimator import BaseEstimator, LossGradientsMixin
from art.estimators.object_detection.object_detector import ObjectDetectorMixin
from art import config

from art.estimators.object_detection import PyTorchObjectDetector
from art.attacks.evasion import RobustDPatch
from torchvision import transforms
from torchvision.datasets import ImageFolder
from detectron2.modeling import build_model

from torch.utils.data import random_split
from torch.utils.data import DataLoader
from torch.utils.data import Subset
import torchvision

from detectron2.structures import Boxes, Instances
from detectron2.utils.events import EventStorage


@pyplugs.register
def load_model(
    model_loc: str,
) -> Any:
    """Generates an adversarial dataset using the Pixel Threshold attack.
    This attack attempts to evade a classifier by changing a set number of
    pixels below a certain threshold.
    Args:
        model_loc: The location of the model on disk to load from
        metrics: A list of metrics to be evaluated by the model during testing.
    """
    cfg = get_cfg()
    
    model_name = "COCO-Detection/retinanet_R_50_FPN_3x.yaml"

    cfg.merge_from_file(model_zoo.get_config_file(model_name))
    cfg.DATASETS.TRAIN = ("signs_training",)
    cfg.DATASETS.TEST = ()
    cfg.DATALOADER.NUM_WORKERS = 2
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(model_name)  # Let training initialize from model zoo
    cfg.SOLVER.IMS_PER_BATCH = 4
    cfg.SOLVER.BASE_LR = 0.00025  # Learning rate.
    cfg.SOLVER.MAX_ITER = 500 #3000    
    cfg.SOLVER.STEPS = []        # decay learning rate

    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128  # (default: 512)
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 4 
    cfg.MODEL.RETINANET.NUM_CLASSES = 4

    
    cfg.MODEL.WEIGHTS = os.path.join(model_loc, "model_final.pth")
    #LOGGER.info(cfg.MODEL.WEIGHTS)
    # path to the model we just trained
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7   # set a custom testing threshold
    model = DefaultPredictor(cfg)
    
    frcnn = DetectronObjectDetector(detectron_model=model,
        clip_values=(0,255),
        attack_losses=["loss_cls", "loss_box_reg"]
    )
    #frcnn = PyTorchFasterRCNN(
    #    clip_values=(0, 255), attack_losses=["loss_classifier", "loss_box_reg", "loss_objectness", "loss_rpn_box_reg"]
    #)

    return frcnn

class DetectronObjectDetector(PyTorchObjectDetector):
    def __init__(
        self,
        detectron_model,
        clip_values: Optional["CLIP_VALUES_TYPE"] = None,
        channels_first: Optional[bool] = None,
        preprocessing_defences: Union["Preprocessor", List["Preprocessor"], None] = None,
        postprocessing_defences: Union["Postprocessor", List["Postprocessor"], None] = None,
        preprocessing: "PREPROCESSING_TYPE" = None,
        attack_losses: Tuple[str, ...] = (
            "loss_cls",
            "loss_box_reg"
        ),
        device_type: str = "gpu",
    ):   
        super().__init__(
            model=detectron_model.model,
            clip_values=clip_values,
            channels_first=channels_first,
            preprocessing_defences=preprocessing_defences,
            postprocessing_defences=postprocessing_defences,
            preprocessing=preprocessing,
            attack_losses=attack_losses,
            device_type=device_type
        )
        self._detectron_model = detectron_model
        
    def format_detectron(self, inputs_t, labels_t=None):
        detectron_x = [{"image": np.squeeze(z).permute(0,1,2)} for z in inputs_t]
        if (labels_t is not None):
            for i in range(len(labels_t)):
                label = labels_t[i]
                instances = Instances((inputs_t[0].shape[1], inputs_t[0].shape[2]))
                instances.gt_boxes = Boxes(label['boxes'])
                instances.gt_classes = label['labels']
                detectron_x[i]["instances"] = instances
        return detectron_x

    def predict(self, x: np.ndarray, batch_size: int = 128, **kwargs) -> List[Dict[str, np.ndarray]]:
        """
        Perform prediction for a batch of inputs.
        :param x: Samples of shape (nb_samples, height, width, nb_channels).
        :param batch_size: Batch size.
        :return: Predictions of format `List[Dict[str, np.ndarray]]`, one for each input image. The fields of the Dict
                 are as follows:
                 - boxes [N, 4]: the boxes in [x1, y1, x2, y2] format, with 0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H.
                 - labels [N]: the labels for each image
                 - scores [N]: the scores or each prediction.
        """
        import torchvision  # lgtm [py/repeated-import]

        self._model.eval()

        # Apply preprocessing
        x, _ = self._apply_preprocessing(x, y=None, fit=False)

        transform = torchvision.transforms.Compose([torchvision.transforms.ToTensor()])
        image_tensor_list: List[np.ndarray] = list()

        if self.clip_values is not None:
            norm_factor = self.clip_values[1]
        else:
            norm_factor = 1.0
        for i in range(x.shape[0]):
            image_tensor_list.append(transform(x[i]).to(self.device))
            
        predictions = [self._detectron_model(dx.permute(1,2,0).detach().cpu().numpy()) for dx in image_tensor_list]

        for i_prediction, _ in enumerate(predictions):
            predictions[i_prediction]["boxes"] = predictions[i_prediction]['instances'].get_fields()["pred_boxes"].tensor.detach().cpu().numpy()
            predictions[i_prediction]["labels"] = predictions[i_prediction]['instances'].get_fields()["pred_classes"].detach().cpu().numpy()
            predictions[i_prediction]["scores"] = predictions[i_prediction]['instances'].get_fields()["scores"].detach().cpu().numpy()
            if "masks" in predictions[i_prediction]:
                predictions[i_prediction]["masks"] = predictions[i_prediction]["masks"].detach().cpu().numpy().squeeze()

        return predictions
    def _get_losses(
        self, x: np.ndarray, y: Union[List[Dict[str, np.ndarray]], List[Dict[str, "torch.Tensor"]]]
    ) -> Tuple[Dict[str, "torch.Tensor"], List["torch.Tensor"], List["torch.Tensor"]]:
        import torch  # lgtm [py/repeated-import]
        import torchvision  # lgtm [py/repeated-import]

        self._model.train()

        # Apply preprocessing
        if self.all_framework_preprocessing:
            if isinstance(x, torch.Tensor):
                raise NotImplementedError

            if y is not None and isinstance(y[0]["boxes"], np.ndarray):
                y_tensor = list()
                for i, y_i in enumerate(y):
                    y_t = dict()
                    y_t["boxes"] = torch.from_numpy(y_i["boxes"]).type(torch.float).to(self.device)
                    y_t["labels"] = torch.from_numpy(y_i["labels"]).type(torch.int64).to(self.device)
                    if "masks" in y_i:
                        y_t["masks"] = torch.from_numpy(y_i["masks"]).type(torch.int64).to(self.device)
                    y_tensor.append(y_t)
            else:
                y_tensor = y

            transform = torchvision.transforms.Compose([torchvision.transforms.ToTensor()])
            image_tensor_list_grad = list()
            y_preprocessed = list()
            inputs_t = list()

            for i in range(x.shape[0]):
                if self.clip_values is not None:
                    x_grad = transform(x[i] / self.clip_values[1]).to(self.device)
                else:
                    x_grad = transform(x[i]).to(self.device)
                x_grad.requires_grad = True
                image_tensor_list_grad.append(x_grad)
                x_grad_1 = torch.unsqueeze(x_grad, dim=0)
                x_preprocessed_i, y_preprocessed_i = self._apply_preprocessing(
                    x_grad_1, y=[y_tensor[i]], fit=False, no_grad=False
                )
                x_preprocessed_i = torch.squeeze(x_preprocessed_i)
                y_preprocessed.append(y_preprocessed_i[0])
                inputs_t.append(x_preprocessed_i)

        elif isinstance(x, np.ndarray):
            x_preprocessed, y_preprocessed = self._apply_preprocessing(x, y=y, fit=False, no_grad=True)

            if y_preprocessed is not None and isinstance(y_preprocessed[0]["boxes"], np.ndarray):
                y_preprocessed_tensor = list()
                for i, y_i in enumerate(y_preprocessed):
                    y_preprocessed_t = dict()
                    y_preprocessed_t["boxes"] = torch.from_numpy(y_i["boxes"]).type(torch.float).to(self.device)
                    y_preprocessed_t["labels"] = torch.from_numpy(y_i["labels"]).type(torch.int64).to(self.device)
                    if "masks" in y_i:
                        y_preprocessed_t["masks"] = torch.from_numpy(y_i["masks"]).type(torch.uint8).to(self.device)
                    y_preprocessed_tensor.append(y_preprocessed_t)
                y_preprocessed = y_preprocessed_tensor

            transform = torchvision.transforms.Compose([torchvision.transforms.ToTensor()])
            image_tensor_list_grad = list()

            for i in range(x_preprocessed.shape[0]):
                if self.clip_values is not None:
                    x_grad = transform(x_preprocessed[i] / self.clip_values[1]).to(self.device)
                else:
                    x_grad = transform(x_preprocessed[i]).to(self.device)
                x_grad.requires_grad = True
                image_tensor_list_grad.append(x_grad)

            inputs_t = image_tensor_list_grad

        else:
            raise NotImplementedError("Combination of inputs and preprocessing not supported.")

        if isinstance(y_preprocessed, np.ndarray):
            labels_t = torch.from_numpy(y_preprocessed).to(self.device)  # type: ignore
        else:
            labels_t = y_preprocessed  # type: ignore
        
        detectron_x = self.format_detectron(inputs_t, labels_t)
        with EventStorage() as storage: 
            output =  self._model(detectron_x)
            #print("WEIGHTS-LOSSES:")
            #for param in self._model.parameters():
            #    print(param.data)
            #    break
        return output, inputs_t, image_tensor_list_grad
