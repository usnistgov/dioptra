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
"""
Exception classes which are applicable across the families of endpoints, or
to general software layers below the endpoint controllers.
"""
from collections.abc import Iterable


class ResourceError(Exception):  # Make this an ABC?
    """
    Instances represent an error related to a particular resource or resources.
    They capture information about the resource(s), including ID(s) and
    optionally a resource type.
    """

    def __init__(
        self, resource_id: int | Iterable[int] | None, resource_type: str | None = None
    ) -> None:
        """
        Initialize this exception object.

        Args:
            resource_id: The resource primary key ID (or iterable of IDs).
                Nullable to support reporting from an ORM instance which has
                not been persisted to the DB, so it does not yet have an ID.
                The exception info will not be very informative in that case,
                since it will not identify a particular database resource.
            resource_type: A resource type.  Obviously a resource which does
                not exist has no type (or anything else, for that matter).  In
                that case, this should reflect the context of the error.  What
                type of resource was intended?  Nullable, in case it is not
                known at the point the exception is originally thrown.  It can
                be filled in later, if desired.

                It is implied that if multiple IDs are given for resource_id,
                they are all for resources of the same type.
        """
        self.resource_type = resource_type
        self.resource_id = resource_id

    def _get_resource_id_str(self) -> str:
        """
        Helper for subclasses to get the resource IDs associated with this
        error as a string useful in an error message.  If there are multiple
        IDs, this returns a string formatted with a comma-delimited syntax.

        Returns:
            Resource ID or IDs as a string
        """
        if self.resource_id is None:
            resource_id_str = "<no-ID>"
        elif isinstance(self.resource_id, int):
            resource_id_str = str(self.resource_id)
        else:
            resource_id_str = ", ".join(str(i) for i in self.resource_id)

        return resource_id_str


class ResourceNotFoundError(ResourceError):
    """
    Instances represent a search for a resource which found no results, not
    even any deleted resources.  This is an error in contexts where the
    resource must exist (whether deleted or not).
    """

    def __str__(self) -> str:
        resource_type = self.resource_type or "resource"
        resource_id_str = self._get_resource_id_str()

        message = f"{resource_type} not found: {resource_id_str}"
        return message


class ResourceDeletedError(ResourceError):
    """
    Instances represent a search for a resource which found a deleted resource.
    This is an error in contexts where the resource either must not exist at
    all, or must exist and not be deleted.
    """

    def __str__(self) -> str:
        resource_type = self.resource_type or "resource"
        resource_id_str = self._get_resource_id_str()

        message = f"{resource_type} is deleted: {resource_id_str}"
        return message


class ResourceExistsError(ResourceError):
    """
    Instances represent a successful search for a resource, where the resource
    was found to be not deleted.  This is an error in contexts where either the
    resource must not exist at all, or must be deleted.
    """

    def __str__(self) -> str:
        resource_type = self.resource_type or "resource"
        resource_id_str = self._get_resource_id_str()

        message = f"{resource_type} exists, not deleted: {resource_id_str}"
        return message
