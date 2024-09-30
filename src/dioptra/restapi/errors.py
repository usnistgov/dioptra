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

import typing
from io import StringIO

import structlog
from flask import request
from flask_restx import Api
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

"""
Helper function to add attribute name/value pairs to StringIO instance as an error
message.
Args:
    buffer: The StringIO instance into which the attribute name/value pairs are to be
    added.
    attributes: the list of attribute value pairs to add to the buffer.
"""


def add_attribute_values(buffer: StringIO, **kwargs: typing.Any) -> None:
    index = 0
    length = len(kwargs)
    for key, value in kwargs.items():
        if index != 0:
            buffer.write(", ")
            if index == length - 1:
                buffer.write("and ")
        buffer.write(f"{key} having value ({value})")
        index += 1


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
        if self.__cause__ is not None:
            if isinstance(self.__cause__, DioptraError):
                self.message = f"{self.message} Cause: {self.__cause__.to_message()}"
            else:
                self.message = f"{self.message} Cause: {self.__cause__}"
        return self.message


class SubmissionError(DioptraError):
    """The submission input is in error.
    Args:
        type: the resource type
        action: the action
    """

    def __init__(self, type: str, action: str):
        super().__init__(f"Input Error while attempting to {action} for {type}.")
        self.resource_type = type
        self.action = action


class EntityDoesNotExistError(DioptraError):
    """
    The requested entity does not exist.
    Args:
        entity_type: the entity type name (e.g. "group" or "queue")
        kwargs: the attribute value pairs used to request the entity
    """

    def __init__(self, entity_type: str, **kwargs: typing.Any):
        buffer = StringIO()
        buffer.write(f"Failed to locate {entity_type} with ")
        add_attribute_values(buffer, **kwargs)
        buffer.write(".")
        super().__init__(buffer.getvalue())
        self.entity_type = entity_type
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
        buffer = StringIO()
        buffer.write(f"The {entity_type} with ")
        add_attribute_values(buffer, **kwargs)
        buffer.write(" is not available.")

        super().__init__(buffer.getvalue())
        self.entity_type = entity_type
        self.entity_attributes = kwargs
        self.existing_id = existing_id


class LockError(DioptraError):
    def __init__(self, message: str):
        super().__init__(message)


class ReadOnlyLockError(LockError):
    """The type has a read-only lock and cannot be modified."""

    def __init__(self, type: str, **kwargs: typing.Any):
        buffer = StringIO()
        buffer.write(f"The {type} type with ")
        add_attribute_values(buffer, **kwargs)
        buffer.write(" has a read-only lock and cannot be modified.")

        super().__init__(buffer.getvalue())
        self.entity_type = type
        self.entity_attributes = kwargs


class QueueLockedError(LockError):
    """The requested queue is locked."""

    def __init__(self, type: str, **kwargs: typing.Any):
        super().__init__("The requested queue is locked.")


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

    def __init__(self):
        super().__init__("The requested draft does not exist.")


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
        buffer = StringIO()
        buffer.write(f"Input parameters for {type} failed {constraint} check for ")
        add_attribute_values(buffer, **kwargs)
        buffer.write(".")
        super().__init__(buffer.getvalue())
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


class EntryPointNotRegisteredToExperimentError(DioptraError):
    """The requested entry point is not registered to the provided experiment."""

    def __init__(self):
        super().__init__(
            "The requested entry point is not registered to the provided " "experiment."
        )


class QueueNotRegisteredToEntryPointError(DioptraError):
    """The requested queue is not registered to the provided entry point."""

    def __init__(self):
        super().__init__(
            "The requested queue is not registered to the provided entry " "point."
        )


class PluginParameterTypeMatchesBuiltinTypeError(DioptraError):
    """The plugin parameter type name cannot match a built-in type."""

    def __init__(self):
        super().__init__(
            "The requested plugin parameter type name matches a built-in "
            "type. Please select another and resubmit."
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


STATUS_MESSAGE: typing.Final[dict[int, str]] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Bad Request",
    422: "Unprocessable Content",
    500: "Internal Error",
    501: "Not Implemented",
}


def error_result(
    error: DioptraError, status: int, detail: dict[str, typing.Any]
) -> tuple[dict[str, typing.Any], int]:
    prefix = STATUS_MESSAGE.get(status, "Error")
    return {
        "error": error.__class__.__name__,
        "message": f"{prefix} - {error.message}",
        "detail": detail,
        "originating_path": request.full_path,
    }, status


# Silenced Complexity error for this function since it is a straitfoward registration of
# error handlers
def register_error_handlers(api: Api, **kwargs) -> None:  # noqa: C901
    """Registers the error handlers with the main application.

    Args:
        api: The main REST |Api| object.
    """
    log: BoundLogger = kwargs.get("log", LOGGER.new())

    @api.errorhandler(EntityDoesNotExistError)
    def handle_resource_does_not_exist_error(error: EntityDoesNotExistError):
        log.debug(
            "Entity not found", entity_type=error.entity_type, **error.entity_attributes
        )
        return error_result(
            error, 404, {"entity_type": error.entity_type, **error.entity_attributes}
        )

    @api.errorhandler(EntityExistsError)
    def handle_entity_exists_error(error: EntityExistsError):
        log.debug(
            "Entity exists",
            entity_type=error.entity_type,
            existing_id=error.existing_id,
            **error.entity_attributes,
        )
        return error_result(
            error,
            409,
            {
                "entity_type": error.entity_type,
                "existing_id": error.existing_id,
                "entity_attributes": {**error.entity_attributes},
            },
        )

    @api.errorhandler(BackendDatabaseError)
    def handle_backend_database_error(error: BackendDatabaseError):
        log.error(error.to_message())
        return error_result(error, 500, {})

    @api.errorhandler(SearchNotImplementedError)
    def handle_search_not_implemented_error(error: SearchNotImplementedError):
        log.debug(error.to_message())
        return error_result(error, 501, {})

    @api.errorhandler(SearchParseError)
    def handle_search_parse_error(error: SearchParseError):
        log.debug(error.to_message())
        return error_result(
            error, 422, {"query": error.args[0], "reason": error.args[1]}
        )

    @api.errorhandler(DraftDoesNotExistError)
    def handle_draft_does_not_exist(error: DraftDoesNotExistError):
        log.debug(error.to_message())
        return error_result(error, 404, {})

    @api.errorhandler(DraftAlreadyExistsError)
    def handle_draft_already_exists(error: DraftAlreadyExistsError):
        log.debug(error.to_message())
        return error_result(error, 400, {})

    @api.errorhandler(LockError)
    def handle_lock_error(error: LockError):
        log.debug(error.to_message())
        return error_result(error, 403, {})

    @api.errorhandler(NoCurrentUserError)
    def handle_no_current_user_error(error: NoCurrentUserError):
        log.debug(error.to_message())
        return error_result(error, 401, {})

    @api.errorhandler(UserPasswordChangeError)
    def handle_password_change_error(error: UserPasswordChangeError):
        log.debug(error.to_message())
        return error_result(error, 403, {})

    @api.errorhandler(UserPasswordError)
    def handle_user_password_error(error: UserPasswordError):
        log.debug(error.to_message())
        return error_result(error, 401, {})

    @api.errorhandler(DioptraError)
    def handle_base_error(error: DioptraError):
        log.debug(error.to_message())
        return error_result(error, 400, {})
