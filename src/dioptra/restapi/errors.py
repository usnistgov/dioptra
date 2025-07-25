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

import http
import typing

import structlog
from flask import request
from flask_restx import Api
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.v1 import utils

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

    def __init__(self, entity_type: str | None, existing_id: int, **kwargs: typing.Any):
        super().__init__(
            "".join(
                [
                    "The ",
                    "entity" if entity_type is None else entity_type,
                    *add_attribute_values(**kwargs),
                    " is not available.",
                ]
            )
        )
        self.entity_type = entity_type
        self.entity_attributes = kwargs
        self.existing_id = existing_id


class EntityDeletedError(DioptraError):
    """
    The requested entity has been deleted.
    Args:
        entity_type: the entity type name (e.g. "group" or "queue")
        existing_id: the id of the deleted entity
        kwargs: the attribute value pairs used to request the entity
    """

    def __init__(self, entity_type: str | None, existing_id: int, **kwargs: typing.Any):
        super().__init__(
            "".join(
                [
                    "The ",
                    "entity" if entity_type is None else entity_type,
                    *add_attribute_values(**kwargs),
                    " is deleted.",
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

    def __init__(self, type: str | None = None, **kwargs: typing.Any):
        super().__init__(
            "".join(
                [
                    f"The {type or 'resource'} type",
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


class DraftResourceModificationsCommitError(DioptraError):
    """The draft modifications to a resource could not be committed"""

    def __init__(
        self,
        resource_type: str,
        resource_id: int,
        draft: models.DraftResource,
        base_snapshot: models.ResourceSnapshot,
        curr_snapshot: models.ResourceSnapshot,
    ):
        super().__init__(
            f"Draft modifications for a [{resource_type}] with id: {resource_id} "
            "could not be commited."
        )
        self.draft = draft
        self.base_snapshot = base_snapshot
        self.curr_snapshot = curr_snapshot


class InvalidDraftBaseResourceSnapshotError(DioptraError):
    """The draft's base snapshot identifier is invalid."""

    def __init__(
        self,
        message: str,
        base_resource_snapshot_id: int,
        provided_resource_snapshot_id: int,
    ):
        super().__init__(message)
        self.base_resource_snapshot_id = base_resource_snapshot_id
        self.provided_resource_snapshot_id = provided_resource_snapshot_id


class SortParameterValidationError(DioptraError):
    """The sort parameters are not valid."""

    def __init__(self, type: str, column: str, **kwargs):
        super().__init__(f"The sort parameter, {column}, for {type} is not sortable.")


class ArtifactTaskPluginTaskOverlapError(DioptraError):
    """Overlap between Artifact Plugins and Task Plugins."""

    def __init__(self, artifacts: str, **kwargs):
        super().__init__(
            f"The artifact task(s) {artifacts} are in the list of task plugins,"
            " when they should be separate."
        )


class PluginTaskArtifactTaskOverlapError(DioptraError):
    """Overlap between Artifact Plugins and Task Plugins."""

    def __init__(self, plugins: str, **kwargs):
        super().__init__(
            f"The plugin task(s) {plugins} are in the list of artifact tasks,"
            " when they should be separate."
        )


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

    names: list[str]
    artifact: bool

    def __init__(self, names: list[str], artifact: bool = False):
        param_type = "artifact parameter" if artifact else "parameter"
        if len(names) == 1:
            message = f"Provided job {param_type} name, {names[0]}, does not match any "
            "entrypoint parameters."
        else:
            joined = ", ".join(names)
            message = f"Provided job {param_type} names, {joined}, do not match any "
            "entrypoint parameters."
        super().__init__(message)
        self.names = names
        self.artifact = artifact


class JobArtifactValueError(DioptraError):
    """The requested artifact value name is invalid."""

    name: str
    artifact_id: int

    def __init__(self, name: str, artifact_id: int):
        super().__init__(
            f"Provided job artifact id, {artifact_id}, for parameter {name} does not "
            "exist."
        )
        self.name = name
        self.artifact_id = artifact_id


class JobArtifactParameterMissingError(DioptraError):
    """The Artifact Parameter is missing a value."""

    name: list[str]

    def __init__(self, names: list[str]):
        super().__init__(
            "The following job Artifact Parameters are missing a value: "
            f"{','.join(names)}."
        )


class JobMlflowRunAlreadySetError(DioptraError):
    """The requested job already has an mlflow run id set."""

    def __init__(self):
        super().__init__(
            "The requested job already has an mlflow run id set. It may not be changed."
        )


class JobMlflowRunNotSetError(DioptraError):
    """The requested job does not have an mlflow run id set."""

    def __init__(self):
        super().__init__(
            "The requested job does not have an mlflow run id set for an operation that"
            "requires an mlflow run id."
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


class InconsistentBuiltinPluginParameterTypesError(DioptraError):
    """
    The built-in plugin parameter types registered in the database is not consistent
    with expectations.
    """

    def __init__(self, missing_names: set[str], extra_names: set[str]):
        super().__init__(
            "The built-in plugin parameter types registered in the database is not "
            "consistent with expectations. A database migration may be necessary. "
            "Please contact the system administrator."
        )
        self.missing_names = missing_names
        self.extra_names = extra_names


class InvalidYamlError(DioptraError):
    """Raised when the provided YAML is invalid and fails to parse."""

    def __init__(self, message: str):
        super().__init__(message)


class InvalidPythonError(DioptraError):
    """Raised when the provided python code is invalid and fails to parse."""

    def __init__(self, message: str):
        super().__init__(message)


# User Errors
class UserDoesNotExistError(DioptraError):
    """The entered username does not exist."""

    def __init__(self, **kwargs: typing.Any):
        super().__init__(
            "".join(
                [
                    "The user",
                    *add_attribute_values(**kwargs),
                    " is not available.",
                ]
            )
        )


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


class JobStoreError(DioptraError):
    """JobStoreError Error."""

    def __init__(self, message: str):
        super().__init__(message)


class GitError(DioptraError):
    """Git Error."""

    def __init__(self, message: str):
        super().__init__(message)


class ImportFailedError(DioptraError):
    """Import failed Error."""

    def __init__(self, message: str, reason: str = ""):
        super().__init__(message)
        self._reason = reason


class UserNotInGroupError(DioptraError):
    """A given user is not in a given group."""

    def __init__(self, user_id: int, group_id: int) -> None:
        msg = f"User {user_id} is not in group {group_id}"
        super().__init__(msg)

        self.user_id = user_id
        self.group_id = group_id


class GroupNeedsAUserError(DioptraError):
    """A group must have at least one user; it can't be empty."""

    def __init__(self, user_id: int, group_id: int) -> None:
        msg = (
            f"Can't remove user {user_id} from group {group_id}: "
            "group would have no users"
        )
        super().__init__(msg)

        self.user_id = user_id
        self.group_id = group_id


class UserNeedsAGroupError(DioptraError):
    """A user must be in at least one group; it can't be groupless."""

    def __init__(self, user_id: int, group_id: int) -> None:
        msg = (
            f"Can't remove user {user_id} from group {group_id}: "
            "user would have no groups"
        )
        super().__init__(msg)

        self.user_id = user_id
        self.group_id = group_id


class GroupNeedsAManagerError(DioptraError):
    """A group must have at least one manager."""

    def __init__(self, user_id: int, group_id: int) -> None:
        msg = (
            f"Can't remove manager {user_id} from group {group_id}: "
            "group would have no managers"
        )
        super().__init__(msg)

        self.user_id = user_id
        self.group_id = group_id


class UserIsManagerError(DioptraError):
    """User can't be removed from a group because he is a group manager."""

    def __init__(self, user_id: int, group_id: int) -> None:
        msg = (
            f"Can't remove manager {user_id} from group {group_id}: "
            "user is a group manager"
        )
        super().__init__(msg)

        self.user_id = user_id
        self.group_id = group_id


class MismatchedResourceTypeError(DioptraError):
    """A snapshot was associated with a resource of the wrong type"""

    def __init__(self, expected_type: str, found_type: str) -> None:
        msg = f"Expected resource type {expected_type!r}: {found_type}"
        super().__init__(msg)

        self.expected_type = expected_type
        self.found_type = found_type


class MalformedDraftResourceError(DioptraError):
    """A draft resource payload was malformed"""

    def __init__(self) -> None:
        msg = (
            'A non-nested draft resource payload must have a "group_id"'
            " property which indicates which group will own the resulting"
            " resource."
        )
        super().__init__(msg)


class DraftTargetOwnerMismatch(DioptraError):
    """
    A draft modification's target_owner doesn't match the owner of the resource
    being modified.
    """

    def __init__(self, target_owner_id: int, resource_owner_id: int) -> None:
        msg = (
            "Draft modification target_owner/resource owner mismatch:"
            f" {target_owner_id}, {resource_owner_id}"
        )
        super().__init__(msg)

        self.draft_owner_id = target_owner_id
        self.resource_owner_id = resource_owner_id


class DraftBaseInvalidError(DioptraError):
    """
    A draft has a base_resource_id referring to a type of resource which is not
    valid as a parent type of the draft resource type.
    """

    def __init__(
        self, base_resource_id: int, parent_type: str, child_type: str
    ) -> None:
        msg = (
            f"Invalid draft base resource ID: resource type {parent_type!r}"
            f" is not a valid parent of resource type {child_type!r}:"
            f" {base_resource_id}"
        )
        super().__init__(msg)

        self.base_resource_id = base_resource_id
        self.parent_type = parent_type
        self.child_type = child_type


class DraftSnapshotIdInvalidError(DioptraError):
    """
    A draft modification's resource snapshot ID does not represent a snapshot
    of the resource represented by the draft's resource ID.
    """

    def __init__(self, resource_id: int, resource_snapshot_id: int):
        msg = (
            f"Resource snapshot {resource_snapshot_id} is not a snapshot"
            f" of resource {resource_id}"
        )
        super().__init__(msg)

        self.resource_id = resource_id
        self.resource_snapshot_id = resource_snapshot_id


class DraftModificationRequiredError(DioptraError):
    """
    A draft modification was required, but a draft resource was given.
    """

    def __init__(self, draft_resource_id: int):
        msg = f"Must be a draft modification: {draft_resource_id}"
        super().__init__(msg)

        self.draft_resource_id = draft_resource_id


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
    log: BoundLogger = kwargs.get("log", LOGGER.new())

    @api.errorhandler(EntityDoesNotExistError)
    def handle_resource_does_not_exist_error(error: EntityDoesNotExistError):
        log.debug(
            "Entity not found", entity_type=error.entity_type, **error.entity_attributes
        )
        return error_result(
            error,
            http.HTTPStatus.NOT_FOUND,
            {"entity_type": error.entity_type, **error.entity_attributes},
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
            http.HTTPStatus.CONFLICT,
            {
                "entity_type": error.entity_type,
                "existing_id": error.existing_id,
                "entity_attributes": {**error.entity_attributes},
            },
        )

    @api.errorhandler(BackendDatabaseError)
    def handle_backend_database_error(error: BackendDatabaseError):
        log.error(error.to_message())
        return error_result(error, http.HTTPStatus.INTERNAL_SERVER_ERROR, {})

    @api.errorhandler(SearchNotImplementedError)
    def handle_search_not_implemented_error(error: SearchNotImplementedError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.NOT_IMPLEMENTED, {})

    @api.errorhandler(SearchParseError)
    def handle_search_parse_error(error: SearchParseError):
        log.debug(error.to_message())
        return error_result(
            error,
            http.HTTPStatus.UNPROCESSABLE_ENTITY,
            {"query": error.args[0], "reason": error.args[1]},
        )

    @api.errorhandler(DraftDoesNotExistError)
    def handle_draft_does_not_exist(error: DraftDoesNotExistError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.NOT_FOUND, {})

    @api.errorhandler(DraftAlreadyExistsError)
    def handle_draft_already_exists(error: DraftAlreadyExistsError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.BAD_REQUEST, {})

    @api.errorhandler(DraftResourceModificationsCommitError)
    def handle_draft_resource_modifications_commit_error(
        error: DraftResourceModificationsCommitError,
    ):
        log.debug(error.to_message())

        return error_result(
            error,
            http.HTTPStatus.BAD_REQUEST,
            {
                "reason": f"The {error.draft.resource_type} has been modified since "
                "this draft was created.",
                "draft": error.draft.payload["resource_data"],
                "base_snapshot_id": error.base_snapshot.resource_snapshot_id,
                "curr_snapshot_id": error.curr_snapshot.resource_snapshot_id,
                "base_snapshot": utils.build_resource(error.base_snapshot),
                "curr_snapshot": utils.build_resource(error.curr_snapshot),
            },
        )

    @api.errorhandler(InvalidDraftBaseResourceSnapshotError)
    def handle_invalid_draft_base_resource_snapshot(
        error: InvalidDraftBaseResourceSnapshotError,
    ):
        log.debug(error.to_message())
        return error_result(
            error,
            http.HTTPStatus.BAD_REQUEST,
            {
                "base_resource_snapshot_id": error.base_resource_snapshot_id,
                "provided_resource_snapshot_id": error.provided_resource_snapshot_id,
            },
        )

    @api.errorhandler(LockError)
    def handle_lock_error(error: LockError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.FORBIDDEN, {})

    @api.errorhandler(InconsistentBuiltinPluginParameterTypesError)
    def handle_inconsistent_builtin_plugin_parameter_types_error(
        error: InconsistentBuiltinPluginParameterTypesError,
    ):
        log.debug(error.to_message())
        return error_result(
            error,
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            {
                "missing_names": sorted(list(error.missing_names)),
                "extra_names": sorted(list(error.extra_names)),
            },
        )

    @api.errorhandler(UserDoesNotExistError)
    def handle_user_does_not_exist_error(error: UserDoesNotExistError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.UNAUTHORIZED, {})

    @api.errorhandler(NoCurrentUserError)
    def handle_no_current_user_error(error: NoCurrentUserError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.UNAUTHORIZED, {})

    @api.errorhandler(UserPasswordChangeError)
    def handle_password_change_error(error: UserPasswordChangeError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.FORBIDDEN, {})

    @api.errorhandler(UserPasswordError)
    def handle_user_password_error(error: UserPasswordError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.UNAUTHORIZED, {})

    @api.errorhandler(JobStoreError)
    def handle_mlflow_error(error: JobStoreError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.INTERNAL_SERVER_ERROR, {})

    @api.errorhandler(GitError)
    def handle_git_error(error: GitError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.INTERNAL_SERVER_ERROR, {})

    @api.errorhandler(ImportFailedError)
    def handle_import_failed_error(error: ImportFailedError):
        log.debug(error.to_message())
        return error_result(
            error,
            http.HTTPStatus.BAD_REQUEST,
            {"reason": error._reason} if error._reason else {},
        )

    @api.errorhandler(DioptraError)
    def handle_base_error(error: DioptraError):
        log.debug(error.to_message())
        return error_result(error, http.HTTPStatus.BAD_REQUEST, {})
