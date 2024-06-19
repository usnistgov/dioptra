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
"""The server-side functions that perform tag endpoint operations."""
from __future__ import annotations

from typing import Any, cast

import structlog
from injector import ClassAssistedBuilder, inject
from sqlalchemy import select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import ResourceDoesNotExistError
from dioptra.restapi.v1.tags.errors import TagDoesNotExistError
from dioptra.restapi.v1.tags.service import TagIdService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class ResourceTagsService(object):
    """The service methods for managing a specific resource tag."""

    @inject
    def __init__(
        self,
        resource_type: str,
        resource_id_service: ClassAssistedBuilder[ResourceIdService],
        tag_id_service: TagIdService,
    ) -> None:
        """Initialize the resource tags service.

        All arguments are provided via dependency injection.

        Args:
            resource_id_service: A ResourceIdService object.
            tag_id_service: A TagIdService object.
        """
        self._resource_id_service = resource_id_service.build(
            resource_type=resource_type
        )
        self._tag_id_service = tag_id_service

    def get(
        self,
        resource_id: int,
        **kwargs,
    ) -> list[models.Tag]:
        """Fetch tags for a resource by resource id.

        Args:
            resource_id: The unique id of the resource.

        Returns:
            The list of tags if the resource is found, otherwise None.

        Raises:
            ResourceDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get tags by resource id", resource_id=resource_id)

        resource = self._resource_id_service.get(resource_id, log=log)

        return list(resource.tags)

    def append(
        self,
        resource_id: int,
        tag_ids: list[int],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> list[models.Tag]:
        """Append one or more Tags

        Args:
            resource_id: The unique id of the resource.
            tag_ids: The list of tag ids to append.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated tag resource object.

        Raises:
            ResourceDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
            TagDoesNotExistError: If one or more tags are not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        resource = self._resource_id_service.get(resource_id, log=log)

        tag_ids = list(set(tag_ids))
        existing_tag_ids = set(tag.tag_id for tag in resource.tags)
        tags = [
            self._tag_id_service.get(
                tag_id, error_if_not_found=error_if_not_found, log=log
            )
            for tag_id in tag_ids
            if tag_id not in existing_tag_ids
        ]

        resource.tags.extend(cast(list[models.Tag], tags))

        if commit:
            db.session.commit()
            log.debug("Tags appended successfully", tag_ids=tag_ids)

        return resource.tags

    def modify(
        self,
        resource_id: int,
        tag_ids: list[int],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> list[models.Tag]:
        """Append one or more Tags

        Args:
            resource_id: The unique id of the resource.
            tag_ids: The list of tag ids to append.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated tag resource object.

        Raises:
            ResourceDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
            TagDoesNotExistError: If one or more tags are not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        resource = self._resource_id_service.get(resource_id, log=log)

        tags = [
            self._tag_id_service.get(
                tag_id, error_if_not_found=error_if_not_found, log=log
            )
            for tag_id in tag_ids
        ]

        resource.tags = cast(list[models.Tag], tags)

        if commit:
            db.session.commit()
            log.debug("Tags updated successfully", tag_ids=tag_ids)

        return resource.tags

    def delete(self, resource_id: int, **kwargs) -> dict[str, Any]:
        """Remove tags from a resource.

        Args:
            resource_id: The unique id of the resource.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        resource = self._resource_id_service.get(resource_id, log=log)
        tag_ids = [tag.tag_id for tag in resource.tags]
        resource.tags = []

        db.session.commit()
        log.debug("Tags removed", resource_id=resource_id, tag_ids=tag_ids)

        return {"status": "Success", "id": tag_ids}


class ResourceTagsIdService(object):
    """The service methods for managing a specific resource tag."""

    @inject
    def __init__(
        self,
        resource_type: str,
        resource_id_service: ClassAssistedBuilder[ResourceIdService],
        tag_id_service: TagIdService,
    ) -> None:
        """Initialize the resource tags service.

        All arguments are provided via dependency injection.

        Args:
            resource_id_service: A ResourceIdService object.
            tag_id_service: A TagIdService object.
        """
        self._resource_id_service = resource_id_service.build(
            resource_type=resource_type
        )
        self._tag_id_service = tag_id_service

    def delete(self, resource_id: int, tag_id, **kwargs) -> dict[str, Any]:
        """Remove a tag from a resource.

        Args:
            resource_id: The unique id of the resource.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        resource = self._resource_id_service.get(
            resource_id, error_if_not_found=True, log=log
        )

        current_tags = resource.tags
        tag_exists = tag_id in {tag.tag_id for tag in current_tags}
        if not tag_exists:
            raise TagDoesNotExistError

        resource.tags = [tag for tag in current_tags if tag.tag_id != tag_id]

        db.session.commit()
        log.debug("Tag removed", resource_id=resource_id, tag_id=tag_id)

        return {"status": "Success", "id": [tag_id]}


class ResourceIdService(object):
    """The service methods for accessing a specific resource."""

    @inject
    def __init__(self, resource_type: str):
        self._resource_type = resource_type

    def get(self, resource_id: int, **kwargs) -> models.Resource:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(f"Retrieving {self._resource_type} resource", resource_id=resource_id)

        stmt = select(models.Resource).filter_by(
            resource_id=resource_id, resource_type=self._resource_type, is_deleted=False
        )
        resource = db.session.scalar(stmt)

        if resource is None:
            log.debug(f"{self._resource_type} not found", resource_id=resource_id)
            raise ResourceDoesNotExistError

        return resource
