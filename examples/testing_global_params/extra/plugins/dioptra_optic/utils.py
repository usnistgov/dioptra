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
import os
from typing import Any

import keras
import numpy as np
import structlog
import tensorflow as tf
from keras.callbacks import Callback
from keras.src.metrics.reduction_metrics import MeanMetricWrapper

from dioptra import pyplugs
from dioptra.sdk.utilities.auth_client import get_authenticated_worker_client

LOGGER = structlog.get_logger()


@pyplugs.register
def set_random_seed(seed: int | None = 10145783023) -> int:
    """
    Sets the random seed for python, numpy, and backend frameworks (e.g. tensorflow) and logs the
    seed as a metric for the job.

    Args:
        seed: The seed value to be set. If none a random seed is chosen.
    """
    seed = seed or np.random.randint(np.iinfo(np.uint32).max)
    keras.utils.set_random_seed(seed)
    LOGGER.info("set random seed", seed=seed, task="set_random_seed")
    return seed


class LpNorm(MeanMetricWrapper):
    def __init__(self, norm=1, **kwargs):
        name = f"l_{norm}_norm"
        super().__init__(fn=lambda x1, x2: lp_norm(x1, x2, norm), name=name, **kwargs)
        self.norm = norm

    def get_config(self):
        return {"name": self.name, "norm": str(self.norm)}


def lp_norm(x1, x2, norm):
    return tf.map_fn(lambda x: tf.norm(x, ord=norm), x1 - x2)


class DioptraMetricsLoggingCallback(Callback):
    """
    A Keras Callback for logging metrics to the current Dioptra job.
    """

    def __init__(self, logger):
        self._logger = logger
        self._dioptra_client = get_authenticated_worker_client(LOGGER, "json")

    def _log_metrics(
        self,
        metrics: dict[str, Any] | None,
        epoch: int | None = None,
        prefix: str | None = None,
    ):
        if metrics is None:
            return

        if prefix is not None:
            metrics = {f"{prefix}_{name}": value for name, value in metrics.items()}

        try:  # don't want to crash if logging fails
            for metric, value in metrics.items():
                self._dioptra_client.jobs.append_metric_by_id(
                    job_id=os.environ["__JOB_ID"],
                    metric_name=metric,
                    metric_value=float(value),
                    metric_step=epoch,
                )
        except Exception as e:
            LOGGER.warning(e)

    def on_epoch_end(self, epoch, logs=None):
        self._logger.info(f"epoch {epoch} complete", metrics=logs)
        self._log_metrics(logs, epoch)

    def on_test_end(self, logs=None):
        self._logger.info(f"test complete", metrics=logs)
        self._log_metrics(logs, prefix="test")

    def on_predict_end(self, logs=None):
        self._logger.info(f"predict complete", metrics=logs)
        self._log_metrics(logs, prefix="predict")
