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
import datetime
from typing import Any, Dict, List

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.models import Queue
from mitre.securingai.restapi.queue.routes import BASE_ROUTE as QUEUE_BASE_ROUTE
from mitre.securingai.restapi.queue.service import QueueService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def queue_registration_request() -> Dict[str, Any]:
    return {"name": "tensorflow_cpu"}


def test_queue_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetallunlocked(self, *args, **kwargs) -> List[Queue]:
        LOGGER.info("Mocking QueueService.get_all_unlocked()")
        queue: Queue = Queue(
            queue_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="tensorflow_cpu",
        )
        return [queue]

    monkeypatch.setattr(QueueService, "get_all_unlocked", mockgetallunlocked)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{QUEUE_BASE_ROUTE}/"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "queueId": 1,
                "createdOn": "2020-08-17T18:46:28.717559",
                "lastModified": "2020-08-17T18:46:28.717559",
                "name": "tensorflow_cpu",
            }
        ]

        assert response == expected


@freeze_time("2020-08-17T18:46:28.717559")
def test_queue_resource_post(
    app: Flask,
    db: SQLAlchemy,
    queue_registration_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockcreate(*args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.create()")
        timestamp = datetime.datetime.now()
        return Queue(
            queue_id=1,
            created_on=timestamp,
            last_modified=timestamp,
            name="tensorflow_cpu",
        )

    monkeypatch.setattr(QueueService, "create", mockcreate)

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{QUEUE_BASE_ROUTE}/",
            content_type="multipart/form-data",
            data=queue_registration_request,
            follow_redirects=True,
        ).get_json()
        LOGGER.info("Response received", response=response)

        expected: Dict[str, Any] = {
            "queueId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "tensorflow_cpu",
        }

        assert response == expected


def test_queue_id_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyid(self, queue_id: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_id()")
        return Queue(
            queue_id=queue_id,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="tensorflow_cpu",
        )

    monkeypatch.setattr(QueueService, "get_by_id", mockgetbyid)
    queue_id: int = 1

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(
            f"/api/{QUEUE_BASE_ROUTE}/{queue_id}"
        ).get_json()

        expected: Dict[str, Any] = {
            "queueId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "tensorflow_cpu",
        }

        assert response == expected


def test_queue_id_resource_put(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyid(self, queue_id: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_id()")
        return Queue(
            queue_id=queue_id,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="tensorflow_cpu",
        )

    def mockrenamequeue(self, queue: Queue, new_name: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.rename_queue()", new_name=new_name)
        queue.name = new_name
        queue.last_modified = datetime.datetime(2020, 8, 17, 20, 0, 0, 0)
        return queue

    monkeypatch.setattr(QueueService, "get_by_id", mockgetbyid)
    monkeypatch.setattr(QueueService, "rename_queue", mockrenamequeue)
    queue_id: int = 1
    payload: Dict[str, Any] = {"name": "tf_cpu"}

    with app.test_client() as client:
        response: Dict[str, Any] = client.put(
            f"/api/{QUEUE_BASE_ROUTE}/{queue_id}",
            json=payload,
        ).get_json()

        expected: Dict[str, Any] = {
            "queueId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T20:00:00",
            "name": "tf_cpu",
        }

        assert response == expected


def test_queue_id_resource_delete(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockdeletequeue(self, queue_id: int, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking QueueService.delete_queue()")
        return [queue_id]

    monkeypatch.setattr(QueueService, "delete_queue", mockdeletequeue)
    queue_id: int = 1

    with app.test_client() as client:
        response: Dict[str, Any] = client.delete(
            f"/api/{QUEUE_BASE_ROUTE}/{queue_id}"
        ).get_json()

        expected: Dict[str, Any] = {
            "status": "Success",
            "id": [1],
        }

        assert response == expected


def test_queue_id_lock_resource_delete(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyid(self, queue_id: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_id()")
        return Queue(
            queue_id=queue_id,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="tensorflow_cpu",
        )

    def mockunlockqueue(self, queue: Queue, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking QueueService.unlock_queue()")
        return [queue.queue_id]

    monkeypatch.setattr(QueueService, "get_by_id", mockgetbyid)
    monkeypatch.setattr(QueueService, "unlock_queue", mockunlockqueue)
    queue_id: int = 1

    with app.test_client() as client:
        response: Dict[str, Any] = client.delete(
            f"/api/{QUEUE_BASE_ROUTE}/{queue_id}/lock"
        ).get_json()

        expected: Dict[str, Any] = {
            "status": "Success",
            "id": [1],
        }

        assert response == expected


def test_queue_id_lock_resource_put(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyid(self, queue_id: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_id()")
        return Queue(
            queue_id=queue_id,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="tensorflow_cpu",
        )

    def mocklockqueue(self, queue: Queue, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking QueueService.lock_queue()")
        return [queue.queue_id]

    monkeypatch.setattr(QueueService, "get_by_id", mockgetbyid)
    monkeypatch.setattr(QueueService, "lock_queue", mocklockqueue)
    queue_id: int = 1

    with app.test_client() as client:
        response: Dict[str, Any] = client.put(
            f"/api/{QUEUE_BASE_ROUTE}/{queue_id}/lock"
        ).get_json()

        expected: Dict[str, Any] = {
            "status": "Success",
            "id": [1],
        }

        assert response == expected


def test_queue_name_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyname(self, queue_name: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_name()")
        return Queue(
            queue_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name=queue_name,
        )

    monkeypatch.setattr(QueueService, "get_by_name", mockgetbyname)
    queue_name: str = "tensorflow_cpu"

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(
            f"/api/{QUEUE_BASE_ROUTE}/name/{queue_name}"
        ).get_json()

        expected: Dict[str, Any] = {
            "queueId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "tensorflow_cpu",
        }

        assert response == expected


def test_queue_name_resource_put(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyname(self, queue_name: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_name()")
        return Queue(
            queue_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name=queue_name,
        )

    def mockrenamequeue(self, queue: Queue, new_name: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.rename_queue()", new_name=new_name)
        queue.name = new_name
        queue.last_modified = datetime.datetime(2020, 8, 17, 20, 0, 0, 0)
        return queue

    monkeypatch.setattr(QueueService, "get_by_name", mockgetbyname)
    monkeypatch.setattr(QueueService, "rename_queue", mockrenamequeue)
    queue_name: str = "tensorflow_cpu"
    payload: Dict[str, Any] = {"name": "tf_cpu"}

    with app.test_client() as client:
        response: Dict[str, Any] = client.put(
            f"/api/{QUEUE_BASE_ROUTE}/name/{queue_name}",
            json=payload,
        ).get_json()

        expected: Dict[str, Any] = {
            "queueId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T20:00:00",
            "name": "tf_cpu",
        }

        assert response == expected


def test_queue_name_resource_delete(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyname(self, queue_name: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_name()")
        return Queue(
            queue_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name=queue_name,
        )

    def mockdeletequeue(self, queue_id: int, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking QueueService.delete_queue()")
        return [queue_id]

    monkeypatch.setattr(QueueService, "get_by_name", mockgetbyname)
    monkeypatch.setattr(QueueService, "delete_queue", mockdeletequeue)
    queue_name: str = "tensorflow_cpu"

    with app.test_client() as client:
        response: Dict[str, Any] = client.delete(
            f"/api/{QUEUE_BASE_ROUTE}/name/{queue_name}"
        ).get_json()

        expected: Dict[str, Any] = {
            "status": "Success",
            "id": [1],
        }

        assert response == expected


def test_queue_name_lock_resource_delete(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyname(self, queue_name: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_name()")
        return Queue(
            queue_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name=queue_name,
        )

    def mockunlockqueue(self, queue: Queue, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking QueueService.unlock_queue()")
        return [queue.queue_id]

    monkeypatch.setattr(QueueService, "get_by_name", mockgetbyname)
    monkeypatch.setattr(QueueService, "unlock_queue", mockunlockqueue)
    queue_name: str = "tensorflow_cpu"

    with app.test_client() as client:
        response: Dict[str, Any] = client.delete(
            f"/api/{QUEUE_BASE_ROUTE}/name/{queue_name}/lock"
        ).get_json()

        expected: Dict[str, Any] = {
            "status": "Success",
            "name": [queue_name],
        }

        assert response == expected


def test_queue_name_lock_resource_put(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyname(self, queue_name: str, *args, **kwargs) -> Queue:
        LOGGER.info("Mocking QueueService.get_by_name()")
        return Queue(
            queue_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name=queue_name,
        )

    def mocklockqueue(self, queue: Queue, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking QueueService.lock_queue()")
        return [queue.queue_id]

    monkeypatch.setattr(QueueService, "get_by_name", mockgetbyname)
    monkeypatch.setattr(QueueService, "lock_queue", mocklockqueue)
    queue_name: str = "tensorflow_cpu"

    with app.test_client() as client:
        response: Dict[str, Any] = client.put(
            f"/api/{QUEUE_BASE_ROUTE}/name/{queue_name}/lock"
        ).get_json()

        expected: Dict[str, Any] = {
            "status": "Success",
            "name": [queue_name],
        }

        assert response == expected
