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
The experiments repository: data operations related to experiments
"""

from collections.abc import Iterable, Sequence
from typing import Any, Final, overload

import dioptra.restapi.db.repository.utils as utils
from dioptra.restapi.db.models import (
    EntryPoint,
    Experiment,
    Group,
    Tag,
)


class ExperimentRepository:
    SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "name": lambda x: Experiment.name.like(x, escape="/"),
        "description": lambda x: Experiment.description.like(x, escape="/"),
        "tag": lambda x: Experiment.tags.any(Tag.name.like(x, escape="/")),
    }

    # Maps a general sort criterion name to an Experiment attribute name
    SORTABLE_FIELDS: Final[dict[str, str]] = {
        "name": "name",
        "createdOn": "created_on",
        "lastModifiedOn": "last_modified_on",
        "description": "description",
    }

    def __init__(self, session: utils.CompatibleSession[utils.S]):
        self.session = session

    def create(self, experiment: Experiment):
        """
        Create a new experiment resource.  This creates both the resource and
        the initial snapshot.

        Args:
            experiment: The experiment to create

        Raises:
            EntityExistsError: if the experiment resource or snapshot already
                exists, or the experiment name collides with another experiment
                in the same group
            EntityDoesNotExistError: if any child entry point doesn't exist, or
                the group owner or user creator do not exist
            EntityDeletedError: if the experiment, its creator, or its group
                owner is deleted, or if all entrypoint children exist but some
                are deleted
            UserNotInGroupError: if the experiment creator is not a member of
                the group who will own the resource
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "experiment"
        """
        utils.assert_can_create_resource(self.session, experiment, "experiment")
        utils.assert_resource_name_available(self.session, experiment)

        self.session.add(experiment)

    def create_snapshot(self, experiment: Experiment):
        """
        Create a new experiment snapshot.

        Args:
            experiment: An Experiment object with the desired snapshot settings

        Raises:
            EntityDoesNotExistError: if the experiment resource, snapshot
                creator user, or any child entry point does not exist
            EntityExistsError: if the snapshot already exists, or this new
                snapshot's experiment name collides with another experiment in
                the same group
            EntityDeletedError: if the experiment resource is deleted, snapshot
                creator user is deleted, or if all child resources exist but
                some are deleted
            UserNotInGroupError: if the snapshot creator user is not a member
                of the group who owns the experiment
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "experiment"
        """
        utils.assert_can_create_snapshot(self.session, experiment, "experiment")
        utils.assert_snapshot_name_available(self.session, experiment)

        # Assume that the new snapshot's created_on timestamp is later than the
        # current latest timestamp?

        self.session.add(experiment)

    @overload
    def get(  # noqa: E704
        self,
        resource_ids: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Experiment | None: ...

    @overload
    def get(  # noqa: E704
        self,
        resource_ids: Iterable[int],
        deletion_policy: utils.DeletionPolicy,
    ) -> Sequence[Experiment]: ...

    def get(
        self,
        resource_ids: int | Iterable[int],
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Experiment | Sequence[Experiment] | None:
        """
        Get the latest snapshot of the given experiment resource(s).

        Args:
            resource_ids: A single or iterable of experiment resource IDs
            deletion_policy: Whether to look at deleted experiments,
                non-deleted experiments, or all experiments

        Returns:
            A Experiment/list of Experiment objects, or None/empty list if
            none were found with the given ID(s)
        """
        return utils.get_latest_snapshots(
            self.session, Experiment, resource_ids, deletion_policy
        )

    def get_one(
        self,
        resource_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Experiment:
        """
        Get the latest snapshot of the given experiment resource; require that
        exactly one is found, or raise an exception.

        Args:
            resource_id: A resource ID
            deletion_policy: Whether to look at deleted experiments, non-deleted
                experiments, or all experiments

        Returns:
            An Experiment object

        Raises:
            EntityDoesNotExistError: if the resource is not found
        """
        return utils.get_one_latest_snapshot(
            self.session, Experiment, resource_id, deletion_policy
        )

    def get_by_name(
        self,
        name: str,
        group: Group | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Experiment | None:
        """
        Get an experiment by name.  This returns the latest version (snapshot)
        of the experiment.

        Args:
            name: An experiment name
            group: A group/group ID, to disambiguate same-named experiments
                across groups
            deletion_policy: Whether to look at deleted experiments,
                non-deleted experiments, or all experiments

        Returns:
            An experiment, or None if one was not found

        Raises:
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """
        return utils.get_snapshot_by_name(
            self.session, Experiment, name, group, deletion_policy
        )

    def get_entrypoints(
        self,
        experiment: Experiment | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Sequence[EntryPoint]:
        """
        Get the child entry points of the given experiment as their latest
        snapshots.  If an Experiment object is given, the returned sequence
        may be shorter than len(experiment.children) if any of the children
        don't exist, or were filtered out due to deletion policy.

        Args:
            experiment: An Experiment object or resource_id integer primary key
                value
            deletion_policy: Whether to look at deleted entry points,
                non-deleted entry points, or all entry points

        Returns:
            The entry points

        Raises:
            EntityDoesNotExistError: if parent does not exist
            EntityDeletedError: if parent is deleted
        """

        return utils.get_latest_child_snapshots(
            self.session,
            EntryPoint,
            experiment,
            deletion_policy,
        )

    def set_entrypoints(
        self,
        experiment: Experiment | int,
        children: Iterable[EntryPoint | int],
    ) -> Sequence[EntryPoint]:
        """
        Set the children of the given experiment to the given entry points.
        This replaces all existing children with the given resources.

        Args:
            experiment: An Experiment object or resource_id integer primary key
                value
            children: The entry points to set as children

        Returns:
            The new children, as their latest snapshots

        Raises:
            EntityDoesNotExistError: if experiment or any entry point not exist
            EntityDeletedError: if experiment or any entry point is deleted
        """

        child_snaps = utils.set_resource_children(
            self.session,
            EntryPoint,
            experiment,
            children,
        )

        return child_snaps

    def add_entrypoints(
        self,
        experiment: Experiment | int,
        children: Iterable[EntryPoint | int],
    ) -> list[EntryPoint]:
        """
        Add the given entry points as children of the given experiment.

        Args:
            experiment: An Experiment object or resource_id integer primary key
                value
            children: The entry points to add

        Returns:
            The complete list of entry point children, as latest snapshots
            (including both pre-existing and new children).

        Raises:
            EntityDoesNotExistError: if parent or any new child does not exist
            EntityDeletedError: if parent or any new child is deleted
        """
        return utils.append_resource_children(
            self.session, EntryPoint, experiment, children
        )

    def unlink_entrypoint(
        self,
        experiment: Experiment | int,
        entrypoint: EntryPoint | int,
    ):
        """
        "Unlink" the given child entry point from the given experiment.  This
        only severs the relationship; it does not delete either resource.  If
        there is no parent/child relationship, this is a no-op.

        Args:
            experiment: An experiment or resource_id integer primary key value
            entrypoint: An entry point or resource_id integer primary key value

        Raises:
            EntityDoesNotExistError: if parent or child do not exist
        """
        utils.unlink_child(self.session, experiment, entrypoint)

    def delete(self, experiment: Experiment | int) -> None:
        """
        Delete an experiment.  No-op if the experiment is already deleted.

        Args:
            experiment: A Experiment object or resource_id primary key value
                identifying an experiment resource

        Raises:
            EntityDoesNotExistError: if the experiment does not exist
        """

        utils.delete_resource(self.session, experiment)

    def get_by_filters_paged(
        self,
        group: Group | int | None,
        filters: list[dict],
        page_start: int,
        page_length: int,
        sort_by: str | None,
        descending: bool,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[Experiment], int]:
        """
        Get some experiments according to search criteria.

        Args:
            group: Limit experiments to those owned by this group; None to not
                limit the search
            filters: Search criteria, see parse_search_text()
            page_start: Zero-based row index where the page should start
            page_length: Maximum number of rows in the page; use <= 0 for
                unlimited length
            sort_by: Sort criterion; must be a key of SORTABLE_FIELDS.  None
                to sort in an implementation-dependent way.
            descending: Whether to sort in descending order; only applicable
                if sort_by is given
            deletion_policy: Whether to look at deleted experiments, non-deleted
                experiments, or all experiments

        Returns:
            A 2-tuple including the page of experiments and total count of
            matching experiments which exist

        Raises:
            SearchParseError: if filters includes a non-searchable field
            SortParameterValidationError: if sort_by is a non-sortable field
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """

        return utils.get_by_filters_paged(
            self.session,
            Experiment,
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
