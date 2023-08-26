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
import os
import shutil
import urllib.parse
from pathlib import Path
from typing import Any, Iterator, Mapping, MutableMapping, Optional

import boto3
import structlog
from botocore.client import BaseClient
from rq.job import get_current_job

from dioptra.task_engine.task_engine import run_experiment
from dioptra.task_engine.validation import is_valid


def _get_logger() -> Any:
    """
    Get a logger for this module.

    Returns:
        A logger object
    """
    return structlog.get_logger(__name__)


def _s3_uri_to_bucket_prefix(s3_uri: str) -> tuple[Optional[str], str]:
    """
    Given an S3 URI in the form:

        s3://<bucket>/<key_prefix>

    extract the bucket and key prefix parts, and return them.

    Args:
        s3_uri: An S3 URI

    Returns:
        A bucket, prefix 2-tuple.
    """
    uri_parts = urllib.parse.urlparse(s3_uri)
    bucket = uri_parts.hostname
    prefix = uri_parts.path.lstrip("/")

    return bucket, prefix


def _get_s3_keys(s3: BaseClient, bucket: str, prefix: str) -> Iterator[str]:
    """
    Generate all keys in the given S3 bucket, having the given prefix.

    Args:
        s3: A boto3 S3 client object
        bucket: An S3 bucket name
        prefix: A key prefix

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


def _download_task_plugins(s3: BaseClient, s3_uri: str, dest_dir: Path):
    """
    Download all task plugin files from the given S3 URI to the given
    directory.

    Args:
        s3: A boto3 S3 client object
        s3_uri: An S3 URI in the form "s3://<bucket>/<key_prefix>"
        dest_dir: A Path object referring to the directory where files
            will be downloaded to
    """

    log = _get_logger()

    bucket, prefix = _s3_uri_to_bucket_prefix(s3_uri)
    assert bucket  # For mypy; assume correct environment variables

    # To satisfy S3 security policy, key prefixes must end with
    # a "/".
    if not prefix.endswith("/"):
        prefix = prefix + "/"

    for key in _get_s3_keys(s3, bucket, prefix):
        key_path = dest_dir / key
        key_path.parent.mkdir(parents=True, exist_ok=True)

        log.debug("Downloading s3 key %s -> %s", key, str(key_path))
        s3.download_file(bucket, key, str(key_path))


def _clear_plugins_dir(plugin_dir: Path):
    """
    Remove the builtins and custom plugin collection subdirectories from
    the given directory.

    Args:
        plugin_dir: A Path object referring to a directory
    """
    builtins_dir = plugin_dir / "dioptra_builtins"
    custom_dir = plugin_dir / "dioptra_custom"

    for subdir in (builtins_dir, custom_dir):
        if subdir.exists():
            shutil.rmtree(subdir)


def _setup_task_plugins(
    s3: BaseClient,
    dioptra_plugin_dir: str,
    dioptra_plugins_s3_uri: str,
    dioptra_custom_plugins_s3_uri: str,
):
    """
    Establish the given plugins directory, by downloading from the given
    S3 buckets.

    Args:
        s3: A boto3 S3 client object
        dioptra_plugin_dir: The directory to download to
        dioptra_plugins_s3_uri: An S3 URI to download builtin plugins from
        dioptra_custom_plugins_s3_uri: An S3 URI to download custom plugins
            from
    """
    log = _get_logger()

    # Make sure the plugins dir exists!
    plugin_dir_path = Path(dioptra_plugin_dir)
    plugin_dir_path.mkdir(parents=True, exist_ok=True)

    log.info("Clearing directory: %s", dioptra_plugin_dir)
    _clear_plugins_dir(plugin_dir_path)

    log.info("Downloading plugins: %s", dioptra_plugins_s3_uri)
    _download_task_plugins(s3, dioptra_plugins_s3_uri, plugin_dir_path)

    log.info("Downloading plugins: %s", dioptra_custom_plugins_s3_uri)
    _download_task_plugins(s3, dioptra_custom_plugins_s3_uri, plugin_dir_path)


def run_task_engine(
    experiment_desc: Mapping[str, Any],
    global_parameters: MutableMapping[str, Any],
    s3: Optional[BaseClient] = None,
):
    """
    Run an experiment via the task engine.

    Args:
        experiment_desc: A declarative experiment description, as a mapping
        global_parameters: Global parameters for this run, as a mapping from
            parameter name to value
        s3: An optional boto3 S3 client object to use.  If not given, construct
            one according to environment variables.  This argument is not
            normally used, but useful in unit tests when you need a specially
            configured object with stubbed responses.
    """
    rq_job = get_current_job()
    rq_job_id = rq_job.get_id() if rq_job else None

    with structlog.contextvars.bound_contextvars(rq_job_id=rq_job_id):
        log = _get_logger()

        mlflow_s3_endpoint_url = os.getenv("MLFLOW_S3_ENDPOINT_URL")
        dioptra_plugins_s3_uri = os.getenv("DIOPTRA_PLUGINS_S3_URI")
        dioptra_custom_plugins_s3_uri = os.getenv("DIOPTRA_CUSTOM_PLUGINS_S3_URI")
        dioptra_plugin_dir = os.getenv("DIOPTRA_PLUGIN_DIR")

        # For mypy; assume correct environment variables
        assert mlflow_s3_endpoint_url
        assert dioptra_plugins_s3_uri
        assert dioptra_custom_plugins_s3_uri
        assert dioptra_plugin_dir

        if not s3:
            s3 = boto3.client("s3", endpoint_url=mlflow_s3_endpoint_url)

        if is_valid(experiment_desc):
            _setup_task_plugins(
                s3,
                dioptra_plugin_dir,
                dioptra_plugins_s3_uri,
                dioptra_custom_plugins_s3_uri,
            )

            run_experiment(experiment_desc, global_parameters)
        else:
            log.error("Experiment description was invalid!")
