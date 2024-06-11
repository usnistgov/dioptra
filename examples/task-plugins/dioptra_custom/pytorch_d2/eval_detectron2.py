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

import structlog
from structlog.stdlib import BoundLogger
import os
from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

from detectron2.engine import DefaultPredictor
from detectron2.structures import BoxMode


from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader

@pyplugs.register
def eval_dataset(dataset_name, classifier, confidence, cfg, poison=False):
    model_filepath = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")

    cfg.MODEL.WEIGHTS = model_filepath
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = confidence
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = confidence

    evaluator = COCOEvaluator(dataset_name, output_dir="./output")
    val_loader = build_detection_test_loader(cfg, dataset_name)
    results = inference_on_dataset(classifier, val_loader, evaluator)['bbox']
    new_results = {}
    if not poison:
        return results
    else:
        for key in results:
            new_results['poison-'+key] = results[key]
        return new_results
