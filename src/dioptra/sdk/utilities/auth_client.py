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
import os
from typing import Any, Final, Literal

from structlog.stdlib import BoundLogger

from dioptra.client import (
    DioptraClient,
    connect_json_dioptra_client,
    connect_response_dioptra_client,
)
from dioptra.client.base import DioptraResponseProtocol

ENV_DIOPTRA_API: Final[str] = "DIOPTRA_API"
ENV_DIOPTRA_WORKER_USERNAME: Final[str] = "DIOPTRA_WORKER_USERNAME"
ENV_DIOPTRA_WORKER_PASSWORD: Final[str] = "DIOPTRA_WORKER_PASSWORD"


def get_authenticated_worker_client(
    log: logging.Logger | BoundLogger,
    client_type: Literal["json", "response"] = "response",
) -> DioptraClient:
    if (username := os.getenv(ENV_DIOPTRA_WORKER_USERNAME)) is None:
        log.error(f"{ENV_DIOPTRA_WORKER_USERNAME} environment variable is not set")
        raise ValueError(
            f"{ENV_DIOPTRA_WORKER_USERNAME} environment variable is not set"
        )

    if (password := os.getenv(ENV_DIOPTRA_WORKER_PASSWORD)) is None:
        log.error(f"{ENV_DIOPTRA_WORKER_PASSWORD} environment variable is not set")
        raise ValueError(
            f"{ENV_DIOPTRA_WORKER_PASSWORD} environment variable is not set"
        )

    # Instantiate a Dioptra client and login using worker's authentication details
    client: DioptraClient[DioptraResponseProtocol] | DioptraClient[dict[str, Any]]
    try:
        if client_type == "json":
            client = connect_json_dioptra_client()
        else:
            client = connect_response_dioptra_client()

    except ValueError:
        log.error(f"{ENV_DIOPTRA_API} environment variable is not set")
        raise ValueError(f"{ENV_DIOPTRA_API} environment variable is not set") from None

    client.auth.login(username=username, password=password)

    return client
