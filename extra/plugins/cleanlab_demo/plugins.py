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
from tensorflow.compat.v1 import disable_eager_execution
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
from art.defences.trainer import AdversarialTrainerMadryPGD
from art.estimators.classification import KerasClassifier
from art.utils import load_mnist, preprocess

from tensorflow.keras.preprocessing.image import save_img
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv2D, MaxPooling2D, Activation, Dropout

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
    np.append(
        label_issues,
        find_label_issues(
            labels=labels, pred_probs=pred_probs, filter_by="confident_learning", return_indices_ranked_by="self_confidence"
        )
    )
    np.append(
        label_issues,
        find_label_issues(
            labels=labels, pred_probs=pred_probs, filter_by="predicted_neq_given", return_indices_ranked_by="self_confidence"
        )
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
    nb_epochs: int = 10,
    norm: int | str = 2,
    max_iter:int  = 100,
    clean_label = True,
) -> None:
    # some of this function's parameters are unused, support for these parameters are
    # also in the toml but the function itself currently does not support them 
    # TODO: add support for the unused parameters within the function body as they may be useful

    # Create Keras convolutional neural network - basic architecture from Keras examples
    # Source here: https://github.com/keras-team/keras/blob/master/examples/mnist_cnn.py
    def create_model():    
        model = Sequential()
        model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(28, 28, 1)))
        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        model.add(Flatten())
        model.add(Dense(128, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(10, activation='softmax'))

        model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
        return model

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

    perturbation = add_pattern_bd
    backdoor = PoisoningAttackBackdoor(perturbation)

    # TODO: this way of creating and training a poisoning model (pulled from the ART notebook) works very well 
    # with poisoning, but something is different in Dioptra's create model plugin, figure out discrepency
    # and replace?
    # Source: https://github.com/Trusted-AI/adversarial-robustness-toolbox/blob/e30d32d1a1ef296be65097a98391fc2c53a8e509/notebooks/poisoning_attack_clean_label_backdoor.ipynb
    if clean_label:
        (x_raw, y_raw), (x_raw_test, y_raw_test), min_, max_ = load_mnist(raw=True)

        # Random Selection:
        n_train = np.shape(x_raw)[0]
        num_selection = 10000
        random_selection_indices = np.random.choice(n_train, num_selection)
        x_raw = x_raw[random_selection_indices]
        y_raw = y_raw[random_selection_indices]
        # Poison training data
        percent_poison = percentage
        x_train, y_train = preprocess(x_raw, y_raw)
        x_train = np.expand_dims(x_train, axis=3)

        x_test, _ = preprocess(x_raw_test, y_raw_test)
        x_test = np.expand_dims(x_test, axis=3)

        # Shuffle training data
        n_train = np.shape(y_train)[0]
        shuffled_indices = np.arange(n_train)
        np.random.shuffle(shuffled_indices)
        x_train = x_train[shuffled_indices]
        y_train = y_train[shuffled_indices]
        
        proxy = AdversarialTrainerMadryPGD(KerasClassifier(create_model(),clip_values=[0,1]), nb_epochs=10, eps=0.15, eps_step=0.001)
        proxy.fit(x_train, y_train)
        targets = to_categorical([9], 10)[0] 


        attack = PoisoningAttackCleanLabelBackdoor(backdoor=backdoor, proxy_classifier=proxy.get_classifier(),
                                           target=targets, pp_poison=percent_poison, norm=2, eps=5,
                                           eps_step=0.1, max_iter=200)
    else:
        attack = backdoor

    # Saving the resulting poisoned files
    img_filenames = [Path(x) for x in dataset.file_paths]

    for batch_num, (x, y) in enumerate(dataset):
        # This try except is to catch an error for when the set poison tries to poison is empty
        # It seems like batch_size must be sufficently large enough that probablistically, some
        # of the batch continues to be poisoned]
        try:
            if clean_label:
                poisoned_batch_data, poisoned_batch_labels = attack.poison(x.numpy(), y)
            else:
                poisoned_batch_data, poisoned_batch_labels = attack.poison(x.numpy(), y)
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