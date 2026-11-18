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
"""Validate production HTTP Host values before Flask can generate redirect URLs.

An authority is a hostname/IP plus an optional port, such as public.example:8443.
The API permits only configured authorities, including its direct internal name
and the public name nginx supplies. HTTPS comes from the API's native TLS
connection; client-supplied forwarding headers do not establish request identity.
Checking before routing prevents a trailing-slash redirect from reflecting an
unknown Host into its Location header.
"""

import ipaddress
import re
from collections.abc import Iterable
from urllib.parse import urlsplit

from flask import Flask
from werkzeug.exceptions import BadRequest
from werkzeug.wsgi import get_host


def parse_authority(value: str) -> tuple[str, int]:
    """Parse an HTTPS Host value into a comparable hostname and port.

    This checks and normalizes Host syntax; it does not approve the name for requests or
    confirm that a certificate covers it. The application must separately compare the
    result with its configured permitted hosts.

    Args:
        value: DNS hostname, IPv4 address or bracketed IPv6 address, optionally followed
            by a port. This is a Host-header value, not a complete URL.

    Returns:
        A lowercase hostname and numeric port. An omitted port is treated as 443, so
        EXAMPLE.org and example.org:443 compare equally.

    Raises:
        ValueError: The value includes credentials, URL components, whitespace,
            wildcards, invalid DNS labels, unbracketed IPv6 or an invalid port.
    """
    if not value or any(c.isspace() or c in "/\\?#@%," for c in value):
        raise ValueError("expected a hostname or bracketed IP authority")
    parsed = urlsplit("//" + value)
    host = parsed.hostname
    if not host or parsed.netloc.endswith(":"):
        raise ValueError("expected a hostname and optional valid port")
    port = parsed.port if parsed.port is not None else 443
    if not 1 <= port <= 65535:
        raise ValueError("authority port must be between 1 and 65535")
    _validate_host(host, parsed.netloc.startswith("["))
    literal = f"[{host}]" if ":" in host else host
    rendered = f"{literal}:{parsed.port}" if parsed.port is not None else literal
    if rendered != value.lower():
        raise ValueError("malformed authority")
    return host.lower(), port


def _validate_host(host: str, bracketed: bool) -> None:
    """Validate DNS labels or an explicitly bracketed IPv6 host.

    Args:
        host: Host text parsed from an authority, without brackets or a port.
        bracketed: True when the original authority used IPv6 brackets.

    Returns:
        None.

    Raises:
        ValueError: The IPv6 address, DNS characters, DNS labels or hostname length is
            invalid.
    """
    if len(host) > 253:
        raise ValueError("authority hostname is too long")
    if bracketed:
        ipaddress.IPv6Address(host)
        return
    if re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", host) is None:
        raise ValueError("invalid DNS or IP authority")
    if any(
        not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
        for label in host.split(".")
    ):
        raise ValueError("invalid DNS authority labels")


def validate_authorities(values: list[str]) -> None:
    """Validate the configured list of permitted HTTPS Host values.

    Check each configured entry's syntax without changing the list. ApprovedAuthorities
    separately checks whether a request's Host belongs to this list.

    Args:
        values: Hostnames or IP addresses with optional ports, accepted by
            parse_authority. Each entry is checked; the list is not modified.

    Returns:
        None.

    Raises:
        ValueError: An entry is invalid. The public error names the configuration
            setting without echoing submitted values.
    """
    try:
        for value in values:
            parse_authority(value)
    except (ValueError, UnicodeError) as exc:
        raise ValueError(
            "DIOPTRA_TLS_ALLOWED_AUTHORITIES requires valid HTTPS authorities"
        ) from exc


class ApprovedAuthorities:
    """Reject unapproved HTTP Host headers before Flask can generate redirects.

    Flask can generate a trailing-slash redirect while matching a route. Check Host
    before routing so that redirect cannot advertise an unknown server. Use the native
    TLS connection for HTTPS and nginx's configured public Host for proxied requests;
    client-supplied forwarding headers do not authorize a different scheme or host.

    Args:
        application: WSGI application called for accepted requests.
        authorities: Permitted HTTPS Host values, including ports where required. DNS
            case and an omitted default port use parse_authority normalization.
    """

    def __init__(self, application, authorities: Iterable[str]) -> None:
        """Normalize the allowed hosts and retain the wrapped WSGI application.

        Args:
            application: WSGI callable used for requests with an approved Host.
            authorities: Host/port strings accepted by parse_authority.

        Raises:
            ValueError: A configured authority has invalid syntax.
        """
        self.application = application
        self.allowed = frozenset(parse_authority(value) for value in authorities)

    def __call__(self, environ, start_response):
        """Validate the request Host before handing control to the application.

        Args:
            environ: WSGI request environment containing HTTP_HOST and server identity.
            start_response: WSGI callback used to send response status and headers.

        Returns:
            The wrapped application's response iterable, or a 400 response iterable for
            a malformed or unapproved Host. It does not consume the request body.
        """
        try:
            raw = environ.get("HTTP_HOST", "")
            # Validate the unmodified header too: supported host parsing removes
            # the default port but must not hide malformed authority syntax.
            authority = parse_authority(raw)
            parsed = parse_authority(get_host(environ))
            if authority != parsed or authority not in self.allowed:
                raise ValueError("unknown authority")
        except (ValueError, UnicodeError):
            return BadRequest("Unrecognized or malformed Host header.")(
                environ, start_response
            )
        return self.application(environ, start_response)


class AuthorityCheckedFlask(Flask):
    """Apply the production host allowlist before Flask creates a request context.

    The application configuration must contain DIOPTRA_TLS_ALLOWED_AUTHORITIES.
    All ordinary Flask routes and request processing remain in the wrapped app.
    """

    def wsgi_app(self, environ, start_response):
        """Check the request host and dispatch through Flask's normal WSGI handler.

        Args:
            environ: WSGI request environment supplied by the server.
            start_response: WSGI status/header callback supplied by the server.

        Returns:
            Flask's response iterable for an approved host, or an HTTP 400 iterable.
        """
        checked = ApprovedAuthorities(
            super().wsgi_app, self.config["DIOPTRA_TLS_ALLOWED_AUTHORITIES"]
        )
        return checked(environ, start_response)
