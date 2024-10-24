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
"""A module for registering the error handlers for the application.

.. |Api| replace:: :py:class:`flask_restx.Api`
"""
from __future__ import annotations

import http
import typing

import structlog
from flask import request
from flask_restx import Api
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def add_attribute_values(**kwargs: typing.Any) -> list[str]:
    """
    Helper function to add attribute name/value pairs to a list for use in an error
    message.

    Args:
        buffer: The StringIO instance into which the attribute name/value pairs are to
        be added.
        attributes: the list of attribute value pairs to add to the buffer.
    """
    length = len(kwargs)

    def sep(index: int) -> str:
        if index == 0:
            return " with"

        if index == length - 1:
            return ", and"

        return ","

    return [
        f"{sep(index)} {key} having value ({value})"
        for index, (key, value) in enumerate(kwargs.items())
    ]


class DioptraError(Exception):
    """
    Generic Dioptra Error.
    Args:
        message: An error specific message to display that provide context for why the
        error was raised.
    """

    def __init__(self, message: str):
        self.message: str = message

    def to_message(self) -> str:
        if self.__cause__ is None:
            return self.message

        if isinstance(self.__cause__, DioptraError):
            return f"{self.message} Cause: {self.__cause__.to_message()}"

        return f"{self.message} Cause: {self.__cause__}"


class EntityDoesNotExistError(DioptraError):
    """
    The requested entity does not exist.
    Args:
        entity_type: the entity type name (e.g. "group" or "queue")
        kwargs: the attribute value pairs used to request the entity
    """

    def __init__(self, entity_type: str | None = None, **kwargs: typing.Any):
        super().__init__(
            "".join(
                [
                    "Failed to locate ",
                    "an entity" if entity_type is None else entity_type,
                    *add_attribute_values(**kwargs),
                    ".",
                ]
            )
        )
        self.entity_type = "unknown" if entity_type is None else entity_type
        self.entity_attributes = kwargs


class EntityExistsError(DioptraError):
    """
    The requested entity already exists.
    Args:
        entity_type: the entity type name (e.g. "group" or "queue")
        existing_id: the id of the existing entity
        kwargs: the attribute value pairs used to request the entity
    """

    def __init__(self, entity_type: str, existing_id: int, **kwargs: typing.Any):
        super().__init__(
            "".join(
                [
                    f"The {entity_type}",
                    *add_attribute_values(**kwargs),
                    " is not available.",
                ]
            )
        )
        self.entity_type = entity_type
        self.entity_attributes = kwargs
        self.existing_id = existing_id


class LockError(DioptraError):
    """
    Top-level Lock Error.

    Args:
        message: a message describing the lock error
    """

    def __init__(self, message: str):
        super().__init__(message)


class ReadOnlyLockError(LockError):
    """The type has a read-only lock and cannot be modified."""

    def __init__(self, type: str, **kwargs: typing.Any):
        super().__init__(
            "".join(
                [
                    f"The {type} type",
                    *add_attribute_values(**kwargs),
                    " has a read-only lock and cannot be modified.",
                ]
            )
        )
        self.entity_type = type
        self.entity_attributes = kwargs


class BackendDatabaseError(DioptraError):
    """The backend database returned an unexpected response."""

    def __init__(self):
        super().__init__(
            "The backend database returned an unexpected response, please "
            "contact the system administrator."
        )


class SearchNotImplementedError(DioptraError):
    """The search functionality has not been implemented."""

    def __init__(self):
        super().__init__("The search functionality has not been implemented.")


class SearchParseError(DioptraError):
    """The search query could not be parsed."""

    def __init__(self, context: str, error: str):
        super().__init__("The provided search query could not be parsed.")
        self.context = context
        self.error = error


class DraftDoesNotExistError(DioptraError):
    """The requested draft does not exist."""

    def __init__(self, **kwargs: typing.Any):
        super().__init__(
            "".join(
                [
                    "The requested draft",
                    *add_attribute_values(**kwargs),
                    " does not exist.",
                ]
            )
        )
        self.entity_attributes = kwargs


class DraftAlreadyExistsError(DioptraError):
    """The draft already exists."""

    def __init__(self, type: str, id: int):
        super().__init__(f"A draft for a [{type}] with id: {id} already exists.")
        self.resource_type = type
        self.resource_id = id


class SortParameterValidationError(DioptraError):
    """The sort parameters are not valid."""

    def __init__(self, type: str, column: str, **kwargs):
        super().__init__(f"The sort parameter, {column}, for {type} is not sortable.")


class QueryParameterValidationError(DioptraError):
    """Input parameters failed validation."""

    def __init__(self, type: str, constraint: str, **kwargs):
        super().__init__(
            "".join(
                [
                    f"Input parameters for {type} failed {constraint} check",
                    *add_attribute_values(**kwargs),
                    ".",
                ]
            )
        )
        self.resource_type = type
        self.constraint = constraint
        self.parameters = kwargs


class QueryParameterNotUniqueError(QueryParameterValidationError):
    """Query Parameters failed unique validatation check."""

    def __init__(self, type: str, **kwargs):
        super().__init__(type, "unique", **kwargs)


class JobInvalidStatusTransitionError(DioptraError):
    """The requested status transition is invalid."""

    def __init__(self):
        super().__init__("The requested job status update is invalid.")


class JobInvalidParameterNameError(DioptraError):
    """The requested job parameter name is invalid."""

    def __init__(self):
        super().__init__(
            "A provided job parameter name does not match any entrypoint " "parameters."
        )


class JobMlflowRunAlreadySetError(DioptraError):
    """The requested job already has an mlflow run id set."""

    def __init__(self):
        super().__init__(
            "The requested job already has an mlflow run id set. It may "
            "not be changed."
        )


class EntityDependencyError(DioptraError):
    """
    Base Error for dependency problems between entities.

    Args:
        message: a message describing the dependecy error
    """

    def __init__(self, message: str):
        super().__init__(message)


class EntityNotRegisteredError(DioptraError):
    """
    An entity could not be located based on a relationship with another entity.

    Args:
        parent_type: the parent or owning type of the relation
        parent_id: the parent or owning id of the relation
        child_type: the child or dependent type of the relation
        child_id: the child or dependent id of the relation
    """

    def __init__(
        self, parent_type: str, parent_id: int, child_type: str, child_id: int
    ):
        super().__init__(
            f"The requested {child_type} having id ({child_id}) is not registered to "
            f"the {parent_type} having id ({parent_id})."
        )
        self.parent_type = parent_type
        self.parent_id = parent_id
        self.child_type = child_type
        self.child_id = child_id


class PluginParameterTypeMatchesBuiltinTypeError(DioptraError):
    """The plugin parameter type name cannot match a built-in type."""

    def __init__(self):
        super().__init__(
            "The requested plugin parameter type name matches a built-in "
            "type. Please select another and resubmit."
        )


class EntrypointWorkflowYamlValidationError(DioptraError):
    """The entrypoint workflow yaml has validation errors."""

    def __init__(self):
        super().__init__(
            "The entrypoint workflow yaml submitted by the user has "
            "validation errors."
        )


# User Errors
class NoCurrentUserError(DioptraError):
    """There is no currently logged-in user."""

    def __init__(self):
        super().__init__("There is no currently logged-in user.")


class UserPasswordChangeError(DioptraError):
    """Password change failed."""

    def __init__(self, message: str):
        super().__init__(message)


class UserPasswordError(DioptraError):
    """Password Error."""

    def __init__(self, message: str):
        super().__init__(message)


def error_result(
    error: DioptraError, status: http.HTTPStatus, detail: dict[str, typing.Any]
) -> tuple[dict[str, typing.Any], int]:
    return {
        "error": error.__class__.__name__,
        "message": f"{status.phrase} - {error.message}",
        "detail": detail,
        "originating_path": request.full_path,
    }, status.value


# Silenced Complexity error for this function since it is a straitfoward registration of
# error handlers
def register_error_handlers(api: Api, **kwargs) -> None:  # noqa: C901
    """Registers the error handlers with the main application.

    Args:
        api: The main REST |Api| object.
    """

    from dioptra.restapi import v1

    register_base_error_handlers(api)
    v1.artifacts.errors.register_error_handlers(api)
    v1.entrypoints.errors.register_error_handlers(api)
    v1.experiments.errors.register_error_handlers(api)
    v1.groups.errors.register_error_handlers(api)
    v1.jobs.errors.register_error_handlers(api)
    v1.models.errors.register_error_handlers(api)
    v1.plugin_parameter_types.errors.register_error_handlers(api)
    v1.plugins.errors.register_error_handlers(api)
    v1.queues.errors.register_error_handlers(api)
    v1.tags.errors.register_error_handlers(api)
    v1.users.errors.register_error_handlers(api)
    v1.workflows.errors.register_error_handlers(api)
