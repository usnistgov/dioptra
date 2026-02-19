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
from typing import Any, ClassVar, Final, TypeVar

from .base import CollectionClient, DioptraSession
from .snapshots import SnapshotsSubCollectionClient
from .utils import FileTypes

FILES: Final[str] = "files"
CONTENTS: Final[str] = "contents"

T = TypeVar("T")


class ArtifactsCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /artifacts collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "artifacts"

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the ArtifactsCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)
        self._snapshots = ArtifactsSnapshotCollectionClient[T](
            session=session, root_collection=self
        )

    @property
    def snapshots(self) -> "ArtifactsSnapshotCollectionClient[T]":
        """The client for retrieving artifact resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the artifact snapshots sub-collection. Below are examples of how HTTP
        requests to this sub-collection translate into method calls for an
        active Python Dioptra Python client called ``client``::

            # GET /api/v1/artifacts/1/snapshots
            client.artifacts.snapshots.get(1)

            # GET /api/v1/artifacts/1/snapshots/2
            client.artifacts.snapshots.get_by_id(1, snapshot_id=2)

            # GET /api/v1/artifacts/1/snapshots/2/contents?fileType=tar_gz&path=%2Fpath
            client.artifacts.snapshots.get_contents(
                1, snapshot_id=2, file_type=FileTypes.TAR_GZ, path="/path"
            )
        """
        return self._snapshots

    def get(
        self,
        group_id: int | None = None,
        index: int = 0,
        page_length: int = 10,
        sort_by: str | None = None,
        descending: bool | None = None,
        search: str | None = None,
    ) -> T:
        """Get a list of artifacts.

        Args:
            group_id: The group id the artifacts belong to. If None, return
                artifacts from all groups that the user has access to. Optional,
                defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of artifacts to return in the paged
                response. Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional,
                defaults to None.
            descending: Sort the returned list in descending order.
                Optional, defaults to None.
            search: Search for artifacts using the Dioptra API's query
                language. Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        params: dict[str, Any] = {
            "index": index,
            "pageLength": page_length,
        }

        if sort_by is not None:
            params["sortBy"] = sort_by

        if descending is not None:
            params["descending"] = descending

        if search is not None:
            params["search"] = search

        if group_id is not None:
            params["groupId"] = group_id

        return self._session.get(
            self.url,
            params=params,
        )

    def get_by_id(self, artifact_id: str | int) -> T:
        """Get the artifact matching the provided id.

        Args:
            artifact_id: The artifact id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(artifact_id))

    def create(
        self,
        group_id: str | int,
        job_id: str | int,
        artifact_uri: str,
        plugin_snapshot_id: str | int | None = None,
        task_id: str | int | None = None,
        description: str | None = None,
    ) -> T:
        """Creates an artifact and associates with an existing Job.

            Both plugin_snapshot_id and must be None or not None. If None, then the
            artifact is unavailable for use as input into another job and may only be
            downloaded.

        Args:
            group_id: The id of the group that will own the artifact.
            job_id: The id of the job that produced this artifact.
            artifact_uri: The URI pointing to the location of the artifact.
            plugin_snapshot_id: the plugin snapshot id of the plugin
                containing the artifact task used to serialize/deserialize the artifact,
                defaults to None.
            task_id: the task id of the plugin artifact task used to
                serialize/deserialize the artifact, defaults to None
            description: The description of the new artifact. Optional, defaults to
                None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {
            "group": int(group_id),
            "job": int(job_id),
            "artifactUri": artifact_uri,
        }

        if plugin_snapshot_id is not None:
            json_["pluginSnapshotId"] = int(plugin_snapshot_id)

        if task_id is not None:
            json_["taskId"] = int(task_id)

        if description is not None:
            json_["description"] = description

        return self._session.post(self.url, json_=json_)

    def modify_by_id(
        self,
        artifact_id: str | int,
        plugin_snapshot_id: str | int | None = None,
        task_id: str | int | None = None,
        description: str | None = None,
    ) -> T:
        """Modify the artifact matching the provided id.

            Both plugin_snapshot_id and must be None or not None. If None, then the
            artifact is unavailable for use as input into another job and may only be
            downloaded.
        Args:
            artifact_id: The artifact id, an integer.
            plugin_snapshot_id: the plugin snapshot id of the plugin containing the
                artifact task used to serialize/deserialize the artifact. A value of
                None removes the association with the artifact task.
            task_id: the task id of the plugin artifact task used to
                serialize/deserialize the artifact. A value of None removes the
                association with the artifact task.
            description: The new description of the artifact. To remove the description,
                pass None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {}

        if plugin_snapshot_id is not None:
            json_["pluginSnapshotId"] = int(plugin_snapshot_id)

        if task_id is not None:
            json_["taskId"] = int(task_id)

        if description is not None:
            json_["description"] = description

        return self._session.put(self.url, str(artifact_id), json_=json_)

    def get_files(self, artifact_id: str | int) -> T:
        """Get the file listing for the artifact matching the provided id.

        Args:
            artifact_id: The artifact id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(artifact_id), FILES)

    def get_contents(
        self,
        artifact_id: str | int,
        file_type: FileTypes | None = None,
        artifact_path: str | None = None,
        output_dir: Path | None = None,
        file_stem: str = "contents",
    ) -> Path:
        """Get the contents of an artifact with the given artifact resource id.

        Args:
            artifact_id: The artifact resource id, an integer.
            file_type: if the artifact is a directory, this indicates the file type of
                the bundle that is returned, defaults to None. A value of None must be
                provided if the artifact is a file. If the artifact is a directory and
                None is provided, then a default of FileTypes.TAR_GZ is used.
            artifact_path: if the artifact is a directory, then a
                value other than None indicates a path in the directory structure to
                retrieve. if the artifact is a file, None must be provided. All of the
                files for a directory artifact are returned if None is provided.
            output_dir: the directory to save the downloaded artifact,
                defaults to None. If None, then the current working directory will be
                used.
            file_stem: the file prefix or stem to use for the name of the
                downloaded file. Defaults to the value of "contents".

        Returns:
            A path to where the contents are downloaded.
        """
        contents_path = (
            Path(file_stem) if output_dir is None else Path(output_dir, file_stem)
        )

        params = {}
        if file_type is not None:
            contents_path = contents_path.with_suffix(file_type.suffix)
            params["fileType"] = file_type.value
        if artifact_path is not None:
            params["path"] = artifact_path

        return self._session.download(
            self.url,
            str(artifact_id),
            CONTENTS,
            output_path=contents_path,
            params=params,
        )


class ArtifactsSnapshotCollectionClient(SnapshotsSubCollectionClient[T]):
    def __init__(
        self,
        session: DioptraSession[T],
        root_collection: ArtifactsCollectionClient[T],
    ):
        super().__init__(session=session, root_collection=root_collection)

    def get_contents(
        self,
        artifact_id: str | int,
        artifact_snapshot_id: str | int,
        file_type: FileTypes | None = None,
        artifact_path: str | None = None,
        output_dir: Path | None = None,
        file_stem: str = "contents",
    ) -> Path:
        """Get the contents of an artifact with the given artifact resource id and
        artifact snapshot id.

        Args:
            artifact_id: The artifact resource id, an integer.
            artifact_snapshot_id: The artifact snapshot id, an integer.
            file_type: if the artifact is a directory, this indicates the file type of
                the bundle that is returned, defaults to None. A value of None must be
                provided if the artifact is a file. If the artifact is a directory and
                None is provided, then a default of FileTypes.TAR_GZ is used.
            artifact_path: if the artifact is a directory, then a
                value other than None indicates a path in the directory structure to
                retrieve. if the artifact is a file, None must be provided. All of the
                files for a directory artifact are returned if None is provided.
            output_dir: the directory to save the downloaded artifact,
                defaults to None. If None, then the current working directory will be
                used.
            file_stem: the file prefix or stem to use for the name of the
                downloaded file. Defaults to the value of "contents".

        Returns:
            A path to where the contents are downloaded.
        """
        contents_path = (
            Path(file_stem) if output_dir is None else Path(output_dir, file_stem)
        )
        params = {}
        if file_type is not None:
            contents_path = contents_path.with_suffix(file_type.suffix)
            params["fileType"] = file_type.value
        if artifact_path is not None:
            params["path"] = artifact_path

        return self._session.download(
            self.build_sub_collection_url(artifact_id),
            str(artifact_snapshot_id),
            CONTENTS,
            output_path=contents_path,
            params=params,
        )
