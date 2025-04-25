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
from typing import Any, ClassVar, Final, TypeVar

from .base import CollectionClient, DioptraSession
from .drafts import (
    ModifyResourceDraftsSubCollectionClient,
    NewResourceDraftsSubCollectionClient,
    make_draft_fields_validator,
)
from .snapshots import SnapshotsSubCollectionClient
from .tags import TagsSubCollectionClient

DRAFT_FIELDS: Final[set[str]] = {"name", "description"}

T1 = TypeVar("T1")
T2 = TypeVar("T2")


class QueuesCollectionClient(CollectionClient[T1, T2]):
    """The client for managing Dioptra's /queues collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "queues"

    def __init__(self, session: DioptraSession[T1, T2]) -> None:
        """Initialize the QueuesCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)
        self._new_resource_drafts = NewResourceDraftsSubCollectionClient[T1, T2](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
        )
        self._modify_resource_drafts = ModifyResourceDraftsSubCollectionClient[T1, T2](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
        )
        self._snapshots = SnapshotsSubCollectionClient[T1, T2](
            session=session, root_collection=self
        )
        self._tags = TagsSubCollectionClient[T1, T2](
            session=session, root_collection=self
        )

    @property
    def new_resource_drafts(self) -> NewResourceDraftsSubCollectionClient[T1, T2]:
        """The client for managing the new queue drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the new queue drafts sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/queues/drafts
            client.queues.new_resource_drafts.get()

            # GET /api/v1/queues/drafts/1
            client.queues.new_resource_drafts.get_by_id(draft_id=1)

            # PUT /api/v1/queues/drafts/1
            client.queues.new_resource_drafts.modify(
                draft_id=1, name="new-name", description="new-description"
            )

            # POST /api/v1/queues/drafts
            client.queues.new_resource_drafts.create(
                group_id=1, name="name", description="description"
            )

            # DELETE /api/v1/queues/drafts/1
            client.queues.new_resource_drafts.delete(draft_id=1)
        """
        return self._new_resource_drafts

    @property
    def modify_resource_drafts(self) -> ModifyResourceDraftsSubCollectionClient[T1, T2]:
        """The client for managing the queue modification drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the queue modification drafts sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/queues/1/draft
            client.queues.modify_resource_drafts.get_by_id(1)

            # PUT /api/v1/queues/1/draft
            client.queues.modify_resource_drafts.modify(
                1,
                resource_snapshot_id=1,
                name="new-name",
                description="new-description"
            )

            # POST /api/v1/queues/1/draft
            client.queues.modify_resource_drafts.create(
                1, name="name", description="description"
            )

            # DELETE /api/v1/queues/1/draft
            client.queues.modify_resource_drafts.delete(1)
        """
        return self._modify_resource_drafts

    @property
    def snapshots(self) -> SnapshotsSubCollectionClient[T1, T2]:
        """The client for retrieving queue resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the queue snapshots sub-collection. Below are examples of how HTTP
        requests to this sub-collection translate into method calls for an active Python
        Dioptra Python client called ``client``::

            # GET /api/v1/queues/1/snapshots
            client.queues.snapshots.get(1)

            # GET /api/v1/queues/1/snapshots/2
            client.queues.snapshots.get_by_id(1, snapshot_id=2)
        """
        return self._snapshots

    @property
    def tags(self) -> TagsSubCollectionClient[T1, T2]:
        """
        The client for managing the tags sub-collection owned by the /queues collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the tags sub-collection. Below are examples of how HTTP requests to
        this sub-collection translate into method calls for an active Python Dioptra
        Python client called ``client``::

            # GET /api/v1/queues/1/tags
            client.queues.tags.get(1)

            # PUT /api/v1/queues/1/tags
            client.queues.tags.modify(1, ids=[2, 3])

            # POST /api/v1/queues/1/tags
            client.queues.tags.append(1, ids=[2, 3])

            # DELETE /api/v1/queues/1/tags/3
            client.queues.tags.remove(1, tag_id=3)

            # DELETE /api/v1/queues/1/tags
            client.queues.tags.remove(1)
        """
        return self._tags

    def get(
        self,
        group_id: int | None = None,
        index: int = 0,
        page_length: int = 10,
        sort_by: str | None = None,
        descending: bool | None = None,
        search: str | None = None,
    ) -> T1:
        """Get a list of queues.

        Args:
            group_id: The group id the queues belong to. If None, return queues from all
                groups that the user has access to. Optional, defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of queues to return in the paged response.
                Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for queues using the Dioptra API's query language. Optional,
                defaults to None.

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

    def get_by_id(self, queue_id: str | int) -> T1:
        """Get the queue matching the provided id.

        Args:
            queue_id: The queue id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(queue_id))

    def create(self, group_id: int, name: str, description: str | None = None) -> T1:
        """Creates a queue.

        Args:
            group_id: The id of the group that will own the queue.
            name: The name of the new queue.
            description: The description of the new queue. Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {
            "group": group_id,
            "name": name,
        }

        if description is not None:
            json_["description"] = description

        return self._session.post(self.url, json_=json_)

    def modify_by_id(
        self, queue_id: str | int, name: str, description: str | None
    ) -> T1:
        """Modify the queue matching the provided id.

        Args:
            queue_id: The queue id, an integer.
            name: The new name of the queue.
            description: The new description of the queue. To remove the description,
                pass None.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"name": name}

        if description is not None:
            json_["description"] = description

        return self._session.put(self.url, str(queue_id), json_=json_)

    def delete_by_id(self, queue_id: str | int) -> T1:
        """Delete the queue matching the provided id.

        Args:
            queue_id: The queue id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, str(queue_id))
