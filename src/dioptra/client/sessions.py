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
import logging
from abc import ABC, abstractmethod
from http import HTTPStatus
from io import BufferedReader
from pathlib import Path
from typing import Any, Callable, ClassVar, Final, Generic, TypeAlias, TypeVar, cast
from urllib.parse import urlparse, urlunparse

import requests
from requests_toolbelt import MultipartEncoder

from .base import (
    APIConnectionError,
    DioptraClientError,
    DioptraFile,
    DioptraResponseProtocol,
    DioptraSession,
    IllegalArgumentError,
    JSONDecodeError,
    StatusCodeError,
)

LOGGER = logging.getLogger(__name__)

DIOPTRA_API_VERSION: Final[str] = "v1"

T = TypeVar("T")

RequestsFileDataStructureType: TypeAlias = (
    tuple[str, BufferedReader] | tuple[str, BufferedReader, str]
)
MultipartEncoderFields: TypeAlias = list[
    tuple[str, RequestsFileDataStructureType | Any]
]


def wrap_request_method(
    func: Any,
) -> Callable[..., DioptraResponseProtocol]:
    """Wrap a requests method to log the request and response data.

    Args:
        func: The requests method to wrap.

    Returns:
        A wrapped version of the requests method that logs the request and response
        data.
    """

    def wrapper(url: str, *args, **kwargs) -> DioptraResponseProtocol:
        """Wrap the requests method to log the request and response data.

        The returned response object will follow the DioptraResponseProtocol interface.

        Args:
            url: The URL of the API endpoint.
            *args: Additional arguments to pass to the requests method.
            **kwargs: Additional keyword arguments to pass to the requests method.

        Returns:
            The response from the requests method.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
        """
        LOGGER.debug(
            "Request made: url=%s  method=%s",
            url,
            str(func.__name__).upper(),
        )

        try:
            response = cast(DioptraResponseProtocol, func(url, *args, **kwargs))

        except requests.ConnectionError as err:
            raise APIConnectionError(f"Connection failed: {url}") from err

        LOGGER.debug("Response received: status_code=%s", str(response.status_code))
        return response

    return wrapper


def convert_response_to_dict(response: DioptraResponseProtocol) -> dict[str, Any]:
    """Convert a response object to a JSON-like Python dictionary.

    Args:
        response: A response object that follows the DioptraResponseProtocol interface.

    Returns:
        A Python dictionary containing the response data.

    Raises:
        StatusCodeError: If the response status code is not in the 2xx range.
        JSONDecodeError: If the response data cannot be parsed as JSON.
    """
    if not is_2xx(response.status_code):
        LOGGER.debug(
            "HTTP error code returned: status_code=%s  method=%s  url=%s  text=%s",
            response.status_code,
            response.request.method,
            response.request.url,
            response.text,
        )
        raise StatusCodeError(response.status_code, response.text)

    try:
        response_dict = response.json()

    except requests.JSONDecodeError as err:
        LOGGER.debug(
            "Failed to parse HTTP response data as JSON: method=%s  url=%s  text=%s",
            response.request.method,
            response.request.url,
            response.text,
        )
        raise JSONDecodeError("Failed to parse HTTP response data as JSON") from err

    return response_dict


def is_2xx(status_code: int) -> bool:
    """Check if the status code is in the 2xx range.

    Args:
        status_code: The HTTP status code to check.

    Returns:
        True if the status code is in the 2xx range, False otherwise.
    """
    return status_code >= HTTPStatus.OK and status_code < HTTPStatus.MULTIPLE_CHOICES


def format_file_for_request(file_: DioptraFile) -> RequestsFileDataStructureType:
    """Format the DioptraFile object into a requests-compatible data structure.

    Returns:
        The file encoded as either a 2-tuple ("filename", fileobj) or a 3-tuple
        ("filename", fileobj, "content_type").
    """
    if file_.content_type is None:
        return (file_.filename, file_.stream)

    return (file_.filename, file_.stream, file_.content_type)


def to_multipart_encoder(
    data: dict[str, Any] | None,
    files: dict[str, DioptraFile | list[DioptraFile]] | None,
) -> MultipartEncoder:
    """Consolidate data and files into a multipart encoder.

    Args:
        data: A dictionary to send in the body of the request as part of a multipart
            form.
        files: Dictionary of "name": DioptraFile or lists of DioptraFile pairs to be
            uploaded.

    Returns:
        A MultipartEncoder object containing the data and files.
    """
    merged: MultipartEncoderFields = []

    if data is not None:
        for key, value in data.items():
            merged.append((key, value))

    if files is not None:
        for key, value in files.items():
            if isinstance(value, DioptraFile):
                merged.append((key, format_file_for_request(value)))

            else:
                try:
                    for dioptra_file in value:
                        if not isinstance(dioptra_file, DioptraFile):
                            raise IllegalArgumentError(
                                "Illegal type for files (reason: a list can only "
                                f"contain the DioptraFile type): {type(dioptra_file)}."
                            )

                        merged.append((key, format_file_for_request(dioptra_file)))

                except TypeError as err:
                    raise IllegalArgumentError(
                        "Illegal type for files (reason: must be a DioptraFile or a "
                        f"list of DioptraFile): {type(value)}."
                    ) from err

    return MultipartEncoder(merged)


class BaseDioptraRequestsSession(DioptraSession[T], ABC, Generic[T]):
    """
    The interface for communicating with the Dioptra API using the requests library.

    Attributes:
        DOWNLOAD_CHUNK_SIZE: The number of bytes to read into memory per chunk when
            downloading a file from the API.
    """

    DOWNLOAD_CHUNK_SIZE: ClassVar[int] = 10 * 1024

    def __init__(self, address: str) -> None:
        """Initialize the Dioptra API session object.

        Args:
            address: The base URL of the API endpoints.
        """
        self._scheme, self._netloc, self._path, _, _, _ = urlparse(address)
        self._session: requests.Session | None = None

    @property
    def url(self) -> str:
        """The base URL of the API endpoints."""
        return urlunparse((self._scheme, self._netloc, self._path, "", "", ""))

    def connect(self) -> None:
        """Connect to the API using a requests Session."""
        if self._session is None:
            self._session = requests.Session()

    def close(self) -> None:
        """Close the connection to the API by closing the requests Session."""
        if self._session is None:
            return None

        self._session.close()
        self._session = None

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

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
            IllegalArgumentError: If the values passed to the arguments are not
                supported by the requested method.
        """
        session = self._get_requests_session()
        methods_registry: dict[str, Callable[..., DioptraResponseProtocol]] = {
            "get": wrap_request_method(session.get),
            "patch": wrap_request_method(session.patch),
            "post": wrap_request_method(session.post),
            "put": wrap_request_method(session.put),
            "delete": wrap_request_method(session.delete),
        }

        if method_name not in methods_registry:
            raise DioptraClientError(
                f"Unsupported method requested (reason: must be one of "
                f"{sorted(methods_registry.keys())}): {method_name}."
            )

        method = methods_registry[method_name]
        method_kwargs: dict[str, Any] = {}

        if method_name != "post":
            if data:
                raise IllegalArgumentError(
                    "Illegal value for data (reason: data is only supported for POST "
                    f"requests): {data}."
                )

            if files:
                raise IllegalArgumentError(
                    "Illegal value for files (reason: files is only supported for POST "
                    f"requests): {files}."
                )

        if json_:
            if data:
                raise IllegalArgumentError(
                    "Illegal value for json_ (reason: json_ is not supported if data "
                    f"is not None): {json_}."
                )

            if files:
                raise IllegalArgumentError(
                    "Illegal value for json_ (reason: json_ is not supported if files "
                    f"is not None): {json_}."
                )

            method_kwargs["json"] = json_

        if params:
            method_kwargs["params"] = params

        if data or files:
            merged_data = to_multipart_encoder(data=data, files=files)
            method_kwargs["data"] = merged_data
            method_kwargs["headers"] = {"Content-Type": merged_data.content_type}

        return method(url, **method_kwargs)

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

        Raises:
            DioptraClientError: If the output path is a directory or if creating the
                output directory fails.
            StatusCodeError: If the response status code is not in the 2xx range.
        """
        if output_path.exists() and output_path.is_dir():
            raise DioptraClientError(
                f"Invalid output filepath (reason: path is a directory): {output_path}"
            )

        if not output_path.parent.exists():
            try:
                output_path.parent.mkdir(parents=True)

            except OSError as err:
                raise DioptraClientError(
                    f"Output directory creation failed (reason: {err.strerror}): "
                    f"{output_path.parent}"
                ) from err

        kwargs: dict[str, Any] = {}

        if params:
            kwargs["params"] = params

        session = self._get_requests_session()
        response = session.get(self.build_url(endpoint, *parts), stream=True, **kwargs)

        if not is_2xx(response.status_code):
            LOGGER.debug(
                "HTTP error code returned: status_code=%s  method=%s  url=%s  text=%s",
                response.status_code,
                response.request.method,
                response.request.url,
                response.text,
            )
            raise StatusCodeError(response.status_code, response.text)

        with output_path.open(mode="wb") as f:
            for chunk in response.iter_content(chunk_size=self.DOWNLOAD_CHUNK_SIZE):
                f.write(chunk)

        return output_path

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

    def _get_requests_session(self) -> requests.Session:
        """Get the requests Session object.

        This method will start a new session if one does not already exist.

        Returns:
            The requests Session object.

        Raises:
            APIConnectionError: If the session connection fails.
        """
        self.connect()

        if self._session is None:
            raise APIConnectionError(f"Failed to start session connection: {self.url}")

        return self._session


class DioptraRequestsSession(BaseDioptraRequestsSession[DioptraResponseProtocol]):
    """
    The interface for communicating with the Dioptra API using the requests library.

    The responses from the HTTP methods will be requests Response objects, which follow
    the DioptraResponseProtocol interface.

    Attributes:
        DOWNLOAD_CHUNK_SIZE: The number of bytes to read into memory per chunk when
            downloading a file from the API.
    """

    def get(
        self, endpoint: str, *parts, params: dict[str, Any] | None = None
    ) -> DioptraResponseProtocol:
        """Make a GET request to the API.

        The response will be a requests Response object, which follows the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.

        Returns:
            A requests Response object.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
        """
        return self._get(endpoint, *parts, params=params)

    def patch(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a PATCH request to the API.

        The response will be a requests Response object, which follows the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A requests Response object.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
        """
        return self._patch(endpoint, *parts, params=params, json_=json_)

    def post(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, DioptraFile | list[DioptraFile]] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a POST request to the API.

        The response will be a requests Response object, which follows the
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
            A requests Response object.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
        """
        return self._post(
            endpoint, *parts, params=params, json_=json_, data=data, files=files
        )

    def delete(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a DELETE request to the API.

        The response will be a requests Response object, which follows the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A requests Response object.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
        """
        return self._delete(endpoint, *parts, params=params, json_=json_)

    def put(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> DioptraResponseProtocol:
        """Make a PUT request to the API.

        The response will be a requests Response object, which follows the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A requests Response object.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
        """
        return self._put(endpoint, *parts, params=params, json_=json_)


class DioptraRequestsSessionJson(BaseDioptraRequestsSession[dict[str, Any]]):
    """
    The interface for communicating with the Dioptra API using the requests library.

    The responses from the HTTP methods will be JSON-like Python dictionaries. Responses
    that are not in the 2xx range will raise an exception.

    Attributes:
        DOWNLOAD_CHUNK_SIZE: The number of bytes to read into memory per chunk when
            downloading a file from the API.
    """

    def get(
        self, endpoint: str, *parts, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a GET request to the API.

        The response will be a JSON-like Python dictionary.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.

        Returns:
            A Python dictionary containing the response data.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
            JSONDecodeError: If the response data cannot be parsed as JSON.
            StatusCodeError: If the response status code is not in the 2xx range.
        """
        return convert_response_to_dict(self._get(endpoint, *parts, params=params))

    def patch(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PATCH request to the API.

        The response will be a JSON-like Python dictionary.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A Python dictionary containing the response data.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
            JSONDecodeError: If the response data cannot be parsed as JSON.
            StatusCodeError: If the response status code is not in the 2xx range.
        """
        return convert_response_to_dict(
            self._patch(endpoint, *parts, params=params, json_=json_)
        )

    def post(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, DioptraFile | list[DioptraFile]] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request to the API.

        The response will be a JSON-like Python dictionary.

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
            A Python dictionary containing the response data.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
            JSONDecodeError: If the response data cannot be parsed as JSON.
            StatusCodeError: If the response status code is not in the 2xx range.
        """
        return convert_response_to_dict(
            self._post(
                endpoint, *parts, params=params, json_=json_, data=data, files=files
            )
        )

    def delete(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a DELETE request to the API.

        The response will be a JSON-like Python dictionary.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A Python dictionary containing the response data.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
            JSONDecodeError: If the response data cannot be parsed as JSON.
            StatusCodeError: If the response status code is not in the 2xx range.
        """
        return convert_response_to_dict(
            self._delete(endpoint, *parts, params=params, json_=json_)
        )

    def put(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PUT request to the API.

        The response will be a JSON-like Python dictionary.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A Python dictionary containing the response data.

        Raises:
            APIConnectionError: If the connection to the REST API fails.
            DioptraClientError: If an unsupported method is requested.
            JSONDecodeError: If the response data cannot be parsed as JSON.
            StatusCodeError: If the response status code is not in the 2xx range.
        """
        return convert_response_to_dict(
            self._put(endpoint, *parts, params=params, json_=json_)
        )
