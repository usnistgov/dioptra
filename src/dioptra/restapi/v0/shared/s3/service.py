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

import os
from pathlib import Path
from typing import IO, Any, Dict, List, Optional, Union
from urllib.parse import urlunparse

import structlog
from boto3.session import Session
from botocore.client import BaseClient
from botocore.exceptions import ClientError
from injector import inject
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class S3Service(object):
    @inject
    def __init__(self, session: Session, client: BaseClient) -> None:
        self._session = session
        self._client = client

    def delete_prefix(self, bucket: str, prefix: str, **kwargs):
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info(
            "Deleting prefix from S3",
            bucket=bucket,
            prefix=prefix,
        )

        delete_objects_list: List[Dict[str, str]] = [
            dict(Key=x)
            for x in self.list_objects(bucket=bucket, prefix=prefix, log=log)
        ]

        response: Dict[str, Any] = self._client.delete_objects(
            Bucket=bucket,
            Delete=dict(Objects=delete_objects_list),
        )

        return [x["Key"] for x in response.get("Deleted", [])]

    def list_directories(self, bucket: str, prefix: str, **kwargs) -> List[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Listing directories in S3 bucket", bucket=bucket, prefix=prefix)

        try:
            response: Dict[str, Any] = self._client.list_objects_v2(
                Bucket=bucket, Prefix=prefix, Delimiter="/"
            )

        except ClientError as e:
            log.exception("Failed to list objects in S3", bucket=bucket, prefix=prefix)
            raise e

        return self.extract_directories(response=response, prefix=prefix, log=log)

    def list_objects(self, bucket: str, prefix: str, **kwargs) -> List[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Listing objects in S3 bucket", bucket=bucket, prefix=prefix)

        try:
            response: Dict[str, Any] = self._client.list_objects_v2(
                Bucket=bucket, Prefix=prefix
            )

        except ClientError as e:
            log.exception("Failed to list objects in S3", bucket=bucket, prefix=prefix)
            raise e

        return self.extract_keys(response=response, log=log)

    def upload(
        self, fileobj: Union[IO[bytes], FileStorage], bucket: str, key: str, **kwargs
    ) -> Optional[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Uploading data to S3", fileobj=fileobj, bucket=bucket, key=key)

        try:
            self._client.upload_fileobj(Fileobj=fileobj, Bucket=bucket, Key=key)

        except ClientError:
            log.exception("S3 upload failed", fileobj=fileobj, bucket=bucket, key=key)
            return None

        uri: str = self.as_uri(bucket=bucket, key=key)
        log.info("S3 upload successful", uri=uri)

        return uri

    def upload_directory(
        self,
        directory: str,
        bucket: str,
        prefix: str,
        include_suffixes: Optional[List[str]],
        **kwargs,
    ) -> Optional[List[str]]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info(
            "Uploading directory to S3",
            directory=directory,
            bucket=bucket,
            prefix=prefix,
        )

        staging_dirname: Path = Path(directory)
        upload_spec_list: List[Dict[str, str]] = []

        for dirpath, _, filenames in os.walk(top=directory):
            key_prefix: Path = Path(prefix) / Path(dirpath).relative_to(staging_dirname)
            upload_spec_list.extend(
                self.as_upload_spec(
                    dirpath=dirpath,
                    filenames=filenames,
                    prefix=key_prefix.as_posix(),
                    include_suffixes=include_suffixes,
                    log=log,
                )
            )

        for upload_spec in upload_spec_list:
            try:
                self._client.upload_file(
                    Filename=upload_spec["source"],
                    Bucket=bucket,
                    Key=upload_spec["target"],
                )

            except ClientError:
                log.exception(
                    "S3 upload file failed",
                    filename=upload_spec["source"],
                    bucket=bucket,
                    key=upload_spec["target"],
                )
                return None

        uri_list: List[str] = [
            self.as_uri(bucket=bucket, key=x["target"]) for x in upload_spec_list
        ]
        log.info("S3 directory upload successful", uri_list=uri_list)

        return uri_list

    @staticmethod
    def as_upload_spec(
        dirpath: str,
        filenames: List[str],
        prefix: str,
        include_suffixes: Optional[List[str]],
        **kwargs,
    ) -> List[Dict[str, str]]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        if include_suffixes is None:
            return [
                dict(
                    source=str(Path(dirpath) / x),
                    target=(Path(prefix) / x).as_posix(),
                )
                for x in filenames
            ]

        return [
            dict(
                source=str(Path(dirpath) / x),
                target=(Path(prefix) / x).as_posix(),
            )
            for x in filenames
            if Path(x).suffix in include_suffixes
        ]

    @staticmethod
    def as_uri(bucket: Optional[str], key: Optional[str], **kwargs) -> str:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return urlunparse(("s3", bucket or "", key or "", "", "", ""))

    @staticmethod
    def extract_directories(
        response: Dict[str, Any], prefix: str, **kwargs
    ) -> List[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return [
            "".join(x["Prefix"].rstrip("/").split(prefix))
            for x in response.get("CommonPrefixes", [])
        ]

    @staticmethod
    def extract_keys(response: Dict[str, Any], **kwargs) -> List[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return [x["Key"] for x in response.get("Contents", [])]

    @staticmethod
    def normalize_prefix(prefix: str, **kwargs) -> str:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        prefix = prefix.strip()

        if prefix == "/":
            return "/"

        return f"{Path(prefix.lstrip('/')).as_posix()}/"
