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

LOGGER: BoundLogger = structlog.stdlib.get_logger()

def get_n_classes_from_directory_iterator(ds: Dataset) -> int:
    """Returns the number of unique labels found by the |directory_iterator|.

    Args:
        ds: A |directory_iterator| object.

    Returns:
        The number of unique labels in the dataset.
    """
    return len(ds.class_names)

def predictions_to_df(
    predictions: np.ndarray,
    dataset: Dataset = None,
    show_actual: bool = False,
    show_target: bool = False,
) -> pd.DataFrame:
    n_classes = get_n_classes_from_directory_iterator(dataset)

    
    df = pd.DataFrame(predictions)
    df.columns = [f'prob_{n}' for n in range(n_classes)] # note: applicable to classification only

    if (show_actual):
        y_pred = np.argmax(predictions, axis=1)
        df.insert(0, 'actual', y_pred)
    if (show_target):
        y_true = np.argmax(np.concatenate([y.index for x, y in dataset], axis=0).astype(np.int32) , axis=1)
        df.insert(0, 'target', y_true)

    df.insert(0, 'id', dataset.file_paths)

    return df


@pyplugs.register
def clean (
    classifier: Model,
    dataset: Dataset, 
    delete_confidence: float = 0.05,
    relabel_confidence: float = 0.10
) -> tuple[np.ndarray, pd.DataFrame]:
    
    # later on found https://cleanlab.ai/blog/cleanlab-2.3
    # https://docs.cleanlab.ai/stable/cleanlab/models/keras.html
    # i didnt spend too long on this but this was *not* a one line change

    class SKLearnClassifierPredictProba(SKLearnClassifier):
        def predict_proba(self, x, **kwargs):
            return self.model_.predict(x, **kwargs)

    data = []
    labels = []

    model = SKLearnClassifierPredictProba(classifier)
    for _, (x, y) in enumerate(dataset):
        x_prime = [reshape(xs, [-1]) for xs in x] 
        data.extend(x_prime)
        y_prime = [np.argmax(ys) for ys in y]
        labels.extend(y_prime)
    print("ARRAY", np.array(data).shape)

    pred_probs = cross_val_predict(
        model,
        np.array(data),
        np.array(labels),
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
    
    #this output looks a bit wrong
    xval = dict()
    for index in label_issues:
        xval[dataset.file_paths[index]] = pred_probs[index]
        # print(dataset.file_paths[index])
    return (label_issues, pd.DataFrame.from_dict(xval, orient='index'))