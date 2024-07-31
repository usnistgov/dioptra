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
from abc import ABC, abstractmethod
from posixpath import join as urljoin
from typing import Any, ClassVar, Final, Protocol
from urllib.parse import urlparse, urlunparse

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

DIOPTRA_API_VERSION: Final[str] = "v1"


class APIConnectionError(Exception):
    """Class for connection errors"""


class StatusCodeError(Exception):
    """Class for status code errors"""


class JSONDecodeError(Exception):
    """Class for JSON decode errors"""


class DioptraResponseProtocol(Protocol):
    @property
    def status_code(self) -> int:
        ...  # fmt: skip

    @property
    def text(self) -> str:
        ...  # fmt: skip

    def json(self) -> dict[str, Any]:
        ...  # fmt: skip


def debug_request(url: str, method: str, data: dict[str, Any] | None = None) -> None:
    LOGGER.debug("Request made.", url=url, method=method, data=data)


def debug_response(response: DioptraResponseProtocol) -> None:
    LOGGER.debug("Response received.", status_code=response.status_code)


class DioptraSession(ABC):
    def __init__(self, address: str | None = None) -> None:
        detected_address = (
            f"{address}/api/{DIOPTRA_API_VERSION}"
            if address
            else f"{os.environ['DIOPTRA_RESTAPI_URI']}/api/{DIOPTRA_API_VERSION}"
        )
        self._scheme, self._netloc, self._path, _, _, _ = urlparse(detected_address)

    @property
    def url(self) -> str:
        return urlunparse((self._scheme, self._netloc, self._path, "", "", ""))

    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def make_request(
        self,
        method_name: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_: dict[str, Any] | None = None,
    ) -> DioptraResponseProtocol:
        raise NotImplementedError

    @abstractmethod
    def handle_error(
        self,
        url: str,
        method: str,
        data: dict[str, Any],
        response: DioptraResponseProtocol,
        error: Exception,
    ) -> None:
        raise NotImplementedError

    def get(
        self, endpoint: str, *parts, params: dict[str, Any] | None = None
    ) -> DioptraResponseProtocol:
        url = urljoin(endpoint, *parts)
        debug_request(url, "GET")
        return self.make_request("get", url, params=params)

    def post(
        self, endpoint: str, *parts, json_: dict[str, Any]
    ) -> DioptraResponseProtocol:
        url = urljoin(endpoint, *parts)
        debug_request(url, "POST", json_)
        return self.make_request("post", url, json_=json_)

    def delete(
        self, endpoint: str, *parts, json_: dict[str, Any]
    ) -> DioptraResponseProtocol:
        url = urljoin(endpoint, *parts)
        debug_request(url, "DELETE", json_)
        return self.make_request("delete", url, json_=json_)

    def put(
        self, endpoint: str, *parts, json_: dict[str, Any]
    ) -> DioptraResponseProtocol:
        url = urljoin(endpoint, *parts)
        debug_request(url, "PUT", json_)
        return self.make_request("put", url, json_=json_)


class Endpoint(object):

    name: ClassVar[str]

    def __init__(self, session: DioptraSession) -> None:
        self._session = session

    @property
    def url(self) -> str:
        return urljoin(self._session.url, self.name)
