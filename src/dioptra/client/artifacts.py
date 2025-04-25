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
from typing import Any, ClassVar, TypeVar

from .base import CollectionClient, DioptraSession
from .snapshots import SnapshotsSubCollectionClient

T1 = TypeVar("T1")
T2 = TypeVar("T2")


class ArtifactsCollectionClient(CollectionClient[T1, T2]):
    """The client for managing Dioptra's /artifacts collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "artifacts"

    def __init__(self, session: DioptraSession[T1, T2]) -> None:
        """Initialize the ArtifactsCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)
        self._snapshots = SnapshotsSubCollectionClient[T1, T2](
            session=session, root_collection=self
        )

    @property
    def snapshots(self) -> SnapshotsSubCollectionClient[T1, T2]:
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
    ) -> T1:
        """Get a list of artifacts.

        Args:
            group_id: The group id the artifacts belong to. If None, return artifacts
                from all groups that the user has access to. Optional, defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of artifacts to return in the paged
                response. Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for artifacts using the Dioptra API's query language.
                Optional, defaults to None.

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

    def get_by_id(self, artifact_id: str | int) -> T1:
        """Get the artifact matching the provided id.

        Args:
            artifact_id: The artifact id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(artifact_id))

    def create(
        self, group_id: int, job_id: str | int, uri: str, description: str | None = None
    ) -> T1:
        """Creates an artifact.

        Args:
            group_id: The id of the group that will own the artifact.
            job_id: The id of the job that produced this artifact.
            uri: The URI pointing to the location of the artifact.
            description: The description of the new artifact. Optional, defaults to
                None.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {
            "group": group_id,
            "job": job_id,
            "uri": uri,
        }

        if description is not None:
            json_["description"] = description

        return self._session.post(self.url, json_=json_)

    def modify_by_id(self, artifact_id: str | int, description: str | None) -> T1:
        """Modify the artifact matching the provided id.

        Args:
            artifact_id: The artifact id, an integer.
            description: The new description of the artifact. To remove the description,
                pass None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {}

        if description is not None:
            json_["description"] = description

        return self._session.put(self.url, str(artifact_id), json_=json_)
