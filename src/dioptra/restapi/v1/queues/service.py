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
"""The server-side functions that perform queue endpoint operations."""
from __future__ import annotations

from typing import Any, Final

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError, SearchNotImplementedError
from dioptra.restapi.v1.groups.service import GroupIdService

from .errors import QueueAlreadyExistsError, QueueDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "queue"


class QueueService(object):
    """The service methods for registering and managing queues by their unique id."""

    @inject
    def __init__(
        self,
        queue_name_service: QueueNameService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the queue service.

        All arguments are provided via dependency injection.

        Args:
            queue_name_service: A QueueNameService object.
            group_id_service: A GroupIdService object.
        """
        self._queue_name_service = queue_name_service
        self._group_id_service = group_id_service

    def create(
        self,
        name: str,
        description: str,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> models.Queue:
        """Create a new queue.

        Args:
            name: The name of the queue. The combination of name and group_id must be
                unique.
            description: The description of the queue.
            group_id: The group that will own the queue.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created queue object.

        Raises:
            QueueAlreadyExistsError: If a queue with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if self._queue_name_service.get(name, group_id=group_id, log=log) is not None:
            log.debug("Queue name already exists", name=name, group_id=group_id)
            raise QueueAlreadyExistsError

        group = self._group_id_service.get(group_id, error_if_not_found=True)

        resource = models.Resource(resource_type="queue", owner=group)
        new_queue = models.Queue(
            name=name, description=description, resource=resource, creator=current_user
        )
        db.session.add(new_queue)

        if commit:
            db.session.commit()
            log.debug(
                "Queue registration successful",
                queue_id=new_queue.resource_id,
                name=new_queue.name,
            )

        return new_queue

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> Any:
        """Fetch a list of queues, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of queues to be returned.

        Returns:
            A tuple containing a list of queues and the total number of queues matching
            the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when counting
                the number of queues.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of queues")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            log.debug("Searching is not implemented", search_string=search_string)
            raise SearchNotImplementedError

        stmt = (
            select(func.count(models.Queue.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Queue.resource_snapshot_id,
            )
        )
        total_num_queues = db.session.scalars(stmt).first()

        if total_num_queues is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_queues == 0:
            return [], total_num_queues

        stmt = (
            select(models.Queue)  # type: ignore
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Queue.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        queues = db.session.scalars(stmt).all()

        return queues, total_num_queues


class QueueIdService(object):
    """The service methods for registering and managing queues by their unique id."""

    @inject
    def __init__(
        self,
        queue_name_service: QueueNameService,
    ) -> None:
        """Initialize the queue service.

        All arguments are provided via dependency injection.

        Args:
            queue_name_service: A QueueNameService object.
        """
        self._queue_name_service = queue_name_service

    def get(
        self,
        queue_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.Queue | None:
        """Fetch a queue by its unique id.

        Args:
            queue_id: The unique id of the queue.
            error_if_not_found: If True, raise an error if the queue is not found.
                Defaults to False.

        Returns:
            The queue object if found, otherwise None.

        Raises:
            QueueDoesNotExistError: If the queue is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get queue by id", queue_id=queue_id)

        stmt = (
            select(models.Queue)
            .join(models.Resource)
            .where(
                models.Queue.resource_id == queue_id,
                models.Queue.resource_snapshot_id == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        queue = db.session.scalars(stmt).first()

        if queue is None:
            if error_if_not_found:
                log.debug("Queue not found", queue_id=queue_id)
                raise QueueDoesNotExistError

            return None

        return queue

    def modify(
        self,
        queue_id: int,
        name: str,
        description: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> models.Queue | None:
        """Rename a queue.

        Args:
            queue_id: The unique id of the queue.
            name: The new name of the queue.
            description: The new description of the queue.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated queue object.

        Raises:
            QueueDoesNotExistError: If the queue is not found and `error_if_not_found`
                is True.
            QueueAlreadyExistsError: If the queue name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        queue = self.get(queue_id, error_if_not_found=error_if_not_found, log=log)

        if queue is None:
            return None

        group_id = queue.resource.group_id
        if (
            name != queue.name
            and self._queue_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Queue name already exists", name=name, group_id=group_id)
            raise QueueAlreadyExistsError

        new_queue = models.Queue(
            name=name,
            description=description,
            resource=queue.resource,
            creator=current_user,
        )
        db.session.add(new_queue)

        if commit:
            db.session.commit()
            log.debug(
                "Queue modification successful",
                queue_id=queue_id,
                name=name,
                description=description,
            )

        return new_queue

    def delete(self, queue_id: int, **kwargs) -> dict[str, Any]:
        """Delete a queue.

        Args:
            queue_id: The unique id of the queue.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=queue_id, resource_type=RESOURCE_TYPE, is_deleted=False
        )
        queue_resource = db.session.scalars(stmt).first()

        if queue_resource is None:
            raise QueueDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type="delete",
            resource=queue_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Queue deleted", queue_id=queue_id)

        return {"status": "Success", "queue_id": queue_id}


class QueueNameService(object):
    """The service methods for managing queues by their name."""

    def get(
        self,
        name: str,
        group_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.Queue | None:
        """Fetch a queue by its name.

        Args:
            name: The name of the queue.
            group_id: The the group id of the queue.
            error_if_not_found: If True, raise an error if the queue is not found.
                Defaults to False.

        Returns:
            The queue object if found, otherwise None.

        Raises:
            QueueDoesNotExistError: If the queue is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get queue by name", queue_name=name, group_id=group_id)

        stmt = (
            select(models.Queue)
            .join(models.Resource)
            .where(
                models.Queue.name == name,
                models.Resource.group_id == group_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Queue.resource_snapshot_id,
            )
        )
        queue = db.session.scalars(stmt).first()

        if queue is None:
            if error_if_not_found:
                log.debug("Queue not found", name=name)
                raise QueueDoesNotExistError

            return None

        return queue
