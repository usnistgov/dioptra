# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from typing import Any, BinaryIO, Dict, List

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.models import TaskPlugin
from mitre.securingai.restapi.shared.s3.service import S3Service
from mitre.securingai.restapi.task_plugin.routes import (
    BASE_ROUTE as TASK_PLUGIN_BASE_ROUTE,
)
from mitre.securingai.restapi.task_plugin.service import TaskPluginService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def task_plugin_upload_form_request(task_plugin_archive: BinaryIO) -> Dict[str, Any]:
    return {
        "task_plugin_name": "new_plugin_one",
        "collection": "securingai_custom",
        "task_plugin_file": (task_plugin_archive, "task_plugin_new_package.tar.gz"),
    }


def test_task_plugin_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetall(self, *args, **kwargs) -> List[TaskPlugin]:
        LOGGER.info("Mocking TaskPluginService.get_all()")
        return [
            TaskPlugin(
                "artifacts", "securingai_builtins", ["__init__.py", "mlflow.py"]
            ),
            TaskPlugin("attacks", "securingai_builtins", ["__init__.py", "fgm.py"]),
            TaskPlugin(
                "new_plugin_one", "securingai_custom", ["__init__.py", "plugin_one.py"]
            ),
            TaskPlugin(
                "new_plugin_two", "securingai_custom", ["__init__.py", "plugin_two.py"]
            ),
        ]

    monkeypatch.setattr(TaskPluginService, "get_all", mockgetall)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "taskPluginName": "artifacts",
                "collection": "securingai_builtins",
                "modules": ["__init__.py", "mlflow.py"],
            },
            {
                "taskPluginName": "attacks",
                "collection": "securingai_builtins",
                "modules": ["__init__.py", "fgm.py"],
            },
            {
                "taskPluginName": "new_plugin_one",
                "collection": "securingai_custom",
                "modules": ["__init__.py", "plugin_one.py"],
            },
            {
                "taskPluginName": "new_plugin_two",
                "collection": "securingai_custom",
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
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/",
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
