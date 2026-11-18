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
"""Verify a live TLS 1.3 endpoint against explicit trust, identity and fingerprint."""

import argparse
import hashlib
import json
import socket
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Standard HTTPS port, omitted when formatting a default HTTPS authority.
DEFAULT_HTTPS_PORT = 443
# Concrete local destinations for loopback listeners and wildcard bind mappings.
IPV4_LOOPBACK = "127.0.0.1"
IPV6_LOOPBACK = "::1"
# Matches the temporary listener in scripts/ssl_hybrid_nginx.conf.
HYBRID_PROBE_PORT = 18443


def context(trust: Path, hybrid: bool = False) -> ssl.SSLContext:
    """Build a TLS 1.3 client context with explicit CA trust and optional hybrid exchange.

    Args:
        trust: PEM file containing the selected validation roots.
        hybrid: Require X25519MLKEM768 when True, without a classical fallback.

    Returns:
        A new hostname-verifying SSLContext. Other clients are not modified.

    Raises:
        ValueError: Hybrid exchange cannot be enforced.
        OSError: The trust file cannot be loaded.
    """
    selected = ssl.create_default_context(cafile=str(trust))
    selected.minimum_version = ssl.TLSVersion.TLSv1_3
    if hybrid:
        select_hybrid(selected)
    return selected


def select_hybrid(selected: ssl.SSLContext) -> None:
    """Require hybrid exchange on the context used for the connection.

    Restrict the supplied context to X25519MLKEM768. This requires both
    SSLContext.set_groups and runtime support for that group; an unsupported request
    fails instead of selecting a different key exchange.

    Args:
        selected: Client or server SSLContext to modify in place.

    Returns:
        None.

    Raises:
        ValueError: The runtime cannot select the required hybrid group.
    """
    setter = getattr(selected, "set_groups", None)
    if not callable(setter):
        raise ValueError(
            "hybrid-required needs SSLContext.set_groups and X25519MLKEM768 support"
        )
    try:
        setter("X25519MLKEM768")
    except (ValueError, ssl.SSLError) as exc:
        raise ValueError(
            "hybrid-required cannot select X25519MLKEM768 on this runtime"
        ) from exc


def hybrid_context() -> ssl.SSLContext:
    """Check whether the local Python/OpenSSL runtime can require hybrid exchange.

    Returns:
        A newly configured hybrid TLS context.

    Raises:
        ValueError: The required group API or algorithm is unavailable.
    """
    selected = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    selected.minimum_version = ssl.TLSVersion.TLSv1_3
    select_hybrid(selected)
    return selected


class HybridHealthcheck(BaseHTTPRequestHandler):
    """Serve a temporary TLS capability response without application authentication."""

    def do_GET(self) -> None:
        """Return HTTP 204 with an empty body to the temporary capability probe.

        Returns:
            None.
        """
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args) -> None:
        """Suppress request logging in the temporary capability server.

        Args:
            args: BaseHTTPRequestHandler logging arguments, intentionally discarded.

        Returns:
            None.
        """


def serve_hybrid(certificate: Path, key: Path, port: int) -> None:
    """Run a loopback HTTPS server for hybrid TLS capability checks.

    This local server lets capability checks make a real hybrid TLS connection inside
    the helper container. It uses the supplied server certificate and key and runs until
    the caller terminates the helper. It does not need the signing CA's private key or
    bind a production service port.

    Args:
        certificate: PEM server certificate-chain file.
        key: Matching unencrypted server private-key file.
        port: Loopback TCP port to listen on.
    """
    selected = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    selected.minimum_version = ssl.TLSVersion.TLSv1_3
    select_hybrid(selected)
    selected.load_cert_chain(certificate, key)
    with HTTPServer((IPV4_LOOPBACK, port), HybridHealthcheck) as server:
        server.socket = selected.wrap_socket(server.socket, server_side=True)
        server.serve_forever()


def verify(
    connect: str,
    port: int,
    identity: str,
    trust: Path,
    fingerprint: str,
    *,
    hybrid: bool = False,
    path: str = "/health",
) -> dict:
    """Require the expected certificate, trusted identity and successful HTTPS response.

    Make one HTTPS request using the supplied trust roots and server identity, then
    compare the peer certificate with the expected fingerprint. No credentials are sent
    and redirects are not followed. Success establishes that this endpoint serves the
    expected certificate and response; it does not establish successful user
    authentication.

    Args:
        connect: Network address to connect to; it can differ from the verified
            identity.
        port: TCP port on that address.
        identity: DNS name or IP validated by TLS and sent in the HTTP Host header.
        trust: PEM validation root file.
        fingerprint: Expected server-certificate SHA-256 fingerprint.
        hybrid: Require the hybrid group as well as TLS 1.3 when True.
        path: HTTP request path, defaulting to /health.

    Returns:
        Dictionary containing negotiated TLS version, peer fingerprint, identity and
        HTTP status for the successful check.

    Raises:
        ValueError: The TLS version, peer fingerprint or HTTP response does not satisfy
            the check.
        ssl.SSLError: Certificate trust, identity or protocol negotiation fails.
        OSError: The connection or socket operation fails.
    """
    selected = context(trust, hybrid)
    with socket.create_connection((connect, port), timeout=10) as connection:
        with selected.wrap_socket(connection, server_hostname=identity) as secured:
            peer = secured.getpeercert(binary_form=True)
            if peer is None:
                raise ValueError(f"{identity}:{port}: peer supplied no certificate")
            observed = hashlib.sha256(peer).hexdigest()
            if observed != fingerprint:
                raise ValueError(
                    f"{identity}:{port}: certificate fingerprint {observed} differs from expected {fingerprint}"
                )
            authority = f"[{identity}]" if ":" in identity else identity
            secured.sendall(
                f"GET {path} HTTP/1.1\r\nHost: {authority}:{port}\r\nConnection: close\r\n\r\n".encode(
                    "ascii"
                )
            )
            response = secured.recv(4096).split(b"\r\n", 1)[0]
            parts = response.split()
            if (
                len(parts) < 2
                or not parts[1].isdigit()
                or not 200 <= int(parts[1]) < 300
            ):
                raise ValueError(
                    f"{identity}:{port}: unexpected HTTP response {response!r}"
                )
            return {
                "identity": identity,
                "port": port,
                "fingerprint_sha256": observed,
                "tls_version": secured.version(),
                "http_status": int(parts[1]),
            }


def main() -> None:
    """Dispatch the standalone TLS check or temporary hybrid capability server.
    Reads argparse options from the process command line and prints JSON for a
    successful verification. Check/server errors propagate as a failing process.
    This module is copied into containers and therefore imports only the standard
    library, without depending on the surrounding support package.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-hybrid", action="store_true")
    parser.add_argument("--serve-hybrid", action="store_true")
    parser.add_argument("--certificate", type=Path)
    parser.add_argument("--key", type=Path)
    parser.add_argument("--connect")
    parser.add_argument("--port", type=int)
    parser.add_argument("--identity")
    parser.add_argument("--trust", type=Path)
    parser.add_argument("--fingerprint")
    parser.add_argument("--path", default="/health")
    parser.add_argument("--hybrid", action="store_true")
    args = parser.parse_args()
    if args.serve_hybrid:
        if args.certificate is None or args.key is None or args.port is None:
            parser.error("hybrid serving probe requires certificate, key and port")
        serve_hybrid(args.certificate, args.key, args.port)
        return
    if args.check_hybrid:
        hybrid_context()
        print(json.dumps({"hybrid_groups": ["X25519MLKEM768"]}))
        return
    if any(
        value is None
        for value in (
            args.connect,
            args.port,
            args.identity,
            args.trust,
            args.fingerprint,
        )
    ):
        parser.error(
            "live verification requires connect, port, identity, trust and fingerprint"
        )
    print(
        json.dumps(
            verify(
                args.connect,
                args.port,
                args.identity,
                args.trust,
                args.fingerprint,
                hybrid=args.hybrid,
                path=args.path,
            )
        )
    )


if __name__ == "__main__":
    main()
