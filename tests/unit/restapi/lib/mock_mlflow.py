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

import time
from typing import Any, Optional

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

active_runs: dict[str, list[MockMlflowMetric]] = {}
registered_models: dict[str, MockMlflowRegisteredModel] = {}


class MockMlflowClient(object):
    def __init__(self) -> None:
        LOGGER.info(
            "Mocking mlflow.tracking.MlflowClient instance",
        )

    def create_registered_model(
        self, name: str, tags: dict | None = None, descrption: str | None = None
    ) -> MockMlflowRegisteredModel:
        LOGGER.info("Mocking MlflowClient.create_registered_model() function")
        registered_models[name] = MockMlflowRegisteredModel(name)

    def get_run(self, id: str) -> MockMlflowRun:
        # Note: In Mlflow, this function would usually throw an MlflowException
        # if the run id is not found. For simplicity this is left out in favor of
        # assuming the run should exist in this mock instance.

        LOGGER.info("Mocking MlflowClient.get_run() function")
        if id not in active_runs:
            active_runs[id] = []

        run = MockMlflowRun(id)
        metrics: list[MockMlflowMetric] = active_runs[id]
        output_metrics: dict[str, MockMlflowMetric] = {}
        for metric in metrics:
            # find the latest metric for each metric name
            if (
                metric.key not in output_metrics
                # use >= here since we append to the list in log_metric and want to make
                # sure we return the most recent metric if they have the same timestamp
                or metric.timestamp >= output_metrics[metric.key].timestamp
            ):
                output_metrics[metric.key] = metric

        # remove step and timestamp information
        for output in output_metrics.keys():
            run.data.metrics[output] = output_metrics[output].value
        return run

    def log_metric(
        self,
        id: str,
        key: str,
        value: float,
        step: Optional[int] = None,
        timestamp: Optional[int] = None,
    ):
        if id not in active_runs:
            active_runs[id] = []
        if timestamp is None:
            timestamp = time.time_ns() // 1000000
        active_runs[id] += [
            MockMlflowMetric(
                key=key,
                value=value,
                step=0 if step is None else step,
                timestamp=timestamp,
            )
        ]

    def get_metric_history(self, run_id: str, key: str):
        return [metric for metric in active_runs[run_id] if metric.key == key]


class MockMlflowRegisteredModel(object):
    def __init__(self, name: str):
        LOGGER.info("Mocking mlflow.entities.model_registry.RegisteredModel class")
        self._name = name

    @property
    def name(self) -> dict:
        LOGGER.info(
            "Mocking mlflow.entities.model_registry.RegisteredModel.name property"
        )
        return self._mame


class MockMlflowRun(object):
    def __init__(
        self,
        id: str,
    ) -> None:
        LOGGER.info("Mocking mlflow.entities.Run class")
        self._id = id
        self.data = MockMlflowRunData()

    @property
    def id(self) -> str:
        LOGGER.info("Mocking mlflow.entities.Run.id getter")
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        LOGGER.info("Mocking mlflow.entities.Run.id setter", value=value)
        self._id = value

    @property
    def data(self) -> MockMlflowRunData:
        LOGGER.info("Mocking mlflow.entities.Run.data getter")
        return self._data

    @data.setter
    def data(self, value: MockMlflowRunData) -> None:
        LOGGER.info("Mocking mlflow.entities.Run.data setter", value=value)
        self._data = value


class MockMlflowRunData(object):
    def __init__(
        self,
    ) -> None:
        LOGGER.info("Mocking mlflow.entities.RunData class")
        self._metrics: dict[str, Any] = {}

    @property
    def metrics(self) -> dict[str, Any]:
        LOGGER.info("Mocking mlflow.entities.RunData.metrics getter")
        return self._metrics

    @metrics.setter
    def metrics(self, value: dict[str, Any]) -> None:
        LOGGER.info("Mocking mlflow.entities.RunData.metrics setter", value=value)
        self._metrics = value


class MockMlflowMetric(object):
    def __init__(
        self,
        key: str,
        value: float,
        step: int,
        timestamp: int,
    ) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric class")
        self._key = key
        self._value = value
        self._step = step
        self._timestamp = timestamp

    @property
    def key(self) -> str:
        LOGGER.info("Mocking mlflow.entities.Metric.key getter")
        return self._key

    @key.setter
    def key(self, value: str) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric.key setter", value=value)
        self._key = value

    @property
    def value(self) -> float:
        LOGGER.info("Mocking mlflow.entities.Metric.value getter")
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric.value setter", value=value)
        self._value = value

    @property
    def step(self) -> int:
        LOGGER.info("Mocking mlflow.entities.Metric.step getter")
        return self._step

    @step.setter
    def step(self, value: int) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric.step setter", value=value)
        self._step = value

    @property
    def timestamp(self) -> int:
        LOGGER.info("Mocking mlflow.entities.Metric.timestamp getter")
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: int) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric.timestamp setter", value=value)
        self._timestamp = value


class MockMlflowException(Exception):
    def __init__(
        self,
        text: str,
    ) -> None:
        LOGGER.info("Mocking mlflow.exceptions.MlflowException class")
        super().__init__(text)
