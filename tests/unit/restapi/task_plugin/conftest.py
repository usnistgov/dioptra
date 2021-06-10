# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from typing import Any, BinaryIO, Dict

import pytest
from flask import Flask
from werkzeug.datastructures import FileStorage

from mitre.securingai.restapi.models import (
    TaskPlugin,
    TaskPluginUploadForm,
    TaskPluginUploadFormData,
)
from mitre.securingai.restapi.task_plugin.interface import TaskPluginInterface


@pytest.fixture
def new_task_plugin() -> TaskPlugin:
    return TaskPlugin(
        collection="securingai_custom",
        task_plugin_name="new_package",
        modules=["__init__.py", "plugin_module.py"],
    )


@pytest.fixture
def new_task_plugin_interface() -> TaskPluginInterface:
    return TaskPluginInterface(
        collection="securingai_custom",
        task_plugin_name="new_package",
        modules=["__init__.py", "plugin_module.py"],
    )


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
def task_plugin_upload_form_data(
    app: Flask, task_plugin_archive: BinaryIO
) -> TaskPluginUploadFormData:
    return TaskPluginUploadFormData(
        task_plugin_name="new_package",
        collection="securingai_custom",
        task_plugin_file=FileStorage(
            stream=task_plugin_archive,
            filename="task_plugin_new_package.tar.gz",
            name="task_plugin_file",
        ),
    )


@pytest.fixture
def list_objects_v2_collections() -> Dict[str, Any]:
    return {
        "IsTruncated": False,
        "Name": "plugins",
        "Prefix": "/",
        "Delimiter": "/",
        "MaxKeys": 4500,
        "CommonPrefixes": [
            {"Prefix": "securingai_builtins/"},
            {"Prefix": "securingai_custom/"},
        ],
        "EncodingType": "url",
        "KeyCount": 2,
    }


@pytest.fixture
def list_objects_v2_builtins() -> Dict[str, Any]:
    return {
        "IsTruncated": False,
        "Name": "plugins",
        "Prefix": "securingai_builtins/",
        "Delimiter": "/",
        "MaxKeys": 4500,
        "CommonPrefixes": [
            {"Prefix": "securingai_builtins/artifacts/"},
            {"Prefix": "securingai_builtins/attacks/"},
        ],
        "EncodingType": "url",
        "KeyCount": 2,
    }


@pytest.fixture
def list_objects_v2_custom() -> Dict[str, Any]:
    return {
        "IsTruncated": False,
        "Name": "plugins",
        "Prefix": "securingai_custom/",
        "Delimiter": "/",
        "MaxKeys": 4500,
        "CommonPrefixes": [
            {"Prefix": "securingai_custom/new_plugin_one/"},
            {"Prefix": "securingai_custom/new_plugin_two/"},
        ],
        "EncodingType": "url",
        "KeyCount": 2,
    }


@pytest.fixture
def list_objects_v2_builtins_artifacts() -> Dict[str, Any]:
    return {
        "Contents": [
            {"Key": "securingai_builtins/artifacts/__init__.py"},
            {"Key": "securingai_builtins/artifacts/mlflow.py"},
        ],
        "Name": "plugins",
        "Prefix": "securingai_builtins/artifacts",
        "Delimiter": "",
        "MaxKeys": 1000,
        "EncodingType": "url",
        "KeyCount": 2,
    }


@pytest.fixture
def list_objects_v2_builtins_attacks() -> Dict[str, Any]:
    return {
        "Contents": [
            {"Key": "securingai_builtins/attacks/__init__.py"},
            {"Key": "securingai_builtins/attacks/fgm.py"},
        ],
        "Name": "plugins",
        "Prefix": "securingai_builtins/attacks",
        "Delimiter": "",
        "MaxKeys": 1000,
        "EncodingType": "url",
        "KeyCount": 2,
    }


@pytest.fixture
def list_objects_v2_custom_new_plugin_one() -> Dict[str, Any]:
    return {
        "Contents": [
            {"Key": "securingai_custom/new_plugin_one/__init__.py"},
            {"Key": "securingai_custom/new_plugin_one/plugin_one.py"},
        ],
        "Name": "plugins",
        "Prefix": "securingai_custom/new_plugin_one",
        "Delimiter": "",
        "MaxKeys": 1000,
        "EncodingType": "url",
        "KeyCount": 2,
    }


@pytest.fixture
def list_objects_v2_custom_new_plugin_two() -> Dict[str, Any]:
    return {
        "Contents": [
            {"Key": "securingai_custom/new_plugin_two/__init__.py"},
            {"Key": "securingai_custom/new_plugin_two/plugin_two.py"},
        ],
        "Name": "plugins",
        "Prefix": "securingai_custom/new_plugin_two",
        "Delimiter": "",
        "MaxKeys": 1000,
        "EncodingType": "url",
        "KeyCount": 2,
    }
