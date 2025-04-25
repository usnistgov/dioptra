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

T1 = TypeVar("T1")
T2 = TypeVar("T2")


class GroupsCollectionClient(CollectionClient[T1, T2]):
    """The client for managing Dioptra's /groups collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "groups"

    def __init__(self, session: DioptraSession[T1, T2]) -> None:
        """Initialize the GroupsCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)

    def get(
        self,
        index: int = 0,
        page_length: int = 10,
        search: str | None = None,
    ) -> T1:
        """Get a list of groups.

        Args:
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of groups to return in the paged response.
                Optional, defaults to 10.
            search: Search for groups using the Dioptra API's query language. Optional,
                defaults to None.

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
            self.url,
            params=params,
        )

    def get_by_id(self, group_id: str | int) -> T1:
        """Get the group matching the provided id.

        Args:
            group_id: The group id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(group_id))
