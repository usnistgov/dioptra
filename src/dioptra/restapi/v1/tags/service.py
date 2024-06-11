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
"""The server-side functions that perform tags endpoint operations."""
from typing import Any, Final

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError, SearchNotImplementedError
from dioptra.restapi.v1.groups.service import GroupIdService

from .errors import TagAlreadyExistsError, TagDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "tag"


class TagService(object):
    """The service methods for registering and managing tags by their unique id."""

    @inject
    def __init__(
        self,
        tag_name_service: TagNameService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the tag service.

        All arguments are provided via dependency injection.

        Args:
            tag_name_service: A TagNameService object.
            group_id_service: A GroupIdService object.
        """
        self._tag_name_service = tag_name_service
        self._group_id_service = group_id_service

    def create(
        self,
        name: str,
        description: str,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> models.Tag:
        """Create a new tag.

        Args:
            name: The name of the tag. The combination of name and group_id must be
                unique.
            description: The description of the tag.
            group_id: The group that will own the tag.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created tag object.

        Raises:
            TagAlreadyExistsError: If a tag with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Create a new tag")

        if self._tag_name_service.get(name, group_id=group_id, log=log) is not None:
            log.debug("Tag name already exists", name=name, group_id=group_id)
            raise TagAlreadyExistsError

        group = self._group_id_service.get(group_id, error_if_not_found=True)

        resource = models.Resource(resource_type=RESOURCE_TYPE, owner=group)
        new_tag = models.Tag(
            name=name, description=description, resource=resource, creator=current_user
        )
        db.session.add(new_tag)

        if commit:
            db.session.commit()
            log.debug(
                "Tag registration successful",
                tag_id=new_tag.resource_id,
                name=new_tag.name,
            )

        return new_tag

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> Any:
        """Fetch a list of tags, optionally filtering by group id, search string, and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of tags to be returned.

        Returns:
            A tuple containing a list of tags and the total number of tags matching
            the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when counting
                the number of tags.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of tags")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            log.debug("Searching is not implemented", search_string=search_string)
            raise SearchNotImplementedError

        stmt = (
            select(func.count(models.Tag.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Tag.resource_snapshot_id,
            )
        )
        total_num_tags = db.session.scalars(stmt).first()

        if total_num_tags is None:
            log.error(
                "The database query returned a None when counting the number of "
                "tags when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_tags == 0:
            return [], total_num_tags

        stmt = (
            select(models.Tag)  # type: ignore
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Tag.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        tags = db.session.scalars(stmt).all()

        return tags, total_num_tags


class TagIdService(object):
    """The service methods for registering and managing tags by their unique id."""

    @inject
    def __init__(
        self,
        tag_name_service: TagNameService,
    ) -> None:
        """Initialize the tag service.

        All arguments are provided via dependency injection.

        Args:
            tag_name_service: A TagNameService object.
        """
        self._tag_name_service = tag_name_service

    def get(
        self,
        tag_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.Tag | None:
        """Fetch a tag by its unique id.

        Args:
            tag_id: The unique id of the tag.
            error_if_not_found: If True, raise an error if the tag is not found.
                Defaults to False.

        Returns:
            The tag object if found, otherwise None.

        Raises:
            TagDoesNotExistError: If the tagis not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get tag by id", tag_id=tag_id)

        stmt = (
            select(models.Tag)
            .join(models.Resource)
            .where(
                models.Tag.resource_id == tag_id,
                models.Tag.resource_snapshot_id == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        tag = db.session.scalars(stmt).first()

        if tag is None:
            if error_if_not_found:
                log.debug("Tag not found", tag_id=tag_id)
                raise TagDoesNotExistError

            return None

        return tag

    def modify(
        self,
        tag_id: int,
        name: str,
        description: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> models.Tag | None:
        """Rename a tag.

        Args:
            tag_id: The unique id of the tag.
            name: The new name of the tag.
            description: The new description of the tag.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated tag object.

        Raises:
            TagDoesNotExistError: If the tag is not found and `error_if_not_found`
                is True.
            TagAlreadyExistsError: If the tag name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Modify tag by id", tag_id=tag_id)

        tag = self.get(tag_id, error_if_not_found=error_if_not_found, log=log)

        if tag is None:
            return None

        group_id = tag.resource.group_id
        if (
            name != tag.name
            and self._tag_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Tag name already exists", name=name, group_id=group_id)
            raise TagAlreadyExistsError

        new_tag = models.Tag(
            name=name,
            description=description,
            resource=tag.resource,
            creator=current_user,
        )
        db.session.add(new_tag)

        if commit:
            db.session.commit()
            log.debug(
                "Tag modification successful",
                tag_id=tag_id,
                name=name,
                description=description,
            )

        return new_tag

    def delete(self, tag_id: int, **kwargs) -> dict[str, Any]:
        """Delete a tag.

        Args:
            tag_id: The unique id of the tag.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Delete tag by id", tag_id=tag_id)

        stmt = select(models.Resource).filter_by(
            resource_id=tag_id, resource_type=RESOURCE_TYPE, is_deleted=False
        )
        tag_resource = db.session.scalars(stmt).first()

        if tag_resource is None:
            raise TagDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type="delete",
            resource=tag_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Tag deleted", tag_id=tag_id)

        return {"status": "Success", "tag_id": tag_id}


class TagNameService(object):
    """The service methods for managing tags by their name."""

    def get(
        self,
        name: str,
        group_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.Tag | None:
        """Fetch a tag by its name.

        Args:
            name: The name of the tag.
            group_id: The the group id of the tag.
            error_if_not_found: If True, raise an error if the tag is not found.
                Defaults to False.

        Returns:
            The tag object if found, otherwise None.

        Raises:
            TagDoesNotExistError: If the tag is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get tag by name", tag_name=name, group_id=group_id)

        stmt = (
            select(models.Tag)
            .join(models.Resource)
            .where(
                models.Tag.name == name,
                models.Resource.group_id == group_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Tag.resource_snapshot_id,
            )
        )
        tag = db.session.scalars(stmt).first()

        if tag is None:
            if error_if_not_found:
                log.debug("Tag not found", name=name)
                raise TagDoesNotExistError

            return None

        return tag