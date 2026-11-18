"""Verify production transport policy independently of application data services."""

import ssl
import sys

import pytest
from flask import Flask, request
from werkzeug.test import Client, EnvironBuilder
from werkzeug.wrappers import Response

from dioptra.restapi.authorities import ApprovedAuthorities, parse_authority
from dioptra.restapi.config import load_config
from dioptra.restapi.key_file import initialize_key

if sys.platform != "win32":
    from gunicorn.sock import ssl_context

    from dioptra.restapi.cli.production import DioptraApplication

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="Production Gunicorn requires POSIX"
)


@pytest.fixture
def production_configuration(tmp_path, monkeypatch, tls_certificates):
    """Provide resolved production settings and native certificate arguments.

    Returns the settings and argument list used to construct DioptraApplication,
    without starting a server or connecting to database/backend services.
    """
    cert, key, _ = tls_certificates
    signing = tmp_path / "signing/key"
    initialize_key(signing)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.delenv("GUNICORN_CMD_ARGS", raising=False)
    monkeypatch.delenv("FORWARDED_ALLOW_IPS", raising=False)
    monkeypatch.delenv("DIOPTRA_TLS_KEY_EXCHANGE", raising=False)
    settings = load_config(
        "prod",
        overrides={
            "SECRET_KEY_FILE": signing,
            "DIOPTRA_TLS_ALLOWED_AUTHORITIES": ["localhost:8443"],
            "MLFLOW_TRACKING_URI": tmp_path.as_uri(),
        },
    )
    return settings, ["--certfile", str(cert), "--keyfile", str(key)]


def test_native_context_hook_and_reload(production_configuration, tmp_path):
    """Apply TLS policy even when a custom Gunicorn hook bypasses its default factory.

    The hook returns an empty server context with a custom attribute. Construction
    and native reload must preserve that attribute while supplying configured files,
    TLS 1.3 and disabled forwarding trust. This exercises the actual native parser.
    """
    settings, arguments = production_configuration
    path = tmp_path / "gunicorn.py"
    path.write_text(
        "import ssl\ndef ssl_context(conf, factory):\n    c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)\n    c.operator_option = True\n    return c\n"
    )
    app = DioptraApplication(settings, ["-c", str(path), *arguments])
    for _ in range(2):
        context = ssl_context(app.cfg)
        assert context.operator_option
        assert context.minimum_version == ssl.TLSVersion.TLSv1_3
        assert app.cfg.secure_scheme_headers == {}
        assert app.cfg.forwarded_allow_ips == app.cfg.forwarder_headers == []
        app.reload()


@pytest.mark.parametrize(
    "configuration",
    [
        "certfile = None",
        "keyfile = None",
        "proxy_protocol = True",
        "forwarded_allow_ips = '*'",
        "forwarder_headers = '*'",
        "secure_scheme_headers = {'EVIL': 'https'}",
        "def ssl_context(conf, factory):\n    import ssl\n    return ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)",
        "def ssl_context(conf, factory):\n    c = factory()\n    c.check_hostname = True\n    return c",
        "def ssl_context(conf, factory):\n    import ssl\n    c = factory()\n    c.maximum_version = ssl.TLSVersion.TLSv1_2\n    return c",
    ],
)
def test_final_unsafe_configuration_fails(
    production_configuration, tmp_path, configuration
):
    """Refuse unsafe final certificate, context or forwarding configuration.

    Each real Gunicorn config-file input removes a required file or enables an
    unsafe context/proxy option. Production construction must fail before dispatch.
    Missing-file cases omit conflicting command options to respect native precedence.
    """
    settings, arguments = production_configuration
    path = tmp_path / "gunicorn.py"
    path.write_text(configuration + "\n")
    if configuration.startswith(("certfile", "keyfile")):
        arguments = []
    with pytest.raises(SystemExit):
        DioptraApplication(settings, ["-c", str(path), *arguments])


@pytest.mark.parametrize(
    "value",
    [
        "bad.test",
        "localhost:0",
        "localhost:8444",
        "user@localhost:8443",
        "localhost:8443/path",
        "[::1]junk",
        "localhost:08443",
        "localhost,evil",
        "localhost:",
    ],
)
def test_unknown_or_malformed_host_is_rejected_before_routing(value):
    """Reject an unapproved Host before routing can issue a collection redirect.

    A route would normally redirect to its trailing-slash spelling. The request
    uses an unknown name, invalid port or malformed authority. Every case must
    receive 400 without Location, preventing reflection of a forged server identity.
    """
    app = Flask(__name__)
    app.add_url_rule("/collection/", view_func=lambda: "ok")
    client = Client(
        ApprovedAuthorities(app, ["localhost:8443"]), Response, use_cookies=False
    )
    environ = EnvironBuilder(
        path="/collection", base_url="https://localhost:8443"
    ).get_environ()
    environ["HTTP_HOST"] = value
    response = Response.from_app(client.application, environ)
    assert response.status_code == 400
    assert "Location" not in response.headers


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_collection_redirect_preserves_native_authority_query_and_body(method):
    """Keep HTTPS collection redirects independent of forged forwarding headers.

    GET and POST requests include repeated/blank query values and encoded bytes.
    The 308 target must use the approved host/port and preserve the query; repeating
    a POST at that target must retain its body. The resource route remains usable.
    """
    app = Flask(__name__)
    app.add_url_rule(
        "/collection/",
        view_func=lambda: request.get_data() or request.query_string,
        methods=["GET", "POST"],
    )
    app.add_url_rule("/collection/1", endpoint="resource", view_func=lambda: "resource")
    client = Client(
        ApprovedAuthorities(app, ["public.test:8443", "api:5000"]), Response
    )
    query = "page=2&search=a%2Fb+%26&key=1&key=2&blank=&encoded=%252f"
    headers = {
        "Forwarded": "host=evil.test;proto=http",
        "X-Forwarded-Host": "evil.test",
        "X-Forwarded-Proto": "http",
        "X-Forwarded-Port": "80",
    }
    response = client.open(
        "/collection?" + query,
        method=method,
        data=b"payload" if method == "POST" else None,
        base_url="https://PUBLIC.test:8443",
        headers=headers,
    )
    assert response.status_code == 308
    assert response.location == "https://public.test:8443/collection/?" + query
    normalized = client.open(
        response.location,
        base_url="https://public.test:8443",
        method=method,
        data=b"payload" if method == "POST" else None,
    )
    assert normalized.status_code == 200
    assert normalized.data == (b"payload" if method == "POST" else query.encode())
    assert client.get("/collection/1", base_url="https://api:5000").data == b"resource"


@pytest.mark.parametrize(
    "left,right", [("PUBLIC.test", "public.TEST:443"), ("[::1]", "[::1]:443")]
)
def test_documented_authority_equivalence(left, right):
    """Treat DNS case and an omitted default HTTPS port as equivalent authorities.

    Normalization must make these spellings compare equally for DNS and IPv6.
    This permits ordinary Host spelling variations without approving another server.
    """
    assert parse_authority(left) == parse_authority(right)


@pytest.mark.parametrize("source", ["configuration", "environment", "command"])
def test_tls_uses_final_native_certificate_precedence(
    production_configuration, tmp_path, monkeypatch, source
):
    """Load the pair selected by Gunicorn's configuration/environment/CLI precedence.

    Earlier sources deliberately name missing files when a later source supplies
    the real pair. Construction must use the final paths and TLS policy instead of
    rejecting superseded paths or validating a certificate before precedence resolves.
    """
    settings, native = production_configuration
    cert, key = native[1], native[3]
    configuration = tmp_path / "server.conf.py"
    configured_cert = cert if source == "configuration" else "missing-config.crt"
    configured_key = key if source == "configuration" else "missing-config.key"
    configuration.write_text(
        f"certfile = {configured_cert!r}\nkeyfile = {configured_key!r}\nworkers = 2\n"
    )
    arguments = ["-c", str(configuration)]
    if source != "configuration":
        selected_cert = cert if source == "environment" else "missing-env.crt"
        selected_key = key if source == "environment" else "missing-env.key"
        monkeypatch.setenv(
            "GUNICORN_CMD_ARGS",
            f"--certfile '{selected_cert}' --keyfile '{selected_key}' --workers 3",
        )
    if source == "command":
        arguments.extend([*native, "--workers", "4"])
    app = DioptraApplication(settings, arguments)
    assert (app.cfg.certfile, app.cfg.keyfile) == (cert, key)
    assert (
        app.cfg.workers == {"configuration": 2, "environment": 3, "command": 4}[source]
    )
    assert ssl_context(app.cfg).minimum_version == ssl.TLSVersion.TLSv1_3
