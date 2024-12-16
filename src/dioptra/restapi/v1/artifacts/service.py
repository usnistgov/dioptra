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
"""The server-side functions that perform artifact endpoint operations."""
from __future__ import annotations

import json
import mimetypes
import os
import tarfile
import time
import zipfile
from io import BytesIO
from pathlib import Path
from posixpath import join as urljoin
from tempfile import TemporaryDirectory
from tkinter import NO
from typing import Any, Final, List, Union, cast

import art
import mlflow
import requests
import structlog
from flask import send_from_directory
from flask_login import current_user
from flask_migrate import current
from injector import inject
from numpy import full
from scipy.fft import dst
from sqlalchemy import Integer, func, select
from structlog.stdlib import BoundLogger
from traitlets import Bool
from werkzeug.datastructures import FileStorage

from dioptra.restapi.db import db, models
from dioptra.restapi.db.models.artifacts import Artifact
from dioptra.restapi.errors import (
    BackendDatabaseError,
    DioptraError,
    EntityDoesNotExistError,
    EntityExistsError,
    QueryParameterValidationError,
    SortParameterValidationError,
)
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.jobs.service import ExperimentJobIdService, JobIdService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters
from dioptra.sdk.utilities.paths import set_cwd

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "artifact"
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "uri": lambda x: models.Artifact.uri.like(x, escape="/"),
    "description": lambda x: models.Artifact.description.like(x, escape="/"),
}
SORTABLE_FIELDS: Final[dict[str, Any]] = {
    "uri": models.Artifact.uri,
    "createdOn": models.Artifact.created_on,
    "lastModifiedOn": models.Resource.last_modified_on,
    "description": models.Artifact.description,
}


class ArtifactService(object):
    """The service methods for registering and managing artifacts by their unique id."""

    @inject
    def __init__(
        self,
        artifact_uri_service: ArtifactUriService,
        job_id_service: JobIdService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the artifact service.

        All arguments are provided via dependency injection.

        Args:
            artifact_uri_service: An ArtifactUriService object.
            job_id_service: A JobIdService object.
            group_id_service: A GroupIdService object.
        """
        self._artifact_uri_service = artifact_uri_service
        self._job_id_service = job_id_service
        self._group_id_service = group_id_service

    def create(
        self,
        artifact_file: FileStorage | None,
        artifact_type: str,
        description: str,
        group_id: int,
        job_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict:
        """Create a new artifact.

        Args:
            artifact_name: Name of the Artifact.
            artifact_file: The contents of the Artifact file.
            artifact_type: Either file or dir.
            description: The description of the artifact.
            group_id: The group that will own the artifact.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created artifact object.

        Raises:
            EntityExistsError: If the artifact already exists.

        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_dict = cast(
            utils.JobDict,
            self._job_id_service.get(job_id, error_if_not_found=True, log=log),
        )
        job = job_dict["job"]
        job_artifacts = job_dict["artifacts"]

        if artifact_file is None:
            raise DioptraError("Failed to read uploaded file.")

        artifact_file_name = artifact_file.filename
        if artifact_file_name is None:
            raise DioptraError("Invalid file name to be uploaded.")

        # check the job's artifacts for a file with a matching name
        duplicate = _get_duplicate_artifact(job_artifacts, artifact_file_name)

        if duplicate is not None:
            raise EntityExistsError(
                RESOURCE_TYPE, duplicate.resource_id, uri=duplicate.uri
            )

        if artifact_type == "file":
            with TemporaryDirectory() as tmp_dir, set_cwd(tmp_dir):
                working_dir = Path(tmp_dir)
                artifact_bytes = artifact_file.stream.read()
                temp_file_path = os.path.join(working_dir, artifact_file_name)
                try:
                    with open(temp_file_path, "wb") as temp_file:
                        temp_file.write(artifact_bytes)
                except Exception as e:
                    raise DioptraError("Failed to write temp file.") from e

                uri = _upload_file_as_artifact(artifact_path=temp_file_path)
        elif artifact_type == "dir" or artifact_type == "archive":
            uri = _upload_archive_as_artifact(artifact_file, artifact_file_name)

        else:
            raise DioptraError("Wrong artifact_type was provided.")

        group = self._group_id_service.get(group_id, error_if_not_found=True, log=log)

        resource = models.Resource(resource_type="artifact", owner=group)
        new_artifact = models.Artifact(
            uri=uri,
            description=description,
            resource=resource,
            creator=current_user,
        )
        job.children.append(new_artifact.resource)
        db.session.add(new_artifact)

        if commit:
            db.session.commit()
            log.debug(
                "Artifact registration successful", artifact_id=new_artifact.resource_id
            )

        return utils.ArtifactDict(artifact=new_artifact, has_draft=False)

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> Any:
        """Fetch a list of artifacts, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of artifacts to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

        Returns:
            A tuple containing a list of artifacts and the total number of artifacts
            matching the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when counting
                the number of artifacts.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of artifacts")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)
            )

        stmt = (
            select(func.count(models.Artifact.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Artifact.resource_snapshot_id,
            )
        )
        total_num_artifacts = db.session.scalars(stmt).first()

        if total_num_artifacts is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_artifacts == 0:
            return [], total_num_artifacts

        # get latest artifact snapshots
        latest_artifacts_stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Artifact.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )

        if sort_by_string and sort_by_string in SORTABLE_FIELDS:
            sort_column = SORTABLE_FIELDS[sort_by_string]
            if descending:
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
            latest_artifacts_stmt = latest_artifacts_stmt.order_by(sort_column)
        elif sort_by_string and sort_by_string not in SORTABLE_FIELDS:
            raise SortParameterValidationError(RESOURCE_TYPE, sort_by_string)

        artifacts = db.session.scalars(latest_artifacts_stmt).all()

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(tuple(artifact.resource_id for artifact in artifacts)),
            models.DraftResource.user_id == current_user.user_id,
        )
        artifacts_dict: dict[int, utils.ArtifactDict] = {
            artifact.resource_id: utils.ArtifactDict(artifact=artifact, has_draft=False)
            for artifact in artifacts
        }
        for resource_id in db.session.scalars(drafts_stmt):
            artifacts_dict[resource_id]["has_draft"] = True

        return list(artifacts_dict.values()), total_num_artifacts


class JobArtifactService(object):
    """The service methods for registering and managing artifacts by their unique id."""

    @inject
    def __init__(
        self,
        artifact_service: ArtifactService,
        experiment_job_id_service: ExperimentJobIdService,
    ) -> None:
        """Initialize the artifact service.

        All arguments are provided via dependency injection.

        Args:
            artifact_service: An ArtifactService object.
            experiment_job_id_service: A JobIdService object.
        """
        self._artifact_service = artifact_service
        self._experiment_job_id_service = experiment_job_id_service

    def create(
        self,
        experiment_id: int,
        job_id: int,
        uri: str,
        description: str,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_dict = cast(
            utils.JobDict,
            self._experiment_job_id_service.get(
                experiment_id, job_id, error_if_not_found=True, log=log
            ),
        )
        job = job_dict["job"]

        resource = models.Resource(resource_type="artifact", owner=job.resource.owner)
        new_artifact = models.Artifact(
            uri=uri,
            description=description,
            resource=resource,
            creator=current_user,
        )
        job.children.append(new_artifact.resource)
        db.session.add(new_artifact)

        if commit:
            db.session.commit()
            log.debug(
                "Artifact registration successful", artifact_id=new_artifact.resource_id
            )

        return utils.ArtifactDict(artifact=new_artifact, has_draft=False)


class ArtifactUriService(object):
    """The service methods for managing artifacts by their uri."""

    def get(
        self,
        artifact_uri: str,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.Artifact | None:
        """Fetch an artifact by its unique uri.

        Args:
            artifact_uri: the unique uri of the artifact.
            error_if_not_found: If True, raise an error if the artifact is not found.
                Defaults to False.


        Returns:
            The artifact object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the artifact is not found and
                `error_if_not_found` is True.

        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get artifact by id", artifact_uri=artifact_uri)

        stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .where(
                models.Artifact.uri == artifact_uri,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Artifact.resource_snapshot_id,
            )
        )
        artifact = db.session.scalars(stmt).first()

        if artifact is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(RESOURCE_TYPE, artifact_uri=artifact_uri)

            return None

        return artifact


class ArtifactIdService(object):
    """The service methods for retrieving artifacts by their unique id."""

    def get(
        self,
        artifact_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.ArtifactDict | str | None:
        """Fetch a artifact by its unique id.

        Args:
            artifact_id: The unique id of the artifact.
            error_if_not_found: If True, raise an error if the artifact is not found.
                Defaults to False.

        Returns:
            The artifact object if found, otherwise None, or a directory listing if 
            multiple artifact files exist.

        Raises:
            EntityDoesNotExistError: If the artifact is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get artifact by id", artifact_id=artifact_id)

        stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .where(
                models.Artifact.resource_id == artifact_id,
                models.Artifact.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        artifact = db.session.scalars(stmt).first()

        if artifact is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(RESOURCE_TYPE, artifact_id=artifact_id)

            return None

        drafts_stmt = (
            select(models.DraftResource.draft_resource_id)
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == artifact.resource_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        single_artifact = utils.ArtifactDict(artifact=artifact, has_draft=has_draft)

        artifact_list = mlflow.artifacts.list_artifacts(artifact_uri=artifact.uri)
        if artifact_list is None:
            raise DioptraError(
                f'An artifact file with path "{artifact.uri}" does not exist in MLFlow.'
            )
        artifact_listing = _get_artifact_file_list(
            artifact_uri=artifact.uri,
            current_uri=artifact.uri,
            artifact_list=artifact_list,
            subfolder_path="",
        )
        if len(artifact_listing) > 0:
            return json.dumps(artifact_listing)

        return single_artifact

    def modify(
        self,
        artifact_id: int,
        description: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict | None:
        """Modify a artifact.

        Args:
            artifact_id: The unique id of the artifact.
            description: The new description of the artifact.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated artifact object.

        Raises:
            EntityDoesNotExistError: If the artifact is not found and
                `error_if_not_found` is True.
            EntityExistsError: If the artifact name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        artifact_dict = self.get(
            artifact_id, error_if_not_found=error_if_not_found, log=log
        )

        if artifact_dict is None:
            return None

        artifact = artifact_dict["artifact"]
        has_draft = artifact_dict["has_draft"]

        new_artifact = models.Artifact(
            uri=artifact.uri,
            description=description,
            resource=artifact.resource,
            creator=current_user,
        )
        db.session.add(new_artifact)

        if commit:
            db.session.commit()
            log.debug(
                "Artifact modification successful",
                artifact_id=artifact_id,
                description=description,
            )

        return utils.ArtifactDict(artifact=new_artifact, has_draft=has_draft)


class ArtifactIdContentsService(object):
    """ """

    def get(
        self,
        artifact_id: int,
        path: str | None,
        **kwargs,
    ) -> Any:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get artifact contents by artifact id", artifact_id=artifact_id)

        artifact_stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .where(
                models.Artifact.resource_id == artifact_id,
                models.Artifact.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        db_artifact = db.session.scalar(artifact_stmt)
        if db_artifact is None:
            raise EntityDoesNotExistError(RESOURCE_TYPE, artifact_id=artifact_id)

        # These will remain the same when no path parameter is provided
        artifact_full_path = os.path.normpath(db_artifact.uri)
        artifact_base_uri = os.path.normpath(db_artifact.uri)

        sanitized_path = None
        if path is not None:
            if ".." in path:
                raise QueryParameterValidationError(
                    RESOURCE_TYPE, constraint="invalid path query parameter"
                )
            sanitized_path = os.path.normpath(path)  # TODO: expand on cleaning the path
            artifact_full_path = os.path.join(artifact_base_uri, sanitized_path)

        # Check MLFlow for the specified artifact
        artifact_list = mlflow.artifacts.list_artifacts(artifact_uri=artifact_full_path)
        if artifact_list is None:
            raise DioptraError(
                f'An artifact file with path "{artifact_full_path}" does not exist in MLFlow.'
            )

        is_dir = True
        if len(artifact_list) == 0:
            is_dir = False

        with TemporaryDirectory() as tmp_dst_dir, set_cwd(tmp_dst_dir):
            if is_dir:
                contents = self._get_artifact_zip_file(artifact_base_uri)
            else:
                contents = self._get_artifact_file_contents(
                    artifact_full_path, tmp_dst_dir
                )
            
            artifact_name = os.path.basename(artifact_full_path) 
            if is_dir:
                artifact_name += '.tar.gz'
                
            mimetype = mimetypes.guess_type(artifact_name)[0]

        return contents, is_dir, os.path.basename(artifact_full_path), mimetype

    def _get_artifact_zip_file(
        self,
        full_path: str,
    ) -> BytesIO:
        zip_name = os.path.basename(full_path)
        contents = BytesIO()

        with TemporaryDirectory() as temp_dir, set_cwd(temp_dir):
            temp_artifact = _download_all_artifacts(
                uris=[full_path], dst_path=temp_dir
            )[0]

            with tarfile.open(fileobj=contents, mode="w") as tar:
                tar.add(temp_artifact, arcname=zip_name)

        contents.seek(0)
        return contents

    def _get_artifact_file_contents(
        self,
        artifact_url: str,
        destination_dir: str,
    ) -> BytesIO:
        temp_artifact_path = _download_all_artifacts(
            uris=[artifact_url], dst_path=destination_dir
        )[0]

        with open(temp_artifact_path, "rb") as file:
            file_contents = file.read()
            contents = BytesIO(file_contents)
            contents.seek(0)
        return contents

def _get_artifact_file_list(
    artifact_uri: str,
    current_uri: str,
    artifact_list: list[Any],
    subfolder_path: str,
) -> list[Any]:

    contents = []
    relative_path = ""

    for artifact in artifact_list:
        if artifact.is_dir:
            new_artifact_path = os.path.join(
                current_uri, os.path.basename(artifact.path)
            )
            new_artifact_list = mlflow.artifacts.list_artifacts(
                artifact_uri=new_artifact_path
            )
            if new_artifact_list is None:
                raise DioptraError(
                    f'An artifact file with path "{current_uri}" does not exist in MLFlow.'
                )

            # If it is empty, it means it is a directory with no contents
            if len(new_artifact_list) == 0:
                relative_path = current_uri.replace(artifact_uri, "/")

                contents.append(
                    {
                        "relativePath": relative_path,
                        "fileSize": artifact.file_size,
                        "is_dir": artifact.is_dir,
                        "url": artifact_uri,
                    }
                )

            # If the directory has file(s), recurse
            else:
                relative_path = new_artifact_path.replace(artifact_uri + "/", "")

                # Recurse into the subdirectory
                contents.extend(
                    _get_artifact_file_list(
                        artifact_uri=artifact_uri,
                        current_uri=new_artifact_path,
                        artifact_list=new_artifact_list,
                        subfolder_path=relative_path,
                    )
                )
        else:
            # Else it is a file
            if subfolder_path:
                # Keep track of the subfolder depth to properly build the relative path
                relative_path = os.path.join(
                    subfolder_path, os.path.basename(artifact.path)
                )
            else:
                # Remove the artifact name, since it is not needed in relative path
                artifact_name = os.path.basename(artifact_uri)
                relative_path = artifact.path.replace(artifact_name + "/", "")

            contents.append(
                {
                    "relativePath": relative_path,
                    "fileSize": artifact.file_size,
                    "is_dir": artifact.is_dir,
                    "url": artifact_uri,
                }
            )
    return contents


def _get_duplicate_artifact(job_artifacts, new_artifact_name) -> models.Artifact | None:
    for artifact in job_artifacts:
        existing_artifact_name = os.path.basename(artifact.uri)
        if new_artifact_name == existing_artifact_name:
            return artifact

    return None


def _download_all_artifacts(uris: List[str], dst_path: str) -> List[str]:
    download_paths = []
    for uri in uris:
        try:
            download_path: str = mlflow.artifacts.download_artifacts(
                artifact_uri=uri, dst_path=dst_path
            )
            LOGGER.info(
                "Artifact downloaded from MLFlow run", artifact_path=download_path
            )
            download_paths += [download_path]
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"The specified file with uri {uri} could not be found.", e
            )
        except:
            raise DioptraError(
                f"The specified file with uri {uri} could not be downloaded."
            )
    return download_paths


def _get_logged_in_session():
    session = requests.Session()
    url = "http://localhost:5000/api/v1"
    # url = "http://dioptra-deployment-restapi:5000/api/v1"

    login = _post(
        session,
        url,
        {
            "username": os.environ["DIOPTRA_WORKER_USERNAME"],
            "password": os.environ["DIOPTRA_WORKER_PASSWORD"],
        },
        "auth",
        "login",
    )
    LOGGER.info("login request sent", response=str(login))

    return session, url


def _post(session, endpoint, data, *features):
    _debug_request(urljoin(endpoint, *features), "POST", data)
    return _make_request(session, "post", endpoint, data, *features)


def _upload_artifact_to_restapi(
    source_uri, group_id: int, job_id: int, description: str
):
    session, url = _get_logged_in_session()

    artifact = _post(
        session,
        url,
        {
            "group": str(group_id),
            "description": f"{description}",
            "job": str(job_id),
            "uri": source_uri,
        },
        "artifacts",
    )
    LOGGER.info("artifact", response=artifact)


def _upload_file_as_artifact(artifact_path: Union[str, Path]) -> str:
    """Uploads a file as an artifact of the active MLFlow run.

    Args:
        artifact_path: The location of the file to be uploaded.

    See Also:
        - :py:func:`mlflow.log_artifact`
    """
    artifact_path = Path(artifact_path)
    mlflow.log_artifact(str(artifact_path))
    uri = mlflow.get_artifact_uri(str(artifact_path.name))
    # _upload_artifact_to_restapi(uri, group_id, job_id, description)
    LOGGER.info("Artifact uploaded for current MLFlow run", filename=artifact_path.name)
    return uri


def _upload_archive_as_artifact(
    artifact_archive: FileStorage, artifact_file_name: str
) -> str:
    """Uploads the files of an archive as an artifact of the active MLFlow run.

    Args:
        artifact_archive: The contents of the archive to be uploaded.
        artifact_file_name: The name of the archive file.
    """
    with TemporaryDirectory() as temp_dir, set_cwd(temp_dir):
        # create the name for the top level directory for the artifacts
        # based on the artifact archive without any extensions
        top_dir_name, _, _ = artifact_file_name.partition(".")

        # create a top level directory to hold archive contents
        outer_dir = os.path.join(temp_dir, top_dir_name)

        # extract the archive to the temp folder and upload the contents to MLFlow
        if tarfile.is_tarfile(artifact_archive.stream):
            with tarfile.open(fileobj=artifact_archive.stream, mode="r:*") as tar_file:
                tar_file.extractall(path=outer_dir)
                mlflow.log_artifacts(local_dir=outer_dir, artifact_path=top_dir_name)
                uri = mlflow.get_artifact_uri(top_dir_name)
        elif zipfile.is_zipfile(artifact_archive.stream):
            with zipfile.ZipFile(artifact_archive.stream, mode="r") as zip_file:
                # An extra temp directory with name __MACOSX is sometimes created
                # when unpacking a .zip file created on macOS. Do not unpack these
                # temp files/directories to avoid uploading them to MLFlow.
                macos_temp_name = "__MACOSX/"
                for entry in zip_file.infolist():
                    if not entry.filename.startswith(macos_temp_name):
                        zip_file.extract(entry)

                mlflow.log_artifacts(local_dir=outer_dir, artifact_path=top_dir_name)
                uri = mlflow.get_artifact_uri(top_dir_name)
        else:
            raise DioptraError(
                f"The provdided file archive ({artifact_file_name}) is an invalid archive type."
            )

        LOGGER.info(
            "Artifact folder uploaded for current MLFlow run", filename=outer_dir
        )
        return uri


def _debug_request(url, method, data=None):
    LOGGER.debug("Request made.", url=url, method=method, data=data)


def _debug_response(json):
    LOGGER.debug("Response received.", json=json)


def _make_request(session, method_name, endpoint, data, *features):
    url = urljoin(endpoint, *features)
    method = getattr(session, method_name)
    response = ""
    try:
        if data:
            response = method(url, json=data)
        else:
            response = method(url)
        if response.status_code != 200:
            raise StatusCodeError()
        json = response.json()
        _debug_response(json=json)
        return json
    except (requests.ConnectionError, StatusCodeError, requests.JSONDecodeError) as e:
        _handle_error(session, url, method_name.upper(), data, response, e)


def _handle_error(session, url, method, data, response, error):
    if type(error) is requests.ConnectionError:
        restapi = os.environ["DIOPTRA_RESTAPI_URI"]
        message = (
            f"Could not connect to the REST API. Is the server running at {restapi}?"
        )
        LOGGER.error(message, url=url, method=method, data=data, response=response)
        raise APIConnectionError(message)
    if type(error) is StatusCodeError:
        message = f"Error code {response.status_code} returned."
        LOGGER.error(message, url=url, method=method, data=data, response=response)
        raise StatusCodeError(message)
    if type(error) is requests.JSONDecodeError:
        message = "JSON response could not be decoded."
        LOGGER.error(message, url=url, method=method, data=data, response=response)
        raise JSONDecodeError(message)


class APIConnectionError(Exception):
    """Class for connection errors"""


class StatusCodeError(Exception):
    """Class for status code errors"""


class JSONDecodeError(Exception):
    """Class for JSON decode errors"""
