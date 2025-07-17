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
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
import structlog

from dioptra import pyplugs
from structlog.stdlib import BoundLogger
from tensorflow import reshape
from tensorflow.data import Dataset
from tensorflow.keras.models import Model
from cleanlab.filter import find_label_issues
from sklearn.model_selection import cross_val_predict
from keras.wrappers import SKLearnClassifier
from .restapi import post_metrics

from art.attacks.poisoning import (
    PoisoningAttackBackdoor,
    PoisoningAttackCleanLabelBackdoor,
)
from art.attacks.poisoning.perturbations import add_pattern_bd
from art.utils import to_categorical

from tensorflow.keras.preprocessing.image import save_img

LOGGER: BoundLogger = structlog.stdlib.get_logger()

@pyplugs.register
def clean (
    classifier: Model,
    dataset: Dataset,
) -> tuple[np.ndarray, pd.DataFrame]:

    # later on found https://cleanlab.ai/blog/cleanlab-2.3 which might solve of the 
    # below class manipulations
    # https://docs.cleanlab.ai/stable/cleanlab/models/keras.html

    class SKLearnClassifierPredictProba(SKLearnClassifier):
        def predict_proba(self, x, **kwargs):
            return self.model_.predict(x, **kwargs)

    data = []
    labels = []

    model = SKLearnClassifierPredictProba(classifier)
    for (x, y) in dataset:
        x_prime = [reshape(xs, [-1]) for xs in x] 
        data.extend(x_prime)
        y_prime = np.argmax(y, axis=1)
        labels.extend(y_prime)
    # print("ARRAY", np.array(data).shape)

    data = np.array(data)
    labels = np.array(labels)

    pred_probs = cross_val_predict(
        model,
        data,
        labels,
        cv=5,
        method="predict_proba",
    )

    # print("\n", type(pred_probs))
    # print(pred_probs.shape)
    # print(pred_probs[1], "\n")

    label_issues = find_label_issues(
        labels=labels, pred_probs=pred_probs, return_indices_ranked_by="self_confidence"
    )

    LOGGER.info(
        f"Number of potential label errors found: {len(label_issues)}"
    )
    post_metrics(metric_name="cleanlab_label_errors", metric_value=float(len(label_issues)))
    
    xval = dict()
    for index in label_issues:
        xval[dataset.file_paths[index]] = pred_probs[index]
        # print(dataset.file_paths[index])
    return (label_issues, pd.DataFrame.from_dict(xval, orient='index'))

@pyplugs.register
def parse_csv(
    csv_file: list[str] | list[Path]
) -> np.ndarray:
    import os
    print("current dir: ", os.getcwd())
    print("dir list: ", os.listdir("."))
    file = csv_file[0]

    # read csv and turn all of the file paths into indicies
    df = pd.read_csv(file)

    # isolate the file name of the image
    df = df.iloc[:, 0].apply(lambda pathstr: Path(pathstr).name)
    df = df.to_numpy()

    LOGGER.info(
        f"Filtering out {len(df)} data points with ids:\n {df}"
    )
    return df

@pyplugs.register
def filter_data (
    dataset: Dataset,
    delete_idxs: np.ndarray,
    clean_data_dir: str | Path,
    save: bool,
    batch_size: int
) -> Dataset:
    img_filenames = [Path(x) for x in dataset.file_paths]

    if save:
        for batch_num, (x, y) in enumerate(dataset):
            clean_filenames = img_filenames[ batch_num * batch_size : (batch_num + 1) * batch_size  ]
            _save_adv_batch(x, Path(clean_data_dir), np.argmax(y, axis=1), clean_filenames, curridx=batch_num*batch_size, filtered=delete_idxs)

@pyplugs.register
def poison (
    dataset: Dataset,
    classifier: Model,
    percentage: float,
    adv_data_dir: str | Path,
    batch_size: int,
    target_idx: int = 0,
    eps: float = 0.3,
    eps_step: float = 0.1,
    max_iter:int  = 100,
    clean_label = True,
) -> None:

    assert (0 < percentage) and (percentage < 1), \
        "the percentage must be between 0 and 1"

    if clean_label:
        LOGGER.info(
            f"Poisoning target {target_idx}\n"
        )
    else:
        LOGGER.info(
            f"Adding backdoors\n"
        )

    # construct target from target idx
    # the len call could be replaced with a function from mnist_demo for readability
    n_classes = len(dataset.class_names)
    target = to_categorical([target_idx], n_classes)[0]

    perturbation = add_pattern_bd
    backdoor = PoisoningAttackBackdoor(perturbation)
    if clean_label:
        attack = PoisoningAttackCleanLabelBackdoor(backdoor,
                                                classifier,
                                                target,
                                                percentage,
                                                eps=eps,
                                                eps_step=eps_step,
                                                max_iter=max_iter)
    else:
        attack = backdoor

    img_filenames = [Path(x) for x in dataset.file_paths]

    for batch_num, (x, y) in enumerate(dataset):
        # This try except is to catch an error for when the set poison tries to poison is empty
        # It seems like batch_size must be sufficently large enough that probablistically, some
        # of the batch continues to be poisoned]
        try:
            if clean_label:
                poisoned_batch_data, poisoned_batch_labels = attack.poison(x.numpy(), y)
            else:
                poisoned_batch_data, poisoned_batch_labels = attack.poison(x.numpy(), target)
        except:
            poisoned_batch_data, poisoned_batch_labels = (x, y)

        clean_filenames = img_filenames[ batch_num * batch_size : (batch_num + 1) * batch_size  ]
        poisoned_batch_labels = np.argmax(y, axis=1)
        _save_adv_batch(poisoned_batch_data, Path(adv_data_dir), poisoned_batch_labels, clean_filenames)

# from mnist demo with an extra parameter
def _save_adv_batch(adv_batch, adv_data_dir, y, clean_filenames, curridx=0, filtered=[]) -> None:
    """Saves a batch of adversarial images to disk.

    Args:
        adv_batch: A generated batch of adversarial images.
        adv_data_dir: The directory to use when saving the generated adversarial images.
        y: An array containing the target labels of the original images.
        clean_filenames: A list containing the filenames of the original images.
    """
    for batch_image_num, adv_image in enumerate(adv_batch):
        if clean_filenames[batch_image_num].name not in filtered:
            adv_image_path = (
                adv_data_dir
                / f"{y[batch_image_num]}"
                / f"adv_{clean_filenames[batch_image_num].name}"
            )

            if not adv_image_path.parent.exists():
                adv_image_path.parent.mkdir(parents=True)

            save_img(path=str(adv_image_path), x=adv_image)
