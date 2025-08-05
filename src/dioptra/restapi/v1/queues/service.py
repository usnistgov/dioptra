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

from typing import Any, Final

import structlog
from flask_login import current_user
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.db.repository.utils import DeletionPolicy
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.errors import EntityDoesNotExistError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entity_types import EntityTypes
from dioptra.restapi.v1.shared.search_parser import parse_search_text

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[EntityTypes] = EntityTypes.QUEUE


class QueueService(object):
    """The service methods for registering and managing queues by their unique id."""

    @inject
    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the queue service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

    def create(
        self,
        name: str,
        description: str,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.QueueDict:
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
            EntityExistsError: If a queue with the given name already exists.
            EntityDoesNotExistError: If the group with the provided ID does not exist.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        group = self._uow.group_repo.get_one(group_id, DeletionPolicy.NOT_DELETED)

        resource = models.Resource(
            resource_type=RESOURCE_TYPE.get_db_schema_name(), owner=group
        )
        new_queue = models.Queue(
            name=name, description=description, resource=resource, creator=current_user
        )

        try:
            self._uow.queue_repo.create(new_queue)
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()
        log.debug(
            "Queue registration successful",
            queue_id=new_queue.resource_id,
            name=new_queue.name,
        )

        return utils.QueueDict(queue=new_queue, has_draft=False)

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> tuple[list[utils.QueueDict], int]:
        """Fetch a list of queues, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of queues to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

        Returns:
            A tuple containing a list of queues and the total number of queues matching
            the query.

        Raises:
            BackendDatabaseError: If the database query returns a None when counting
                the number of queues.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of queues")

        search_struct = parse_search_text(search_string)

        queues, total_num_queues = self._uow.queue_repo.get_by_filters_paged(
            group_id,
            search_struct,
            page_index,
            page_length,
            sort_by_string,
            descending,
            DeletionPolicy.NOT_DELETED,
        )

        queues_dict: dict[int, utils.QueueDict] = {
            queue.resource_id: utils.QueueDict(queue=queue, has_draft=False)
            for queue in queues
        }

        resource_ids_with_drafts = self._uow.drafts_repo.has_draft_modifications(
            queues,
            current_user,
        )
        for resource_id in resource_ids_with_drafts:
            queues_dict[resource_id]["has_draft"] = True

        return list(queues_dict.values()), total_num_queues


class QueueIdService(object):
    """The service methods for registering and managing queues by their unique id."""

    @inject
    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the queue service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

    def get(
        self,
        queue_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.QueueDict | None:
        """Fetch a queue by its unique id.

        Args:
            queue_id: The unique id of the queue.
            error_if_not_found: If True, raise an error if the queue is not found.
                Defaults to False.

        Returns:
            The queue object if found, otherwise None.

        Raises:
            ResourceNotFoundError: If the queue is not found and `error_if_not_found`
                is True.
            ResourceDeletedError: If the queue is deleted and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get queue by id", queue_id=queue_id)

        queue = self._uow.queue_repo.get(queue_id, DeletionPolicy.ANY)

        if not queue:
            if error_if_not_found:
                raise EntityDoesNotExistError(EntityTypes.QUEUE, resource_id=queue_id)
            else:
                return None
        elif queue.resource.is_deleted:
            if error_if_not_found:
                # treat "deleted" as if "not found"?
                raise EntityDoesNotExistError(EntityTypes.QUEUE, resource_id=queue_id)
            else:
                return None

        has_draft = self._uow.drafts_repo.has_draft_modification(
            queue,
            current_user,
        )

        return utils.QueueDict(queue=queue, has_draft=has_draft)

    def modify(
        self,
        queue_id: int,
        name: str,
        description: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.QueueDict | None:
        """Modify a queue.

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
            ResourceNotFoundError: If the queue is not found and `error_if_not_found`
                is True.
            ResourceDeletedError: If the queue is deleted and `error_if_not_found`
                is True.
            EntityExistsError: If the queue name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        queue = self._uow.queue_repo.get(queue_id, DeletionPolicy.ANY)

        if not queue:
            if error_if_not_found:
                raise EntityDoesNotExistError(EntityTypes.QUEUE, resource_id=queue_id)
            else:
                return None
        elif queue.resource.is_deleted:
            if error_if_not_found:
                # treat "deleted" as if "not found"?
                raise EntityDoesNotExistError(EntityTypes.QUEUE, resource_id=queue_id)
            else:
                return None

        new_queue = models.Queue(
            name=name,
            description=description,
            resource=queue.resource,
            creator=current_user,
        )
        try:
            self._uow.queue_repo.create_snapshot(new_queue)
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()

        log.debug(
            "Queue modification successful",
            queue_id=queue_id,
            name=name,
            description=description,
        )

        return utils.QueueDict(queue=new_queue, has_draft=False)

    def delete(self, queue_id: int, **kwargs) -> dict[str, Any]:
        """Delete a queue.

        Args:
            queue_id: The unique id of the queue.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            ResourceNotFoundError: If the queue is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        with self._uow:
            # No-op if already deleted
            self._uow.queue_repo.delete(queue_id)

        log.debug("Queue deleted", queue_id=queue_id)

        return {"status": "Success", "queue_id": queue_id}


class QueueIdsService(object):
    """The service methods for retrieving queues from a list of ids."""

    @inject
    def __init__(self, uow: UnitOfWork):
        """Initialize the queue IDs service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

    def get(
        self,
        queue_ids: list[int],
        error_if_not_found: bool = False,
        **kwargs,
    ) -> list[models.Queue]:
        """Fetch a list of queues by their unique ids.

        Args:
            queue_ids: The unique ids of the queues.
            error_if_not_found: If True, raise an error if any queues are not found.
                Defaults to False.

        Returns:
            The queue objects if found, otherwise None.

        Raises:
            ResourceNotFoundError: If any queues are not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get queue by id", queue_ids=queue_ids)

        # More complex situation here where some queues could be deleted and
        # some may not exist at all.  For now, just treat both as not existing.
        queues = self._uow.queue_repo.get(queue_ids, DeletionPolicy.NOT_DELETED)

        if len(queues) != len(queue_ids) and error_if_not_found:
            queue_ids_missing = set(queue_ids) - set(
                queue.resource_id for queue in queues
            )
            log.debug("Queue not found", queue_ids=list(queue_ids_missing))
            raise EntityDoesNotExistError(
                EntityTypes.QUEUE, resource_ids=queue_ids_missing
            )

        return list(queues)


class QueueNameService(object):
    """The service methods for managing queues by their name."""

    @inject
    def __init__(self, uow: UnitOfWork):
        """Initialize the queue name service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

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
            group_id: The group id of the queue.
            error_if_not_found: If True, raise an error if the queue is not found.
                Defaults to False.

        Returns:
            The queue object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the queue is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get queue by name", queue_name=name, group_id=group_id)

        queue = self._uow.queue_repo.get_by_name(
            name, group_id, DeletionPolicy.NOT_DELETED
        )

        if queue is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(RESOURCE_TYPE, name=name)

            return None

        return queue
