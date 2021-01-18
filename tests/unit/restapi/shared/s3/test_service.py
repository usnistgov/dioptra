import datetime
from typing import Any, BinaryIO, Dict

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from botocore.stub import Stubber
from dateutil.tz.tz import tzutc
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.shared.s3.service import S3Service

LOGGER: BoundLogger = structlog.stdlib.get_logger()


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
