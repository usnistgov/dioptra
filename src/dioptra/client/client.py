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
import os
from posixpath import join as urljoin
from typing import Any, Final, Generic, TypeVar

import structlog
from structlog.stdlib import BoundLogger

from .auth import AuthCollectionClient
from .base import DioptraResponseProtocol, DioptraSession
from .queues import QueuesCollectionClient
from .tags import TagsCollectionClient
from .users import UsersCollectionClient

LOGGER: BoundLogger = structlog.stdlib.get_logger()

DIOPTRA_V1_ROOT: Final[str] = "api/v1"
ENV_DIOPTRA_API: Final[str] = "DIOPTRA_API"

T = TypeVar("T")


class DioptraClient(Generic[T]):
    """The Dioptra API client."""

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the DioptraClient instance.

        Args:
            session: The Dioptra API session object.
        """
        self._session = session
        self._users = UsersCollectionClient[T](session)
        self._auth = AuthCollectionClient[T](session)
        self._queues = QueuesCollectionClient[T](session)
        self._tags = TagsCollectionClient[T](session)
        # self._groups = GroupsCollectionClient[T](session)
        # self._plugins = PluginsCollectionClient[T](session)
        # self._plugin_parameter_types = (
        #     PluginParameterTypesCollectionClient[T](session)
        # )
        # self._experiments = ExperimentsCollectionClient[T](session)
        # self._jobs = JobsCollectionClient[T](session)
        # self._entrypoints = EntrypointsCollectionClient[T](session)
        # self._models = ModelsCollectionClient[T](session)
        # self._artifacts = ArtifactsCollectionClient[T](session)

    @property
    def users(self) -> UsersCollectionClient[T]:
        """The Dioptra API's /users endpoint."""
        return self._users

    @property
    def auth(self) -> AuthCollectionClient[T]:
        """The Dioptra API's /auth endpoint."""
        return self._auth

    @property
    def queues(self) -> QueuesCollectionClient[T]:
        """The Dioptra API's /queues endpoint."""
        return self._queues

    @property
    def tags(self) -> TagsCollectionClient[T]:
        """The Dioptra API's /tags endpoint."""
        return self._tags

    # @property
    # def groups(self) -> GroupsCollectionClient[T]:
    #     """The Dioptra API's /groups endpoint."""
    #     return self._groups

    # @property
    # def plugins(self) -> PluginsCollectionClient[T]:
    #     """The Dioptra API's /plugins endpoint."""
    #     return self._plugins

    # @property
    # def plugin_parameter_types(self) -> PluginParameterTypesCollectionClient[T]:
    #     """The Dioptra API's /pluginParameterTypes endpoint."""
    #     return self._plugin_parameter_types

    # @property
    # def experiments(self) -> ExperimentsCollectionClient[T]:
    #     """The Dioptra API's /experiments endpoint."""
    #     return self._experiments

    # @property
    # def jobs(self) -> JobsCollectionClient[T]:
    #     """The Dioptra API's /jobs endpoint."""
    #     return self._jobs

    # @property
    # def entrypoints(self) -> EntrypointsCollectionClient[T]:
    #     """The Dioptra API's /entrypoints endpoint."""
    #     return self._entrypoints

    # @property
    # def models(self) -> ModelsCollectionClient[T]:
    #     """The Dioptra API's /models endpoint."""
    #     return self._models

    # @property
    # def artifacts(self) -> ArtifactsCollectionClient[T]:
    #     """The Dioptra API's /artifacts endpoint."""
    #     return self._artifacts

    def close(self) -> None:
        """Close the client's connection to the API."""
        self._session.close()


def connect_response_dioptra_client(
    address: str | None = None,
) -> DioptraClient[DioptraResponseProtocol]:
    """Connect a client to the Dioptra API that returns response objects.

    This client always returns a response object regardless of the response status code.
    It is the responsibility of the caller to check the status code and handle any
    errors.

    Args:
        address: The Dioptra web address. This is the same address used to access the
            web GUI, e.g. "https://dioptra.example.org". Note that the
            "/api/<apiVersion>" suffix is omitted. If None, then the DIOPTRA_API
            environment variable will be checked and used.

    Returns:
        A Dioptra client.

    Raises:
        ValueError: If address is None and the DIOPTRA_API environment variable is not
            set.
    """
    from .sessions import DioptraRequestsSession

    return DioptraClient[DioptraResponseProtocol](
        session=DioptraRequestsSession(_build_api_address(address))
    )


def connect_json_dioptra_client(
    address: str | None = None,
) -> DioptraClient[dict[str, Any]]:
    """Connect a client to the Dioptra API that returns JSON-like Python dictionaries.

    In contrast to the client that returns response objects, this client will raise an
    exception for any non-2xx response status code.

    Args:
        address: The Dioptra web address. This is the same address used to access the
            web GUI, e.g. "https://dioptra.example.org". Note that the
            "/api/<apiVersion>" suffix is omitted. If None, then the DIOPTRA_API
            environment variable will be checked and used.

    Returns:
        A Dioptra client.

    Raises:
        ValueError: If address is None and the DIOPTRA_API environment variable is not
            set.
    """
    from .sessions import DioptraRequestsSessionJson

    return DioptraClient[dict[str, Any]](
        session=DioptraRequestsSessionJson(_build_api_address(address))
    )


def _build_api_address(address: str | None) -> str:
    """Build the Dioptra API address.

    Args:
        address: The Dioptra web address. This is the same address used to access the
            web GUI, e.g. "https://dioptra.example.org". Note that the
            "/api/<apiVersion>" suffix is omitted. If None, then the DIOPTRA_API
            environment variable will be checked and used.

    Returns:
        The Dioptra API address.

    Raises:
        ValueError: If address is None and the DIOPTRA_API environment variable is not
            set.
    """
    if address is not None:
        return urljoin(address, DIOPTRA_V1_ROOT)

    if (dioptra_api := os.getenv(ENV_DIOPTRA_API)) is None:
        raise ValueError(
            f"The {ENV_DIOPTRA_API} environment variable must be set if the "
            "address is not provided."
        )

    return urljoin(dioptra_api, DIOPTRA_V1_ROOT)
