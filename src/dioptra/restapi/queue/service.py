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

import datetime
from typing import Any, cast

import structlog
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.app import db

from .errors import QueueAlreadyExistsError, QueueDoesNotExistError, QueueLockedError
from .model import Queue, QueueLock

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class QueueService(object):
    """The service methods for registering and managing queues by their unique id."""

    @inject
    def __init__(
        self,
        name_service: QueueNameService,
    ) -> None:
        """Initialize the queue service.

        All arguments are provided via dependency injection.

        Args:
            name_service: The queue name service.
        """
        self._name_service = name_service

    def create(
        self,
        name: str,
        **kwargs,
    ) -> Queue:
        """Create a new queue.

        Args:
            name: The name of the queue.

        Returns:
            The newly created queue object.

        Raises:
            QueueAlreadyExistsError: If a queue with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if self._name_service.get(name, log=log) is not None:
            raise QueueAlreadyExistsError

        timestamp = datetime.datetime.now()
        new_queue: Queue = Queue(
            queue_id=Queue.next_id(),
            name=name,
            created_on=timestamp,
            last_modified=timestamp,
        )
        db.session.add(new_queue)
        db.session.commit()
        log.info(
            "Queue registration successful",
            queue_id=new_queue.queue_id,
            name=new_queue.name,
        )
        return new_queue

    def get(
        self,
        queue_id: int,
        unlocked_only: bool = False,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> Queue | None:
        """Fetch a queue by its unique id.

        Args:
            queue_id: The unique id of the queue.
            unlocked_only: If True, raise an error if the queue is locked. Defaults to
                False.
            error_if_not_found: If True, raise an error if the queue is not found.
                Defaults to False.

        Returns:
            The queue object if found, otherwise None.

        Raises:
            QueueDoesNotExistError: If the queue is not found and `error_if_not_found`
                is True.
            QueueLockedError: If the queue is locked and `unlocked_only` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Get queue by id", queue_id=queue_id)
        queue = Queue.query.filter_by(queue_id=queue_id, is_deleted=False).first()

        if queue is None:
            if error_if_not_found:
                log.error("Queue not found", queue_id=queue_id)
                raise QueueDoesNotExistError

            return None

        if queue.lock and unlocked_only:
            log.error("Queue is locked", queue_id=queue_id)
            raise QueueLockedError

        return cast(Queue, queue)

    def get_all(self, **kwargs) -> list[Queue]:
        """Fetch the list of all queues.

        Returns:
            A list of queues.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Get full list of queues")
        return Queue.query.filter_by(is_deleted=False).all()  # type: ignore

    def get_all_unlocked(self, **kwargs) -> list[Queue]:
        """Fetch the list of all unlocked queues.

        Returns:
            A list of queues.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Get full list of unlocked queues")
        return (  # type: ignore
            Queue.query.outerjoin(QueueLock, Queue.queue_id == QueueLock.queue_id)
            .filter(
                QueueLock.queue_id == None,  # noqa: E711
                Queue.is_deleted == False,  # noqa: E712
            )
            .all()
        )

    def rename(self, queue_id: int, new_name: str, **kwargs) -> Queue:
        """Rename a queue.

        Args:
            queue_id: The unique id of the queue.
            new_name: The new name of the queue.

        Returns:
            The updated queue object.

        Raises:
            QueueDoesNotExistError: If the queue is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        queue = cast(Queue, self.get(queue_id, error_if_not_found=True, log=log))
        queue.update(changes={"name": new_name})
        db.session.commit()
        log.info("Queue renamed", queue_id=queue.queue_id, new_name=new_name)
        return queue

    def delete(self, queue_id: int, **kwargs) -> dict[str, Any]:
        """Delete a queue.

        Args:
            queue_id: The unique id of the queue.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (queue := self.get(queue_id, log=log)) is None:
            return {"status": "Success", "id": []}

        queue.update(changes={"is_deleted": True})
        db.session.commit()
        log.info("Queue deleted", queue_id=queue_id)
        return {"status": "Success", "id": [queue_id]}

    def lock(self, queue_id: int, **kwargs) -> dict[str, Any]:
        """Lock a queue.

        Args:
            queue_id: The unique id of the queue.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            QueueDoesNotExistError: If the queue is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (queue := self.get(queue_id, error_if_not_found=True, log=log)) is None:
            return {"status": "Success", "id": []}

        queue.lock.append(QueueLock())
        db.session.commit()
        log.info("Queue locked", queue_id=queue.queue_id)
        return {"status": "Success", "id": [queue.queue_id]}

    def unlock(self, queue_id: int, **kwargs) -> dict[str, Any]:
        """Unlock a queue.

        Args:
            queue_id: The unique id of the queue.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            QueueDoesNotExistError: If the queue is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (queue := self.get(queue_id, error_if_not_found=True, log=log)) is None:
            return {"status": "Success", "id": []}

        db.session.delete(queue.lock[0])
        db.session.commit()
        log.info("Queue unlocked", queue_id=queue.queue_id)
        return {"status": "Success", "id": [queue.queue_id]}


class QueueNameService(object):
    """The service methods for managing queues by their name."""

    def get(
        self,
        queue_name: str,
        unlocked_only: bool = False,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> Queue | None:
        """Fetch a queue by its name.

        Args:
            queue_name: The name of the queue.
            unlocked_only: If True, raise an error if the queue is locked. Defaults to
                False.
            error_if_not_found: If True, raise an error if the queue is not found.
                Defaults to False.

        Returns:
            The queue object if found, otherwise None.

        Raises:
            QueueDoesNotExistError: If the queue is not found and `error_if_not_found`
                is True.
            QueueLockedError: If the queue is locked and `unlocked_only` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Get queue by name", queue_name=queue_name)
        queue = Queue.query.filter_by(name=queue_name, is_deleted=False).first()

        if queue is None:
            if error_if_not_found:
                log.error("Queue not found", name=queue_name)
                raise QueueDoesNotExistError

            return None

        if queue.lock and unlocked_only:
            log.error("Queue is locked", name=queue_name)
            raise QueueLockedError

        return cast(Queue, queue)

    def delete(self, name: str, **kwargs) -> dict[str, Any]:
        """Delete a queue.

        Args:
            name: The name of the queue.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (queue := self.get(name, log=log)) is None:
            return {"status": "Success", "name": []}

        queue.update(changes={"is_deleted": True})
        db.session.commit()
        log.info("Queue deleted", name=name)
        return {"status": "Success", "name": [name]}

    def lock(self, name: str, **kwargs) -> dict[str, Any]:
        """Lock a queue.

        Args:
            name: The name of the queue.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            QueueDoesNotExistError: If the queue is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (queue := self.get(name, error_if_not_found=True, log=log)) is None:
            return {"status": "Success", "name": []}

        queue.lock.append(QueueLock())
        db.session.commit()
        log.info("Queue locked", name=queue.name)
        return {"status": "Success", "name": [queue.name]}

    def unlock(self, name: str, **kwargs) -> dict[str, Any]:
        """Unlock a queue.

        Args:
            name: The name of the queue.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            QueueDoesNotExistError: If the queue is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (queue := self.get(name, error_if_not_found=True, log=log)) is None:
            return {"status": "Success", "name": []}

        db.session.delete(queue.lock[0])
        db.session.commit()
        log.info("Queue unlocked", name=name)
        return {"status": "Success", "name": [queue.name]}
