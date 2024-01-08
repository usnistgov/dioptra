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
"""The server-side functions that perform job endpoint operations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, cast

import structlog
from sqlalchemy.exc import IntegrityError
from structlog.stdlib import BoundLogger

from dioptra.restapi.app import db
from dioptra.restapi.resource.model import DioptraResource

from .errors import DioptraResourceDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class DioptraResourceService(object):
    def get_all(self, **kwargs) -> List[DioptraResource]:
        """Get a list of all Dioptra resources.

        Returns:
            List[DioptraResource]: A list of DioptraResource objects
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        return DioptraResource.query.all()  # type: ignore

    def get(
        self, resource_id: int, raise_error_if_not_found: bool = False, **kwargs
    ) -> DioptraResource | None:
        """Get a Dioptra resource by its unique ID.

        Args:
            resource_id (int): The unique ID of the Dioptra resource.
            raise_error_if_not_found (bool, optional): If True, raises an error if
                the resource is not found.

        Returns:
            DioptraResource | None: The DioptraResource object if found, otherwise None.

        Raises:
            DioptraResourceDoesNotExistError: If `raise_error_if_not_found` is True
                and the resource with the given ID is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        resource = DioptraResource.query.get(resource_id)
        if raise_error_if_not_found:
            if resource is None:
                log.error("Dioptra Resource not found", resource_id=resource_id)
                raise DioptraResourceDoesNotExistError
        return cast(DioptraResource, resource)

    def create(self, creator_id: int, owner_id: int, **kwargs) -> DioptraResource:
        """Create a new Dioptra resource.

        Args:
            creator_id (int): The unique ID of the creator of the resource.
            owner_id (int): The unique ID of the owner of the resource.

        Returns:
            DioptraResource: The newly created DioptraResource object."""
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        timestamp = datetime.now()

        new_resource = DioptraResource(
            resource_id=DioptraResource.next_id(),
            creator_id=creator_id,
            owner_id=owner_id,
            created_on=timestamp,
            last_modified_on=timestamp,
            is_deleted=False,
        )

        db.session.add(new_resource)
        db.session.commit()

        log.info(
            "DioptraResource submission successful",
            resource_id=new_resource.resource_id,
        )

        return new_resource

    def delete(self, resource_id: int, **kwargs) -> dict[str, Any]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        resource = self.get(resource_id)

        if resource is not None:
            resource.is_deleted = True
            try:
                db.session.commit()
                log.info("DioptraResource deleted", resource_id=resource_id)
                return {"status": "Success", "id": [resource.resource_id]}
            except IntegrityError:
                db.session.rollback()
                log.error("Failed to delete DioptraResource", resource_id=resource_id)
                return {"status": "Failed", "id": [resource.resource_id]}

        return {"status": "Success", "id": []}
