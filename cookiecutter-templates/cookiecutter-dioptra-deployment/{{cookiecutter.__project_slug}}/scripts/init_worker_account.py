#!/usr/bin/env python3
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

"""Create or authenticate the deployment worker account over verified HTTPS.

The Bash launcher runs this helper inside the initialization API container, where
Dioptra is already installed. Credentials come from the container's environment
and are encoded with the standard JSON library. Existing accounts are reused only
after authenticating with the retained password.
"""

import json
import os
import ssl
import sys
from contextlib import closing
from http.client import HTTPException, HTTPSConnection
from urllib.parse import urlsplit

from dioptra.sdk.utilities.tls import enforce_tls

# The API is reached directly on the deployment's internal network.
API_ADDRESS = "https://{{ cookiecutter.__project_slug }}-restapi:5000"
# Bound both connection setup and subsequent socket reads.
REQUEST_TIMEOUT_SECONDS = 30


def post_credentials(
    connection: HTTPSConnection, path: str, credentials: dict[str, str]
) -> int:
    """Send credentials to one API endpoint and return its HTTP status.

    The caller decides which statuses are acceptable. Consume and close the
    response so the connection can be reused for login after a conflict. No
    response body or authentication cookie is printed or saved to disk.

    Args:
        connection: Verified HTTPS connection with the selected TLS policy.
        path: Registration or login path, including the /api/v1 prefix.
        credentials: Username and password fields to serialize as JSON.

    Returns:
        The HTTP response status, including non-success statuses.

    Raises:
        HTTPException: The server response cannot be processed.
        OSError: Connecting, certificate verification or reading the response
            fails, including expiration of the socket timeout.
    """
    connection.request(
        "POST",
        path,
        body=json.dumps(credentials),
        headers={"Content-Type": "application/json"},
    )
    with connection.getresponse() as response:
        response.read()
        return response.status


def register_worker(
    address: str,
    username: str,
    password: str,
    *,
    key_exchange: str = "default",
) -> None:
    """Create the worker account or verify credentials for an existing account.

    Only HTTP 409 from registration permits a login attempt. Other registration
    failures remain failures, and a conflicting username is not accepted unless
    its saved password authenticates. Close the connection on every completion path.

    Args:
        address: API HTTPS address without the /api/v1 suffix.
        username: Nonempty worker username from deployment credentials.
        password: Nonempty retained password for creation or authentication.
        key_exchange: default requires TLS 1.3 with ordinary runtime groups;
            hybrid-required also requires X25519MLKEM768 without fallback.

    Returns:
        None after successful creation or authenticated account reuse.

    Raises:
        ValueError: Credentials are empty, the API address is invalid, or the
            selected TLS policy is invalid or unsupported by the runtime.
        RuntimeError: Registration fails with a status other than 409, or login
            fails after a conflict.
        HTTPException: The server response cannot be processed.
        OSError: HTTPS communication or loading a configured CA bundle fails.
    """
    if not username or not password:
        raise ValueError("Worker username and password must both be nonempty.")
    endpoint = urlsplit(address)
    if (
        endpoint.scheme != "https"
        or endpoint.hostname is None
        or endpoint.username is not None
        or endpoint.password is not None
        or endpoint.path not in ("", "/")
        or endpoint.query
        or endpoint.fragment
    ):
        raise ValueError("The API address must be an HTTPS origin without credentials.")
    # Retain the CA bundle inputs used by the deployed clients. When neither is
    # set, the SSL library uses SSL_CERT_FILE and its operating-system defaults.
    ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("CURL_CA_BUNDLE")
    context = enforce_tls(ssl.create_default_context(cafile=ca_bundle), key_exchange)
    credentials = {"username": username, "password": password}
    with closing(
        HTTPSConnection(
            endpoint.hostname,
            endpoint.port,
            timeout=REQUEST_TIMEOUT_SECONDS,
            context=context,
        )
    ) as connection:
        status = post_credentials(
            connection, "/api/v1/users/", credentials | {"confirmPassword": password}
        )
        operation = "creation"
        if status == 409:
            operation = "login"
            status = post_credentials(connection, "/api/v1/auth/login", credentials)
        if not 200 <= status < 300:
            raise RuntimeError(f"Worker account {operation} returned HTTP {status}.")


def main() -> int:
    """Register the worker using container environment credentials and TLS settings.

    Read DIOPTRA_WORKER_USERNAME and DIOPTRA_WORKER_PASSWORD without printing their
    values. DIOPTRA_TLS_KEY_EXCHANGE defaults to default. Error diagnostics omit
    request bodies, credentials and exception details that might contain them.

    Returns:
        Zero for a usable account, or one after reporting a failure to stderr.
    """
    try:
        register_worker(
            API_ADDRESS,
            os.environ.get("DIOPTRA_WORKER_USERNAME", ""),
            os.environ.get("DIOPTRA_WORKER_PASSWORD", ""),
            key_exchange=os.environ.get("DIOPTRA_TLS_KEY_EXCHANGE", "default"),
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (HTTPException, OSError, ValueError):
        print(
            "Worker account registration failed; check credentials, API access "
            "and TLS settings.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
