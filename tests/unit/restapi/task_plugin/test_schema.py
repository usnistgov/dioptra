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
