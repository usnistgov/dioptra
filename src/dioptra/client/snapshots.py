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

import structlog
from structlog.stdlib import BoundLogger

from .base import SubCollectionClient

LOGGER: BoundLogger = structlog.stdlib.get_logger()

T = TypeVar("T")


class SnapshotsSubCollectionClient(SubCollectionClient[T]):
    """The client for managing a snapshots sub-collection.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str] = "snapshots"

    def get(
        self,
        *resource_ids: str | int,
        index: int = 0,
        page_length: int = 10,
        search: str | None = None,
    ) -> T:
        """Get the list of snapshots for a given resource.

        Args:
            *resource_ids: The parent resource ids that own the snapshots
                sub-collection.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of snapshots to return in the paged
                response. Optional, defaults to 10.
            search: Search for snapshots using the Dioptra API's query language.
                Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        params: dict[str, Any] = {
            "index": index,
            "pageLength": page_length,
        }

        if search is not None:
            params["search"] = search

        return self._session.get(
            self.build_sub_collection_url(*resource_ids), params=params
        )

    def get_by_id(
        self,
        *resource_ids: str | int,
        snapshot_id: int,
    ) -> T:
        """Get a snapshot by its id for a specific resource.

        Args:
            *resource_ids: The parent resource ids that own the snapshots
                sub-collection.
            snapshot_id: The snapshot id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(
            self.build_sub_collection_url(*resource_ids), str(snapshot_id)
        )
