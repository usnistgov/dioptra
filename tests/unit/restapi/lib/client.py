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
from http import HTTPStatus
from pathlib import Path
from typing import Any, Callable, Protocol, cast

import structlog
from flask.testing import FlaskClient
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage
from werkzeug.test import TestResponse

from dioptra.client.base import (
    DioptraClientError,
    DioptraFile,
    DioptraRequestProtocol,
    DioptraResponseProtocol,
    DioptraSession,
    IllegalArgumentError,
    StatusCodeError,
)
from dioptra.restapi.routes import V1_ROOT

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class DioptraTestResponse(object):
    """
    A wrapper for Flask TestResponse objects that follows the DioptraResponseProtocol
    interface.
    """

    def __init__(self, test_response: TestResponse) -> None:
        """Initialize the DioptraTestResponse instance.

        Args:
            test_response: The Flask TestResponse object.
        """
        self._test_response = test_response

    @property
    def request(self) -> DioptraRequestProtocol:
        """The request that generated the response."""
        return cast(DioptraRequestProtocol, self._test_response.request)

    @property
    def status_code(self) -> int:
        """The HTTP status code of the response."""
        return self._test_response.status_code

    @property
    def text(self) -> str:
        """The response body as a string."""
        return self._test_response.text

    def json(self) -> dict[str, Any]:
        """Return the response body as a JSON-like Python dictionary.

        Returns:
            The response body as a dictionary.
        """
        return cast(dict[str, Any], self._test_response.get_json(silent=False))


class RequestMethodProtocol(Protocol):
    """The interface for a FlaskClient request method."""

    def __call__(self, *args: Any, **kw: Any) -> TestResponse:
        """The method signature for a FlaskClient request method.

        Args:
            *args: Positional arguments to pass to the request method.
            **kw: Keyword arguments to pass to the request method.

        Returns:
            A Flask TestResponse object.
        """
        ...  # fmt: skip


def wrap_request_method(
    func: RequestMethodProtocol,
) -> Callable[..., DioptraResponseProtocol]:
    """
    Wrap a FlaskClient request method to log the requests and responses and wrap the
    response in a DioptraTestResponse object.

    Args:
        func: The FlaskClient request method to wrap.

    Returns:
        The wrapped request method.
    """

    def wrapper(url: str, *args, **kwargs) -> DioptraResponseProtocol:
        """Wrap the FlaskClient request method.

        The returned response object will follow the DioptraResponseProtocol interface.

        Args:
            url: The URL of the API endpoint.
            *args: Additional arguments to pass to the requests method.
            **kwargs: Additional keyword arguments to pass to the requests method.

        Returns:
            The response from the requests method.
        """
        LOGGER.debug(
            "Request made.",
            url=url,
            method=str(func.__name__).upper(),  # type: ignore
            method_kwargs=kwargs,
        )
        response = DioptraTestResponse(func(url, *args, **kwargs))
        LOGGER.debug("Response received.", status_code=response.status_code)
        return response

    return wrapper


def is_2xx(status_code: int) -> bool:
    """Check if the status code is in the 2xx range.

    Args:
        status_code: The HTTP status code to check.

    Returns:
        True if the status code is in the 2xx range, False otherwise.
    """
    return status_code >= HTTPStatus.OK and status_code < HTTPStatus.MULTIPLE_CHOICES


def format_file_for_request(file_: DioptraFile) -> FileStorage:
    """Format the DioptraFile object into a FlaskClient-compatible data structure.

    Returns:
        The file encoded as a Werkzeug FileStorage object.
    """
    if file_.content_type is None:
        return FileStorage(stream=file_.stream, filename=file_.filename)

    return FileStorage(
        stream=file_.stream, filename=file_.filename, content_type=file_.content_type
    )


def prepare_data_and_files(
    data: dict[str, Any] | None,
    files: dict[str, DioptraFile | list[DioptraFile]] | None,
) -> dict[str, Any]:
    """Prepare the data and files for the request.

    Args:
        data: A dictionary to send in the body of the request as part of a multipart
            form.
        files: Dictionary of "name": DioptraFile or lists of DioptraFile pairs to be
            uploaded.

    Returns:
        A dictionary containing the prepared data and files dictionary.
    """
    merged: dict[str, Any] = {}

    if data is not None:
        merged = merged | data

    if files is not None:
        for key, value in files.items():
            if isinstance(value, DioptraFile):
                merged[key] = format_file_for_request(value)

            else:
                formatted_files: list[FileStorage] = []

                try:
                    for dioptra_file in value:
                        if not isinstance(dioptra_file, DioptraFile):
                            raise IllegalArgumentError(
                                "Illegal type for files (reason: a list can only "
                                f"contain the DioptraFile type): {type(dioptra_file)}."
                            )

                        formatted_files.append(format_file_for_request(dioptra_file))

                except TypeError as err:
                    raise IllegalArgumentError(
                        "Illegal type for files (reason: must be a DioptraFile or a "
                        f"list of DioptraFile): {type(value)}."
                    ) from err

                merged[key] = formatted_files

    return merged


class DioptraFlaskClientSession(DioptraSession[DioptraResponseProtocol]):
    """
    The interface for communicating with the Dioptra API using the FlaskClient.
    """

    def __init__(self, flask_client: FlaskClient) -> None:
        """Initialize the DioptraFlaskClientSession instance.

        Args:
            flask_client: The FlaskClient object to use for making requests.
        """
        self._session: FlaskClient = flask_client

    @property
    def url(self) -> str:
        """The base URL of the API endpoints."""
        return self.build_url("/", V1_ROOT)

    def connect(self) -> None:
        """Connect to the API. A no-op for the FlaskClient."""
        pass

    def close(self) -> None:
        """Close the connection to the API. A no-op for the FlaskClient."""
        pass

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
            ValueError: If an unsupported method is requested.
        """
        methods_registry: dict[str, Callable[..., DioptraResponseProtocol]] = {
            "get": wrap_request_method(self._session.get),
            "patch": wrap_request_method(self._session.patch),
            "post": wrap_request_method(self._session.post),
            "put": wrap_request_method(self._session.put),
            "delete": wrap_request_method(self._session.delete),
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
        method_kwargs: dict[str, Any] = {"follow_redirects": True}

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
            method_kwargs["query_string"] = params

        if data or files:
            merged_data = prepare_data_and_files(data=data, files=files)
            method_kwargs["data"] = merged_data
            method_kwargs["content_type"] = "multipart/form-data"

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

        response = self._session.get(self.build_url(endpoint, *parts), **kwargs)

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
            f.write(response.get_data(as_text=False))

        return output_path

    def get(
        self, endpoint: str, *parts, params: dict[str, Any] | None = None
    ) -> DioptraResponseProtocol:
        """Make a GET request to the API.

        The response will be a DioptraTestResponse object, which follows the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.

        Returns:
            A DioptraTestResponse object.
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

        The response will be a DioptraTestResponse object, which follows the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A DioptraTestResponse object.
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

        The response will be a DioptraTestResponse object, which follows the
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
            A DioptraTestResponse object.
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

        The response will be a DioptraTestResponse object, which follows the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A DioptraTestResponse object.
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

        The response will be a DioptraTestResponse object, which follows the
        DioptraResponseProtocol interface.

        Args:
            endpoint: The base URL of the API endpoint.
            *parts: Additional parts to append to the base URL.
            params: The query parameters to include in the request. Optional, defaults
                to None.
            json_: The JSON data to include in the request. Optional, defaults to None.

        Returns:
            A DioptraTestResponse object.
        """
        return self._put(endpoint, *parts, params=params, json_=json_)
