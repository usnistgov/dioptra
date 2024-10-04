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

import structlog
from structlog.stdlib import BoundLogger

from .base import CollectionClient, DioptraSession
from .drafts import (
    ExistingResourceDraftsSubCollectionClient,
    NewResourceDraftsSubCollectionClient,
    make_draft_fields_validator,
)
from .snapshots import SnapshotsSubCollectionClient
from .tags import TagsSubCollectionClient

LOGGER: BoundLogger = structlog.stdlib.get_logger()

DRAFT_FIELDS: Final[set[str]] = {"name", "description"}

T = TypeVar("T")


class QueuesCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /queues collection.

    Attributes:
        name: The name of the collection managed by the client.
    """

    name: ClassVar[str] = "queues"

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the QueuesCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)
        self._new_resource_drafts = NewResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
        )
        self._existing_resource_drafts = ExistingResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
        )
        self._snapshots = SnapshotsSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._tags = TagsSubCollectionClient[T](session=session, root_collection=self)

    @property
    def new_drafts(self) -> NewResourceDraftsSubCollectionClient[T]:
        """The client for managing the new queue drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource IDs
        that own the new queue drafts sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/queues/drafts
            client.queues.new_drafts.get()

            # GET /api/v1/queues/drafts/1
            client.queues.new_drafts.get_by_id(draft_id=1)

            # PUT /api/v1/queues/drafts/1
            client.queues.new_drafts.modify(
                draft_id=1, name="new-name", description="new-description"
            )

            # POST /api/v1/queues/drafts
            client.queues.new_drafts.create(
                group_id=1, name="name", description="description"
            )

            # DELETE /api/v1/queues/drafts/1
            client.queues.new_drafts.delete(draft_id=1)
        """
        return self._new_resource_drafts

    @property
    def existing_drafts(self) -> ExistingResourceDraftsSubCollectionClient[T]:
        """The client for managing the existing queue drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource IDs
        that own the existing queue drafts sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/queues/1/draft
            client.queues.existing_drafts.get_by_id(1)

            # PUT /api/v1/queues/1/draft
            client.queues.existing_drafts.modify(
                1, name="new-name", description="new-description"
            )

            # POST /api/v1/queues/1/draft
            client.queues.existing_drafts.create(
                1, name="name", description="description"
            )

            # DELETE /api/v1/queues/1/draft
            client.queues.existing_drafts.delete(1)
        """
        return self._existing_resource_drafts

    @property
    def snapshots(self) -> SnapshotsSubCollectionClient[T]:
        """The client for retrieving queue resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource IDs
        that own the existing queue snapshots sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/queues/1/snapshots
            client.queues.existing_drafts.get_by_id(1)

            # GET /api/v1/queues/1/snapshots/2
            client.queues.existing_drafts.get_by_id(1, snapshot_id=2)
        """
        return self._snapshots

    @property
    def tags(self) -> TagsSubCollectionClient[T]:
        """
        The client for managing the tags sub-collection owned by the /queues collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource IDs
        that own the tags sub-collection. Below are examples of how HTTP requests to
        this sub-collection translate into method calls for an active Python Dioptra
        Python client called ``client``::

            # GET /api/v1/queues/1/tags
            client.queues.tags.get(1)

            # PUT /api/v1/queues/1/tags
            client.queues.tags.modify(1, ids=[2, 3])

            # POST /api/v1/queues/1/tags
            client.queues.tags.modify(1, ids=[2, 3])

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
    ) -> T:
        """Get a list of queues.

        Args:
            group_id: The group ID the queues belong to. If None, return queues from all
                groups that the user has access to.
            index: The paging index.
            page_length: The maximum number of queues to return in the paged response.
            sort_by: The field to use to sort the returned list.
            descending: Sort the returned list in descending order.
            search: Search for queues using the Dioptra API's query language.

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

    def get_by_id(self, queue_id: str | int) -> T:
        """Get the queue matching the provided id.

        Args:
            queue_id: The queue id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(queue_id))

    def create(self, group_id: int, name: str, description: str | None = None) -> T:
        """Creates a queue.

        Args:
            group_id: The ID of the group that will own the queue.
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
    ) -> T:
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

    def delete_by_id(self, queue_id: str | int) -> T:
        """Delete the queue matching the provided id.

        Args:
            queue_id: The queue id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, str(queue_id))
