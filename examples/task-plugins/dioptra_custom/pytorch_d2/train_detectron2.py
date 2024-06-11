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

from typing import Optional, Tuple, Any

import structlog, os
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

from detectron2 import model_zoo
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg

import ssl


# TODO: Incorporate support for all model architectures.
# TODO: Toggle between CPU and GPU settings.
@pyplugs.register()
@pyplugs.task_nout(2)
def train_model(
    dataset_name,
    class_names,
    model_architecture,
    batch_size,
    learning_rate,
    max_iter,
    dataloader_num_workers,
    gpu,
):
    cfg = get_cfg()

    if not gpu:
        cfg.MODEL.DEVICE = "cpu"

    cfg.merge_from_file(model_zoo.get_config_file(model_architecture))
    cfg.DATASETS.TRAIN = dataset_name
    cfg.DATASETS.TEST = ()
    cfg.DATALOADER.NUM_WORKERS = dataloader_num_workers
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
        model_architecture
    )  # Let training initialize from model zoo
    cfg.SOLVER.IMS_PER_BATCH = 2
    cfg.SOLVER.BASE_LR = learning_rate  #
    cfg.SOLVER.MAX_ITER = max_iter
    cfg.SOLVER.STEPS = []
    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = (
        batch_size  # faster, and good enough for this toy dataset (default: 512)
    )
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = len(
        class_names
    )  # only has one class (balloon). (see https://detectron2.readthedocs.io/tutorials/datasets.html#update-the-config-for-new-datasets)
    cfg.MODEL.RETINANET.NUM_CLASSES = len(class_names)
    # NOTE: this config means the number of classes, but a few popular unofficial tutorials incorrect uses num_classes+1 here.

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    trainer = DefaultTrainer(cfg)
    trainer.resume_or_load(resume=False)
    trainer.train()
    return trainer.model, cfg
