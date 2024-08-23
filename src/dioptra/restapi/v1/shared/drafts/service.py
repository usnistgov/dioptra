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
from __future__ import annotations

import datetime
from typing import Any, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import (
    BackendDatabaseError,
    DraftAlreadyExistsError,
    DraftDoesNotExistError,
    ResourceDoesNotExistError,
)
from dioptra.restapi.v1.groups.errors import GroupDoesNotExistError
from dioptra.restapi.v1.groups.service import GroupIdService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class ResourceDraftsService(object):
    """The service methods for managing resource drafts."""

    @inject
    def __init__(
        self,
        resource_type: str,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the draft service.

        All arguments are provided via dependency injection.

        Args:
            group_id_service: A GroupIdService object.
        """
        self._resource_type = resource_type
        self._group_id_service = group_id_service

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

        filters = list()

        if group_id is not None:
            filters.append(models.DraftResource.group_id == group_id)

        if base_resource_id is not None:
            filters.append(
                models.DraftResource.payload["base_resource_id"]
                .as_string()
                .cast(Integer)
                == base_resource_id
            )

        if draft_type == "existing":
            filters.append(
                models.DraftResource.payload["resource_id"].as_string()
                != None  # noqa: E711
            )
        elif draft_type == "new":
            filters.append(
                models.DraftResource.payload["resource_id"].as_string()
                == None  # noqa: E711
            )

        stmt = select(func.count(models.DraftResource.draft_resource_id)).where(
            *filters,
            models.DraftResource.resource_type == self._resource_type,
            models.DraftResource.user_id == current_user.user_id,
        )
        total_num_drafts = db.session.scalars(stmt).first()

        if total_num_drafts is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_drafts == 0:
            return [], total_num_drafts

        stmt = (
            select(models.DraftResource)
            .filter(  # type: ignore
                *filters,
                models.DraftResource.resource_type == self._resource_type,
                models.DraftResource.user_id == current_user.user_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        drafts = db.session.scalars(stmt).all()

        return drafts, total_num_drafts

    def create(
        self,
        base_resource_id: int | None,
        payload: dict[str, Any],
        commit: bool = True,
        **kwargs,
    ) -> models.DraftResource:
        """Create a new draft.

        Args:
            payload: The contents of the draft.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created draft object.

        Raises:
            GroupDoesNotExistError: If the group with the provided ID does not exist.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        group_id = payload.pop("group_id", None)

        if base_resource_id is None:
            group = self._group_id_service.get(group_id, error_if_not_found=True)
        else:
            stmt = select(models.Resource).filter_by(
                resource_id=base_resource_id, is_deleted=False
            )
            resource = db.session.scalar(stmt)
            if resource is None:
                raise GroupDoesNotExistError
            group = resource.owner

        draft_payload = {
            "resource_data": payload,
            "resource_id": None,
            "resource_snapshot_id": None,
            "base_resource_id": base_resource_id,
        }

        draft = models.DraftResource(
            resource_type=self._resource_type,
            target_owner=group,
            payload=draft_payload,
            creator=current_user,
        )
        db.session.add(draft)

        if commit:
            db.session.commit()
            log.debug("Draft creation successful", resource_id=draft.draft_resource_id)

        return draft


class ResourceDraftsIdService(object):
    """The service methods for managing a specific resource draft."""

    @inject
    def __init__(
        self,
        resource_type: str,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the draft service.

        All arguments are provided via dependency injection.

        Args:
            group_id_service: A GroupIdService object.
        """
        self._resource_type = resource_type
        self._group_id_service = group_id_service

    def get(
        self,
        draft_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.DraftResource | None:
        """Fetch a draft by its unique id.

        Args:
            resource_id: The unique id of the resource.
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

        stmt = select(models.DraftResource).filter(
            models.DraftResource.resource_type == self._resource_type,
            models.DraftResource.draft_resource_id == draft_id,
            models.DraftResource.user_id == current_user.user_id,
        )
        draft = db.session.scalars(stmt).first()

        if draft is None:
            if error_if_not_found:
                log.debug("Draft not found", draft_resource_id=draft_id)
                raise DraftDoesNotExistError

            return None

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
        draft.payload["resource_data"] = payload
        draft.last_modified_on = current_timestamp

        if commit:
            db.session.commit()
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

        draft = self.get(draft_id, error_if_not_found=True, log=log)
        db.session.delete(draft)
        db.session.commit()
        log.debug("Draft deleted", draft_resource_id=draft_id)

        return {"status": "Success", "id": [draft_id]}


class ResourceIdDraftService(object):
    """The service methods for managing the draft for an existing resource."""

    def __init__(self, resource_type: str):
        self._resource_type = resource_type

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

        stmt = select(func.count(models.DraftResource.draft_resource_id)).where(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
            == resource_id,
            models.DraftResource.user_id != current_user.user_id,
        )
        num_other_drafts = db.session.scalars(stmt).first()

        if num_other_drafts is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        stmt = select(models.DraftResource).filter(  # type: ignore
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
            == resource_id,
            models.DraftResource.user_id == current_user.user_id,
        )
        draft = cast(models.DraftResource, db.session.scalars(stmt).first())

        if draft is None:
            if error_if_not_found:
                log.debug("Draft not found", resource_id=resource_id)
                raise DraftDoesNotExistError

            return None, num_other_drafts

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

        stmt = select(models.Resource).filter_by(
            resource_id=resource_id, resource_type=self._resource_type, is_deleted=False
        )
        resource = db.session.scalars(stmt).first()

        if resource is None:
            raise ResourceDoesNotExistError

        existing_draft, num_other_drafts = self.get(resource_id, log=log)
        if existing_draft:
            raise DraftAlreadyExistsError

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
        db.session.add(draft)

        if commit:
            db.session.commit()
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

        current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        draft.payload["resource_data"] = payload
        draft.last_modified_on = current_timestamp

        if commit:
            db.session.commit()
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
        db.session.delete(draft)
        db.session.commit()
        log.debug("Draft deleted", resource_id=resource_id)

        return {"status": "Success", "id": [draft_id]}
