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
import io
from typing import Iterator

import boto3
import botocore.stub
import pytest
from botocore.client import BaseClient


def _add_workflow_stubs(stubber: botocore.stub.Stubber) -> dict[str, dict[str, bytes]]:
    # No key listing mockup here: worker doesn't have permission to list keys
    # in the workflow bucket!

    # Mock head response
    head_object_response = {"ContentType": "binary/octet-stream", "ContentLength": 3}

    # Mock file download responses
    workflow_content = b"\x0d\x0e\x0f"
    workflow_content_stream = io.BytesIO(workflow_content)
    workflow_get_object_response = {"Body": workflow_content_stream}

    stubber.add_response(
        "head_object",
        head_object_response,
        {
            "Bucket": "workflow",
            "Key": "0ca807595bb4424c8dcc47a50a81f399/workflow.tar.gz",
        },
    )

    stubber.add_response(
        "get_object",
        workflow_get_object_response,
        {
            "Bucket": "workflow",
            "Key": "0ca807595bb4424c8dcc47a50a81f399/workflow.tar.gz",
        },
    )

    bucket_info = {
        "workflow": {
            "0ca807595bb4424c8dcc47a50a81f399/workflow.tar.gz": workflow_content
        }
    }

    return bucket_info


def _add_plugins_stubs(stubber: botocore.stub.Stubber) -> dict[str, dict[str, bytes]]:
    # Mock key listing responses
    # Split the builtins plugins listing into two pages, to test paging.
    builtins_keys_response_trunc = {
        "IsTruncated": True,
        "Contents": [{"Key": "dioptra_builtins/file1.dat"}],
        "NextContinuationToken": "next",
    }

    builtins_keys_response_cont = {
        "IsTruncated": False,
        "Contents": [{"Key": "dioptra_builtins/file2.dat"}],
    }

    custom_keys_response = {
        "IsTruncated": False,
        "Contents": [
            {"Key": "dioptra_custom/file3.dat"},
            {"Key": "dioptra_custom/file4.dat"},
        ],
    }

    # Mock head response
    # This ought to work for all files, since all are the same size.
    head_object_response = {"ContentType": "binary/octet-stream", "ContentLength": 3}

    # Mock file download responses
    file1_content = b"\x00\x01\x02"
    file2_content = b"\x03\x04\x05"
    file3_content = b"\x06\x07\x08"
    file4_content = b"\x09\x0a\x0b"

    file1_content_stream = io.BytesIO(file1_content)
    file2_content_stream = io.BytesIO(file2_content)
    file3_content_stream = io.BytesIO(file3_content)
    file4_content_stream = io.BytesIO(file4_content)

    file1_get_object_response = {"Body": file1_content_stream}
    file2_get_object_response = {"Body": file2_content_stream}
    file3_get_object_response = {"Body": file3_content_stream}
    file4_get_object_response = {"Body": file4_content_stream}

    # The S3 downloading we're testing uses a boto3 convenience API
    # function, download_file(), to download files.  But we can only mock
    # up actual AWS responses.  The actual sequence of requests that
    # download_file() makes to download its files, is not documented
    # anywhere.  So we have no good way of knowing which responses we need
    # to mock up!  It's a lot of trial and error...

    # Page 1 of dioptra_builtins keys:
    stubber.add_response(
        "list_objects_v2",
        builtins_keys_response_trunc,
        {"Bucket": "plugins", "Prefix": "dioptra_builtins/"},
    )

    # I think the downloader does this because it wants the file size.
    stubber.add_response(
        "head_object",
        head_object_response,
        {"Bucket": "plugins", "Key": "dioptra_builtins/file1.dat"},
    )

    stubber.add_response(
        "get_object",
        file1_get_object_response,
        {"Bucket": "plugins", "Key": "dioptra_builtins/file1.dat"},
    )

    # Page 2 of dioptra_builtins keys:
    stubber.add_response(
        "list_objects_v2",
        builtins_keys_response_cont,
        {
            "Bucket": "plugins",
            "Prefix": "dioptra_builtins/",
            "ContinuationToken": "next",
        },
    )

    stubber.add_response(
        "head_object",
        head_object_response,
        {"Bucket": "plugins", "Key": "dioptra_builtins/file2.dat"},
    )

    stubber.add_response(
        "get_object",
        file2_get_object_response,
        {"Bucket": "plugins", "Key": "dioptra_builtins/file2.dat"},
    )

    # dioptra_custom keys (1 page, 2 files):
    stubber.add_response(
        "list_objects_v2",
        custom_keys_response,
        {"Bucket": "plugins", "Prefix": "dioptra_custom/"},
    )

    stubber.add_response(
        "head_object",
        head_object_response,
        {"Bucket": "plugins", "Key": "dioptra_custom/file3.dat"},
    )

    stubber.add_response(
        "get_object",
        file3_get_object_response,
        {"Bucket": "plugins", "Key": "dioptra_custom/file3.dat"},
    )

    stubber.add_response(
        "head_object",
        head_object_response,
        {"Bucket": "plugins", "Key": "dioptra_custom/file4.dat"},
    )

    stubber.add_response(
        "get_object",
        file4_get_object_response,
        {"Bucket": "plugins", "Key": "dioptra_custom/file4.dat"},
    )

    bucket_info = {
        "plugins": {
            "dioptra_builtins/file1.dat": file1_content,
            "dioptra_builtins/file2.dat": file2_content,
            "dioptra_custom/file3.dat": file3_content,
            "dioptra_custom/file4.dat": file4_content,
        }
    }

    return bucket_info


@pytest.fixture
def s3_stubbed_plugins() -> Iterator[tuple[BaseClient, dict[str, dict[str, bytes]]]]:
    """
    Create a boto3 client for S3 which has stub responses for the plugins
    bucket, and some info about how it was stubbed, for use by unit tests.
    The latter info is a dict which mirrors the stubbed S3 structure: maps a
    bucket name to a dict which maps a key to a value.

    Yields:
        A 2-tuple containing the boto3 client object, and a dict containing
        info about what was stubbed.
    """

    s3 = boto3.client("s3", endpoint_url="http://example.org/")
    with botocore.stub.Stubber(s3) as stubber:
        bucket_info_plugins = _add_plugins_stubs(stubber)

        yield s3, bucket_info_plugins


@pytest.fixture
def s3_stubbed_workflow_plugins() -> (
    Iterator[tuple[BaseClient, dict[str, dict[str, bytes]]]]
):
    """
    Create a boto3 client for S3 which has stub responses for the workflow and
    plugins buckets, and some info about how it was stubbed, for use by unit
    tests.  The latter info is a dict which mirrors the stubbed S3 structure:
    maps a bucket name to a dict which maps a key to a value.

    Yields:
        A 2-tuple containing the boto3 client object, and a dict containing
        info about what was stubbed.
    """

    s3 = boto3.client("s3", endpoint_url="http://example.org/")
    with botocore.stub.Stubber(s3) as stubber:
        # Order is important here: stub response order must match request
        # order.  Workflow is downloaded first, so it must be stubbed first.
        bucket_info_workflow = _add_workflow_stubs(stubber)
        bucket_info_plugins = _add_plugins_stubs(stubber)

        # Just merge the two sets of bucket info together
        bucket_info_workflow.update(bucket_info_plugins)

        yield s3, bucket_info_workflow
