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
from pathlib import Path
from typing import Any, Iterator, Optional, Union

import structlog
from botocore.client import BaseClient

from dioptra.sdk.utilities.s3.uri import s3_uri_to_bucket_prefix


def _get_logger() -> Any:
    """
    Get a logger for this module.

    Returns:
        A logger object
    """
    return structlog.get_logger(__name__)


def get_s3_keys(
    s3: BaseClient, bucket: str, prefix: Optional[str] = None
) -> Iterator[str]:
    """
    Generate all keys in the given S3 bucket, having the given prefix.

    Args:
        s3: A boto3 S3 client object
        bucket: An S3 bucket name
        prefix: An optional key prefix

    Yields:
        Key names
    """

    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    for obj_info in resp.get("Contents", []):
        yield obj_info["Key"]

    while resp["IsTruncated"]:
        resp = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            ContinuationToken=resp["NextContinuationToken"],
        )

        for obj_info in resp.get("Contents", []):
            yield obj_info["Key"]


def download_files_uri(
    s3: BaseClient, dest_dir: Path, s3_uri: str, preserve_key_paths: bool = False
):
    """
    Download all files from the given S3 URI to the given directory.

    Args:
        s3: A boto3 S3 client object
        dest_dir: A string or Path object referring to the directory where
            files will be downloaded to
        s3_uri: An S3 URI in the form "s3://<bucket>/<key_prefix>"
        preserve_key_paths: If True, append matching keys to dest_dir to obtain
            the final directory to download to.  The intermediate
            subdirectories are created automatically.  This causes the
            directory structure represented by the keys to be mirrored in the
            local filesystem.  If False, the last component of matching key
            paths are used as filenames and the rest of the paths are
            discarded.  This causes a directory structure in the bucket to be
            flattened to list of filenames.  No subdirectories are created in
            this case.
    """

    bucket, prefix = s3_uri_to_bucket_prefix(s3_uri)

    if not bucket:
        raise ValueError("S3 URIs must include a bucket: " + s3_uri)

    download_files(s3, dest_dir, bucket, prefix, preserve_key_paths)


def download_files(
    s3: BaseClient,
    dest_dir: Union[str, Path],
    bucket: str,
    prefix: Optional[str] = None,
    preserve_key_paths: bool = False,
):
    """
    Download all files from the given S3 bucket to the given directory, whose
    keys match the given prefix.

    Args:
        s3: A boto3 S3 client object
        dest_dir: A string or Path object referring to the directory where
            files will be downloaded to.  Must already exist.
        bucket: The name of an S3 bucket
        prefix: An optional S3 key prefix, used to limit what is downloaded
        preserve_key_paths: If True, append matching keys to dest_dir to obtain
            the final directory to download to.  The intermediate
            subdirectories are created automatically.  This causes the
            directory structure represented by the keys to be mirrored in the
            local filesystem.  If False, the last component of matching key
            paths are used as filenames and the rest of the paths are
            discarded.  This causes a directory structure in the bucket to be
            flattened to list of filenames.  No subdirectories are created in
            this case.
    """

    log = _get_logger()

    if isinstance(dest_dir, str):
        dest_dir = Path(dest_dir)

    for key in get_s3_keys(s3, bucket, prefix):
        if preserve_key_paths:
            key_path = dest_dir / key
            key_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            key_path = dest_dir / Path(key).name

        log.debug("Downloading s3 key %s -> %s", key, str(key_path))
        s3.download_file(bucket, key, str(key_path))
