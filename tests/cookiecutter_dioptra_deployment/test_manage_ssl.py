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
"""Exercise rendered manager policy, protected state and verified live readiness."""

from __future__ import annotations

import importlib
import json
import os
import ssl
import stat
import subprocess
import sys
import threading
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import pytoml
from click.testing import CliRunner
from cookiecutter.main import cookiecutter
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

# Keep collection possible on Windows; these tests exercise POSIX file protections.
if sys.platform != "win32":
    from dioptra.ssl import certificates as certs

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="Certificate file protections require POSIX"
)


TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "cookiecutter-templates/cookiecutter-dioptra-deployment"
)


@pytest.fixture
def deployment(tmp_path, monkeypatch):
    """Render a fresh deployment with isolated replay files and import its host scripts."""
    root = tmp_path.resolve()
    configuration = root / "cookiecutter.yml"
    configuration.write_text(json.dumps({"replay_dir": str(root / "replay")}))
    project = Path(
        cookiecutter(
            str(TEMPLATE),
            no_input=True,
            output_dir=str(root),
            config_file=str(configuration),
        )
    )
    monkeypatch.syspath_prepend(str(project / "scripts"))
    manager = importlib.import_module("manage_ssl")
    return project, manager


def selected() -> dict:
    """Return normalized default intent without requiring a Docker daemon."""
    endpoint = {
        "source": "generated",
        "dns_sans": ["localhost"],
        "ip_sans": [],
        "trust_files": [],
    }
    return {
        "schema_version": 1,
        "public": {"host": "localhost"},
        "transport": {"key_exchange": "default"},
        "restapi": deepcopy(endpoint),
        "nginx": deepcopy(endpoint),
    }


@pytest.mark.parametrize("umask", [0o000, 0o022, 0o077])
def test_generated_tls_environment_permissions_do_not_depend_on_umask(tmp_path, umask):
    """Render a usable TLS environment with mode 0640 under different user defaults."""
    configuration = tmp_path / "cookiecutter.yml"
    configuration.write_text(json.dumps({"replay_dir": str(tmp_path / "replay")}))
    previous = os.umask(umask)
    try:
        project = Path(
            cookiecutter(
                str(TEMPLATE),
                no_input=True,
                output_dir=str(tmp_path),
                config_file=str(configuration),
            )
        )
    finally:
        os.umask(previous)
    assert stat.S_IMODE((project / "envs/tls.env").stat().st_mode) == 0o640


@pytest.mark.parametrize("mode", [0o600, 0o644, 0o666])
def test_tls_environment_permission_repair_preserves_input(deployment, mode):
    """Repair existing TLS environment permissions while read-only checks refuse them.

    Preserve the input bytes, inode and ownership. Read-only inspection must report
    the incorrect mode without changing it; initialization may then correct it.
    """
    root, manager = deployment
    path = root / "envs/tls.env"
    path.chmod(mode)
    before, content = path.stat(), path.read_bytes()
    with pytest.raises(ValueError, match="expected 0640"):
        manager.directories(root, repair=False)
    assert stat.S_IMODE(path.stat().st_mode) == mode
    manager.directories(root, repair=True)
    after = path.stat()
    assert stat.S_IMODE(after.st_mode) == 0o640
    assert (after.st_uid, after.st_gid, after.st_ino) == (
        before.st_uid,
        before.st_gid,
        before.st_ino,
    )
    assert path.read_bytes() == content


@pytest.mark.parametrize(
    "trust_path", ["ssl/ca-certificates/legacy.crt", "ssl/ca-certificates/./legacy.crt"]
)
def test_distributed_root_becomes_strict_when_selected_for_service(
    deployment, capsys, trust_path
):
    """Apply the service CA policy when an outbound-only root is selected for nginx.

    Execute the real certificate CLI behind a host adapter for the container boundary.
    A certificate lacking CA extensions produces a visible outbound warning, then
    fails when the same path is configured as nginx's trust root.
    """
    from dioptra.ssl.cli import main

    root, manager = deployment
    key = ec.generate_private_key(ec.SECP256R1())
    now = certs.utc_now()
    name = x509.Name(
        [x509.NameAttribute(x509.NameOID.COMMON_NAME, "Legacy outbound CA")]
    )
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    relative = "ssl/ca-certificates/legacy.crt"
    path = root / relative
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    path.chmod(0o644)

    class HostCertificateTool:
        def exec(self, *arguments):
            """Run certificate CLI arguments with the helper's file paths mapped locally."""
            mapped = [
                arg.replace(manager.installation.MATERIAL, str(root) + "/")
                for arg in arguments[1:]
            ]
            result = CliRunner().invoke(main, mapped)
            if result.exit_code:
                raise ValueError(result.output)
            return result.output

    intent = selected()
    manager.installation._validate_roots(HostCertificateTool(), [relative], intent)
    assert "WARNING:" in capsys.readouterr().out
    intent["nginx"]["source"] = "supplied"
    intent["nginx"]["trust_files"] = [trust_path]
    with pytest.raises(ValueError, match="requires basic constraints"):
        manager.installation._validate_roots(HostCertificateTool(), [relative], intent)


def write_configuration(root: Path, *, host: str, supplied=()) -> None:
    """Write explicit endpoint settings for configuration behavior tests.

    Give each configuration test its own explicit inputs so the test can assess
    normalization without relying on Cookiecutter's current default values.

    Args:
        root: Rendered deployment root containing config/ssl.toml.
        host: Public DNS/IP identity selected by this test.
        supplied: Endpoint names that use the test's external.crt trust file.

    Returns:
        None.
    """
    settings = {
        "schema_version": 1,
        "public": {"host": host},
        "transport": {"key_exchange": "default"},
    }
    for endpoint in ("restapi", "nginx"):
        settings[endpoint] = {
            "source": "supplied" if endpoint in supplied else "generated",
            "dns_sans": [],
            "ip_sans": [],
            "trust_files": ["ssl/ca-certificates/external.crt"]
            if endpoint in supplied
            else [],
        }
    (root / "config/ssl.toml").write_text(pytoml.dumps(settings))


@pytest.mark.parametrize("host", ["service.example.org", "127.0.0.1", "::1"])
def test_custom_public_identity(deployment, host):
    """Put an explicitly configured public name in the correct DNS/IP certificate field.

    The test supplies a DNS name, IPv4 address or IPv6 address in its own TOML
    configuration. Loading it must include the required public identity in the
    appropriate nginx SAN list, independently of template defaults or bind addresses.
    """
    root, manager = deployment
    write_configuration(root, host=host)
    intent = manager.config.load(root, "internal-api.test")
    key = "ip_sans" if ":" in host or host == "127.0.0.1" else "dns_sans"
    assert host in intent["nginx"][key]


@pytest.mark.parametrize(
    "extra", ["\nhttps_port = 443\n", '\nbind_address = "127.0.0.1"\n']
)
def test_unknown_toml_fields_fail(deployment, extra):
    """Reject unsupported network settings in certificate configuration.

    An extra port or bind-address field is added to the TOML public table. Loading
    must fail rather than silently ignoring the value, because Compose owns those
    settings and an ignored option could mislead the operator.
    """
    root, manager = deployment
    path = root / "config/ssl.toml"
    path.write_text(path.read_text().replace("[transport]", extra + "[transport]"))
    with pytest.raises(ValueError, match="unsupported fields"):
        manager.config.load(root, "api")


@pytest.mark.parametrize(
    "selection",
    [
        "../outside.crt",
        "ssl/ca-certificates/../../outside.crt",
        "/outside.crt",
        "ssl/ca-certificates/linked.crt",
    ],
)
def test_public_root_containment(deployment, selection):
    """Reject CA-file paths that escape the public distribution directory.

    The selected path uses traversal, an absolute name or a symbolic link to an
    outside file. It must fail before the file can become a trusted/distributed root;
    checking only the lexical prefix would miss the link case.
    """
    root, manager = deployment
    outside = root / "outside.crt"
    outside.write_text("public certificate")
    (root / "ssl/ca-certificates/linked.crt").symlink_to(outside)
    with pytest.raises((ValueError, OSError)):
        manager.config.trust_path(root, selection)


def test_repairs_preserve_contents_owner_and_compliant_rerun(deployment, capsys):
    """Repair a known private file's mode without changing its bytes or owner.

    The fixture deliberately makes a caller-owned file writable by everyone. A
    repair must report the path and old/new modes, retain bytes/ownership and stop
    warning once a second inspection finds the file already compliant.
    """
    root, manager = deployment
    manager.directories(root, repair=True)
    path = root / "ssl/restapi/server.key"
    path.write_bytes(b"protected input")
    path.chmod(0o666)
    owner = path.stat().st_uid, path.stat().st_gid
    assert manager.files.read(path, 0o600, repair=True) == b"protected input"
    warning = capsys.readouterr().err
    assert str(path) in warning and "0666" in warning and "0600" in warning
    assert (path.stat().st_uid, path.stat().st_gid) == owner
    manager.files.read(path, 0o600, repair=True)
    assert capsys.readouterr().err == ""


def test_readonly_permission_check_never_repairs(deployment):
    """Reject an unsafe private-file mode during read-only validation.

    A key fixture is deliberately public-readable. Inspection must raise and leave
    its metadata unchanged, so validation cannot hide the defect by repairing it.
    """
    root, manager = deployment
    path = root / "ssl/nginx/server.key"
    path.write_bytes(b"private fixture")
    path.chmod(0o644)
    before = path.stat()
    with pytest.raises(ValueError, match="mode"):
        manager.files.read(path, 0o600)
    assert path.stat() == before


def test_missing_generated_record_is_not_adopted(deployment):
    """Refuse generated-looking files when no ownership record exists.

    A fresh state is presented with existing generated endpoint bytes. The manager
    must reject them rather than treating possession of a plausible pair as evidence
    that it owns the issuer and may replace or preserve that generation.
    """
    _, manager = deployment
    with pytest.raises(ValueError, match="missing generated ownership record"):
        manager.check_inputs(
            manager.fresh_state(),
            selected(),
            {"ssl/restapi/server.crt": "digest"},
            "init",
            ["restapi", "nginx"],
        )


def test_changed_supplied_inputs_need_explicit_target(deployment):
    """Accept changed supplied bytes only for the endpoint selected for replacement.

    The installed record contains an older API private-key digest. Ordinary init
    and an nginx-only replacement must reject the changed API input; explicit API
    replacement may accept it. This prevents accidental adoption of a new pair.
    """
    _, manager = deployment
    intent = selected()
    intent["restapi"]["source"] = "supplied"
    state = manager.fresh_state()
    state["installed"] = {
        "configuration": intent,
        "manifest": {"ssl/restapi/server.key": "old"},
    }
    with pytest.raises(ValueError, match="explicit replacement"):
        manager.check_inputs(
            state, intent, {"ssl/restapi/server.key": "new"}, "init", ["restapi"]
        )
    manager.check_inputs(
        state, intent, {"ssl/restapi/server.key": "new"}, "replace", ["restapi"]
    )
    with pytest.raises(ValueError, match="outside supplied replacement"):
        manager.check_inputs(
            state, intent, {"ssl/restapi/server.key": "new"}, "replace", ["nginx"]
        )


def test_command_separation(deployment):
    """Require an endpoint selection for pair replacement and keep CA replacement distinct.

    The parser must reject a targetless replace and a targeted replace-ca. This
    protects the public command interface from ambiguous choices that could replace
    an issuer when the operator intended only a server certificate.
    """
    _, manager = deployment
    with pytest.raises(SystemExit):
        manager.parser().parse_args(["replace"])
    with pytest.raises(SystemExit):
        manager.parser().parse_args(["replace-ca", "--target", "all"])
    assert manager.parser().parse_args(["replace-ca"]).command == "replace-ca"


def test_recovery_refuses_changed_intent_and_first_rollback(deployment, monkeypatch):
    """Reject changed recovery settings and rollback without a prior generation.

    A recorded first initialization has a known candidate but no rollback source.
    Rollback must fail; resume with a changed public host must also fail. Neither
    request permits generating a different candidate or changing services.
    """
    _, manager = deployment
    intent = selected()
    runtime = type("Runtime", (), {"config": {"name": "fixture", "services": {}}})()
    identifier = "a" * 32
    state = manager.fresh_state()
    state["active_operation"] = {
        "id": identifier,
        "configuration_digest": manager.config.digest(intent),
        "configuration": intent,
        "runtime_intent": runtime.config,
        "expected_prior_generation": None,
        "candidate": {"generation": identifier},
    }
    with pytest.raises(ValueError, match="rollback is unavailable"):
        manager.recover(Path("unused"), runtime, state, intent, identifier, "rollback")
    changed = deepcopy(intent)
    changed["public"]["host"] = "changed.test"
    with pytest.raises(ValueError, match="intent"):
        manager.recover(Path("unused"), runtime, state, changed, identifier, "resume")


@pytest.mark.parametrize("command", ["init", "recover-init", "replace"])
def test_installation_and_live_completion_boundaries(deployment, monkeypatch, command):
    """Complete initialization offline but require live verification for maintenance.

    Scoped replacements simulate installed files and an unavailable HTTPS endpoint.
    Init and init recovery must complete without service stop/start or a live check.
    Replacement must stop before installation and verify files before restart, then
    retain the interrupted operation when HTTPS cannot be verified.
    """
    root, manager = deployment
    manager.directories(root, repair=True)
    manager.public_names(root, repair=True)
    identifier = "a" * 32
    state = manager.fresh_state()
    operation = {
        "id": identifier,
        "type": "replace" if command == "replace" else "init",
        "phase": "prepared",
        "candidate_generation": identifier,
        "affected_services": ["api"],
        "initialization_volume": "fixture",
        "configuration": selected(),
        "input_digests": {},
        "expected_prior_generation": None,
        "runtime_intent": {"name": "fixture", "services": {}},
    }
    manager.files.ensure_directory(root / ".ssl-private/operations" / identifier)
    state["active_operation"] = operation
    candidate = {
        "generation": identifier,
        "manifest": {},
        "configuration": selected(),
        "transport_policy": {},
    }
    operation["candidate"] = candidate
    events = []
    runtime = type(
        "Runtime",
        (),
        {
            "compose": ["docker", "compose"],
            "config": operation["runtime_intent"],
            "stop": lambda self, services: events.append("stop"),
            "start": lambda self, services: events.append("start"),
        },
    )()

    def validate(*args):
        """Return the isolated certificate-validator result for the lifecycle fixture."""
        return {"restapi": {}, "nginx": {}}

    def install(*args, **kwargs):
        """Record installation without changing real runtime volumes in the lifecycle fixture."""
        events.append("install")

    def inspect(*args):
        """Accept the simulated installed manifest for this isolated lifecycle test."""
        events.append("inspect")

    def unavailable(*args):
        """Represent an unavailable HTTPS endpoint after installation has completed."""
        raise ValueError("injected endpoint unavailability")

    def trust_bundle(*args):
        """Provide the isolated public trust path for the lifecycle fixture."""
        return b"selected validation root"

    def offline(*args):
        """Record the normal-service refusal check without contacting Docker."""
        events.append("offline")

    def report(*args, **kwargs):
        """Require installation reporting to distinguish unperformed live checks."""
        assert kwargs["live_verified"] is False

    with monkeypatch.context() as patch:
        patch.setattr(manager, "require_offline", offline)
        patch.setattr(manager, "report", report)
        patch.setattr(manager, "validate_snapshot", validate)
        patch.setattr(manager.installation, "install", install)
        patch.setattr(manager.installation, "inspect", inspect)
        patch.setattr(manager, "wait_live", unavailable)
        patch.setattr(manager.installation, "trust_bundle", trust_bundle)
        patch.setattr(manager.transport, "publish", install)
        patch.setattr(manager.transport, "reconcile", lambda *args: None)
        patch.setattr(manager.transport, "preflight", lambda *args: None)
        patch.setattr(manager.transport, "inspect", lambda *args: None)
        if command == "replace":
            with pytest.raises(ValueError, match="unavailability"):
                manager.complete(root, runtime, state, operation, candidate, root)
        elif command == "recover-init":
            manager.recover(root, runtime, state, selected(), identifier, "resume")
        else:
            manager.complete(root, runtime, state, operation, candidate, root)
    saved = json.loads((root / ".ssl-private/deployment-state.json").read_text())
    if command == "replace":
        assert events.index("stop") < events.index("install")
        assert events.index("inspect") < events.index("start")
        assert saved["installed_generation"] is None
        assert saved["active_operation"]["phase"] == "installed"
    else:
        assert events.index("offline") < events.index("install")
        assert "stop" not in events and "start" not in events
        assert saved["installed_generation"] == identifier
        assert saved["active_operation"] is None
        assert operation["phase"] == "installed"
        assert "live_checks" not in saved["installed"]


def supplied_ec_pair(
    issuer_key: certs.PrivateKey, issuer: x509.Certificate
) -> tuple[ec.EllipticCurvePrivateKey, x509.Certificate]:
    """Construct a supplied ECDSA leaf independently of the RSA-only generator."""
    from datetime import timedelta

    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import ExtendedKeyUsageOID

    key = ec.generate_private_key(ec.SECP256R1())
    certificate = (
        x509.CertificateBuilder()
        .subject_name(issuer.subject)
        .issuer_name(issuer.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(certs.utc_now() - timedelta(minutes=1))
        .not_valid_after(certs.utc_now() + timedelta(days=30))
        .add_extension(x509.BasicConstraints(False, None), True)
        .add_extension(
            x509.KeyUsage(True, False, False, False, False, False, False, False, False),
            True,
        )
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()),
            False,
        )
        .sign(issuer_key, hashes.SHA256())
    )
    return key, certificate


@pytest.fixture(params=["generated", "supplied-ecdsa"])
def live_server(deployment, tmp_path, request):
    """Serve a real generated certificate over TLS 1.3 with a successful health response."""
    _, manager = deployment
    root = tmp_path.resolve()
    issuer_key, issuer, _ = certs.create_ca("Live fixture", 2048, 365, None)
    key, certificate, _ = certs.issue(
        issuer, issuer_key, certs.identities(("localhost",), ()), 2048, 30, None
    )
    if request.param == "supplied-ecdsa":
        key, certificate = supplied_ec_pair(issuer_key, issuer)
    for name, content in {
        "ca.crt": issuer.public_bytes(serialization.Encoding.PEM),
        "server.crt": certificate.public_bytes(serialization.Encoding.PEM),
        "server.key": key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
    }.items():
        (root / name).write_bytes(content)
        (root / name).chmod(0o600 if name.endswith(".key") else 0o644)

    class Handler(BaseHTTPRequestHandler):
        """Return a controlled successful application response after real TLS."""

        def do_GET(self):
            """Serve a health response without authentication or unrelated application state."""
            if self.headers.get("Host") != f"localhost:{server.server_port}":
                self.send_error(400)
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"healthy"}')

        def log_message(self, *args):
            """Keep routine fixture HTTP logs out of verification output."""
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(root / "server.crt", root / "server.key")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield (
            manager.ssl_probe,
            server.server_port,
            root / "ca.crt",
            certificate.fingerprint(hashes.SHA256()).hex(),
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_live_verified_application_check(live_server):
    """Accept a real TLS 1.3 endpoint only with the expected trusted certificate.

    A local server presents an RSA-generated or supplied-style ECDSA certificate.
    The probe must verify its CA, localhost identity, exact fingerprint and successful
    HTTP response. This qualifies the probe interface, not a full Dioptra deployment.
    """
    probe, port, trust, fingerprint = live_server
    result = probe.verify("127.0.0.1", port, "localhost", trust, fingerprint)
    assert result["tls_version"] == "TLSv1.3"
    assert result["http_status"] == 200
    assert result["fingerprint_sha256"] == fingerprint


@pytest.mark.parametrize("defect", ["identity", "fingerprint", "trust"])
def test_live_check_rejects_wrong_peer(live_server, defect, tmp_path):
    """Reject a live endpoint when trust, identity or certificate fingerprint differs.

    Each case changes one client expectation for the same real TLS server. A
    listening port and successful HTTP handler must not bypass CA/name verification
    or permit a different certificate from the selected generation.
    """
    probe, port, trust, fingerprint = live_server
    identity = "wrong.test" if defect == "identity" else "localhost"
    if defect == "fingerprint":
        fingerprint = "0" * 64
    if defect == "trust":
        _, issuer, _ = certs.create_ca("Other root", 2048, 365, None)
        trust = tmp_path / "other.crt"
        trust.write_bytes(issuer.public_bytes(serialization.Encoding.PEM))
    with pytest.raises((ValueError, ssl.SSLError)):
        probe.verify("127.0.0.1", port, identity, trust, fingerprint)


def test_trust_only_init_preserves_serving_inputs(deployment):
    """Allow a public-root update on init without allowing an implicit key replacement.

    The installed record is compared first with changed public-root bytes, then
    with changed server-key bytes. Only the trust update may use init; the key
    change needs explicit replacement so a rerun preserves serving identity.
    """
    _, manager = deployment
    intent = selected()
    state = manager.fresh_state()
    prior = {
        "ssl/restapi/server.key": "retained",
        "ssl/ca-certificates/corporate.crt": "old",
    }
    state["installed"] = {"manifest": prior, "configuration": intent}
    manager.check_inputs(
        state,
        intent,
        dict(prior, **{"ssl/ca-certificates/corporate.crt": "new"}),
        "init",
        ["restapi", "nginx"],
    )
    with pytest.raises(ValueError, match="explicit replacement"):
        manager.check_inputs(
            state,
            intent,
            dict(prior, **{"ssl/restapi/server.key": "new"}),
            "init",
            ["restapi", "nginx"],
        )


def test_docker_engine_arguments_follow_compose(deployment, monkeypatch):
    """Keep helper operations on the Docker engine explicitly selected for Compose.

    The subprocess interface records commands instead of contacting a remote engine.
    Both Compose resolution and helper exec must retain the chosen context/options.
    An ambiguous executable wrapper must fail rather than use another engine.
    """
    root, manager = deployment
    runtime_module = importlib.import_module("ssl_support.runtime")
    commands = []
    effective = {
        "name": "fixture",
        "services": {
            "fixture-restapi": {"image": "api", "networks": {"default": {}}},
            "fixture-nginx": {
                "image": "nginx",
                "ports": [
                    {"target": 30443, "published": "23443"},
                    {"target": 30080, "published": "23080"},
                ],
            },
        },
        "networks": {"default": {"name": "fixture_default"}},
    }

    def recording(arguments, **kwargs):
        """Record argument arrays while replacing external Docker execution in this test."""
        commands.append(arguments)
        return json.dumps(effective).encode()

    prefix = ["/custom/bin/docker", "--context", "isolated-fixture"]
    with monkeypatch.context() as patch:
        patch.setattr(runtime_module, "run", recording)
        runtime = runtime_module.Runtime(
            root, [*prefix, "compose", "-f", "overrides.yml"]
        )
        container = runtime_module.Container(root, "owned-helper", runtime.docker)
        container.exec("stat", "-c", "%F", "/private")
    assert commands[0][: len(prefix) + 1] == [*prefix, "compose"]
    assert commands[1][: len(prefix) + 2] == [*prefix, "exec", "owned-helper"]
    assert "--project-directory" in commands[0]
    assert "overrides.yml" in commands[0]
    with pytest.raises(ValueError, match="cannot resolve"):
        runtime_module.engine_command(["arbitrary-compose-wrapper", "--remote"])


def test_supplied_only_helper_never_imports_issuer_key(
    deployment, monkeypatch, tmp_path
):
    """Keep a retained CA signing key out of supplied-only validation helpers.

    A mixed deployment retains its local issuer on the host while replacing supplied
    nginx files. Recording transfers and validation arguments must show no signing
    key import or key-based CA check, while the protected host key remains unchanged.
    """
    from contextlib import contextmanager

    root, manager = deployment
    snapshot = tmp_path.resolve() / "snapshot"
    snapshot.mkdir(mode=0o700)
    names = [
        *manager.records.CA_FILES,
        "ssl/ca-certificates/dioptra-local-ca.crt",
        *[
            f"ssl/{endpoint}/server.{suffix}"
            for endpoint in ("restapi", "nginx")
            for suffix in ("crt", "key")
        ],
    ]
    for name in names:
        manager.records.parents(snapshot, name)
        manager.files.write(snapshot / name, b"transfer fixture")
    intent = selected()
    intent["nginx"]["source"] = "supplied"
    intent["nginx"]["trust_files"] = ["ssl/ca-certificates/dioptra-local-ca.crt"]
    transferred = []
    operations = []

    class Container:
        def private_directory(self, destination):
            """Record no filesystem side effects for the isolated transfer test."""

        def exists(self, destination):
            """Treat fixture destinations as initially absent so only selected imports are recorded."""
            return False

        def put(self, source, destination, mode):
            """Record selected container imports without copying private fixture material."""
            transferred.append(destination)

    class Runtime:
        image = "fixture"

        @contextmanager
        def helper(self, *args, **kwargs):
            """Yield an isolated recording helper without starting a real container."""
            yield Container()

    def validation(container, *arguments):
        """Record public-only CA validation arguments and return a valid root result."""
        operations.append(arguments)
        return {"checks": ["self-issued-root"], "warnings": []}

    operation = {
        "configuration": intent,
        "generation_targets": ["nginx"],
        "initialization_volume": "fixture",
    }
    with monkeypatch.context() as patch:
        patch.setattr(manager.installation, "tool", validation)
        manager.construct(
            Runtime(), operation, snapshot, names, set(), ["restapi"], False
        )
    assert not any(path.endswith("/ca.key") for path in transferred)
    ca_checks = [
        arguments
        for arguments in operations
        if "--kind" in arguments and "ca" in arguments
    ]
    assert ca_checks
    assert all("--key" not in arguments for arguments in ca_checks)
    assert (snapshot / manager.records.CA_FILES[1]).read_bytes() == b"transfer fixture"


def test_public_url_and_backup_guidance(deployment, capsys):
    """Report the effective public HTTPS URL without printing private-key digests.

    The record contains an IPv6 public identity, a nondefault published port and a
    private-key digest. Output must bracket the address and use that port, while
    keeping the private digest out of the public report.
    """
    _, manager = deployment
    intent = selected()
    intent["public"]["host"] = "::1"
    certificate = {
        "identities": ["::1"],
        "not_after": "2027-01-01T00:00:00Z",
        "fingerprint_sha256": "public-fingerprint",
    }
    installed = {
        "generation": "a" * 32,
        "configuration": intent,
        "results": {
            "restapi": {"certificate": certificate},
            "nginx": {"certificate": certificate},
        },
        "manifest": {"ssl/restapi/server.key": "private-digest-must-not-print"},
    }
    runtime = type("Runtime", (), {"public_port": lambda self: 54321})()
    manager.report(installed, runtime)
    output = capsys.readouterr().out
    assert "https://[::1]:54321" in output
    assert "private-digest-must-not-print" not in output


def test_invalid_prior_set_does_not_start_rollback(deployment, monkeypatch):
    """Reject an expired prior generation before recording or installing rollback.

    The cryptographic validator is replaced with an expired-certificate failure.
    Rollback must leave the currently installed generation and operation state
    unchanged rather than stopping services for an unusable recovery source.
    """
    root, manager = deployment
    state = manager.fresh_state()
    prior = {"generation": "a" * 32, "configuration": selected(), "volumes": []}
    candidate = {
        "generation": "b" * 32,
        "volumes": [],
        "install_prefixes": ["nginx"],
        "trust_changed": False,
    }
    operation = {"id": "b" * 32, "initialization_volume": "fixture"}

    def expired(*args):
        """Represent rejection of a no-longer-valid prior certificate set."""
        raise ValueError("prior endpoint is expired")

    with monkeypatch.context() as patch:
        patch.setattr(manager, "validate_snapshot", expired)
        with pytest.raises(ValueError, match="expired"):
            manager.restore_prior(root, object(), state, operation, candidate, prior)
    assert state["active_operation"] is None
    assert "recovery_action" not in operation


def test_unsupported_hybrid_stops_before_publication(deployment, monkeypatch):
    """Refuse unsupported hybrid exchange before any service interruption.

    A scoped replacement represents a runtime without the required group API.
    Completion must leave the prepared candidate and installed pointer unchanged,
    and must never call service stop. Capability failure is not permission to fall back.
    """
    root, manager = deployment
    manager.directories(root, repair=True)
    intent = selected()
    intent["transport"]["key_exchange"] = "hybrid-required"
    identifier = "a" * 32
    operation = {
        "id": identifier,
        "candidate_generation": identifier,
        "phase": "prepared",
        "initialization_volume": "fixture",
        "affected_services": ["api"],
        "configuration": intent,
    }
    state = manager.fresh_state()
    state["active_operation"] = operation
    candidate = {"generation": identifier, "configuration": intent, "manifest": {}}
    events = []
    runtime = type(
        "Runtime", (), {"stop": lambda self, services: events.append("stop")}
    )()

    def validated(*args):
        """Return the prepared snapshot result without external certificate validation."""
        return {}

    def unsupported(*args):
        """Represent a runtime that cannot enforce the requested hybrid group."""
        raise ValueError("hybrid-required needs SSLContext.set_groups")

    with monkeypatch.context() as patch:
        patch.setattr(manager, "validate_snapshot", validated)
        patch.setattr(manager, "check_transport", unsupported)
        with pytest.raises(ValueError, match="set_groups"):
            manager.complete(root, runtime, state, operation, candidate, root)
    assert events == []
    assert operation["phase"] == "prepared"
    assert state["installed_generation"] is None


def test_bundle_only_clients_are_affected(deployment):
    """Include public-bundle consumers when selecting services affected by a trust change.

    The effective runtime fixture includes system-store API, bundle-only RustFS
    and dbadmin, and unrelated Redis. Only consumers of changed trust should be
    selected, preventing a client from continuing with a stale public bundle.
    """
    _, manager = deployment
    runtime = type(
        "Runtime",
        (),
        {
            "services": {
                "api": {"volumes": [{"type": "volume", "source": "restapi-etc-ssl"}]},
                "rustfs": {"volumes": [{"type": "volume", "source": "rustfs-certs"}]},
                "dbadmin": {
                    "volumes": [{"type": "volume", "source": "dbadmin-ca-certificates"}]
                },
                "redis": {"volumes": []},
            }
        },
    )()
    assert manager.installation.trust_consumers(runtime) == {"api", "rustfs", "dbadmin"}


def test_hybrid_context_uses_supported_string_api(deployment, monkeypatch):
    """Select the required hybrid group using the runtime's group-list string interface.

    A minimal context records the argument passed to set_groups. It must receive
    X25519MLKEM768 as a string rather than a list or a fallback group. This protects
    the external SSLContext interface on capable Python builds.
    """
    _, manager = deployment
    groups = []

    class Context:
        def set_groups(self, value):
            """Record the exact API argument accepted by supporting Python builds."""
            assert isinstance(value, str)
            groups.append(value)

    with monkeypatch.context() as patch:
        patch.setattr(
            importlib.import_module("ssl_support.probe").ssl,
            "create_default_context",
            lambda **kwargs: Context(),
        )
        importlib.import_module("ssl_support.probe").context(
            Path("unused-public-roots.crt"), hybrid=True
        )
    assert groups == ["X25519MLKEM768"]


def test_completed_operation_has_no_recovery_interface(deployment):
    """Refuse recovery when there is no active interrupted operation.

    A deployment has an installed generation but no active operation. Reusing its
    ID in recover must fail, because recovery resumes an interruption and does not
    provide an implicit rollback command for a successfully completed operation.
    """
    _, manager = deployment
    state = manager.fresh_state()
    state["installed_generation"] = "a" * 32
    with pytest.raises(ValueError, match="recorded interrupted"):
        manager.recovery_operation(state, "a" * 32)


@pytest.mark.parametrize("supplied", [("restapi",), ("nginx",), ("restapi", "nginx")])
def test_rendered_supplied_and_mixed_configuration(deployment, supplied):
    """Normalize independently selected supplied/generated endpoint settings.

    The test writes explicit TOML rather than editing template defaults. Every
    supplied endpoint names an existing contained root. Configuration loading must
    preserve each source selection and include the API/public identities clients
    need to verify, including in mixed deployments.
    """
    root, manager = deployment
    public = root / "ssl/ca-certificates/external.crt"
    public.write_bytes(b"public validation fixture")
    public.chmod(0o644)
    write_configuration(root, host="public.example.org", supplied=supplied)
    intent = manager.config.load(root, "internal-api.test")
    assert {
        name
        for name in manager.config.ENDPOINTS
        if intent[name]["source"] == "supplied"
    } == set(supplied)
    assert "internal-api.test" in intent["restapi"]["dns_sans"]
    assert "public.example.org" in intent["nginx"]["dns_sans"]


def test_unsafe_runtime_marker_refused_before_read(deployment):
    """Reject an unsafe completion-record path before reading JSON from it.

    A recording container presents unsafe metadata for the generation marker.
    Inspection must refuse it before content access so a linked or nonregular file
    cannot be trusted merely because its bytes look like a completion record.
    """
    _, manager = deployment
    events = []

    class Container:
        def safe_destination(self, path):
            """Represent the no-follow container destination check rejecting a symlink."""
            events.append(path)
            raise ValueError("unsafe linked marker")

        def exists(self, path):
            """Fail if an existence probe bypasses the preceding type check."""
            pytest.fail("unsafe marker must be rejected before probing or reading")

    with pytest.raises(ValueError, match="unsafe linked marker"):
        manager.installation._begin_volume(Container(), None, {}, None, True)
    assert events == [manager.installation.MARKER]


class CompletionContainer:
    """Simulate container file operations while retaining the real check implementation."""

    name = "completion-fixture"

    def __init__(
        self,
        manager,
        data: dict[str, bytes],
        metadata: dict[str, list],
        events: list[tuple[str, str]],
    ) -> None:
        """Retain isolated public records, metadata and observable access events."""
        self.manager, self.data, self.metadata, self.events = (
            manager,
            data,
            metadata,
            events,
        )

    def safe_destination(self, path: str) -> None:
        """Represent the no-follow type/link check before any record access."""
        kind, links, _, _ = self.metadata[path]
        if kind != "regular file" or links != 1:
            raise ValueError("unsafe completion record")

    def check(self, path: str, expected: str, mode: int, owner: str) -> None:
        """Use the real runtime checker instead of duplicating digest/metadata policy."""
        importlib.import_module("ssl_support.runtime").Container.check(
            self, path, expected, mode, owner
        )

    def exec(self, *arguments: str) -> bytes:
        """Serve bounded stat/read operations and record any attempted mutation."""
        command, *args = arguments
        path = args[-1]
        if command == "cat":
            self.events.append(("read", path))
            return self.data[path]
        if command == "chmod":
            self.events.append(("mutate", path))
            self.metadata[path][2] = int(args[0], 8)
            return b""
        if command == "stat":
            kind, links, mode, owner = self.metadata[path]
            return (
                f"{mode:o}" if args[1] == "%a" else f"{kind}:{links}:{mode:o}:{owner}"
            ).encode()
        if command == "sha256sum":
            self.events.append(("hash", path))
            return (
                b"OK"
                if args[0] == "-c"
                else (self.manager.files.digest(self.data[path]) + "  " + path).encode()
            )
        raise AssertionError(arguments)


class CompletionRuntime:
    """Expose only the volume/helper interface needed by runtime inspection tests."""

    def __init__(self, container: CompletionContainer, bundle: bool) -> None:
        """Select bundle-only or system-store inventory without an actual Docker engine."""
        self.container = container
        self.volumes: dict[str, dict] = {"rustfs-certs": {}} if bundle else {}

    def volume(self, name: str) -> str:
        """Keep logical volume names stable in the isolated inspection fixture."""
        return name

    @contextmanager
    def helper(self, *args, **kwargs):
        """Yield a recording helper without mutating any actual Docker state."""
        yield self.container


def completion_fixture(manager, target: str, defect: str) -> tuple:
    """Model container records while using the production metadata/digest checker."""
    marker = {"schema_version": 1, "generation": "a" * 32, "files": {}}
    bundle = b"public bundle fixture"
    bundle_marker = {
        "schema_version": 1,
        "generation": "a" * 32,
        "sha256": manager.files.digest(bundle),
    }
    data = {
        manager.installation.MARKER: manager.files.json_bytes(marker),
        manager.installation.CHECKSUMS: manager.installation.completion_checks(marker),
        "/target/dioptra-complete.json": manager.files.json_bytes(bundle_marker),
        "/target/ca-certificates.crt": bundle,
    }
    metadata = {path: ["regular file", 1, 0o644, "0:0"] for path in data}
    if defect == "symlink":
        metadata[target][0] = "symbolic link"
    if defect == "hardlink":
        metadata[target][1] = 2
    if defect == "owner":
        metadata[target][3] = "39000:100"
    if defect == "mode":
        metadata[target][2] = 0o600
    if defect == "contents":
        data[target] += b"unexplained alteration"
    events: list[tuple[str, str]] = []
    entry = {"image": "fixture", "prefix": "nginx", "marker": marker}
    installed = {
        "volumes": [] if target.startswith("/target/") else [entry],
        "bundle_volumes": [
            {
                "image": "fixture",
                "volume": "rustfs-certs",
                "filename": "ca-certificates.crt",
                "marker": bundle_marker,
            }
        ]
        if target.startswith("/target/")
        else [],
    }
    return (
        CompletionRuntime(
            CompletionContainer(manager, data, metadata, events),
            target.startswith("/target/"),
        ),
        installed,
        events,
    )


@pytest.mark.parametrize(
    "target",
    [
        "/etc/ssl/dioptra-complete.json",
        "/etc/ssl/dioptra-complete.sha256",
        "/target/dioptra-complete.json",
    ],
)
@pytest.mark.parametrize("defect", ["symlink", "hardlink", "owner", "mode", "contents"])
def test_readonly_completion_records_rejected_before_read(deployment, target, defect):
    """Refuse unsafe or altered completion records without repairing them.

    Recording containers inject symlink, hard-link, owner, mode or content defects
    at each completion-record location. Unsafe metadata must block reads/hashes;
    changed contents must fail equality checks. Read-only validation must never mutate.
    """
    _, manager = deployment
    runtime, installed, events = completion_fixture(manager, target, defect)
    with pytest.raises(ValueError):
        manager.installation.inspect(runtime, installed, repair=False)
    if defect != "contents" or target != manager.installation.CHECKSUMS:
        assert ("read", target) not in events
    assert not any(event[0] == "mutate" for event in events)
    if defect != "contents":
        assert ("hash", target) not in events


@pytest.mark.parametrize(
    "target",
    [
        "/etc/ssl/dioptra-complete.json",
        "/etc/ssl/dioptra-complete.sha256",
        "/target/dioptra-complete.json",
    ],
)
def test_known_completion_permissions_repair_before_read(deployment, target):
    """Repair only the permissions of a known unchanged completion record.

    The fixture presents a regular root-owned record with the expected digest but
    a wrong mode. Mutating inspection may repair it before JSON parsing. Other
    metadata/content defects remain rejected by the separate refusal cases.
    """
    _, manager = deployment
    runtime, installed, events = completion_fixture(manager, target, "mode")
    manager.installation.inspect(runtime, installed, repair=True)
    assert ("mutate", target) in events
    if target.endswith(".json"):
        assert events.index(("mutate", target)) < events.index(("read", target))


@pytest.mark.parametrize(
    "defect",
    ["header", "duplicate", "unknown", "missing", "missing-newline", "cr-member"],
)
def test_checksum_order_and_exact_membership(deployment, defect):
    """Allow checksum-member reordering while rejecting a changed recorded set.

    The generation header remains first while known member lines are reordered;
    that harmless change must pass. Altered headers, duplicate/unknown/missing
    members or malformed line terminators must fail without repairing the record.
    """
    _, manager = deployment
    runtime, installed, events = completion_fixture(
        manager, manager.installation.CHECKSUMS, "none"
    )
    marker = installed["volumes"][0]["marker"]
    marker["files"] = {
        "/known-one.crt": {"sha256": "a" * 64},
        "/known-two.crt": {"sha256": "b" * 64},
    }
    lines = manager.installation.completion_checks(marker).splitlines()
    runtime.container.data[manager.installation.CHECKSUMS] = (
        b"\n".join(lines[:2] + list(reversed(lines[2:]))) + b"\n"
    )
    manager.installation.inspect_checksums(runtime.container, marker, repair=False)
    if defect == "header":
        lines[0], lines[1] = lines[1], lines[0]
    if defect == "duplicate":
        lines.append(lines[-1])
    if defect == "unknown":
        lines[-1] = b"c" * 64 + b"  /unexpected.crt"
    if defect == "missing":
        lines.pop()
    if defect == "cr-member":
        lines[-1] += b"\r"
    content = b"\n".join(lines) + b"\n"
    if defect == "missing-newline":
        content = content[:-1]
    runtime.container.data[manager.installation.CHECKSUMS] = content
    with pytest.raises(ValueError, match="protected generation"):
        manager.installation.inspect_checksums(runtime.container, marker, repair=False)
    assert not any(event[0] == "mutate" for event in events)


@pytest.fixture
def transport_runtime(deployment):
    """Provide effective Compose data without contacting an engine or changing services."""
    root, manager = deployment
    runtime = manager.Runtime.__new__(manager.Runtime)
    runtime.root = root
    runtime.api, runtime.nginx = (
        "dioptra-deployment-restapi",
        "dioptra-deployment-nginx",
    )
    runtime.config = {
        "name": "fixture",
        "services": {
            runtime.api: {"image": "api", "environment": {}},
            runtime.nginx: {
                "image": "nginx",
                "environment": {},
                "ports": [
                    {"target": 30443, "published": "24443"},
                    {"target": 30080, "published": "24080"},
                ],
            },
        },
    }
    runtime.services = runtime.config["services"]
    runtime.compose, runtime.docker = ["docker", "compose"], ["docker"]
    return runtime


@pytest.mark.parametrize(
    "bind, override, expected",
    [
        ("0.0.0.0", "", "127.0.0.1"),
        ("::", "", "::1"),
        ("192.0.2.10", "", "192.0.2.10"),
        ("0.0.0.0", "host.docker.internal", "host.docker.internal"),
        ("0.0.0.0", "2001:db8::10", "2001:db8::10"),
    ],
)
def test_nginx_probe_selects_connection_address(
    transport_runtime, bind, override, expected
):
    """Use a concrete published bind or an explicit reachable host for nginx probes.

    Wildcard binds select the matching loopback family by default. An explicit
    hostname or IP replaces that destination while the published HTTPS port stays
    unchanged.
    """
    transport_runtime.services[transport_runtime.nginx]["ports"][0]["host_ip"] = bind
    transport_runtime.config["x-dioptra"] = {"nginx-connect-host": override}
    assert transport_runtime.public_connect() == expected
    assert transport_runtime.public_port() == 24443


@pytest.mark.parametrize(
    "address", [None, 443, "https://example.org", "example.org:443", "0.0.0.0", "::"]
)
def test_nginx_probe_rejects_invalid_connection_override(transport_runtime, address):
    """Refuse malformed or wildcard destinations before attempting a connection."""
    transport_runtime.config["x-dioptra"] = {"nginx-connect-host": address}
    with pytest.raises(ValueError, match="nginx-connect-host"):
        transport_runtime.public_connect()


def test_connection_override_preserves_certificate_and_transport_policy(
    deployment, transport_runtime
):
    """Exclude only the local probe address from installation and recovery comparisons.

    Selecting a different route to the same nginx listener must leave the prepared
    certificate and serving policy unchanged. Other Compose extension settings must
    still participate in the comparison, and comparison must preserve the input.
    """
    root, manager = deployment
    intent = selected()
    before = manager.transport.prepare(root, transport_runtime, intent)
    transport_runtime.config["x-dioptra"] = {
        "nginx-connect-host": "host.docker.internal"
    }
    assert manager.transport.prepare(root, transport_runtime, intent) == before
    transport_runtime.config["x-dioptra"]["site"] = "example"
    preserved = deepcopy(transport_runtime.config)
    assert manager.transport.intent(preserved)["x-dioptra"] == {"site": "example"}
    assert transport_runtime.config == preserved
    assert manager.transport.prepare(root, transport_runtime, intent) != before


def test_nginx_override_preserves_live_tls_and_http_identity(
    deployment, transport_runtime, live_server, tmp_path, monkeypatch
):
    """Reach nginx through a different address while requiring its public identity.

    The real TLS server accepts localhost in both its certificate and HTTP Host.
    Compose advertises an unreachable bind address and the override selects loopback.
    Only the independent API helper is replaced; nginx verification uses a real socket,
    selected trust, expected certificate fingerprint and the effective published port.
    """
    root, manager = deployment
    _, port, trust, fingerprint = live_server
    transport_runtime.services[transport_runtime.nginx]["ports"][0].update(
        {"host_ip": "192.0.2.10", "published": str(port)}
    )
    transport_runtime.config["x-dioptra"] = {"nginx-connect-host": "127.0.0.1"}
    snapshot = tmp_path / "snapshot"
    public_root = snapshot / manager.records.CA_FILES[0]
    public_root.parent.mkdir(parents=True)
    public_root.write_bytes(trust.read_bytes())
    public_root.chmod(0o600)
    certificate = {"certificate": {"fingerprint_sha256": fingerprint}}
    candidate = {
        "configuration": selected(),
        "results": {"restapi": certificate, "nginx": certificate},
    }
    monkeypatch.setattr(
        manager, "_verify_api", lambda *args: {"identity": "internal-api"}
    )
    results = manager.verify_live(root, transport_runtime, snapshot, candidate)
    assert results[-1]["identity"] == "localhost"
    assert results[-1]["port"] == port
    assert results[-1]["fingerprint_sha256"] == fingerprint
    assert results[-1]["http_status"] == 200


def test_derived_policy_tracks_ports_without_changing_certificate_intent(
    deployment, transport_runtime
):
    """Update public routing policy when only the published HTTPS port changes.

    The test changes an effective Compose port mapping and derives policy again.
    Approved hosts and nginx redirects must use the new port, while init must not
    select replacement certificates or a new CA solely for a port-only change.
    """
    root, manager = deployment
    selected = manager.config.load(root, transport_runtime.api)
    first = manager.transport.prepare(root, transport_runtime, selected)
    transport_runtime.services[transport_runtime.nginx]["ports"][0]["published"] = (
        "34443"
    )
    second = manager.transport.prepare(root, transport_runtime, selected)
    assert first != second
    assert "localhost:34443" in second["environment"]["DIOPTRA_TLS_ALLOWED_AUTHORITIES"]
    assert "https://localhost:34443$request_uri" in second["nginx"]
    assert "proxy_ssl_name dioptra-deployment-restapi;" in second["nginx"]
    targets, generated, new_ca, omitted = manager.generation_inputs(
        {"installed": {"manifest": {}}},
        {"type": "init", "targets": ["restapi", "nginx"], "configuration": selected},
    )
    assert targets == [] and not new_ca and omitted == set()
    assert generated == ["restapi", "nginx"]


def test_candidate_override_refusal_does_not_publish_policy(
    deployment, transport_runtime, monkeypatch
):
    """Reject a conflicting Compose override before publishing candidate policy.

    The subprocess replacement returns a resolved API environment with an unapproved
    host despite the selected candidate. Preflight must fail and preserve the
    active env-file bytes, leaving services and installed policy untouched.
    """
    root, manager = deployment
    policy = manager.transport.prepare(root, transport_runtime, selected())
    active = root / manager.transport.ENVIRONMENT
    before = active.read_bytes()
    resolved = deepcopy(transport_runtime.config)
    for service in resolved["services"].values():
        service["environment"] = dict(policy["environment"])
    resolved["services"][transport_runtime.api]["environment"][
        "DIOPTRA_TLS_ALLOWED_AUTHORITIES"
    ] = '["unapproved.test"]'

    def compose(arguments, **kwargs):
        """Simulate a conflicting explicit environment value after native Compose resolution."""
        return json.dumps(
            transport_runtime.config if "--no-env-resolution" in arguments else resolved
        ).encode()

    monkeypatch.setattr(manager.transport, "run", compose)
    with pytest.raises(ValueError, match="overrides derived TLS policy"):
        manager.transport.preflight(root, transport_runtime, policy, root)
    assert active.read_bytes() == before


def test_recovery_selects_prior_mapping_only_for_rollback(
    deployment, transport_runtime, monkeypatch
):
    """Require the correct recorded Compose mapping for resume versus rollback.

    A candidate changes the published port. Rollback must refuse the candidate
    mapping until the operator restores the prior one; then it may dispatch rollback.
    Resume must reject that prior mapping because it belongs to a different candidate.
    """
    root, manager = deployment
    selected = manager.config.load(root, transport_runtime.api)
    prior_policy = manager.transport.prepare(root, transport_runtime, selected)
    transport_runtime.services[transport_runtime.nginx]["ports"][0]["published"] = (
        "34443"
    )
    candidate_policy = manager.transport.prepare(root, transport_runtime, selected)
    prior = {
        "generation": "b" * 32,
        "configuration": selected,
        "transport_policy": prior_policy,
    }
    identifier = "a" * 32
    state = {
        "installed": prior,
        "installed_generation": prior["generation"],
        "active_operation": {
            "id": identifier,
            "configuration": selected,
            "runtime_intent": candidate_policy["runtime_intent"],
            "expected_prior_generation": prior["generation"],
            "candidate": {"generation": identifier},
        },
    }
    restored = []

    def restore(*args):
        """Record only recovery dispatch; certificate rollback is qualified separately."""
        restored.append("rollback")

    monkeypatch.setattr(manager, "restore_prior", restore)
    with pytest.raises(ValueError, match="restore the prior Compose mapping"):
        manager.recover(
            root, transport_runtime, state, selected, identifier, "rollback"
        )
    assert restored == []
    transport_runtime.config = deepcopy(prior_policy["runtime_intent"])
    transport_runtime.config["x-dioptra"] = {
        "nginx-connect-host": "host.docker.internal"
    }
    manager.recover(root, transport_runtime, state, selected, identifier, "rollback")
    assert restored == ["rollback"]
    with pytest.raises(ValueError, match="candidate mapping"):
        manager.recover(root, transport_runtime, state, selected, identifier, "resume")


def test_policy_environment_serialization_survives_record_roundtrip(
    deployment, transport_runtime
):
    """Keep candidate environment bytes stable across protected JSON serialization.

    The same policy is serialized with sorted JSON keys and loaded again. Encoding
    its env file must produce identical bytes, so recovery does not mistake harmless
    dictionary ordering for an unrecorded policy change.
    """
    root, manager = deployment
    policy = manager.transport.prepare(root, transport_runtime, selected())
    loaded = json.loads(manager.files.json_bytes(policy))
    assert manager.transport.environment_bytes(
        policy
    ) == manager.transport.environment_bytes(loaded)


def test_initializer_refuses_legacy_plaintext_selection(deployment):
    """Reject an explicit request to disable production nginx TLS before creating state.

    The actual rendered script is invoked with the unsupported disabling option.
    Argument parsing must return nonzero without creating a deployment record. This
    checks the public script invocation directly; it extracts or replaces no functions.
    """
    root, _ = deployment
    result = subprocess.run(
        ["bash", str(root / "init-deployment.sh"), "--no-enable-nginx-ssl"],
        cwd=root,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert not (root / ".ssl-private/deployment-state.json").exists()


@pytest.mark.parametrize("status", [b"204", b"200", b"302", b"200extra"])
def test_curl_hybrid_preflight_requires_verification_and_success(deployment, status):
    """Require curl's explicit hybrid group, trust file and successful HTTP status.

    A recording container returns a selected HTTP-status result without networking.
    Only valid 2xx results may pass; redirects or malformed output fail. The command
    must select the required group and CA file without disabling verification.
    """
    _, manager = deployment
    recorded: list[str] = []

    class Container:
        def exec(self, *arguments):
            """Return only the injected HTTP result while retaining the actual CLI inputs."""
            recorded.extend(arguments)
            return status

    if status in (b"200", b"204"):
        manager.transport.curl_handshake(Container(), "::1", 18443)
    else:
        with pytest.raises(ValueError, match="cannot complete verified hybrid"):
            manager.transport.curl_handshake(Container(), "::1", 18443)
    assert recorded[recorded.index("--curves") + 1] == "X25519MLKEM768"
    assert recorded[recorded.index("--cacert") + 1] == "/curl-ca.crt"
    assert recorded[-1] == "https://[::1]:18443/"
    assert "--insecure" not in recorded


@pytest.mark.parametrize("interrupted_phase", [None, "installing", "installed"])
def test_prepared_rollback_needs_no_published_candidate_digests(
    deployment, monkeypatch, interrupted_phase
):
    """Restore the valid prior generation after a refusal before candidate publication.

    Validation/installation replacements isolate the recovery choice and can
    interrupt rollback during installation. Repeating rollback must still select
    the prior generation without requiring candidate digests that were never published.
    """
    root, manager = deployment
    manager.directories(root, repair=True)
    identifier = "a" * 32
    prior = {
        "generation": "b" * 32,
        "manifest": {},
        "volumes": [],
        "configuration": selected(),
    }
    candidate = {
        "generation": identifier,
        "manifest": {},
        "install_prefixes": [],
        "trust_changed": False,
    }
    operation = {
        "id": identifier,
        "candidate_generation": identifier,
        "phase": "prepared",
        "initialization_volume": "fixture",
    }
    state = manager.fresh_state()
    state.update(
        installed=prior,
        installed_generation=prior["generation"],
        active_operation=operation,
    )
    restored = []

    def validated(*args):
        """Represent successful validation of the recorded prior snapshot."""
        return {}

    def complete(root, runtime, state, operation, rollback, snapshot):
        """Observe the selected complete set without performing Docker installation."""
        restored.append(rollback)
        if interrupted_phase and len(restored) == 1:
            operation["phase"] = interrupted_phase
            manager.records.save(root, state)
            raise OSError("interrupted prepared-origin rollback")

    monkeypatch.setattr(manager, "validate_snapshot", validated)
    monkeypatch.setattr(manager, "complete", complete)
    if interrupted_phase:
        with pytest.raises(OSError, match="interrupted prepared-origin rollback"):
            manager.restore_prior(root, object(), state, operation, candidate, prior)
        state = json.loads((root / ".ssl-private/deployment-state.json").read_text())
        operation = state["active_operation"]
        assert operation["phase"] == interrupted_phase
    manager.restore_prior(root, object(), state, operation, candidate, prior)
    assert operation["rollback_prepublication"] is True
    assert all(item["generation"] == prior["generation"] for item in restored)
    assert all("recovery_source" not in item for item in restored)


@pytest.mark.parametrize(
    ("absent", "running", "stopped", "refused"),
    [
        (False, "api", "", True),
        (False, "", "api", False),
        (True, "", "api", True),
        (True, "init-helper", "", False),
    ],
)
def test_offline_guard_scopes_runtime_services(
    deployment, monkeypatch, absent, running, stopped, refused
):
    """Distinguish stopped certificate init from the full initializer's required teardown.

    The Docker interface supplies running/stopped service names for one effective
    project. Certificate init may accept stopped containers, but full initialization
    requires runtime containers absent. Unrelated setup helpers must not block it,
    and coordinate resolution must work before credentials exist.
    """
    root, manager = deployment
    runtime_module = importlib.import_module("ssl_support.runtime")
    calls = []

    def run(arguments, *, root, env=None):
        """Return effective coordinates and the requested container-state listing."""
        calls.append(arguments)
        if "config" in arguments:
            assert "--no-env-resolution" in arguments
            if absent:
                assert env["RUSTFS_SECRET_KEY"] == "initialization-preflight"
            return json.dumps(
                {"name": "selected-project", "services": {"api": {}}}
            ).encode()
        assert "label=com.docker.compose.project=selected-project" in arguments
        return (running + "\n" + (stopped if "--all" in arguments else "")).encode()

    monkeypatch.setattr(runtime_module, "run", run)
    if refused:
        with pytest.raises(ValueError, match="down without --volumes"):
            runtime_module.require_offline(root, ["docker", "compose"], absent=absent)
    else:
        runtime_module.require_offline(root, ["docker", "compose"], absent=absent)
    assert ("--all" in calls[-1]) is absent
    assert not (root / ".env").exists()


def test_init_refusal_precedes_host_mutation(deployment, monkeypatch):
    """Reject online certificate init before creating or repairing host state.

    The offline guard deliberately reports a running normal service. Command
    dispatch must stop there and preserve the complete host file/directory listing,
    including the absence of a newly created private state directory.
    """
    root, manager = deployment
    before = sorted(str(path.relative_to(root)) for path in root.rglob("*"))

    def running(*args):
        """Represent a normal deployment service that is still running."""
        raise ValueError("normal deployment services must be stopped")

    monkeypatch.setattr(manager, "require_offline", running)
    with pytest.raises(ValueError, match="must be stopped"):
        manager.execute(
            manager.parser().parse_args(["init", "--deployment-root", str(root)])
        )
    assert sorted(str(path.relative_to(root)) for path in root.rglob("*")) == before


@pytest.mark.parametrize("live", [False, True])
def test_preserved_init_and_readonly_validation_have_distinct_live_checks(
    deployment, monkeypatch, live, capsys
):
    """Preserve an unchanged installation offline but require fresh HTTPS for validate.

    The fixture represents a complete known set and an unavailable live endpoint.
    Unchanged init must succeed without contacting it and report no live check.
    Validate must fail honestly for unavailable HTTPS. Both paths leave state unchanged.
    """
    root, manager = deployment
    intent = selected()
    for name in manager.config.ENDPOINTS:
        intent[name]["source"] = "supplied"
    state = manager.fresh_state()
    state["installed"] = {
        "generation": "a" * 32,
        "configuration": intent,
        "manifest": {},
        "transport_policy": {},
    }
    state["installed_generation"] = "a" * 32
    before = deepcopy(state)
    runtime = type("Runtime", (), {"project": "fixture"})()

    def unavailable(*args):
        """Represent an offline application without changing any state."""
        raise ValueError("live HTTPS unavailable")

    monkeypatch.setattr(manager, "current_manifest", lambda *args, **kwargs: {})
    monkeypatch.setattr(manager.transport, "prepare", lambda *args: {})
    monkeypatch.setattr(manager.transport, "inspect", lambda *args: None)
    monkeypatch.setattr(manager.installation, "inspect", lambda *args, **kwargs: None)
    monkeypatch.setattr(manager, "validate_snapshot", lambda *args: {})
    monkeypatch.setattr(manager, "remove_validation_volume", lambda *args: None)
    monkeypatch.setattr(manager, "verify_live", unavailable)
    monkeypatch.setattr(manager, "report", lambda *args, **kwargs: None)
    if live:
        with pytest.raises(ValueError, match="live HTTPS unavailable"):
            manager.inspect_readonly(root, runtime, state, intent)
        assert "live-https: failed or unavailable" in capsys.readouterr().out
    else:
        manager.mutate(
            manager.parser().parse_args(["init"]), root, runtime, state, intent
        )
        assert "live-https: not performed" in capsys.readouterr().out
    assert state == before
