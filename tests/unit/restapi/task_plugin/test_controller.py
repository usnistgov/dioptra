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

from typing import Any, BinaryIO, Dict, List

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from structlog.stdlib import BoundLogger

from dioptra.restapi.routes import TASK_PLUGIN_ROUTE
from dioptra.restapi.shared.s3.service import S3Service
from dioptra.restapi.task_plugin.model import TaskPlugin
from dioptra.restapi.task_plugin.service import TaskPluginService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def task_plugin_upload_form_request(task_plugin_archive: BinaryIO) -> Dict[str, Any]:
    return {
        "taskPluginName": "new_plugin_one",
        "collection": "dioptra_custom",
        "taskPluginFile": (task_plugin_archive, "task_plugin_new_package.tar.gz"),
    }


def test_task_plugin_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetall(self, *args, **kwargs) -> List[TaskPlugin]:
        LOGGER.info("Mocking TaskPluginService.get_all()")
        return [
            TaskPlugin("artifacts", "dioptra_builtins", ["__init__.py", "mlflow.py"]),
            TaskPlugin("attacks", "dioptra_builtins", ["__init__.py", "fgm.py"]),
            TaskPlugin(
                "new_plugin_one", "dioptra_custom", ["__init__.py", "plugin_one.py"]
            ),
            TaskPlugin(
                "new_plugin_two", "dioptra_custom", ["__init__.py", "plugin_two.py"]
            ),
        ]

    monkeypatch.setattr(TaskPluginService, "get_all", mockgetall)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{TASK_PLUGIN_ROUTE}/"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "taskPluginName": "artifacts",
                "collection": "dioptra_builtins",
                "modules": ["__init__.py", "mlflow.py"],
            },
            {
                "taskPluginName": "attacks",
                "collection": "dioptra_builtins",
                "modules": ["__init__.py", "fgm.py"],
            },
            {
                "taskPluginName": "new_plugin_one",
                "collection": "dioptra_custom",
                "modules": ["__init__.py", "plugin_one.py"],
            },
            {
                "taskPluginName": "new_plugin_two",
                "collection": "dioptra_custom",
                "modules": ["__init__.py", "plugin_two.py"],
            },
        ]

        assert response == expected


def test_task_plugin_resource_post(
    app: Flask,
    task_plugin_upload_form_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockcreate(*args, **kwargs) -> TaskPlugin:
        LOGGER.info("Mocking TaskPluginService.create()")
        return TaskPlugin(
            task_plugin_name="new_plugin_one",
            collection="custom",
            modules=["__init__.py", "plugin_module.py"],
        )

    def mockupload(fileobj, bucket, key, *args, **kwargs):
        LOGGER.info(
            "Mocking S3Service.upload()", fileobj=fileobj, bucket=bucket, key=key
        )
        return S3Service.as_uri(bucket=bucket, key=key)

    monkeypatch.setattr(TaskPluginService, "create", mockcreate)
    monkeypatch.setattr(S3Service, "upload", mockupload)

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{TASK_PLUGIN_ROUTE}/",
            content_type="multipart/form-data",
            data=task_plugin_upload_form_request,
            follow_redirects=True,
        ).get_json()
        LOGGER.info("Response received", response=response)

        expected: Dict[str, Any] = {
            "taskPluginName": "new_plugin_one",
            "collection": "custom",
            "modules": ["__init__.py", "plugin_module.py"],
        }

        assert response == expected
