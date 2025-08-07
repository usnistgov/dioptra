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
import json
import posixpath
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BufferedReader
from pathlib import Path, PurePosixPath, PureWindowsPath
from posixpath import join as urljoin
from typing import Any, ClassVar, Generic, Protocol, TypeVar

T = TypeVar("T")

DOTS_REGEX = re.compile(r"^\.\.\.+$")


class DioptraClientError(Exception):
    """Base class for client errors"""


class FieldNameCollisionError(DioptraClientError):
    """Raised when two field names will collide after conversion to camel case."""


class FieldsValidationError(DioptraClientError):
    """Raised when one or more fields are invalid."""


class APIConnectionError(DioptraClientError):
    """Class for connection errors"""


class StatusCodeError(DioptraClientError):
    """Class for status code errors"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        try:
            # assume the message is unformatted json, then re-format
            self.message = json.dumps(json.loads(message), indent=4)
        except Exception:
            # any errors just use the message unchanged
            self.message = message

    def __str__(self):
        return (
            f"Error code returned: {self.status_code}\nError message returned: \n"
            f"{self.message}"
        )


class JSONDecodeError(DioptraClientError):
    """Class for JSON decode errors"""


class IllegalArgumentError(DioptraClientError):
    """Class for illegal argument errors"""


class SubCollectionUrlError(DioptraClientError):
    """Class for errors in the sub-collection URL"""


class DioptraRequestProtocol(Protocol):
    """The interface for a request to the Dioptra API."""

    @property
    def method(self) -> str:
        """The HTTP method used in the request."""
        ...  # fmt: skip

    @property
    def url(self) -> str:
        """The URL the request was made to."""
        ...  # fmt: skip


class DioptraResponseProtocol(Protocol):
    """The interface for a response from the Dioptra API."""

    @property
    def request(self) -> DioptraRequestProtocol:
        """The request that generated the response."""
        ...  # fmt: skip

    @property
    def status_code(self) -> int:
        """The HTTP status code of the response."""
        ...  # fmt: skip

    @property
    def text(self) -> str:
        """The response body as a string."""
        ...  # fmt: skip

    def json(self) -> dict[str, Any]:
        """Return the response body as a JSON-like Python dictionary.

        Returns:
            The response body as a dictionary.
        """
        ...  # fmt: skip


@dataclass
class DioptraFile(object):
    """A file to be uploaded to the Dioptra API.

    Attributes:
        filename: The name of the file.
        stream: The file stream.
        content_type: The content type of the file.
    """

    filename: str
    stream: BufferedReader
    content_type: str | None

    def __post_init__(self) -> None:
        if PureWindowsPath(self.filename).as_posix() != str(PurePosixPath(self.filename)):  # fmt: skip
            raise ValueError(
                "Invalid filename (reason: filename is a Windows path): "
                f"{self.filename}"
            )

        if posixpath.normpath(self.filename) != self.filename:
            raise ValueError(
                "Invalid filename (reason: filename is not normalized): "
                f"{self.filename}"
            )

        if not PurePosixPath(self.filename).is_relative_to("."):
            raise ValueError(
                "Invalid filename (reason: filename is not relative to ./): "
                f"{self.filename}"
            )

        if PurePosixPath("..") in PurePosixPath(posixpath.normpath(self.filename)).parents:  # fmt: skip
            raise ValueError(
                "Invalid filename (reason: filename is not a sub-directory of ./): "
                f"{self.filename}"
            )

        if any(DOTS_REGEX.match(str(x)) for x in PurePosixPath(posixpath.normpath(self.filename)).parts):  # fmt: skip
            raise ValueError(
                "Invalid filename (reason: filename contains a sub-directory name that "
                f"is all dots): {self.filename}"
            )


class DioptraSession(ABC, Generic[T]):
    """The interface for communicating with the Dioptra API."""

    @property
    @abstractmethod
    def url(self) -> str:
        """The base URL of the API endpoints."""
        raise NotImplementedError

    @abstractmethod
    def connect(self) -> None:
        """Connect to the API."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the API."""
        raise NotImplementedError

    @abstractmethod
    def make_request(
        self,
        method_name: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, DioptraFile | list[DioptraFile]] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a request to the API.

        All response objects must implement the DioptraResponseProtocol interface.

        Args:
            method_name: The HTTP method to use. Must be one of "get", "patch", "post",
                "put", or "delete".
            url: The URL of the API endpoint.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.
            data: A dictionary to send in the body of the request as part of a
                multipart form. Optional, defaults to None.
            files: Dictionary of "name": DioptraFile or lists of DioptraFile pairs to be
                uploaded. Optional, defaults to None.

        Returns:
            The response from the API.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, endpoint: str, *parts, params: dict[str, Any] | None = None) -> T:
        """Make a GET request to the API.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.

        Returns:
            The response from the API.
        """
        raise NotImplementedError

    @abstractmethod
    def patch(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> T:
        """Make a PATCH request to the API.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            The response from the API.
        """
        raise NotImplementedError

    @abstractmethod
    def post(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, DioptraFile | list[DioptraFile]] | None = None,
    ) -> T:
        """Make a POST request to the API.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.
            data: A dictionary to send in the body of the request as part of a
                multipart form. Optional, defaults to None.
            files: Dictionary of "name": DioptraFile or lists of DioptraFile pairs to be
                uploaded. Optional, defaults to None.

        Returns:
            The response from the API.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> T:
        """Make a DELETE request to the API.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            The response from the API.
        """
        raise NotImplementedError

    @abstractmethod
    def put(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> T:
        """Make a PUT request to the API.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            The response from the API.
        """
        raise NotImplementedError

    @abstractmethod
    def download(
        self,
        endpoint: str,
        *parts,
        output_path: Path,
        params: dict[str, Any] | None = None,
    ) -> Path:
        """Download a file from the API.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            output_path: The path where the downloaded file should be saved.
            params: The query parameters to include in the request. Optional, defaults
                to None.

        Returns:
            The path to the downloaded file.
        """
        raise NotImplementedError

    def _get(
        self, endpoint: str, *parts, params: dict[str, Any] | None = None
    ) -> DioptraResponseProtocol:
        """Make a GET request to the API.

        The response from this internal method always implements the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.

        Returns:
            A response object that implements the DioptraResponseProtocol interface.
        """
        return self.make_request("get", self.build_url(endpoint, *parts), params=params)

    def _patch(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a PATCH request to the API.

        The response from this internal method always implements the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A response object that implements the DioptraResponseProtocol interface.
        """
        return self.make_request(
            "patch", self.build_url(endpoint, *parts), params=params, json_=json_
        )

    def _post(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, DioptraFile | list[DioptraFile]] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a POST request to the API.

        The response from this internal method always implements the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.
            data: A dictionary to send in the body of the request as part of a
                multipart form. Optional, defaults to None.
            files: Dictionary of "name": DioptraFile or lists of DioptraFile pairs to be
                uploaded. Optional, defaults to None.

        Returns:
            A response object that implements the DioptraResponseProtocol interface.
        """
        return self.make_request(
            "post",
            self.build_url(endpoint, *parts),
            params=params,
            json_=json_,
            data=data,
            files=files,
        )

    def _delete(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a DELETE request to the API.

        The response from this internal method always implements the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A response object that implements the DioptraResponseProtocol interface.
        """
        return self.make_request(
            "delete", self.build_url(endpoint, *parts), params=params, json_=json_
        )

    def _put(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a PUT request to the API.

        The response from this internal method always implements the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A response object that implements the DioptraResponseProtocol interface.
        """
        return self.make_request(
            "put", self.build_url(endpoint, *parts), params=params, json_=json_
        )

    @staticmethod
    def build_url(base: str, *parts) -> str:
        """Build a URL from a base and one or more parts.

        Args:
            base: The base URL.
            *parts: The parts to join to the base URL.

        Returns:
            The joined URL.
        """
        return urljoin(base, *parts)


class CollectionClient(Generic[T]):
    """The interface for an API collection client.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str]

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the CollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        self._session = session

    @property
    def url(self) -> str:
        """The URL of the API endpoint."""
        return self._session.build_url(self._session.url, self.name)


class SubCollectionClient(Generic[T]):
    """The interface for an API sub-collection client.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str]

    def __init__(
        self,
        session: DioptraSession[T],
        root_collection: CollectionClient[T],
        parent_sub_collections: list["SubCollectionClient[T]"] | None = None,
    ) -> None:
        """Initialize the SubCollectionClient instance.

        Args:
            session: The Dioptra API session object.
            root_collection: The client for the root collection that owns this
                sub-collection.
            parent_sub_collections: An ordered list of parent sub-collection clients
                that own this sub-collection and are also owned by the root collection.
                For example, a client for the hypothetical
                /col/{id1}/subColA/{id2}/subColB sub-collection would list the client
                for subColA as the parent sub-collection.
        """
        self._session = session
        self._root_collection = root_collection
        self._parent_sub_collections: list["SubCollectionClient[T]"] = (
            parent_sub_collections or []
        )

    def build_sub_collection_url(self, *resource_ids: str | int) -> str:
        """Build a sub-collection URL owned by one or more parent resources.

        Args:
            *resource_ids: The parent resource ids that own the sub-collection.

        Returns:
            The joined sub-collection URL.

        Raises:
            SubCollectionUrlError: If the number of resource ids does not match the
                expected count. For example, a client for the hypothetical
                /col/{id1}/subColA/{id2}/subColB sub-collection would expect 2 resource
                ids.
        """
        # Running example for hypothetical URL: /col/{id1}/subColA/{id2}/subColB
        self._validate_resource_ids_count(resource_ids)
        # Builds the URL root (ex: /col/{id1})
        parent_url_parts: list[str] = [
            self._root_collection.url,
            str(resource_ids[0]),
        ]

        # Builds the parent sub-collection parts (ex: /subColA/{id2})
        for resource_id, parent_sub_collection in zip(
            resource_ids[1:], self._parent_sub_collections
        ):
            parent_url_parts.extend([parent_sub_collection.name, str(resource_id)])

        # Joins the root and parent parts with the sub-collection name
        # (ex: /col/{id1}/subColA/{id2}/subColB)
        return self._session.build_url(*parent_url_parts, self.name)

    def _validate_resource_ids_count(self, resource_ids: tuple[str | int, ...]) -> None:
        num_resource_ids = len(resource_ids)
        expected_count = len(self._parent_sub_collections) + 1
        if num_resource_ids != expected_count:
            raise SubCollectionUrlError(
                f"Invalid number of resource ids (reason: expected {expected_count}): "
                f"{num_resource_ids}"
            )
