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

DRAFT_FIELDS: Final[set[str]] = {"name", "description", "structure"}

T = TypeVar("T")


class PluginParameterTypesCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /pluginParameterTypes collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "pluginParameterTypes"

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the PluginParameterTypesCollectionClient instance.

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
        self._modify_resource_drafts = ModifyResourceDraftsSubCollectionClient[T](
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
    def new_resource_drafts(self) -> NewResourceDraftsSubCollectionClient[T]:
        """The client for managing the new plugin parameter type drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the new plugin parameter type drafts sub-collection. Below are examples
        of how HTTP requests to this sub-collection translate into method calls for an
        active Python Dioptra Python client called ``client``::

            # GET /api/v1/pluginParameterTypes/drafts
            client.plugin_parameter_types.new_resource_drafts.get()

            # GET /api/v1/pluginParameterTypes/drafts/1
            client.plugin_parameter_types.new_resource_drafts.get_by_id(draft_id=1)

            # PUT /api/v1/pluginParameterTypes/drafts/1
            client.plugin_parameter_types.new_resource_drafts.modify(
                draft_id=1,
                name="new-name",
                description="new-description",
                structure=None,
            )

            # POST /api/v1/pluginParameterTypes/drafts
            client.plugin_parameter_types.new_resource_drafts.create(
                group_id=1, name="name", description="description", structure=None
            )

            # DELETE /api/v1/pluginParameterTypes/drafts/1
            client.plugin_parameter_types.new_resource_drafts.delete(draft_id=1)
        """
        return self._new_resource_drafts

    @property
    def modify_resource_drafts(self) -> ModifyResourceDraftsSubCollectionClient[T]:
        """
        The client for managing the plugin parameter type modification drafts
        sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the plugin parameter type modification drafts sub-collection. Below are
        examples of how HTTP requests to this sub-collection translate into method calls
        for an active Python Dioptra Python client called ``client``::

            # GET /api/v1/pluginParameterTypes/1/draft
            client.plugin_parameter_types.modify_resource_drafts.get_by_id(1)

            # PUT /api/v1/pluginParameterTypes/1/draft
            client.plugin_parameter_types.modify_resource_drafts.modify(
                1, name="new-name", description="new-description", structure=None
            )

            # POST /api/v1/pluginParameterTypes/1/draft
            client.plugin_parameter_types.modify_resource_drafts.create(
                1, name="name", description="description", structure=None
            )

            # DELETE /api/v1/pluginParameterTypes/1/draft
            client.plugin_parameter_types.modify_resource_drafts.delete(1)
        """
        return self._modify_resource_drafts

    @property
    def snapshots(self) -> SnapshotsSubCollectionClient[T]:
        """The client for retrieving plugin parameter type resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the plugin parameter type snapshots sub-collection. Below are examples
        of how HTTP requests to this sub-collection translate into method calls for an
        active Python Dioptra Python client called ``client``::

            # GET /api/v1/pluginParameterTypes/1/snapshots
            client.plugin_parameter_types.snapshots.get(1)

            # GET /api/v1/pluginParameterTypes/1/snapshots/2
            client.plugin_parameter_types.snapshots.get_by_id(1, snapshot_id=2)
        """
        return self._snapshots

    @property
    def tags(self) -> TagsSubCollectionClient[T]:
        """
        The client for managing the tags sub-collection owned by the
        /pluginParameterTypes collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the tags sub-collection. Below are examples of how HTTP requests to
        this sub-collection translate into method calls for an active Python Dioptra
        Python client called ``client``::

            # GET /api/v1/pluginParameterTypes/1/tags
            client.plugin_parameter_types.tags.get(1)

            # PUT /api/v1/pluginParameterTypes/1/tags
            client.plugin_parameter_types.tags.modify(1, ids=[2, 3])

            # POST /api/v1/pluginParameterTypes/1/tags
            client.plugin_parameter_types.tags.append(1, ids=[2, 3])

            # DELETE /api/v1/pluginParameterTypes/1/tags/3
            client.plugin_parameter_types.tags.remove(1, tag_id=3)

            # DELETE /api/v1/pluginParameterTypes/1/tags
            client.plugin_parameter_types.tags.remove(1)
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
        """Get a list of plugin parameter types.

        Args:
            group_id: The group id the plugin parameter types belong to. If None, return
                plugin parameter types from all groups that the user has access to.
                Optional, defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of plugin parameter types to return in the
                paged response. Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for plugin parameter types using the Dioptra API's query
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

    def get_by_id(self, plugin_parameter_type_id: str | int) -> T:
        """Get the plugin parameter type matching the provided id.

        Args:
            plugin_parameter_type_id: The plugin parameter type id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(plugin_parameter_type_id))

    def create(
        self,
        group_id: int,
        name: str,
        description: str | None = None,
        structure: dict[str, Any] | None = None,
    ) -> T:
        """Creates a plugin parameter type.

        Args:
            group_id: The id of the group that will own the plugin parameter type.
            name: The name of the new plugin parameter type.
            description: The description of the new plugin parameter type. Optional,
                defaults to None.
            structure: Used to declare the internal structure of a plugin parameter
                type. If None, then the plugin parameter type is a simple type.
                Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {
            "group": group_id,
            "name": name,
        }

        if description is not None:
            json_["description"] = description

        if structure is not None:
            json_["structure"] = structure

        return self._session.post(self.url, json_=json_)

    def modify_by_id(
        self,
        plugin_parameter_type_id: str | int,
        name: str,
        description: str | None,
        structure: dict[str, Any] | None,
    ) -> T:
        """Modify the plugin parameter type matching the provided id.

        Args:
            plugin_parameter_type_id: The plugin parameter type id, an integer.
            name: The new name of the plugin parameter type.
            description: The new description of the plugin parameter type. To remove the
                description, pass None.
            structure: The internal structure of a plugin type. If None, then the
                plugin parameter type is a simple type. To convert a structured type to
                a simple type, pass None. Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {"name": name}

        if description is not None:
            json_["description"] = description

        if structure is not None:
            json_["structure"] = structure

        return self._session.put(self.url, str(plugin_parameter_type_id), json_=json_)

    def delete_by_id(self, plugin_parameter_type_id: str | int) -> T:
        """Delete the plugin parameter type matching the provided id.

        Args:
            plugin_parameter_type_id: The plugin parameter type id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, str(plugin_parameter_type_id))
