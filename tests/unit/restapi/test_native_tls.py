"""Exercise production TLS through real local Gunicorn processes and restarts."""

import json
import os
import signal
import socket
import ssl
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest
import requests

from dioptra.restapi.config import _ENVIRONMENT_SETTINGS
from dioptra.restapi.key_file import initialize_key

pytestmark = pytest.mark.skipif(os.name == "nt", reason="Gunicorn requires POSIX")


def wait_until(predicate: Callable[[], bool], timeout: float = 20) -> None:
    """Wait up to timeout seconds for an observable server condition.

    Args:
        predicate: Check returning True once the required state is reached.
        timeout: Maximum polling time in seconds.

    Raises:
        Failed: The condition did not become true before the deadline.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    pytest.fail("native server did not reach the expected lifecycle state")


def alternate_pair(root: Path) -> tuple[Path, Path]:
    """Write a second valid pair to detect a hook overriding configured TLS identity.

    Args:
        root: Protected temporary output directory.

    Returns:
        Private-key and certificate paths signed by an unrelated test issuer.
    """
    from dioptra.ssl import certificates, publication

    ca_key, ca, _ = certificates.create_ca("Other test issuer", 2048, 2, None)
    key, cert, _ = certificates.issue(
        ca, ca_key, certificates.identities(("localhost",), ()), 2048, 1, None
    )
    private, chain = root / "other.key", root / "other.crt"
    publication.publish("issue", key, cert, private, chain)
    return private, chain


class NativeApiServer:
    """Run a local API server for native TLS and restart tests.

    The fixture starts the server and always stops its process group afterward,
    including a new master created by Gunicorn re-execution. Each request trusts only
    the selected test CA. Keeping setup and shutdown together makes both ordinary and
    restarted processes part of the same fixture lifetime.

    Args:
        root: Temporary launch directory, distinct from Gunicorn's chdir directory.
        pair: Configured server certificate, key and public trust-file paths.
        invocation: installed for dioptra-api, or module for Python module launch.
        hook_type: empty for a context without a pair, or alternate for an unrelated
            pair. Both must still serve the final configured certificate.
    """

    def __init__(self, root: Path, pair: tuple, invocation: str, hook_type: str):
        self.root = root
        cert, key, self.trust = pair
        self.target = root / "server"
        self.target.mkdir(mode=0o700)
        (self.target / "server.crt").write_bytes(cert.read_bytes())
        (self.target / "server.key").write_bytes(key.read_bytes())
        initialize_key(root / "keys/signing")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.url = f"https://localhost:{self.port}"
        self.pidfile = self.target / "api.pid"
        self.logfile = root / "gunicorn.log"
        self.process: subprocess.Popen | None = None
        hook = [
            "import ssl",
            "def ssl_context(conf, factory):",
            "    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)",
        ]
        if hook_type == "alternate":
            other_key, other_cert = alternate_pair(root)
            hook.append(
                f"    context.load_cert_chain({str(other_cert)!r}, {str(other_key)!r})"
            )
        hook.append("    return context")
        settings = {
            "chdir": str(self.target),
            "certfile": "server.crt",
            "keyfile": "server.key",
            "pidfile": "api.pid",
            "control_socket_disable": True,
            "workers": 1,
            "errorlog": str(self.logfile),
        }
        (root / "server.conf.py").write_text(
            "\n".join(
                [*hook, *(f"{name} = {value!r}" for name, value in settings.items())]
            )
            + "\n"
        )
        self.command = (
            [str(Path(sys.executable).with_name("dioptra-api"))]
            if invocation == "installed"
            else [sys.executable, "-m", "dioptra.restapi.cli.api"]
        )

    def start(self) -> None:
        """Start production Gunicorn and wait for a verified HTTPS health response."""
        environment = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                *_ENVIRONMENT_SETTINGS.values(),
                "GUNICORN_CMD_ARGS",
                "DIOPTRA_DEPLOY_SECRET_KEY",
                "FORWARDED_ALLOW_IPS",
            }
        }
        environment.update(
            DIOPTRA_TLS_ALLOWED_AUTHORITIES=json.dumps([f"localhost:{self.port}"]),
            DIOPTRA_TLS_KEY_EXCHANGE="default",
            MLFLOW_TRACKING_URI="http://127.0.0.1:1",
            NO_PROXY="localhost,127.0.0.1",
        )
        arguments = [
            *self.command,
            "prod",
            "--key-file",
            "keys/signing",
            "-c",
            "server.conf.py",
            "--bind",
            f"127.0.0.1:{self.port}",
        ]
        with self.logfile.open("a") as output:
            self.process = subprocess.Popen(
                arguments,
                cwd=self.root,
                env=environment,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        wait_until(self.healthy)

    def get(self, path: str, **kwargs) -> requests.Response:
        """Perform one fresh verified HTTPS request without following redirects.

        Args:
            path: API path and optional query string relative to this server.
            kwargs: Additional Requests arguments, such as deliberately forged headers.

        Returns:
            Fully read response. Its session is closed before returning.
        """
        with requests.Session() as client:
            client.trust_env = False
            return client.get(
                self.url + path,
                verify=str(self.trust),
                allow_redirects=False,
                timeout=2,
                **kwargs,
            )

    def healthy(self) -> bool:
        """Return whether a fresh trusted connection receives HTTP 200 from /health."""
        try:
            return self.get("/health").status_code == 200
        except requests.RequestException:
            return False

    def reload_workers(self) -> None:
        """Send HUP and wait for Gunicorn to report a new worker and serve trusted HTTPS."""
        assert self.process is not None
        before = self.logfile.read_text().count("Booting worker")
        os.kill(self.process.pid, signal.SIGHUP)
        wait_until(lambda: self.logfile.read_text().count("Booting worker") > before)
        wait_until(self.healthy)

    def reexecute(self) -> None:
        """Send USR2, terminate the old master and wait for its replacement to serve HTTPS."""
        assert self.process is not None
        os.kill(self.process.pid, signal.SIGUSR2)
        replacement = self.pidfile.with_name(self.pidfile.name + ".2")
        wait_until(replacement.exists)
        new_master = int(replacement.read_text())
        assert new_master != self.process.pid
        os.kill(self.process.pid, signal.SIGTERM)
        self.process.wait(timeout=10)
        wait_until(
            lambda: (
                self.pidfile.exists() and int(self.pidfile.read_text()) == new_master
            )
        )
        wait_until(self.healthy)

    def close(self) -> None:
        """Stop the entire owned process group, including any re-executed master."""
        if self.process is None:
            return
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=5)


@pytest.fixture(
    params=[("installed", "empty"), ("installed", "alternate"), ("module", "empty")]
)
def native_server(request, tls_certificates, tmp_path):
    """Start a real production API using relative signing/configuration/certificate paths.

    The three cases cover both launcher forms and hooks that omit or replace the
    serving pair. The fixture owns all process cleanup, including startup failures.
    """
    invocation, hook = request.param
    server = NativeApiServer(tmp_path, tls_certificates, invocation, hook)
    try:
        server.start()
        yield server
    finally:
        server.close()


def test_native_tls_uses_configured_certificate_and_rejects_tls12(native_server):
    """Serve the configured trusted pair and refuse a TLS 1.2-only client.

    The custom context hook is deliberately incomplete or selects an unrelated
    pair. Production must load the configured pair regardless of that hook, while
    enforcing TLS 1.3 on the actual listener rather than just a configuration value.
    """
    assert native_server.get("/health").status_code == 200
    protocol = ssl.create_default_context(cafile=str(native_server.trust))
    protocol.maximum_version = ssl.TLSVersion.TLSv1_2
    with socket.create_connection(
        ("127.0.0.1", native_server.port), timeout=5
    ) as connection:
        with pytest.raises(ssl.SSLError):
            protocol.wrap_socket(connection, server_hostname="localhost")


@pytest.mark.parametrize("restart", ["reload_workers", "reexecute"])
def test_native_restart_preserves_https_redirects_and_host_validation(
    native_server, restart
):
    """Keep trusted HTTPS and safe redirects after a real worker/master replacement.

    HUP replaces workers; USR2 starts a new master and the old master is terminated.
    Both must preserve relative file paths and the configured certificate. A
    collection redirect must keep HTTPS, host/port and repeated/blank query values,
    despite forged forwarding headers. An unknown Host must receive 400 directly.
    """
    getattr(native_server, restart)()
    query = "/api/v1/groups?key=1&key=2&blank="
    response = native_server.get(
        query,
        headers={
            "Forwarded": "host=unknown.test;proto=http",
            "X-Forwarded-Proto": "http",
            "X-Forwarded-Host": "unknown.test",
        },
    )
    assert response.status_code == 308
    assert (
        response.headers["Location"]
        == native_server.url + "/api/v1/groups/?key=1&key=2&blank="
    )
    rejected = native_server.get("/api/v1/groups", headers={"Host": "unknown.test"})
    assert rejected.status_code == 400
    assert "Location" not in rejected.headers
