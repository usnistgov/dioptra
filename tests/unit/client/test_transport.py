"""Exercise scoped HTTPS trust, hybrid exchange and Requests proxy behavior."""

import json
import select
import socket
import socketserver
import ssl
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import cast

import pytest
import requests

from dioptra.client.sessions import DioptraRequestsSession
from dioptra.client.transport import HybridSession, https_origin
from dioptra.sdk.utilities.tls import enforce_tls

CAPABLE = callable(getattr(ssl.SSLContext, "set_groups", None))
hybrid_runtime = pytest.mark.skipif(
    not CAPABLE, reason="requires public context group selection"
)


def select_test_group(context: ssl.SSLContext, group: str) -> None:
    """Select a real OpenSSL peer group using only the capable runtime's public API."""
    setter = getattr(context, "set_groups", None)
    assert callable(setter)
    setter(group)


class TransportHandler(BaseHTTPRequestHandler):
    """Return the negotiated group or an intentional origin-changing redirect."""

    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://other.test/credentials")
        elif self.path == "/relative":
            self.send_response(308)
            self.send_header("Location", "/canonical")
        else:
            self.send_response(200)
        self.end_headers()
        group = getattr(self.connection, "group", lambda: None)()
        self.wfile.write(
            json.dumps({"group": group, "version": self.connection.version()}).encode()
        )

    def log_message(self, *args):
        """Keep fixture logging free of request contents."""


@contextmanager
def https_server(material, group=None):
    """Own one local TLS listener and shut it down even after a rejected handshake."""
    cert, key, _ = material
    context = enforce_tls(ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER))
    context.load_cert_chain(cert, key)
    if group is not None:
        select_test_group(context, group)
    server = ThreadingHTTPServer(("127.0.0.1", 0), TransportHandler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"https://localhost:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class ConnectHandler(socketserver.StreamRequestHandler):
    """Tunnel one CONNECT connection while retaining its observable destination."""

    def handle(self):
        method, destination, _ = self.rfile.readline().decode().split()
        assert method == "CONNECT"
        while self.rfile.readline() != b"\r\n":
            pass
        host, port = destination.rsplit(":", 1)
        with socket.create_connection((host, int(port)), timeout=5) as upstream:
            self.wfile.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            self.wfile.flush()
            cast(ConnectProxy, self.server).destinations.append(destination)
            relay(self.connection, upstream)


def relay(downstream: socket.socket, upstream: socket.socket) -> None:
    """Copy bounded test tunnel traffic until either endpoint closes."""
    sockets = [downstream, upstream]
    while True:
        readable, _, _ = select.select(sockets, [], [], 5)
        if not readable:
            return
        for source in readable:
            content = source.recv(65536)
            if not content:
                return
            (upstream if source is downstream else downstream).sendall(content)


class ConnectProxy(socketserver.ThreadingTCPServer):
    """Retain test observations on the proxy that owns their lifetime."""

    destinations: list[str]


@contextmanager
def connect_proxy(material, secure):
    """Own a test proxy whose optional outer TLS intentionally remains classical."""
    server = ConnectProxy(("127.0.0.1", 0), ConnectHandler)
    server.daemon_threads = True
    server.destinations = []
    if secure:
        context = enforce_tls(ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER))
        context.load_cert_chain(*material[:2])
        select_test_group(context, "X25519")
        server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield (
            server,
            f"{'https' if secure else 'http'}://localhost:{server.server_address[1]}",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://EXAMPLE.test/api", ("https", "example.test", 443)),
        ("https://example.test:443", ("https", "example.test", 443)),
        ("https://[::1]:8443/", ("https", "::1", 8443)),
        ("https://bücher.test/", ("https", "xn--bcher-kva.test", 443)),
    ],
)
def test_origin_matches_requests_preparation(url, expected):
    """Compare the origin Requests will actually connect to, including IDNA and IPv6."""
    prepared = requests.Request("GET", url).prepare()
    assert https_origin(url) == https_origin(str(prepared.url)) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://example.test",
        "https://example.test:0",
        "https://example.test:65536",
        "https://user@example.test",
    ],
)
def test_invalid_hybrid_origin_fails(url):
    """Reject a scheme, port or credential-bearing origin that cannot select safe HTTPS."""
    with pytest.raises(ValueError):
        https_origin(url)


def test_default_session_preserves_environment_ca_and_verification(
    tls_certificates, monkeypatch
):
    """Use configured CA trust through ordinary Requests and reject missing trust.

    The default session must keep supported environment trust without changing
    other library sessions or installing a verification bypass.
    """
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(tls_certificates[2]))
    with https_server(tls_certificates) as url:
        session = DioptraRequestsSession(url)
        session.connect()
        try:
            assert session._session is not None
            assert session._session.get(url, timeout=5).json()["version"] == "TLSv1.3"
            with pytest.raises(requests.exceptions.SSLError):
                session._session.get(url.replace("localhost", "127.0.0.1"), timeout=5)
            monkeypatch.delenv("REQUESTS_CA_BUNDLE")
            # A new connection pool must not inherit a previously loaded CA.
            with requests.Session() as unrelated:
                with pytest.raises(requests.exceptions.SSLError):
                    unrelated.get(url, timeout=5)
        finally:
            session.close()


@pytest.mark.skipif(CAPABLE, reason="requires a runtime without the public group API")
def test_unsupported_hybrid_fails_before_connecting():
    """Fail explicit hybrid selection clearly on the supported Python 3.11 baseline."""
    with pytest.raises(ValueError, match="SSLContext.set_groups"):
        HybridSession("https://localhost:1")


@hybrid_runtime
@pytest.mark.parametrize("proxy_mode", [None, "http", "https"])
def test_hybrid_trust_proxy_redirects_and_unrelated_context(
    tls_certificates, monkeypatch, proxy_mode
):
    """Enforce hybrid only on the API connection while retaining trust and proxies.

    The isolated capable runtime must negotiate the selected group, reject a
    cross-origin redirect and a classical API peer, while another ordinary
    session still connects to that classical peer. A TLS proxy itself remains
    classical so this also detects accidental policy application to that hop.
    """
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(tls_certificates[2]))
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")
    with https_server(tls_certificates, "X25519MLKEM768") as api:
        if proxy_mode is None:
            check_hybrid_api(api)
        else:
            with connect_proxy(tls_certificates, proxy_mode == "https") as (
                proxy,
                address,
            ):
                monkeypatch.setenv("HTTPS_PROXY", address)
                monkeypatch.setenv("NO_PROXY", "")
                check_hybrid_api(api)
                assert proxy.destinations
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")
    with https_server(tls_certificates, "X25519") as classical:
        with HybridSession(classical) as selected:
            with pytest.raises(requests.exceptions.SSLError):
                selected.get(classical, timeout=5)
        with requests.Session() as unrelated:
            assert (
                unrelated.get(classical, timeout=5).json()["group"].lower() == "x25519"
            )


def check_hybrid_api(api: str) -> None:
    """Assert selected negotiation and origin restrictions on a real API connection."""
    with HybridSession(api) as selected:
        response = selected.get(api, timeout=5)
        assert response.json() == {"group": "X25519MLKEM768", "version": "TLSv1.3"}
        assert selected.get(api + "/relative", timeout=5).status_code == 200
        for follow in (False, True):
            with pytest.raises(ValueError, match="outside the API origin"):
                selected.get(api + "/redirect", timeout=5, allow_redirects=follow)
        with pytest.raises(ValueError, match="disabled certificate verification"):
            selected.get(api, verify=False, timeout=5)
