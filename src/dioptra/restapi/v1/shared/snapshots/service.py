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
"""The server-side functions that perform snapshots sub endpoint operations."""
from __future__ import annotations

from typing import Any, Type

import structlog
from injector import inject
from sqlalchemy import func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError, ResourceDoesNotExistError
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class ResourceSnapshotsService(object):
    @inject
    def __init__(
        self,
        resource_model: Type[models.ResourceSnapshot],
        resource_type: str,
        searchable_fields: dict[str, Any],
    ) -> None:
        """Initialize the draft service.

        Args:
            resource_model:
            resource_type:
            searchable_fields:
        """
        self.resource_model = resource_model
        self._resource_type = resource_type
        self._searchable_fields = searchable_fields

    def get(
        self,
        resource_id: int,
        search_string: str,
        page_index: int,
        page_length: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> tuple[list[dict[str, Any]], int] | None:
        """Fetch a list of snapshots of a resource.

        Args:
            resource_id: The unique id of the resource.
            search_string: A search string used to filter results.
            page_index: The index of the first snapshot to be returned.
            page_length: The maximum number of snapshots to be returned.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.

        Returns:
            The list of resource snapshots of the resource object if found, otherwise
                None.

        Raises:
            ResourceDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get resource snapshots by id", resource_id=resource_id)

        stmt = select(models.Resource).filter_by(
            resource_id=resource_id, resource_type=self._resource_type, is_deleted=False
        )
        resource = db.session.scalars(stmt).first()

        if resource is None:
            if error_if_not_found:
                log.debug("Resource not found", resource_id=resource_id)
                raise ResourceDoesNotExistError

            return None

        filters = list()

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, self._searchable_fields)
            )

        stmt = (
            select(func.count(self.resource_model.resource_id))  # type: ignore
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.resource_id == resource_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        total_num_snapshots = db.session.scalars(stmt).unique().first()

        if total_num_snapshots is None:
            log.error(
                "The database query returned a None when counting the number of "
                "snapshots when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_snapshots == 0:
            return [], total_num_snapshots

        stmt = (
            select(self.resource_model)
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.resource_id == resource_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
            .order_by(self.resource_model.created_on)
            .offset(page_index)
            .limit(page_length)
        )
        snapshots = [
            {self._resource_type: snapshot, "has_draft": None}
            for snapshot in db.session.scalars(stmt).unique()
        ]

        return snapshots, total_num_snapshots


class ResourceSnapshotsIdService(object):
    @inject
    def __init__(
        self,
        resource_model: Type[models.ResourceSnapshot],
        resource_type: str,
    ) -> None:
        """Initialize the draft service.

        Args:
            resource_model: model
            resource_type: type
        """
        self.resource_model = resource_model
        self._resource_type = resource_type

    def get(
        self,
        resource_id: int,
        snapshot_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Fetch a specific snapshot of a resource.

        Args:
            resource_id: The unique id of the resource.
            snapshot_id: A search string used to filter results.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.

        Returns:
            The requested snapshot the resource object if found, otherwise None.

        Raises:
            ResourceDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get resource snapshot by id", resource_id=resource_id)

        stmt = select(models.Resource).filter_by(
            resource_id=resource_id, resource_type=self._resource_type, is_deleted=False
        )
        resource = db.session.scalars(stmt).first()

        if resource is None:
            if error_if_not_found:
                log.debug("Resource not found", resource_id=resource_id)
                raise ResourceDoesNotExistError

            return None

        stmt = (
            select(self.resource_model)
            .join(models.Resource)
            .where(
                models.ResourceSnapshot.resource_snapshot_id == snapshot_id,
                models.Resource.resource_id == resource_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        snapshot = db.session.scalars(stmt).first()

        if snapshot is None:
            if error_if_not_found:
                log.debug("Resource snapshot not found", snapshot_id=snapshot_id)
                raise ResourceDoesNotExistError

            return None

        return {self._resource_type: snapshot, "has_draft": None}
