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

import datetime
from typing import Any, Final

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import TagAlreadyExistsError, TagDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.Tag.name.like(x),
}


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
            GroupDoesNotExistError: If the group with the provided ID does not exist.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if self._tag_name_service.get(name, group_id=group_id, log=log) is not None:
            log.debug("Tag name already exists", name=name, group_id=group_id)
            raise TagAlreadyExistsError

        group = self._group_id_service.get(group_id, error_if_not_found=True)

        new_tag = models.Tag(name=name, owner=group, creator=current_user)
        db.session.add(new_tag)

        if commit:
            db.session.commit()
            log.debug(
                "Tag creation successful", tag_id=new_tag.tag_id, name=new_tag.name
            )

        return new_tag

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[models.Tag], int]:
        """Fetch a list of tags, optionally filtering by search string and paging
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
            BackendDatabaseError: If the database query returns a None when counting
                the number of tags.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of tags")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)
            )

        count_tags_stmt = select(func.count(models.Tag.tag_id)).where(*filters)
        total_num_tags = db.session.scalar(count_tags_stmt)

        if total_num_tags is None:
            log.error(
                "The database query returned a None when counting the number of "
                "tags when it should return a number.",
                sql=str(count_tags_stmt),
            )
            raise BackendDatabaseError

        tags_stmt = (
            select(models.Tag).where(*filters).offset(page_index).limit(page_length)
        )
        tags = list(db.session.scalars(tags_stmt).all())

        return tags, total_num_tags


class TagIdService(object):
    """The service methods for registering and managing tags by their unique id."""

    @inject
    def __init__(
        self,
        tag_name_service: TagNameService,
    ) -> None:
        """Initialize the tag id service.

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
            TagDoesNotExistError: If the tag is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get tag by id", tag_id=tag_id)

        stmt = select(models.Tag).where(models.Tag.tag_id == tag_id)
        tag = db.session.scalar(stmt)

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
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> models.Tag | None:
        """Modify a tag.

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

        tag = self.get(tag_id, error_if_not_found=error_if_not_found, log=log)

        if tag is None:
            return None

        group_id = tag.group_id
        if (
            name != tag.name
            and self._tag_name_service.get(name, group_id=group_id, log=log) is not None
        ):
            log.debug("Tag name already exists", name=name, group_id=group_id)
            raise TagAlreadyExistsError

        current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        tag.name = name
        tag.last_modified_on = current_timestamp

        if commit:
            db.session.commit()
            log.debug(
                "Tag modification successful",
                tag_id=tag_id,
                name=name,
            )

        return tag

    def delete(
        self,
        tag_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """Delete a tag by its unique id.

        Args:
            tag_id: The unique id of the tag.

        Returns:
            The tag object if found, otherwise None.

        Raises:
            TagDoesNotExistError: If the tag is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get tag by id", tag_id=tag_id)

        stmt = select(models.Tag).where(models.Tag.tag_id == tag_id)
        tag = db.session.scalar(stmt)

        if tag is None:
            log.debug("Tag not found", tag_id=tag_id)
            raise TagDoesNotExistError

        tag_id = tag.tag_id
        db.session.delete(tag)
        db.session.commit()
        log.debug("Tag deleted", tag_id=tag_id)

        return {"status": "Success", "id": [tag_id]}


class TagIdResourcesService(object):
    """The service methods for retrieving resources with a given Tag."""

    @inject
    def __init__(
        self,
        tag_name_service: TagNameService,
    ) -> None:
        """Initialize the tag id service.

        All arguments are provided via dependency injection.

        Args:
            tag_name_service: A TagNameService object.
        """
        self._tag_name_service = tag_name_service

    def get(
        self,
        tag_id: int,
        resource_type: str | None,
        page_index: int,
        page_length: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> tuple[list[models.Resource], int] | None:
        """Fetch a list of resources with the Tag.

        Args:
            tag_id: The unique id of the tag.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of tags to be returned.
            error_if_not_found: If True, raise an error if the tag is not found.
                Defaults to False.

        Returns:
            The tag object if found, otherwise None.

        Raises:
            TagDoesNotExistError: If the tag is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get tag by id", tag_id=tag_id)

        tag_stmt = select(models.Tag).where(models.Tag.tag_id == tag_id)
        tag = db.session.scalar(tag_stmt)

        if tag is None:
            if error_if_not_found:
                log.debug("Tag not found", tag_id=tag_id)
                raise TagDoesNotExistError

            return None

        filters = []
        if resource_type is not None:
            filters.append(models.Resource.resource_type == resource_type)

        count_resources_stmt = select(func.count(models.Resource.resource_id)).where(
            *filters,
            models.Resource.tags.any(models.Tag.tag_id == tag_id),
        )
        total_num_resources = db.session.scalar(count_resources_stmt)

        if total_num_resources is None:
            log.error(
                "The database query returned a None when counting the number of "
                "resources when it should return a number.",
                sql=str(count_resources_stmt),
            )
            raise BackendDatabaseError

        resources_stmt = (
            select(models.Resource)
            .where(
                *filters,
                models.Resource.tags.any(models.Tag.tag_id == tag_id),
            )
            .offset(page_index)
            .limit(page_length)
        )
        resources = list(db.session.scalars(resources_stmt).all())

        return resources, total_num_resources


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

        stmt = select(models.Tag).where(
            models.Tag.name == name,
            models.Tag.group_id == group_id,
        )
        tag = db.session.scalars(stmt).first()

        if tag is None:
            if error_if_not_found:
                log.debug("Tag not found", name=name)
                raise TagDoesNotExistError

            return None

        return tag
