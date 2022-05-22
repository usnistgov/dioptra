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
import warnings
from typing import Tuple, Any
from pathlib import Path

warnings.filterwarnings("ignore")



import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from art.estimators.classification import PyTorchClassifier
from art.attacks.inference.membership_inference.black_box import MembershipInferenceBlackBox
from torch.nn import CrossEntropyLoss
import numpy
from torch.autograd import Variable
from dioptra import pyplugs

LOGGER = structlog.get_logger()
DISTANCE_METRICS = [
]

def wrap_torch_classifier(torch_model, loss_fn, input_shape, classes):
    return PyTorchClassifier(model=torch_model, loss=loss_fn, input_shape=input_shape, nb_classes=classes)

def init_mi(model, loss_fn, input_shape, classes, attack_type, **kwargs):
    classifier = wrap_torch_classifier(model, loss_fn, input_shape, classes, **kwargs)
    attack = MembershipInferenceBlackBox(classifier=classifier,
                                         input_type="loss",
                                         attack_model_type=attack_type,
                                         **kwargs)
    return classifier, attack

@pyplugs.register
def infer_membership(
    training_ds: Any,
    testing_ds: Any,
    model: Any,
    attack_type: str = "nn",
    split: float = 0.5,
    balance_sets: bool = True,
    image_size: Tuple[int, int, int] = (1, 28, 28),
    **kwargs,
):

    x_train = next(iter(training_ds))[0].numpy()
    y_train = next(iter(training_ds))[1].numpy()
    
    x_test = next(iter(testing_ds))[0].numpy()
    y_test = next(iter(testing_ds))[1].numpy()
    
    classes = len(numpy.unique(y_train))
    LOGGER.info("Classes:" + str(classes))

    classifier, attack = init_mi(model=model,
                                 loss_fn=CrossEntropyLoss(),
                                 input_shape=image_size,
                                 classes=classes,
                                 attack_type=attack_type,
                                 **kwargs)
    
    attack_train_size = int(len(x_train) * split)
    attack_test_size = int(len(x_test) * split)
      
    # Take the lesser of the two sizes if we want to keep it balanced
    if balance_sets:
        if attack_train_size < attack_test_size:
            attack_test_size = attack_train_size
        else:
            attack_train_size = attack_test_size

    attack.fit(
        x_train[:attack_train_size], y_train[:attack_train_size], x_test[:attack_test_size], y_test[:attack_test_size]
    )

    # infer attacked feature on remainder of data
    inferred_train = attack.infer(x_train[attack_train_size:], y_train[attack_train_size:])
    inferred_test = attack.infer(x_test[attack_test_size:], y_test[attack_test_size:])

    log_mi_metrics(inferred_train, inferred_test)
    

    return None

def log_mi_metrics(inferred_train, inferred_test):
    trainacc = (sum(inferred_train)) / len(inferred_train)
    testacc = (sum(inferred_test)) / len(inferred_test)

    accuracy = (sum(inferred_train) + sum(inferred_test)) / (len(inferred_train) + len(inferred_test))
    mlflow.log_metric(key="acc",value=accuracy)
    mlflow.log_metric(key="acc_train",value=trainacc)
    mlflow.log_metric(key="acc_test",value=testacc)
