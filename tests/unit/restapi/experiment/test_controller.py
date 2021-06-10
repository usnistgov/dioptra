# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import datetime
from typing import Any, Dict, List

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.experiment.routes import (
    BASE_ROUTE as EXPERIMENT_BASE_ROUTE,
)
from mitre.securingai.restapi.experiment.service import ExperimentService
from mitre.securingai.restapi.models import Experiment

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def experiment_registration_request() -> Dict[str, Any]:
    return {"name": "mnist"}


def test_experiment_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetall(self, *args, **kwargs) -> List[Experiment]:
        LOGGER.info("Mocking ExperimentService.get_all()")
        experiment: Experiment = Experiment(
            experiment_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="mnist",
        )
        return [experiment]

    monkeypatch.setattr(ExperimentService, "get_all", mockgetall)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{EXPERIMENT_BASE_ROUTE}/"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "experimentId": 1,
                "createdOn": "2020-08-17T18:46:28.717559",
                "lastModified": "2020-08-17T18:46:28.717559",
                "name": "mnist",
            }
        ]

        assert response == expected


@freeze_time("2020-08-17T18:46:28.717559")
def test_experiment_resource_post(
    app: Flask,
    db: SQLAlchemy,
    experiment_registration_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockcreate(*args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.create()")
        timestamp = datetime.datetime.now()
        return Experiment(
            experiment_id=1,
            created_on=timestamp,
            last_modified=timestamp,
            name="mnist",
        )

    monkeypatch.setattr(ExperimentService, "create", mockcreate)

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{EXPERIMENT_BASE_ROUTE}/",
            content_type="multipart/form-data",
            data=experiment_registration_request,
            follow_redirects=True,
        ).get_json()
        LOGGER.info("Response received", response=response)

        expected: Dict[str, Any] = {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist",
        }

        assert response == expected


def test_experiment_id_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyid(self, experiment_id: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.get_by_id()")
        return Experiment(
            experiment_id=experiment_id,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="mnist",
        )

    monkeypatch.setattr(ExperimentService, "get_by_id", mockgetbyid)
    experiment_id: int = 1

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(
            f"/api/{EXPERIMENT_BASE_ROUTE}/{experiment_id}"
        ).get_json()

        expected: Dict[str, Any] = {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist",
        }

        assert response == expected


def test_experiment_name_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyname(self, experiment_name: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.get_by_name()")
        return Experiment(
            experiment_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name=experiment_name,
        )

    monkeypatch.setattr(ExperimentService, "get_by_name", mockgetbyname)
    experiment_name: str = "mnist"

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(
            f"/api/{EXPERIMENT_BASE_ROUTE}/name/{experiment_name}"
        ).get_json()

        expected: Dict[str, Any] = {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist",
        }

        assert response == expected
