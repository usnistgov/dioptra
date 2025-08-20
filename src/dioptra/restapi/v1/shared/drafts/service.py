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
"""The server-side functions that perform draft endpoint operations."""

import datetime
from typing import Any, cast

import structlog
from flask_login import current_user
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.db.repository.drafts import DraftType
from dioptra.restapi.db.repository.utils import DeletionPolicy
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.errors import (
    DraftDoesNotExistError,
    EntityDoesNotExistError,
    InvalidDraftBaseResourceSnapshotError,
    MalformedDraftResourceError,
)
from dioptra.restapi.v1.entity_types import EntityTypes

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class ResourceDraftsService(object):
    """The service methods for managing resource drafts."""

    @inject
    def __init__(
        self,
        resource_type: str,
        uow: UnitOfWork,
    ) -> None:
        """Initialize the draft service.

        All arguments are provided via dependency injection.

        Args:
            group_id_service: A GroupIdService object.
        """
        self._resource_type = resource_type
        self._uow = uow

    def get(
        self,
        draft_type: str,
        group_id: int | None,
        base_resource_id: int | None,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> Any:
        """Fetch a list of drafts

        Args:
            draft_type: The type of drafts to retrieve (all, existing, or new)
            group_id: A group ID used to filter results.
            base_resource_id: An additional resource ID used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of drafts to be returned.

        Returns:
            A tuple containing a list of drafts and the total number of drafts.

        Raises:
            BackendDatabaseError: If the database query returns a None when counting
                the number of drafts.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of drafts")

        if draft_type == "existing":
            draft_type_enum = DraftType.MODIFICATION
        elif draft_type == "new":
            draft_type_enum = DraftType.RESOURCE
        else:
            draft_type_enum = DraftType.ANY

        drafts, total_num_drafts = self._uow.drafts_repo.get_by_filters_paged(
            draft_type_enum,
            self._resource_type,
            # probably should not reference a flask detail like this from
            # a service.
            current_user,
            group_id,
            base_resource_id,
            page_index,
            page_length,
        )

        return drafts, total_num_drafts

    def create(
        self,
        base_resource_id: int | None,
        payload: dict[str, Any],
        commit: bool = True,
        **kwargs,
    ) -> models.DraftResource:
        log: BoundLogger = kwargs.get("log") or LOGGER.new()

        # apparently group_id should not be in the payload
        group_id: int | None = payload.pop("group_id", None)

        # Really need objects here, not IDs, to create the DraftResource
        if base_resource_id is None:
            if group_id is None:
                raise MalformedDraftResourceError()
            owner = self._uow.group_repo.get_one(group_id, DeletionPolicy.ANY)
        else:
            base_resource = self._uow.drafts_repo.get_resource(
                base_resource_id, DeletionPolicy.ANY
            )
            if not base_resource:
                raise EntityDoesNotExistError(
                    EntityTypes.get_from_string(None), resource_id=base_resource_id
                )

            owner = base_resource.owner

        toplevel_data = {
            "resource_data": payload,
            "resource_id": None,
            "resource_snapshot_id": None,
            "base_resource_id": base_resource_id,
        }

        draft = models.DraftResource(
            self._resource_type,
            toplevel_data,
            owner,
            # probably should not reference a flask detail like this from
            # a service.
            current_user,
        )

        try:
            self._uow.drafts_repo.create_draft_resource(draft)
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()

        log.debug("Draft creation successful", resource_id=draft.draft_resource_id)

        return draft


class ResourceDraftsIdService(object):
    """The service methods for managing a specific resource draft."""

    @inject
    def __init__(
        self,
        resource_type: str,
        uow: UnitOfWork,
    ) -> None:
        """Initialize the draft service.

        All arguments are provided via dependency injection.

        Args:
            resource_type: A resource type
            uow: A UnitOfWork object
        """
        self._resource_type = resource_type
        self._uow = uow

    def get(
        self,
        draft_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.DraftResource | None:
        """Fetch a draft by its unique id.

        Args:
            draft_id: The unique id of the resource.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.

        Returns:
            The draft object if found, otherwise None.

        Raises:
            DraftDoesNotExistError: If the draft is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get draft by id", draft_id=draft_id)

        draft = self._uow.drafts_repo.get(
            # probably should not reference a flask detail like this from
            # a service.
            draft_id,
            self._resource_type,
            current_user,
        )

        if draft is None and error_if_not_found:
            raise DraftDoesNotExistError(draft_resource_id=draft_id)

        return draft

    def modify(
        self,
        draft_id: int,
        payload: dict[str, Any],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> models.DraftResource | None:
        """Modify a Draft

        Args:
            resource_id: The unique id of the resource.
            payload: The contents of the draft.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated draft resource object.

        Raises:
            DraftDoesNotExistError: If the draft is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        draft = self.get(draft_id, error_if_not_found=error_if_not_found, log=log)

        if draft is None:
            return None

        current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        # TODO: sanity check the payload?
        draft.payload["resource_data"] = payload
        draft.last_modified_on = current_timestamp

        if commit:
            self._uow.commit()
            log.debug("Draft modification successful", draft_resource_id=draft_id)

        return draft

    def delete(self, draft_id: int, **kwargs) -> dict[str, Any]:
        """Delete a draft.

        Args:
            draft_id: The unique id of the draft.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        with self._uow:
            self._uow.drafts_repo.delete(draft_id)
        log.debug("Draft deleted", draft_resource_id=draft_id)

        return {"status": "Success", "id": [draft_id]}


class ResourceIdDraftService(object):
    """The service methods for managing the draft for an existing resource."""

    @inject
    def __init__(self, resource_type: str, uow: UnitOfWork):
        self._resource_type = resource_type
        self._uow = uow

    def get(
        self,
        resource_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> tuple[models.DraftResource | None, int]:
        """Fetch a draft by its unique id.

        Args:
            resource_id: The unique id of the draft.
            error_if_not_found: If True, raise an error if the draft is not found.
                Defaults to False.

        Returns:
            The draft object if found, otherwise None.

        Raises:
            DraftDoesNotExistError: If the draft is not found and `error_if_not_found`
                is True.
            BackendDatabaseError: If the database query returns a None when counting
                the number of drafts.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get draft by resource id", resource_id=resource_id)

        draft = self._uow.drafts_repo.get_draft_modification_by_user(
            # probably should not reference a flask detail like this from
            # a service.
            current_user,
            resource_id,
        )

        if draft is None and error_if_not_found:
            raise DraftDoesNotExistError(resource_id=resource_id)

        num_other_drafts = self._uow.drafts_repo.get_num_draft_modifications(
            resource_id,
            current_user,
        )

        return draft, num_other_drafts

    def create(
        self,
        resource_id: int,
        base_resource_id: int | None,
        payload: dict[str, Any],
        commit: bool = True,
        **kwargs,
    ) -> tuple[models.DraftResource | None, int]:
        """Create a new draft from an existing resource.

        Args:
            resource_id: The ID of the resource this draft modifies.
            payload: The contents of the draft.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created draft object.

        Raises:
            DraftAlreadyExistsError: If a draft already exists for this resource.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        resource = self._uow.drafts_repo.get_resource(
            resource_id,
            DeletionPolicy.ANY,
        )

        if resource is None or resource.resource_type != self._resource_type:
            raise EntityDoesNotExistError(
                EntityTypes.get_from_string(self._resource_type),
                resource_id=resource_id,
            )

        num_other_drafts = self._uow.drafts_repo.get_num_draft_modifications(
            # probably should not reference a flask detail like this from
            # a service.
            resource,
            current_user,
        )

        draft_payload = {
            "resource_data": payload,
            "resource_id": resource_id,
            "resource_snapshot_id": resource.latest_snapshot_id,
            "base_resource_id": base_resource_id,
        }

        draft = models.DraftResource(
            resource_type=self._resource_type,
            target_owner=resource.owner,
            payload=draft_payload,
            creator=current_user,
        )

        try:
            self._uow.drafts_repo.create_draft_modification(draft)
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()
            log.debug("Draft creation successful", resource_id=draft.draft_resource_id)

        return draft, num_other_drafts

    def modify(
        self,
        resource_id: int,
        payload: dict[str, Any],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> tuple[models.DraftResource | None, int]:
        """Modify a draft.

        Args:
            resource_id: The unique id of the resource.
            payload: The contents of the draft.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated draft resource object.

        Raises:
            DraftDoesNotExistError: If the draft is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        draft, num_other_drafts = self.get(
            resource_id, error_if_not_found=error_if_not_found, log=log
        )

        if draft is None:
            return None, num_other_drafts

        if draft.payload["resource_snapshot_id"] > payload["resource_snapshot_id"]:
            raise InvalidDraftBaseResourceSnapshotError(
                "The provided resource snapshot must be greater than or equal to "
                "the base resource snapshot.",
                base_resource_snapshot_id=draft.payload["resource_snapshot_id"],
                provided_resource_snapshot_id=payload["resource_snapshot_id"],
            )

        try:
            self._uow.drafts_repo.update(
                draft,
                payload["resource_data"],
                payload["resource_snapshot_id"],
            )
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()
            log.debug("Draft modification successful", resource_id=resource_id)

        return draft, num_other_drafts

    def delete(self, resource_id: int, **kwargs) -> dict[str, Any]:
        """Delete a draft.

        Args:
            resource_id: The unique id of the resource.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        draft, _ = cast(
            tuple[models.DraftResource, int],
            self.get(resource_id, error_if_not_found=True, log=log),
        )
        draft_id = draft.draft_resource_id
        with self._uow:
            self._uow.drafts_repo.delete(draft)

        log.debug("Draft deleted", resource_id=resource_id)

        return {"status": "Success", "id": [draft_id]}
