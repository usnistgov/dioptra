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
)
from .snapshots import SnapshotsSubCollectionClient
from .tags import TagsSubCollectionClient
from .utils import FileTypes

PLUGINS_DRAFT_FIELDS: Final[set[str]] = {"name", "description"}
PLUGIN_FILES_DRAFT_FIELDS: Final[set[str]] = {
    "filename",
    "contents",
    "tasks",
    "description",
}

FILES: Final[str] = "files"
BUNDLE: Final[str] = "bundle"

T = TypeVar("T")


class PluginFilesSubCollectionClient(SubCollectionClient[T]):
    """The client for managing Dioptra's /plugins collection.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str] = "files"

    def __init__(
        self,
        session: DioptraSession[T],
        root_collection: CollectionClient[T],
        parent_sub_collections: list["SubCollectionClient[T]"] | None = None,
    ) -> None:
        """Initialize the PluginFilesSubCollectionClient instance.

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
        self._new_resource_drafts = NewResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=PLUGIN_FILES_DRAFT_FIELDS,
                resource_name=f"plugin {self.name}",
            ),
            root_collection=root_collection,
            parent_sub_collections=[self],
        )
        self._modify_resource_drafts = ModifyResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=PLUGIN_FILES_DRAFT_FIELDS,
                resource_name=f"plugin {self.name}",
            ),
            root_collection=root_collection,
            parent_sub_collections=[self],
        )
        self._snapshots = SnapshotsSubCollectionClient[T](
            session=session,
            root_collection=root_collection,
            parent_sub_collections=[self],
        )
        self._tags = TagsSubCollectionClient[T](
            session=session,
            root_collection=root_collection,
            parent_sub_collections=[self],
        )

    @property
    def new_resource_drafts(self) -> NewResourceDraftsSubCollectionClient[T]:
        """The client for managing the new plugin file drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the new plugin file drafts sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/plugins/1/files/drafts
            client.plugins.files.new_resource_drafts.get(1)

            # GET /api/v1/plugins/1/files/drafts/1
            client.plugins.files.new_resource_drafts.get_by_id(1, draft_id=1)

            # PUT /api/v1/plugins/1/files/drafts/1
            client.plugins.files.new_resource_drafts.modify(
                1,
                draft_id=1,
                filename="new_name.py",
                contents="",
                tasks=[],
                description="new-description"
            )

            # POST /api/v1/plugins/1/files/drafts
            client.plugins.files.new_resource_drafts.create(
                1,
                filename="name.py",
                contents="",
                tasks=[],
                description="description"
            )

            # DELETE /api/v1/plugins/1/files/drafts/1
            client.plugins.files.new_resource_drafts.delete(1, draft_id=1)
        """
        return self._new_resource_drafts

    @property
    def modify_resource_drafts(self) -> ModifyResourceDraftsSubCollectionClient[T]:
        """The client for managing the plugin file modification drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the plugin file modification drafts sub-collection. Below are examples
        of how HTTP requests to this sub-collection translate into method calls for an
        active Python Dioptra Python client called ``client``::

            # GET /api/v1/plugins/1/files/2/draft
            client.plugins.files.modify_resource_drafts.get_by_id(1, 2)

            # PUT /api/v1/plugins/1/files/2/draft
            client.plugins.files.modify_resource_drafts.modify(
                1,
                2,
                resource_snapshot_id=1,
                filename="new_name.py",
                contents="",
                tasks=[],
                description="new-description"
            )

            # POST /api/v1/plugins/1/files/2/draft
            client.plugins.files.modify_resource_drafts.create(
                1,
                2,
                filename="name.py",
                contents="",
                tasks=[],
                description="description"
            )

            # DELETE /api/v1/plugins/1/files/2/draft
            client.plugins.files.modify_resource_drafts.delete(1, 2)
        """
        return self._modify_resource_drafts

    @property
    def snapshots(self) -> SnapshotsSubCollectionClient[T]:
        """The client for retrieving plugin file resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the plugin file snapshots sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/plugins/1/files/2/snapshots
            client.plugins.files.snapshots.get(1, 2)

            # GET /api/v1/plugins/1/files/2/snapshots/3
            client.plugins.files.snapshots.get_by_id(1, 2, snapshot_id=3)
        """
        return self._snapshots

    @property
    def tags(self) -> TagsSubCollectionClient[T]:
        """The client for managing the plugin file tags sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the tags sub-collection. Below are examples of how HTTP requests to
        this sub-collection translate into method calls for an active Python Dioptra
        Python client called ``client``::

            # GET /api/v1/plugins/1/files/2/tags
            client.plugins.files.tags.get(1, 2)

            # PUT /api/v1/plugins/1/files/2/tags
            client.plugins.files.tags.modify(1, 2, ids=[3, 4])

            # POST /api/v1/plugins/1/files/2/tags
            client.plugins.files.tags.append(1, 2, ids=[3, 4])

            # DELETE /api/v1/plugins/1/files/2/tags/3
            client.plugins.files.tags.remove(1, 2, tag_id=3)

            # DELETE /api/v1/plugins/1/files/2/tags
            client.plugins.files.tags.remove(1, 2)
        """
        return self._tags

    def get(
        self,
        plugin_id: int | str,
        index: int = 0,
        page_length: int = 10,
        sort_by: str | None = None,
        descending: bool | None = None,
        search: str | None = None,
    ) -> T:
        """Get a list of plugin files for a specific plugin.

        Args:
            plugin_id: The id for the plugin that owns the plugin files.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of plugins to return in the paged response.
                Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for plugins using the Dioptra API's query language. Optional,
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

        return self._session.get(
            self.build_sub_collection_url(plugin_id),
            params=params,
        )

    def get_by_id(self, plugin_id: str | int, plugin_file_id: str | int) -> T:
        """Get the plugin file matching the provided ids.

        Args:
            plugin_id: The id for the plugin that owns the plugin file.
            plugin_file_id: The plugin file id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(
            self.build_sub_collection_url(plugin_id),
            str(plugin_file_id),
        )

    def create(
        self,
        plugin_id: str | int,
        filename: str,
        contents: str,
        function_tasks: list[dict[str, Any]] | None = None,
        artifact_tasks: list[dict[str, Any]] | None = None,
        description: str | None = None,
    ) -> T:
        """Creates a plugin file.

        Either function_tasks or artifact_tasks should be provided. Mixing the two
        types of tasks is not recommended.

        Args:
            plugin_id: The id for the plugin that will own the new plugin file.
            filename: The filename for the new plugin file.
            contents: The contents of the new Python file.
            function_tasks: The information needed to register plugin function tasks
                contained in the plugin file, a list. Can be empty.
            artifact_tasks: The information needed to register plugin artfiact tasks
                contained in the plugin file, a list. Can be empty.
            description: The description of the new plugin file. Optional, defaults to
                None.

        Returns:
            The response from the Dioptra API.
        """
        tasks: dict[str, list[dict[str, Any]]] = {}
        json_ = {
            "filename": filename,
            "contents": contents,
            "tasks": tasks,
        }

        if function_tasks is not None:
            tasks["functions"] = function_tasks

        if artifact_tasks is not None:
            tasks["artifacts"] = artifact_tasks

        if description is not None:
            json_["description"] = description

        return self._session.post(self.build_sub_collection_url(plugin_id), json_=json_)

    def modify_by_id(
        self,
        plugin_id: str | int,
        plugin_file_id: str | int,
        filename: str,
        contents: str,
        function_tasks: list[dict[str, Any]] | None = None,
        artifact_tasks: list[dict[str, Any]] | None = None,
        description: str | None = None,
    ) -> T:
        """Modify a plugin file matching the provided ids.

        Either function_tasks or artifact_tasks should be provided. Mixing the two
        types of tasks is not recommended.

        Args:
            plugin_id: The id for the plugin that owns the plugin file.
            plugin_file_id: The plugin file id, an integer.
            filename: The filename for the new plugin file.
            contents: The contents of the new Python file.
            function_tasks: The information needed to register plugin function tasks
                contained in the plugin file, a list. Can be empty.
            artifact_tasks: The information needed to register plugin artfiact tasks
                contained in the plugin file, a list. Can be empty.
            description: The description of the new plugin file. Optional, defaults to
                None.

        Returns:
            The response from the Dioptra API.
        """
        tasks: dict[str, list[dict[str, Any]]] = {}
        json_ = {
            "filename": filename,
            "contents": contents,
            "tasks": tasks,
        }

        if function_tasks is not None:
            tasks["functions"] = function_tasks

        if artifact_tasks is not None:
            tasks["artifacts"] = artifact_tasks

        if description is not None:
            json_["description"] = description

        return self._session.put(
            self.build_sub_collection_url(plugin_id), str(plugin_file_id), json_=json_
        )

    def delete_by_id(self, plugin_id: str | int, plugin_file_id: str | int) -> T:
        """Delete a plugin file.

        Args:
            plugin_id: The id for the plugin that owns the plugin file to be deleted.
            plugin_file_id: The plugin file id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(
            self.build_sub_collection_url(plugin_id), str(plugin_file_id)
        )

    def delete_all(self, plugin_id: str | int) -> T:
        """Delete all plugin files owned by the plugin matching the provided id.

        Args:
            plugin_id: The id for the plugin that owns the plugin files to be deleted.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.build_sub_collection_url(plugin_id))


class PluginsSnapshotCollectionClient(SnapshotsSubCollectionClient[T]):
    def __init__(
        self,
        session: DioptraSession[T],
        root_collection: "PluginsCollectionClient[T]",
    ):
        super().__init__(session=session, root_collection=root_collection)

    def get_files_bundle(
        self,
        plugin_id: str | int,
        plugin_snapshot_id: str | int,
        file_type: FileTypes = FileTypes.TAR_GZ,
        output_dir: Path | None = None,
        file_stem: str = "task-plugins",
    ) -> Path:
        """Get the task plugins bundle for the entrypoint matching the provided
            snapshot id.

        Args:
            entrypoint_id: The entrypoint id, an integer.
            entrypoint_snapshot_id: The entrypoint snapshot id, an integer.
            file_type: The file type of the bundle that is returned, defaults to None.
                If None is provided, then a default of FileTypes.TAR_GZ is used.
            output_dir: the directory to save the downloaded artifact,
                defaults to None. If None, then the current working directory will be
                used.
            file_stem: the file prefix or stem to use for the name of the
                downloaded file. Defaults to the value of "task-plugins".
        Returns:
            The response from the Dioptra API.
        """
        bundle_path = (
            Path(file_stem).with_suffix(file_type.suffix)
            if output_dir is None
            else Path(output_dir, file_stem).with_suffix(file_type.suffix)
        )
        params = {"fileType": file_type.value}

        return self._session.download(
            self.build_sub_collection_url(plugin_id),
            str(plugin_snapshot_id),
            FILES,
            BUNDLE,
            output_path=bundle_path,
            params=params,
        )


class PluginsCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /plugins collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "plugins"

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the PluginsCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)
        self._files = PluginFilesSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._new_resource_drafts = NewResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=PLUGINS_DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
        )
        self._modify_resource_drafts = ModifyResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=PLUGINS_DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
        )
        self._snapshots = PluginsSnapshotCollectionClient[T](
            session=session, root_collection=self
        )
        self._tags = TagsSubCollectionClient[T](session=session, root_collection=self)

    @property
    def files(self) -> PluginFilesSubCollectionClient[T]:
        """The client for managing the plugin files sub-collection."""
        return self._files

    @property
    def new_resource_drafts(self) -> NewResourceDraftsSubCollectionClient[T]:
        """The client for managing the new plugin drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the new plugin drafts sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/plugins/drafts
            client.plugins.new_resource_drafts.get()

            # GET /api/v1/plugins/drafts/1
            client.plugins.new_resource_drafts.get_by_id(draft_id=1)

            # PUT /api/v1/plugins/drafts/1
            client.plugins.new_resource_drafts.modify(
                draft_id=1, name="new-name", description="new-description"
            )

            # POST /api/v1/plugins/drafts
            client.plugins.new_resource_drafts.create(
                group_id=1, name="name", description="description"
            )

            # DELETE /api/v1/plugins/drafts/1
            client.plugins.new_resource_drafts.delete(draft_id=1)
        """
        return self._new_resource_drafts

    @property
    def modify_resource_drafts(self) -> ModifyResourceDraftsSubCollectionClient[T]:
        """The client for managing the plugin modification drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the plugin modification drafts sub-collection. Below are examples of
        how HTTP requests to this sub-collection translate into method calls for an
        active Python Dioptra Python client called ``client``::

            # GET /api/v1/plugins/1/draft
            client.plugins.modify_resource_drafts.get_by_id(1)

            # PUT /api/v1/plugins/1/draft
            client.plugins.modify_resource_drafts.modify(
                1,
                resource_snapshot_id=1,
                name="new-name",
                description="new-description"
            )

            # POST /api/v1/plugins/1/draft
            client.plugins.modify_resource_drafts.create(
                1, name="name", description="description"
            )

            # DELETE /api/v1/plugins/1/draft
            client.plugins.modify_resource_drafts.delete(1)
        """
        return self._modify_resource_drafts

    @property
    def snapshots(self) -> PluginsSnapshotCollectionClient[T]:
        """The client for retrieving plugin resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the plugin snapshots sub-collection. Below are examples of how HTTP
        requests to this sub-collection translate into method calls for an active Python
        Dioptra Python client called ``client``::

            # GET /api/v1/plugins/1/snapshots
            client.plugins.snapshots.get(1)

            # GET /api/v1/plugins/1/snapshots/2
            client.plugins.snapshots.get_by_id(1, snapshot_id=2)

            # GET /api/v1/plugins/1/snapshots/2/files/bundle?fileType=tar_gz
            client.plugins.snapshots.get_files_bundle(1, snapshot_id=2)
        """
        return self._snapshots

    @property
    def tags(self) -> TagsSubCollectionClient[T]:
        """The client for managing the plugin tags sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the tags sub-collection. Below are examples of how HTTP requests to
        this sub-collection translate into method calls for an active Python Dioptra
        Python client called ``client``::

            # GET /api/v1/plugins/1/tags
            client.plugins.tags.get(1)

            # PUT /api/v1/plugins/1/tags
            client.plugins.tags.modify(1, ids=[2, 3])

            # POST /api/v1/plugins/1/tags
            client.plugins.tags.append(1, ids=[2, 3])

            # DELETE /api/v1/plugins/1/tags/3
            client.plugins.tags.remove(1, tag_id=3)

            # DELETE /api/v1/plugins/1/tags
            client.plugins.tags.remove(1)
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
        """Get a list of plugins.

        Args:
            group_id: The group id the plugins belong to. If None, return plugins from
                all groups that the user has access to. Optional, defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of plugins to return in the paged response.
                Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for plugins using the Dioptra API's query language. Optional,
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

    def get_by_id(self, plugin_id: str | int) -> T:
        """Get the plugin matching the provided id.

        Args:
            plugin_id: The plugin id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(plugin_id))

    def create(self, group_id: int, name: str, description: str | None = None) -> T:
        """Creates a plugin.

        Args:
            group_id: The id of the group that will own the plugin.
            name: The name of the new plugin.
            description: The description of the new plugin. Optional, defaults to None.

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
        self, plugin_id: str | int, name: str, description: str | None
    ) -> T:
        """Modify the plugin matching the provided id.

        Args:
            plugin_id: The plugin id, an integer.
            name: The new name of the plugin.
            description: The new description of the plugin. To remove the description,
                pass None.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"name": name}

        if description is not None:
            json_["description"] = description

        return self._session.put(self.url, str(plugin_id), json_=json_)

    def delete_by_id(self, plugin_id: str | int) -> T:
        """Delete the plugin matching the provided id.

        Args:
            plugin_id: The plugin id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, str(plugin_id))
