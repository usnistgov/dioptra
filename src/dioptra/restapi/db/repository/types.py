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
"""
The type repository: data operations related to types
"""

from collections.abc import Iterable, Sequence, Set
from typing import Any, Final, overload

import dioptra.restapi.db.repository.utils as utils
from dioptra.restapi.db.models import (
    Group,
    PluginTaskParameterType,
    Tag,
)


class TypeRepository:
    SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "name": lambda x: PluginTaskParameterType.name.like(x, escape="/"),
        "description": lambda x: PluginTaskParameterType.description.like(
            x, escape="/"
        ),
        "tag": lambda x: PluginTaskParameterType.tags.any(Tag.name.like(x, escape="/")),
    }

    SORTABLE_FIELDS: Final[dict[str, Any]] = {
        "name": "name",
        "createdOn": "created_on",
        "lastModifiedOn": "last_modified_on",
        "description": "description",
    }

    def __init__(self, session: utils.CompatibleSession[utils.S]):
        self.session = session

    def create(
        self,
        type_: PluginTaskParameterType,
        locks: Set[utils.ResourceLockType] = frozenset(),
    ) -> None:
        """
        Create a new type resource.  This creates both the resource and the
        initial snapshot.

        Args:
            type_: The type to create
            locks: The locks to add to the type, if any

        Raises:
            EntityExistsError: if the type resource or snapshot already exists,
                or the type name collides with another type in the same group
            EntityDoesNotExistError: if the type owner or user creator does
                not exist
            EntityDeletedError: if the type, its creator, or its group owner is
                deleted
            UserNotInGroupError: if the user creator is not a member of the
                group who will own the resource
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "plugin_task_parameter_type"
        """

        utils.assert_can_create_resource(
            self.session, type_, "plugin_task_parameter_type"
        )
        utils.assert_resource_name_available(self.session, type_)

        self.session.add(type_)
        utils.add_resource_lock_types(self.session, type_, locks)

    def create_snapshot(self, type_: PluginTaskParameterType) -> None:
        """
        Create a new type snapshot.

        Args:
            type_: A PluginTaskParameterType object with the desired snapshot
                settings

        Raises:
            EntityDoesNotExistError: if the type resource or snapshot creator
                user does not exist
            EntityExistsError: if the snapshot already exists, or this new
                snapshot's type name collides with another type in the same
                group
            EntityDeletedError: if the type or snapshot creator user are
                deleted
            UserNotInGroupError: if the snapshot creator user is not a member
                of the group who owns the type
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "plugin_task_parameter_type"
            ReadOnlyLockError: if the resource has a read-only lock
        """

        utils.assert_can_create_snapshot(
            self.session, type_, "plugin_task_parameter_type"
        )
        utils.assert_snapshot_name_available(self.session, type_)

        self.session.add(type_)

    @overload
    def get(  # noqa: E704
        self,
        resource_ids: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> PluginTaskParameterType | None: ...

    @overload
    def get(  # noqa: E704
        self,
        resource_ids: Iterable[int],
        deletion_policy: utils.DeletionPolicy,
    ) -> Sequence[PluginTaskParameterType]: ...

    def get(
        self,
        resource_ids: int | Iterable[int],
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> PluginTaskParameterType | Sequence[PluginTaskParameterType] | None:
        """
        Get the latest snapshot of the given type resource(s).

        Args:
            resource_ids: A single or iterable of type resource IDs
            deletion_policy: Whether to look at deleted types, non-deleted
                types, or all types

        Returns:
            A PluginTaskParameterType/list of PluginTaskParameterType objects,
            or None/empty list if none were found with the given ID(s)
        """
        return utils.get_latest_snapshots(
            self.session, PluginTaskParameterType, resource_ids, deletion_policy
        )

    def get_one(
        self,
        resource_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> PluginTaskParameterType:
        """
        Get the latest snapshot of the given type resource; require that
        exactly one is found, or raise an exception.

        Args:
            resource_id: A resource ID
            deletion_policy: Whether to look at deleted types, non-deleted
                types, or all types

        Returns:
            A PluginTaskParameterType object

        Raises:
            EntityDoesNotExistError: if the type does not exist in the database
                (deleted or not)
            EntityExistsError: if the type exists and is not deleted, but
                policy was to find a deleted type
            EntityDeletedError: if the type is deleted, but policy was to find
                a non-deleted type
        """
        return utils.get_one_latest_snapshot(
            self.session, PluginTaskParameterType, resource_id, deletion_policy
        )

    @overload
    def get_by_name(  # type: ignore[overload-overlap]  # noqa: E704
        self,
        name: str,
        group: Group | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> PluginTaskParameterType | None: ...

    @overload
    def get_by_name(  # noqa: E704
        self,
        name: Iterable[str],
        group: Group | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Sequence[PluginTaskParameterType]: ...

    def get_by_name(
        self,
        name: str | Iterable[str],
        group: Group | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> PluginTaskParameterType | Sequence[PluginTaskParameterType] | None:
        """
        Get type(s) by name(s).  This returns the latest version(s)
        (snapshots) of the type.

        Args:
            name: A type name or names
            group: A group/group ID, to disambiguate same-named types across
                groups
            deletion_policy: Whether to look at deleted types, non-deleted
                types, or all types

        Returns:
            If a single name is passed, a type is returned, or None if one was
            not found with the given name.  If an iterable of names is passed,
            a sequence of snapshots is returned, which will be empty if none
            were found.

        Raises:
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """
        return utils.get_snapshot_by_name(
            self.session, PluginTaskParameterType, name, group, deletion_policy
        )

    def get_by_filters_paged(
        self,
        group: Group | int | None,
        filters: list[dict],
        page_start: int,
        page_length: int,
        sort_by: str | None,
        descending: bool,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[PluginTaskParameterType], int]:
        """
        Get some types according to search criteria.

        Args:
            group: Limit types to those owned by this group; None to not
                limit the search
            filters: Search criteria, see parse_search_text()
            page_start: Zero-based row index where the page should start
            page_length: Maximum number of rows in the page; use <= 0 for
                unlimited length
            sort_by: Sort criterion; must be a key of SORTABLE_FIELDS.  None
                to sort in an implementation-dependent way.
            descending: Whether to sort in descending order; only applicable
                if sort_by is given
            deletion_policy: Whether to look at deleted types, non-deleted
                types, or all types

        Returns:
            A 2-tuple including the page of types and total count of matching
            types which exist

        Raises:
            SearchParseError: if filters includes a non-searchable field
            SortParameterValidationError: if sort_by is a non-sortable field
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """

        return utils.get_by_filters_paged(
            self.session,
            PluginTaskParameterType,
            self.SORTABLE_FIELDS,
            self.SEARCHABLE_FIELDS,
            group,
            filters,
            page_start,
            page_length,
            sort_by,
            descending,
            deletion_policy,
        )

    def delete(self, type_: PluginTaskParameterType | int) -> None:
        """
        Delete a type.  No-op if the type is already deleted.

        Args:
            type_: A PluginTaskParameterType object or resource_id primary key
                value identifying a type resource

        Raises:
            EntityDoesNotExistError: if the type does not exist
        """
        utils.delete_resource(self.session, type_)
