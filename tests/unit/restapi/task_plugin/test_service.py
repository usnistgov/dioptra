# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from botocore.stub import Stubber
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.models import TaskPlugin, TaskPluginUploadFormData
from mitre.securingai.restapi.shared.s3.service import S3Service
from mitre.securingai.restapi.task_plugin.service import TaskPluginService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def task_plugin_service(dependency_injector) -> TaskPluginService:
    return dependency_injector.get(TaskPluginService)


@pytest.fixture
def s3_service(dependency_injector) -> S3Service:
    return dependency_injector.get(S3Service)


def test_create(
    s3_service: S3Service,
    task_plugin_service: TaskPluginService,
    task_plugin_upload_form_data: TaskPluginUploadFormData,
    new_task_plugin: TaskPlugin,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    list_objects_v2_expected_params: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "securingai_custom/new_package/",
    }
    uri_list: List[str] = []
    output_dir: Path = tmp_path / "tmpdir"
    output_dir.mkdir()

    def mockenter(*args, **kwargs):
        LOGGER.info("Mocking TemporaryDirectory.__enter__", args=args, kwargs=kwargs)
        return str(output_dir)

    def mockexit(*args, **kwargs):
        LOGGER.info("Mocking TemporaryDirectory.__exit__", args=args, kwargs=kwargs)
        return None

    def mockuploadfile(*args, **kwargs) -> None:
        LOGGER.info("Mocking client.upload_file() function", args=args, kwargs=kwargs)
        uri_list.append(
            S3Service.as_uri(bucket=kwargs.get("Bucket"), key=kwargs.get("Key"))
        )

    with Stubber(s3_service._client) as stubber, monkeypatch.context() as m:
        m.setattr(TemporaryDirectory, "__enter__", mockenter)
        m.setattr(TemporaryDirectory, "__exit__", mockexit)
        m.setattr(s3_service._client, "upload_file", mockuploadfile)
        stubber.add_response(
            "list_objects_v2",
            dict(Name="plugins", Prefix="securingai_custom/new_package"),
            list_objects_v2_expected_params,
        )
        response_task_plugin: TaskPlugin = task_plugin_service.create(
            task_plugin_upload_form_data=task_plugin_upload_form_data, bucket="plugins"
        )
        stubber.assert_no_pending_responses()

    assert new_task_plugin == response_task_plugin
    assert len(uri_list) == 2


def test_delete_prefix(
    s3_service: S3Service,
    task_plugin_service: TaskPluginService,
    list_objects_v2_custom_new_plugin_one: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockdeleteprefix(*args, **kwargs) -> Dict[str, Any]:
        LOGGER.info(
            "Mocking client.delete_objects() function", args=args, kwargs=kwargs
        )
        return dict(Deleted=kwargs.get("Delete", {}).get("Objects"))

    list_objects_v2_expected_params1: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "securingai_custom/new_plugin_one/",
    }

    list_objects_v2_expected_params2: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "securingai_custom/new_plugin_one",
    }

    with Stubber(s3_service._client) as stubber, monkeypatch.context() as m:
        m.setattr(s3_service._client, "delete_objects", mockdeleteprefix)
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_custom_new_plugin_one,
            list_objects_v2_expected_params1,
        )
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_custom_new_plugin_one,
            list_objects_v2_expected_params2,
        )
        response: List[TaskPlugin] = task_plugin_service.delete(
            collection="securingai_custom",
            task_plugin_name="new_plugin_one",
            bucket="plugins",
        )
        stubber.assert_no_pending_responses()

    expected_response: List[TaskPlugin] = [
        TaskPlugin(
            "new_plugin_one", "securingai_custom", ["__init__.py", "plugin_one.py"]
        )
    ]
    assert response == expected_response


def test_get_all(
    s3_service: S3Service,
    task_plugin_service: TaskPluginService,
    list_objects_v2_collections: Dict[str, Any],
    list_objects_v2_builtins: Dict[str, Any],
    list_objects_v2_custom: Dict[str, Any],
    list_objects_v2_builtins_artifacts: Dict[str, Any],
    list_objects_v2_builtins_attacks: Dict[str, Any],
    list_objects_v2_custom_new_plugin_one: Dict[str, Any],
    list_objects_v2_custom_new_plugin_two: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    list_objects_v2_expected_params1: Dict[str, Any] = {
        "Bucket": "plugins",
        "Delimiter": "/",
        "Prefix": "/",
    }
    list_objects_v2_expected_params2: Dict[str, Any] = {
        "Bucket": "plugins",
        "Delimiter": "/",
        "Prefix": "securingai_builtins/",
    }
    list_objects_v2_expected_params3: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "securingai_builtins/artifacts/",
    }
    list_objects_v2_expected_params4: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "securingai_builtins/attacks/",
    }
    list_objects_v2_expected_params5: Dict[str, Any] = {
        "Bucket": "plugins",
        "Delimiter": "/",
        "Prefix": "securingai_custom/",
    }
    list_objects_v2_expected_params6: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "securingai_custom/new_plugin_one/",
    }
    list_objects_v2_expected_params7: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "securingai_custom/new_plugin_two/",
    }

    with Stubber(s3_service._client) as stubber:
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_collections,
            list_objects_v2_expected_params1,
        )
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_builtins,
            list_objects_v2_expected_params2,
        )
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_builtins_artifacts,
            list_objects_v2_expected_params3,
        )
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_builtins_attacks,
            list_objects_v2_expected_params4,
        )
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_custom,
            list_objects_v2_expected_params5,
        )
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_custom_new_plugin_one,
            list_objects_v2_expected_params6,
        )
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_custom_new_plugin_two,
            list_objects_v2_expected_params7,
        )
        response_task_plugin: List[TaskPlugin] = task_plugin_service.get_all(
            bucket="plugins"
        )
        stubber.assert_no_pending_responses()

    expected_response: List[TaskPlugin] = [
        TaskPlugin("artifacts", "securingai_builtins", ["__init__.py", "mlflow.py"]),
        TaskPlugin("attacks", "securingai_builtins", ["__init__.py", "fgm.py"]),
        TaskPlugin(
            "new_plugin_one", "securingai_custom", ["__init__.py", "plugin_one.py"]
        ),
        TaskPlugin(
            "new_plugin_two", "securingai_custom", ["__init__.py", "plugin_two.py"]
        ),
    ]

    assert response_task_plugin == expected_response
