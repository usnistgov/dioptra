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
from dataclasses import dataclass

# Adapted from:
# https://scikit-learn.org/stable/auto_examples/classification/plot_digits_classification.html#sphx-glr-auto-examples-classification-plot-digits-classification-py
# Authors: The scikit-learn developers
# SPDX-License-Identifier: BSD-3-Clause
import numpy as np

# import matplotlib.pyplot as plt
import pandas as pd
import structlog
from sklearn import datasets, metrics, svm
from sklearn.base import BaseEstimator
from sklearn.model_selection import train_test_split

from dioptra import pyplugs

LOGGER = structlog.get_logger()


@pyplugs.register
def load_toy_dataset(name: str) -> list[np.ndarray]:
    load_fn = {
        "iris": datasets.load_iris,
        "diabetes": datasets.load_diabetes,
        "digits": datasets.load_digits,
        "linnerud": datasets.load_linnerud,
        "wine": datasets.load_wine,
        "breast_cancer": datasets.load_breast_cancer,
    }.get(name)
    dataset = load_fn()

    # flatten the images
    n_samples = len(dataset.images)
    data = dataset.images.reshape((n_samples, -1))

    # Split data into 50% train and 50% test subsets
    x_train, x_test, y_train, y_test = train_test_split(
        data, dataset.target, test_size=0.5, shuffle=False
    )

    return x_train, y_train, x_test, y_test


@pyplugs.register
def train_model(x_train: np.ndarray, y_train: np.ndarray) -> BaseEstimator:
    model = svm.SVC(gamma=0.001)

    model.fit(x_train, y_train)

    return model


@pyplugs.register
def model_predict(model, x) -> np.ndarray:
    return model.predict(x)


@pyplugs.register
def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> pd.DataFrame:
    metrics_dict = metrics.classification_report(y_true, y_pred, output_dict=True)
    return pd.DataFrame(metrics_dict)
