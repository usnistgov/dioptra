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
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any, Callable, Final, Generic, TypeVar, cast
from urllib.parse import urlparse, urlunparse

import requests
import structlog
from structlog.stdlib import BoundLogger

from .base import (
    APIConnectionError,
    DioptraResponseProtocol,
    DioptraSession,
    JSONDecodeError,
    StatusCodeError,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

DIOPTRA_API_VERSION: Final[str] = "v1"

T = TypeVar("T")


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
            "Request made.",
            url=url,
            method=str(func.__name__).upper(),
        )

        try:
            response = cast(DioptraResponseProtocol, func(url, *args, **kwargs))

        except requests.ConnectionError as err:
            LOGGER.error(
                "Connection to REST API failed",
                url=url,
            )
            raise APIConnectionError(f"Connection failed: {url}") from err

        LOGGER.debug("Response received.", status_code=response.status_code)
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
    if is_not_2xx(response.status_code):
        LOGGER.error(
            "HTTP error code returned",
            status_code=response.status_code,
            method=response.request.method,
            text=response.text,
            url=response.request.url,
        )
        raise StatusCodeError(f"Error code returned: {response.status_code}")

    try:
        response_dict = response.json()

    except requests.JSONDecodeError as err:
        LOGGER.error(
            "Failed to parse HTTP response data as JSON",
            method=response.request.method,
            text=response.text,
            url=response.request.url,
        )
        raise JSONDecodeError("Failed to parse HTTP response data as JSON") from err

    return response_dict


def is_not_2xx(status_code: int) -> bool:
    """Check if the status code is not in the 2xx range.

    Args:
        status_code: The HTTP status code to check.

    Returns:
        True if the status code is not in the 2xx range, False otherwise.
    """
    return status_code < HTTPStatus.OK or status_code >= HTTPStatus.MULTIPLE_CHOICES


class BaseDioptraRequestsSession(DioptraSession[T], ABC, Generic[T]):
    """
    The interface for communicating with the Dioptra API using the requests library.
    """

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
    ) -> DioptraResponseProtocol:
        """Make a request to the API.

        Args:
            method_name: The HTTP method to use. Must be one of "get", "patch", "post",
                "put", or "delete".
            url: The URL of the API endpoint.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            The response from the API.

        Raises:
            ValueError: If an unsupported method is requested.
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
            LOGGER.error(
                "Unsupported method requested. Must be one of "
                f"{sorted(methods_registry.keys())}.",
                name=method_name,
            )
            raise ValueError(
                f"Unsupported method requested. Must be one of "
                f"{sorted(methods_registry.keys())}."
            )

        method = methods_registry[method_name]
        method_kwargs: dict[str, Any] = {}

        if json_:
            method_kwargs["json"] = json_

        if params:
            method_kwargs["params"] = params

        return method(url, **method_kwargs)

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
    ) -> T:
        """Make a POST request to the API.

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
            LOGGER.error(
                "Failed to start session connection.",
                address=self.url,
            )
            raise APIConnectionError("Failed to start session connection.")

        return self._session


class DioptraRequestsSession(BaseDioptraRequestsSession[DioptraResponseProtocol]):
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
        """
        return self._patch(endpoint, *parts, params=params, json_=json_)

    def post(
        self,
        endpoint: str,
        *parts,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
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

        Returns:
            A requests Response object.
        """
        return self._post(endpoint, *parts, params=params, json_=json_)

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
        """
        return self._put(endpoint, *parts, params=params, json_=json_)


class DioptraRequestsSessionJson(BaseDioptraRequestsSession[dict[str, Any]]):
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
    ) -> dict[str, Any]:
        """Make a POST request to the API.

        The response will be a JSON-like Python dictionary.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A Python dictionary containing the response data.
        """
        return convert_response_to_dict(
            self._post(endpoint, *parts, params=params, json_=json_)
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
        """
        return convert_response_to_dict(
            self._put(endpoint, *parts, params=params, json_=json_)
        )
