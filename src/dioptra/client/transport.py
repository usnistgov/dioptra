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
"""Limit optional hybrid TLS API sessions to one explicitly selected HTTPS server.

Ordinary API connections use Requests directly. Hybrid sessions require the
X25519MLKEM768 key-exchange group and refuse requests or redirects to another
scheme, host or port. Certificate trust and proxy selection still use Requests'
normal inputs; the required TLS context is kept separate for each trust selection.
"""

from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from requests.adapters import HTTPAdapter
from requests.utils import DEFAULT_CA_BUNDLE_PATH
from urllib3.util.ssl_ import create_urllib3_context

from dioptra.sdk.utilities.tls import enforce_tls


def https_origin(url: str) -> tuple[str, str, int]:
    """Normalize an HTTPS URL to the server identity used for redirect checks.

    Args:
        url: Absolute HTTPS URL without a username or password. Paths and queries are
            allowed but are not part of the server identity.

    Returns:
        A tuple of scheme, lowercase hostname and port. An omitted port becomes 443;
        Requests normalizes international hostname spelling before comparison.

    Raises:
        ValueError: The URL lacks an HTTPS host, includes credentials, or has an invalid
            port or URL syntax.
    """
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            "hybrid-required requires an HTTPS API URL without user information"
        )
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError("hybrid-required requires an HTTPS port between 1 and 65535")
    prepared = requests.PreparedRequest()
    prepared.prepare_url(url, None)
    normalized = urlsplit(str(prepared.url))
    return (
        normalized.scheme,
        str(normalized.hostname).lower(),
        normalized.port if normalized.port is not None else 443,
    )


class HybridAdapter(HTTPAdapter):
    """Require hybrid key exchange for API HTTPS connection pools.

    Each pool receives its own SSL context so one pool's CA bundle cannot extend
    another pool's trust. Requests still selects CA files, client certificates and
    proxies. HTTPS connections to the proxy use Requests' ordinary TLS policy; the
    API connection through the proxy must use the required hybrid key exchange.
    """

    def __init__(self) -> None:
        """Initialize the Requests adapter and its per-pool SSL-context cache."""
        super().__init__()
        self.contexts: dict[tuple[Any, Any], Any] = {}

    def build_connection_pool_key_attributes(self, request, verify, cert=None):
        """Select a connection pool and enforce its API-side hybrid TLS policy.

        Args:
            request: Prepared Requests request identifying the destination server.
            verify: True for Requests' CA bundle or a CA file/directory path. False is
                rejected because this adapter requires certificate verification.
            cert: Optional Requests client-certificate path or certificate/key pair.

        Returns:
            The Requests host-parameters and pool-parameters dictionaries, with a
            per-trust-selection SSL context added to the pool parameters.

        Raises:
            ValueError: Verification is disabled or the runtime cannot enforce the
                required hybrid group and TLS version.
            OSError: The selected certificate trust data cannot be loaded.
        """
        if verify is False:
            raise ValueError(
                "hybrid-required does not permit disabled certificate verification"
            )
        host, pool = super().build_connection_pool_key_attributes(request, verify, cert)
        # Requests supplies its preloaded certifi context for verify=True. Retain
        # its trust source without mutating that process-shared context. Explicit
        # environment CA bundles remain in the pool arguments returned above.
        key = (verify, cert)
        if key not in self.contexts:
            context = create_urllib3_context()
            if verify is True:
                context.load_verify_locations(DEFAULT_CA_BUNDLE_PATH)
            self.contexts[key] = enforce_tls(context, "hybrid-required")
        pool["ssl_context"] = self.contexts[key]
        return host, pool


class HybridSession(requests.Session):
    """Allow hybrid HTTPS requests only to the selected API server.

    Use Requests' normal CA environment and proxy settings, but permit API requests only
    to the configured HTTPS server. Reject a request or redirect that changes scheme,
    hostname or port before connecting to that destination. This prevents API
    credentials from being sent to a different server.

    Args:
        address: API HTTPS URL without credentials. Its normalized hostname and port
            define the only permitted origin, including redirect targets.
    """

    def __init__(self, address: str) -> None:
        """Select the API origin and check hybrid support before any network access.

        Args:
            address: Absolute HTTPS API URL, normalized by https_origin.

        Raises:
            ValueError: The URL is invalid or this runtime cannot enforce hybrid TLS.
        """
        super().__init__()
        self.origin = https_origin(address)
        # Fail unsupported selection before credentials or network operations.
        enforce_tls(create_urllib3_context(), "hybrid-required")
        self.adapter = HybridAdapter()

    def get_adapter(self, url: str) -> HTTPAdapter:
        """Return the hybrid adapter only for an approved destination.

        Args:
            url: Absolute request or redirect URL.

        Returns:
            This session's adapter for requests to its configured HTTPS origin.

        Raises:
            ValueError: The URL is invalid or changes the configured scheme, hostname or
                port.
        """
        if https_origin(url) != self.origin:
            raise ValueError(
                "hybrid-required refuses a request or redirect outside the API origin"
            )
        return self.adapter

    def get_redirect_target(self, response: requests.Response) -> str | None:
        """Read a redirect target and reject a change to another server.

        Requests can inspect a redirect even when the caller disables redirect
        following; this method enforces the same destination restriction in both cases.

        Args:
            response: Requests response whose Location header is inspected. Relative
                targets are resolved against response.url.

        Returns:
            The original Location value, or None when Requests finds no redirect.

        Raises:
            ValueError: The target is malformed or changes the configured HTTPS
                origin. The response is closed before raising, releasing its connection.
        """
        target = super().get_redirect_target(response)
        if target is not None:
            try:
                origin = https_origin(urljoin(response.url, target))
                if origin != self.origin:
                    raise ValueError("origin changed")
            except ValueError as exc:
                response.close()
                raise ValueError(
                    "hybrid-required refuses a redirect outside the API origin"
                ) from exc
        return target

    def close(self) -> None:
        """Release this session's hybrid connection pools and ordinary Requests resources.

        Returns:
            None. The caller should close the session or use it as a context manager.
        """
        self.adapter.close()
        super().close()
