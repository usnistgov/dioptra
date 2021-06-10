# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from typing import Any, BinaryIO, Dict

import pytest
import structlog
from flask import Flask
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from mitre.securingai.restapi.models import TaskPlugin, TaskPluginUploadForm
from mitre.securingai.restapi.task_plugin.schema import (
    TaskPluginSchema,
    TaskPluginUploadFormSchema,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def task_plugin_upload_form(
    app: Flask, task_plugin_archive: BinaryIO
) -> TaskPluginUploadForm:
    with app.test_request_context():
        form = TaskPluginUploadForm(
            data={
                "task_plugin_name": "new_plugin_one",
                "collection": "securingai_custom",
                "task_plugin_file": FileStorage(
                    stream=task_plugin_archive,
                    filename="task_plugin_new_package.tar.gz",
                    name="task_plugin_file",
                ),
            }
        )

    return form


@pytest.fixture
def task_plugin_schema() -> TaskPluginSchema:
    return TaskPluginSchema()


@pytest.fixture
def task_plugin_upload_form_schema() -> TaskPluginUploadFormSchema:
    return TaskPluginUploadFormSchema()


def test_TaskPluginSchema_create(
    task_plugin_schema: TaskPluginSchema,
) -> None:
    assert isinstance(task_plugin_schema, TaskPluginSchema)


def test_TaskPluginUploadFormSchema(
    task_plugin_upload_form_schema: TaskPluginUploadFormSchema,
) -> None:
    assert isinstance(task_plugin_upload_form_schema, TaskPluginUploadFormSchema)


def test_TaskPluginSchema_load_works(
    task_plugin_schema: TaskPluginSchema,
) -> None:
    task_plugin: TaskPlugin = task_plugin_schema.load(
        {
            "taskPluginName": "new_plugin_one",
            "collection": "securingai_custom",
            "modules": ["__init__.py", "plugin_module.py"],
        }
    )

    assert task_plugin.task_plugin_name == "new_plugin_one"
    assert task_plugin.collection == "securingai_custom"
    assert task_plugin.modules == ["__init__.py", "plugin_module.py"]


def test_TaskPluginSchema_dump_works(
    task_plugin_schema: TaskPluginSchema,
) -> None:
    task_plugin: TaskPlugin = TaskPlugin(
        task_plugin_name="new_plugin_one",
        collection="securingai_custom",
        modules=["__init__.py", "plugin_module.py"],
    )
    task_plugin_serialized: Dict[str, Any] = task_plugin_schema.dump(task_plugin)

    assert task_plugin_serialized["taskPluginName"] == "new_plugin_one"
    assert task_plugin_serialized["collection"] == "securingai_custom"
    assert task_plugin_serialized["modules"] == ["__init__.py", "plugin_module.py"]


def test_TaskPluginUploadFormSchema_dump_works(
    task_plugin_upload_form: TaskPluginUploadForm,
    task_plugin_upload_form_schema: TaskPluginUploadFormSchema,
    task_plugin_archive: BinaryIO,
) -> None:
    task_plugin_upload_form_serialized: Dict[
        str, Any
    ] = task_plugin_upload_form_schema.dump(task_plugin_upload_form)

    assert task_plugin_upload_form_serialized["task_plugin_name"] == "new_plugin_one"
    assert task_plugin_upload_form_serialized["collection"] == "securingai_custom"
    assert (
        task_plugin_upload_form_serialized["task_plugin_file"].stream
        == task_plugin_archive
    )
    assert (
        task_plugin_upload_form_serialized["task_plugin_file"].filename
        == "task_plugin_new_package.tar.gz"
    )
