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
from pathlib import Path
from typing import Any, BinaryIO, Dict, List

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from botocore.stub import Stubber
from dateutil.tz.tz import tzlocal, tzutc
from structlog.stdlib import BoundLogger

from dioptra.restapi.v0.shared.s3.service import S3Service

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def list_objects_v2_plugin_artifacts_response() -> Dict[str, Any]:
    return {
        "ResponseMetadata": {
            "RequestId": "167A72C9F1046510",
            "HostId": "",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "accept-ranges": "bytes",
                "content-length": "1736",
                "content-security-policy": "block-all-mixed-content",
                "content-type": "application/xml",
                "server": "MinIO",
                "vary": "Origin",
                "x-amz-request-id": "167A72C9F1046510",
                "x-xss-protection": "1; mode=block",
                "date": "Thu, 29 Apr 2021 21:53:47 GMT",
            },
            "RetryAttempts": 0,
        },
        "IsTruncated": False,
        "Contents": [
            {
                "Key": "dioptra_custom/artifacts/__init__.py",
                "LastModified": datetime.datetime(
                    2021, 4, 26, 21, 2, 18, 688000, tzinfo=tzlocal()
                ),
                "ETag": '"2fe369e96fea5d62a27f273c96fc3cab"',
                "Size": 85,
                "StorageClass": "STANDARD",
                "Owner": {
                    "DisplayName": "minio",
                    "ID": "02d6176db174dc93cb1b899f7c6078f08654445fe8cf1b6ce98d8855"
                    "f66bdbf4",
                },
            },
            {
                "Key": "dioptra_custom/artifacts/exceptions.py",
                "LastModified": datetime.datetime(
                    2021, 4, 26, 21, 2, 18, 809000, tzinfo=tzlocal()
                ),
                "ETag": '"b75bac005df1346cf9dba3d54adba6cc"',
                "Size": 280,
                "StorageClass": "STANDARD",
                "Owner": {
                    "DisplayName": "minio",
                    "ID": "02d6176db174dc93cb1b899f7c6078f08654445fe8cf1b6ce98d8855"
                    "f66bdbf4",
                },
            },
            {
                "Key": "dioptra_custom/artifacts/mlflow.py",
                "LastModified": datetime.datetime(
                    2021, 4, 26, 21, 2, 18, 818000, tzinfo=tzlocal()
                ),
                "ETag": '"476b2cd34ea5c5631eb1eab0ad969beb"',
                "Size": 7552,
                "StorageClass": "STANDARD",
                "Owner": {
                    "DisplayName": "minio",
                    "ID": "02d6176db174dc93cb1b899f7c6078f08654445fe8cf1b6ce98d8855"
                    "f66bdbf4",
                },
            },
            {
                "Key": "dioptra_custom/artifacts/utils.py",
                "LastModified": datetime.datetime(
                    2021, 4, 26, 21, 2, 18, 810000, tzinfo=tzlocal()
                ),
                "ETag": '"94760357c1c79c69b11b709e90aa6e5e"',
                "Size": 1436,
                "StorageClass": "STANDARD",
                "Owner": {
                    "DisplayName": "minio",
                    "ID": "02d6176db174dc93cb1b899f7c6078f08654445fe8cf1b6ce98d8855"
                    "f66bdbf4",
                },
            },
        ],
        "Name": "plugins",
        "Prefix": "dioptra_custom/artifacts",
        "Delimiter": "",
        "MaxKeys": 4500,
        "EncodingType": "url",
        "KeyCount": 4,
    }


@pytest.fixture
def list_objects_v2_common_prefix_response() -> Dict[str, Any]:
    return {
        "ResponseMetadata": {
            "RequestId": "167A6835FF3B9793",
            "HostId": "",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "accept-ranges": "bytes",
                "content-length": "1027",
                "content-security-policy": "block-all-mixed-content",
                "content-type": "application/xml",
                "server": "MinIO",
                "vary": "Origin",
                "x-amz-request-id": "167A6835FF3B9793",
                "x-xss-protection": "1; mode=block",
                "date": "Thu, 29 Apr 2021 18:39:57 GMT",
            },
            "RetryAttempts": 0,
        },
        "IsTruncated": False,
        "Name": "plugins",
        "Prefix": "dioptra_builtins/",
        "Delimiter": "/",
        "MaxKeys": 4500,
        "CommonPrefixes": [
            {"Prefix": "dioptra_builtins/artifacts/"},
            {"Prefix": "dioptra_builtins/attacks/"},
            {"Prefix": "dioptra_builtins/backend_configs/"},
            {"Prefix": "dioptra_builtins/data/"},
            {"Prefix": "dioptra_builtins/estimators/"},
            {"Prefix": "dioptra_builtins/metrics/"},
            {"Prefix": "dioptra_builtins/random/"},
            {"Prefix": "dioptra_builtins/registry/"},
            {"Prefix": "dioptra_builtins/tracking/"},
        ],
        "EncodingType": "url",
        "KeyCount": 9,
    }


@pytest.fixture
def list_objects_v2_response() -> Dict[str, Any]:
    return {
        "ResponseMetadata": {
            "RequestId": "16315C630D1850D8",
            "HostId": "",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "accept-ranges": "bytes",
                "content-length": "555",
                "content-security-policy": "block-all-mixed-content",
                "content-type": "application/xml",
                "server": "MinIO/RELEASE.2020-09-02T18-19-50Z",
                "vary": "Origin",
                "x-amz-request-id": "16315C630D1850D8",
                "x-xss-protection": "1; mode=block",
                "date": "Thu, 03 Sep 2020 19:22:03 GMT",
            },
            "RetryAttempts": 0,
        },
        "IsTruncated": False,
        "Contents": [
            {
                "Key": "workflows.tar.gz",
                "LastModified": datetime.datetime(
                    2020, 9, 3, 17, 3, 4, 616000, tzinfo=tzutc()
                ),
                "ETag": '"266b055dd65b80e8f12c794d167ba0f1"',
                "Size": 7593,
                "StorageClass": "STANDARD",
                "Owner": {"DisplayName": "", "ID": ""},
            }
        ],
        "Name": "workflow",
        "Prefix": "",
        "Delimiter": "",
        "MaxKeys": 1000,
        "EncodingType": "url",
        "KeyCount": 1,
    }


@pytest.fixture
def s3_service(dependency_injector) -> S3Service:
    return dependency_injector.get(S3Service)


def test_list_directories(
    s3_service: S3Service,
    list_objects_v2_common_prefix_response: Dict[str, Any],
) -> None:
    list_objects_v2_expected_params: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "dioptra_builtins/",
        "Delimiter": "/",
    }
    expected_response: List[str] = [
        "artifacts",
        "attacks",
        "backend_configs",
        "data",
        "estimators",
        "metrics",
        "random",
        "registry",
        "tracking",
    ]

    with Stubber(s3_service._client) as stubber:
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_common_prefix_response,
            list_objects_v2_expected_params,
        )
        service_response: List[str] = s3_service.list_directories(
            bucket="plugins", prefix="dioptra_builtins/"
        )
        stubber.assert_no_pending_responses()

    assert set(service_response) == set(expected_response)


def test_list_objects(
    s3_service: S3Service,
    list_objects_v2_plugin_artifacts_response: Dict[str, Any],
) -> None:
    list_objects_v2_expected_params: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "dioptra_custom/",
    }
    expected_response: List[str] = [
        "dioptra_custom/artifacts/__init__.py",
        "dioptra_custom/artifacts/exceptions.py",
        "dioptra_custom/artifacts/mlflow.py",
        "dioptra_custom/artifacts/utils.py",
    ]

    with Stubber(s3_service._client) as stubber:
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_plugin_artifacts_response,
            list_objects_v2_expected_params,
        )
        service_response: List[str] = s3_service.list_objects(
            bucket="plugins", prefix="dioptra_custom/"
        )
        stubber.assert_no_pending_responses()

    assert set(service_response) == set(expected_response)


def test_upload(
    s3_service: S3Service,
    workflow_tar_gz: BinaryIO,
    list_objects_v2_response: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockuploadfileobj(*args, **kwargs) -> str:
        LOGGER.info(
            "Mocking client.upload_fileobj() function", args=args, kwargs=kwargs
        )
        assert kwargs.get("Fileobj") == workflow_tar_gz
        uri: str = S3Service.as_uri(bucket=kwargs.get("Bucket"), key=kwargs.get("Key"))
        return uri

    list_objects_v2_expected_params = {"Bucket": "workflow"}

    with monkeypatch.context() as m:
        m.setattr(s3_service._client, "upload_fileobj", mockuploadfileobj)
        service_response = s3_service.upload(
            fileobj=workflow_tar_gz, bucket="workflow", key="workflows.tar.gz"
        )

    with Stubber(s3_service._client) as stubber:
        stubber.add_response(
            "list_objects_v2", list_objects_v2_response, list_objects_v2_expected_params
        )
        list_objects_v2_service_response = s3_service._client.list_objects_v2(
            Bucket="workflow"
        )
        stubber.assert_no_pending_responses()

    assert service_response == "s3://workflow/workflows.tar.gz"
    assert list_objects_v2_service_response == list_objects_v2_response


def test_upload_directory(
    s3_service: S3Service,
    task_plugins_dir: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    uri_list: List[str] = []
    data_json_uri: str = S3Service.as_uri(
        bucket="plugins", key="dioptra_custom/models/data.json"
    )

    def mockuploadfile(*args, **kwargs) -> None:
        LOGGER.info("Mocking client.upload_file() function", args=args, kwargs=kwargs)
        uri_list.append(
            S3Service.as_uri(bucket=kwargs.get("Bucket"), key=kwargs.get("Key"))
        )

    with monkeypatch.context() as m:
        m.setattr(s3_service._client, "upload_file", mockuploadfile)
        service_response: List[str] = s3_service.upload_directory(
            directory=task_plugins_dir,
            bucket="plugins",
            prefix="dioptra_custom",
            include_suffixes=[".py"],
        )

    assert set(service_response) == set(uri_list)
    assert data_json_uri not in set(service_response)


def test_delete_prefix(
    s3_service: S3Service,
    list_objects_v2_plugin_artifacts_response: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockdeleteprefix(*args, **kwargs) -> Dict[str, Any]:
        LOGGER.info(
            "Mocking client.delete_objects() function", args=args, kwargs=kwargs
        )
        return dict(Deleted=kwargs.get("Delete", {}).get("Objects"))

    list_objects_v2_expected_params: Dict[str, Any] = {
        "Bucket": "plugins",
        "Prefix": "dioptra_custom/artifacts",
    }
    expected_response: List[str] = [
        "dioptra_custom/artifacts/__init__.py",
        "dioptra_custom/artifacts/exceptions.py",
        "dioptra_custom/artifacts/mlflow.py",
        "dioptra_custom/artifacts/utils.py",
    ]

    with Stubber(s3_service._client) as stubber, monkeypatch.context() as m:
        m.setattr(s3_service._client, "delete_objects", mockdeleteprefix)
        stubber.add_response(
            "list_objects_v2",
            list_objects_v2_plugin_artifacts_response,
            list_objects_v2_expected_params,
        )
        service_response: List[str] = s3_service.delete_prefix(
            bucket="plugins",
            prefix="dioptra_custom/artifacts",
        )
        stubber.assert_no_pending_responses()

    assert set(service_response) == set(expected_response)


def test_normalize_prefix(s3_service: S3Service) -> None:
    assert s3_service.normalize_prefix(prefix="/") == "/"
    assert (
        s3_service.normalize_prefix(prefix="///dioptra_builtins") == "dioptra_builtins/"
    )
    assert s3_service.normalize_prefix(prefix="dioptra_builtins") == "dioptra_builtins/"
    assert (
        s3_service.normalize_prefix(prefix="dioptra_builtins/") == "dioptra_builtins/"
    )
    assert (
        s3_service.normalize_prefix(prefix="dioptra_builtins//") == "dioptra_builtins/"
    )
