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

from .base import (
    CollectionClient,
    DioptraClientError,
    DioptraSession,
    SubCollectionClient,
)
from .drafts import (
    ModifyResourceDraftsSubCollectionClient,
    NewResourceDraftsSubCollectionClient,
    make_draft_fields_validator,
    make_field_names_to_camel_case_converter,
)
from .snapshots import SnapshotsSubCollectionClient
from .tags import TagsSubCollectionClient

DRAFT_FIELDS: Final[set[str]] = {
    "name",
    "description",
    "taskGraph",
    "parameters",
    "queues",
    "plugins",
}
MODIFY_DRAFT_FIELDS: Final[set[str]] = {
    "name",
    "description",
    "taskGraph",
    "parameters",
    "queues",
}
FIELD_NAMES_TO_CAMEL_CASE: Final[dict[str, str]] = {
    "task_graph": "taskGraph",
}

T = TypeVar("T")


class EntrypointPluginsSubCollectionClient(SubCollectionClient[T]):
    """The client for managing Dioptra's /entrypoints/{id}/plugins sub-collection.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str] = "plugins"

    def __init__(
        self,
        session: DioptraSession[T],
        root_collection: CollectionClient[T],
        parent_sub_collections: list["SubCollectionClient[T]"] | None = None,
    ) -> None:
        """Initialize the EntrypointPluginsSubCollectionClient instance.

        Args:
            session: The Dioptra API session object.
            root_collection: The client for the root collection that owns this
                sub-collection.
            parent_sub_collections: Unused in this client, must be None.
        """
        if parent_sub_collections is not None:
            raise DioptraClientError(
                "The parent_sub_collections argument must be None for this client."
            )

        super().__init__(
            session=session,
            root_collection=root_collection,
            parent_sub_collections=parent_sub_collections,
        )

    def get(self, entrypoint_id: int | str) -> T:
        """Get a list of plugins added to the entrypoint.

        Args:
            entrypoint_id: The entrypoint id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.build_sub_collection_url(entrypoint_id))

    def get_by_id(self, entrypoint_id: str | int, plugin_id: str | int) -> T:
        """Get the entrypoint plugin matching the provided id.

        Args:
            entrypoint_id: The entrypoint id, an integer.
            plugin_id: The id for the plugin that will be removed.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(
            self.build_sub_collection_url(entrypoint_id), str(plugin_id)
        )

    def create(
        self,
        entrypoint_id: str | int,
        plugin_ids: list[int],
    ) -> T:
        """Adds one or more plugins to the entrypoint.

        If a plugin id matches an plugin that is already attached to the entrypoint,
        then the entrypoint will update the plugin to the latest version.

        Args:
            entrypoint_id: The entrypoint id, an integer.
            plugin_ids: A list of plugin ids that will be registered to the entrypoint.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"plugins": plugin_ids}
        return self._session.post(
            self.build_sub_collection_url(entrypoint_id), json_=json_
        )

    def delete_by_id(self, entrypoint_id: str | int, plugin_id: str | int) -> T:
        """Remove a plugin from the entrypoint.

        Args:
            entrypoint_id: The entrypoint id, an integer.
            plugin_id: The id for the plugin that will be removed.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(
            self.build_sub_collection_url(entrypoint_id), str(plugin_id)
        )


class EntrypointQueuesSubCollectionClient(SubCollectionClient[T]):
    """The client for managing Dioptra's /entrypoints/{id}/queues sub-collection.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str] = "queues"

    def __init__(
        self,
        session: DioptraSession[T],
        root_collection: CollectionClient[T],
        parent_sub_collections: list["SubCollectionClient[T]"] | None = None,
    ) -> None:
        """Initialize the EntrypointQueuesSubCollectionClient instance.

        Args:
            session: The Dioptra API session object.
            root_collection: The client for the root collection that owns this
                sub-collection.
            parent_sub_collections: Unused in this client, must be None.
        """
        if parent_sub_collections is not None:
            raise DioptraClientError(
                "The parent_sub_collections argument must be None for this client."
            )

        super().__init__(
            session=session,
            root_collection=root_collection,
            parent_sub_collections=parent_sub_collections,
        )

    def get(self, entrypoint_id: int | str) -> T:
        """Get a list of queues added to the entrypoint.

        Args:
            entrypoint_id: The entrypoint id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.build_sub_collection_url(entrypoint_id))

    def create(
        self,
        entrypoint_id: str | int,
        queue_ids: list[int],
    ) -> T:
        """Adds one or more queues to the entrypoint.

        Args:
            entrypoint_id: The entrypoint id, an integer.
            queue_ids: A list of queue ids that will be registered to the entrypoint.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"ids": queue_ids}
        return self._session.post(
            self.build_sub_collection_url(entrypoint_id), json_=json_
        )

    def delete(self, entrypoint_id: str | int) -> T:
        """Remove all queues from the entrypoint.

        Args:
            entrypoint_id: The entrypoint id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.build_sub_collection_url(entrypoint_id))

    def modify_by_id(
        self,
        entrypoint_id: str | int,
        queue_ids: list[int],
    ) -> T:
        """Replaces the entrypoint's full list of queues.

        If an empty list is provided, then all queues will be removed from the
        entrypoint.

        Args:
            entrypoint_id: The entrypoint id, an integer.
            queue_ids: A list of queue ids that will replace the current list of
                entrypoint queues.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"ids": queue_ids}
        return self._session.put(
            self.build_sub_collection_url(entrypoint_id), json_=json_
        )

    def delete_by_id(self, entrypoint_id: str | int, queue_id: str | int) -> T:
        """Remove a queue from the entrypoint.

        Args:
            entrypoint_id: The entrypoint id, an integer.
            queue_id: The id for the queue that will be removed.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(
            self.build_sub_collection_url(entrypoint_id), str(queue_id)
        )


class EntrypointsCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /entrypoints collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "entrypoints"

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the EntrypointsCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)
        self._plugins = EntrypointPluginsSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._queues = EntrypointQueuesSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._new_resource_drafts = NewResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
            convert_field_names_fn=make_field_names_to_camel_case_converter(
                name_mapping=FIELD_NAMES_TO_CAMEL_CASE
            ),
        )
        self._modify_resource_drafts = ModifyResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=MODIFY_DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
            convert_field_names_fn=make_field_names_to_camel_case_converter(
                name_mapping=FIELD_NAMES_TO_CAMEL_CASE
            ),
        )
        self._snapshots = SnapshotsSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._tags = TagsSubCollectionClient[T](session=session, root_collection=self)

    @property
    def plugins(self) -> EntrypointPluginsSubCollectionClient[T]:
        """The client for managing the plugins sub-collection."""
        return self._plugins

    @property
    def queues(self) -> EntrypointQueuesSubCollectionClient[T]:
        """The client for managing the queues sub-collection."""
        return self._queues

    @property
    def new_resource_drafts(self) -> NewResourceDraftsSubCollectionClient[T]:
        """The client for managing the new entrypoint drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the new entrypoint drafts sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/entrypoints/drafts
            client.entrypoints.new_resource_drafts.get()

            # GET /api/v1/entrypoints/drafts/1
            client.entrypoints.new_resource_drafts.get_by_id(draft_id=1)

            # PUT /api/v1/entrypoints/drafts/1
            client.entrypoints.new_resource_drafts.modify(
                draft_id=1, name="new-name", description="new-description"
            )

            # POST /api/v1/entrypoints/drafts
            client.entrypoints.new_resource_drafts.create(
                group_id=1, name="name", description="description"
            )

            # DELETE /api/v1/entrypoints/drafts/1
            client.entrypoints.new_resource_drafts.delete(draft_id=1)
        """
        return self._new_resource_drafts

    @property
    def modify_resource_drafts(self) -> ModifyResourceDraftsSubCollectionClient[T]:
        """The client for managing the entrypoint modification drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the entrypoint modification drafts sub-collection. Below are examples
        of how HTTP requests to this sub-collection translate into method calls for an
        active Python Dioptra Python client called ``client``::

            # GET /api/v1/entrypoints/1/draft
            client.entrypoints.modify_resource_drafts.get_by_id(1)

            # PUT /api/v1/entrypoints/1/draft
            client.entrypoints.modify_resource_drafts.modify(
                1,
                resource_snapshot_id=1,
                name="new-name",
                description="new-description"
            )

            # POST /api/v1/entrypoints/1/draft
            client.entrypoints.modify_resource_drafts.create(
                1, name="name", description="description"
            )

            # DELETE /api/v1/entrypoints/1/draft
            client.entrypoints.modify_resource_drafts.delete(1)
        """
        return self._modify_resource_drafts

    @property
    def snapshots(self) -> SnapshotsSubCollectionClient[T]:
        """The client for retrieving entrypoint resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the entrypoint snapshots sub-collection. Below are examples of how HTTP
        requests to this sub-collection translate into method calls for an active Python
        Dioptra Python client called ``client``::

            # GET /api/v1/entrypoints/1/snapshots
            client.entrypoints.snapshots.get(1)

            # GET /api/v1/entrypoints/1/snapshots/2
            client.entrypoints.snapshots.get_by_id(1, snapshot_id=2)
        """
        return self._snapshots

    @property
    def tags(self) -> TagsSubCollectionClient[T]:
        """
        The client for managing the tags sub-collection owned by the /entrypoints
        collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the tags sub-collection. Below are examples of how HTTP requests to
        this sub-collection translate into method calls for an active Python Dioptra
        Python client called ``client``::

            # GET /api/v1/entrypoints/1/tags
            client.entrypoints.tags.get(1)

            # PUT /api/v1/entrypoints/1/tags
            client.entrypoints.tags.modify(1, ids=[2, 3])

            # POST /api/v1/entrypoints/1/tags
            client.entrypoints.tags.append(1, ids=[2, 3])

            # DELETE /api/v1/entrypoints/1/tags/3
            client.entrypoints.tags.remove(1, tag_id=3)

            # DELETE /api/v1/entrypoints/1/tags
            client.entrypoints.tags.remove(1)
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
        """Get a list of entrypoints.

        Args:
            group_id: The group id the entrypoints belong to. If None, return
                entrypoints from all groups that the user has access to. Optional,
                defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of entrypoints to return in the paged
                response. Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for entrypoints using the Dioptra API's query language.
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

    def get_by_id(self, entrypoint_id: str | int) -> T:
        """Get the entrypoint matching the provided id.

        Args:
            entrypoint_id: The entrypoint id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(entrypoint_id))

    def create(
        self,
        group_id: int,
        name: str,
        task_graph: str,
        description: str | None = None,
        parameters: list[dict[str, Any]] | None = None,
        queues: list[int] | None = None,
        plugins: list[int] | None = None,
    ) -> T:
        """Creates a entrypoint.

        Args:
            group_id: The id of the group that will own the entrypoint.
            name: The name of the new entrypoint.
            task_graph: The task graph for the new entrypoint as a YAML-formatted
                string.
            description: The description of the new entrypoint. Optional, defaults to
                None.
            parameters: The list of parameters for the new entrypoint. Optional,
                defaults to None.
            queues: A list of queue ids to associate with the new entrypoint. Optional,
                defaults to None.
            plugins: A list of plugin ids to associate with the new entrypoint.
                Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {
            "group": group_id,
            "name": name,
            "taskGraph": task_graph,
        }

        if description is not None:
            json_["description"] = description

        if parameters is not None:
            json_["parameters"] = parameters

        if queues is not None:
            json_["queues"] = queues

        if plugins is not None:
            json_["plugins"] = plugins

        return self._session.post(self.url, json_=json_)

    def modify_by_id(
        self,
        entrypoint_id: str | int,
        name: str,
        task_graph: str,
        description: str | None,
        parameters: list[dict[str, Any]] | None,
        queues: list[int] | None,
    ) -> T:
        """Modify the entrypoint matching the provided id.

        Args:
            entrypoint_id: The entrypoint id, an integer.
            name: The new name of the entrypoint.
            task_graph: The new task graph for the entrypoint as a YAML-formatted
                string.
            description: The new description of the entrypoint. To remove the
                description, pass None.
            parameters: The new list of parameters for the entrypoint. To remove all
                parameters, pass None.
            queues: The new list of queue ids to associate with the entrypoint. To
                remove all associated queues, pass None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {"name": name, "taskGraph": task_graph}

        if description is not None:
            json_["description"] = description

        if parameters is not None:
            json_["parameters"] = parameters

        if queues is not None:
            json_["queues"] = queues

        return self._session.put(self.url, str(entrypoint_id), json_=json_)

    def delete_by_id(self, entrypoint_id: str | int) -> T:
        """Delete the entrypoint matching the provided id.

        Args:
            entrypoint_id: The entrypoint id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, str(entrypoint_id))
