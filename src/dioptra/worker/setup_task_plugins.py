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
from typing import Any, Union

import structlog
from botocore.client import BaseClient

from dioptra.sdk.utilities.paths import clear_directory
from dioptra.sdk.utilities.s3 import download_files, s3_uri_to_bucket_prefix


def _get_logger() -> Any:
    """
    Get a logger for this module.

    Returns:
        A logger object
    """
    return structlog.get_logger(__name__)


def _normalize_s3_prefix(prefix: str) -> str:
    """
    Allow a little wiggle room with S3 key prefixes, to ensure they are
    compatible with security policy.  Policy is defined with key prefix
    patterns which look like "foo/*".  This makes the slash a required
    character.  E.g. listing keys with prefix "foo" will not work, but "foo/"
    will work.

    This function ensures that a prefix which is a bare word gets a trailing
    slash.  E.g. "foo" becomes "foo/", but "foo/bar" is left alone.

    Args:
        prefix: An S3 key prefix

    Returns:
        A normalized S3 key prefix
    """
    if "/" not in prefix:
        prefix = prefix + "/"

    return prefix


def setup_task_plugins(
    s3: BaseClient, dioptra_plugin_dir: Union[str, Path], *s3_uris: str
):
    """
    Establish the given plugins directory, by downloading from the given
    S3 buckets.

    Args:
        s3: A boto3 S3 client object
        dioptra_plugin_dir: The directory to download to
        s3_uris: S3 URIs to download task plugins from.
    """
    log = _get_logger()

    bucket_info = []
    for s3_uri in s3_uris:
        bucket, prefix = s3_uri_to_bucket_prefix(s3_uri)

        if not bucket:
            raise ValueError("S3 URIs must include a bucket: " + s3_uri)

        prefix = _normalize_s3_prefix(prefix)

        bucket_info.append((bucket, prefix))

    # Make sure the plugins dir exists!
    plugin_dir_path = Path(dioptra_plugin_dir)
    plugin_dir_path.mkdir(parents=True, exist_ok=True)

    log.info("Clearing directory: %s", dioptra_plugin_dir)
    clear_directory(plugin_dir_path)

    for s3_uri, (bucket, prefix) in zip(s3_uris, bucket_info):
        log.info("Downloading plugins: %s", s3_uri)
        download_files(s3, plugin_dir_path, bucket, prefix)
