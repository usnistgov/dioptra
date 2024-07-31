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
from typing import Any, Callable

import requests
import structlog
from structlog.stdlib import BoundLogger

from .base import (
    APIConnectionError,
    DioptraResponseProtocol,
    DioptraSession,
    JSONDecodeError,
    StatusCodeError,
    debug_response,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class DioptraRequestsSession(DioptraSession):
    def __init__(self, address: str | None = None) -> None:
        super().__init__(address=address)
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        self.connect()

        if self._session is None:
            LOGGER.error(
                "Failed to start session connection.",
                address=self.url,
            )
            raise APIConnectionError("Failed to start session connection.")

        return self._session

    def connect(self) -> None:
        if self._session is None:
            self._session = requests.Session()

    def close(self) -> None:
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
        method = self._get_request_method(method_name)
        method_kwargs: dict[str, Any] = {}

        if json_:
            method_kwargs["json"] = json_

        if params:
            method_kwargs["params"] = params

        try:
            response = method(url, **method_kwargs)
            if response.status_code != 200:
                raise StatusCodeError()

        except (
            requests.ConnectionError,
            StatusCodeError,
            requests.JSONDecodeError,
        ) as e:
            self.handle_error(url, method_name.upper(), json_, response, e)

        debug_response(response)
        return response

    def handle_error(
        self,
        url: str,
        method: str,
        data: dict[str, Any] | None,
        response: DioptraResponseProtocol,
        error: Exception,
    ) -> None:
        if type(error) is requests.ConnectionError:
            message = (
                "Could not connect to the REST API. Is the server running at "
                f"{self.url}?"
            )
            LOGGER.error(
                message, url=url, method=method, data=data, response=response.text
            )
            raise APIConnectionError(message)

        if type(error) is StatusCodeError:
            message = f"Error code {response.status_code} returned."
            LOGGER.error(
                message, url=url, method=method, data=data, response=response.text
            )
            raise StatusCodeError(message)

        if type(error) is requests.JSONDecodeError:
            message = "JSON response could not be decoded."
            LOGGER.error(
                message, url=url, method=method, data=data, response=response.text
            )
            raise JSONDecodeError(message)

    def _get_request_method(self, name: str) -> Callable[..., DioptraResponseProtocol]:
        methods_registry: dict[str, Callable[..., DioptraResponseProtocol]] = {
            "get": self.session.get,
            "post": self.session.post,
            "put": self.session.put,
            "delete": self.session.delete,
        }

        if name not in methods_registry:
            LOGGER.error(
                "Unsupported method requested. Must be one of "
                f"{sorted(methods_registry.keys())}.",
                name=name,
            )
            raise ValueError(
                f"Unsupported method requested. Must be one of "
                f"{sorted(methods_registry.keys())}."
            )

        return methods_registry[name]
