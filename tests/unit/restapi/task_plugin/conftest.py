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
