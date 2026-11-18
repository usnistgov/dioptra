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
"""Protect certificate policy and no-overwrite standalone operations."""

from __future__ import annotations

import json
import os
import stat
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa

# Keep collection possible on Windows; these tests exercise POSIX file protections.
if sys.platform != "win32":
    from dioptra.ssl import certificates as certs
    from dioptra.ssl import files, publication
    from dioptra.ssl.cli import main

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="Certificate file protections require POSIX"
)


@pytest.fixture
def ca():
    """Use one healthy issuer to keep negative tests focused on their own defect."""
    key, certificate, _ = certs.create_ca("Test CA", 2048, 1825, None)
    return key, certificate


@pytest.fixture
def pair(ca):
    """Issue a current server pair with both DNS and IP expectations."""
    issuer_key, issuer = ca
    names = certs.identities(("service.test",), ("127.0.0.1",))
    key, certificate, _ = certs.issue(issuer, issuer_key, names, 2048, 365, None)
    return key, certificate, names


def save_pair(
    root: Path, key: certs.PrivateKey, certificate: x509.Certificate, prefix: str
) -> tuple[Path, Path]:
    """Write reusable protected inputs, independently of the publisher under test."""
    key_path, cert_path = root / (prefix + ".key"), root / (prefix + ".crt")
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    key_path.chmod(0o600)
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    cert_path.chmod(0o644)
    return key_path, cert_path


@pytest.mark.parametrize(
    "defect",
    ["basic", "usage", "noncritical", "not-ca", "no-sign", "algorithm", "expired"],
)
def test_outbound_ca_policy_warns_but_service_ca_policy_rejects(ca, tmp_path, defect):
    """Keep outbound-only trust warnings separate from service CA authorization.

    Each certificate violates one service CA requirement. The same PEM must be
    inspectable for outbound trust with a warning and refused by strict CA validation.
    No network connection or workstation trust modification is involved.
    """
    key, issuer = ca
    now = certs.utc_now()
    public = ed25519.Ed25519PrivateKey.generate() if defect == "algorithm" else key
    builder = (
        x509.CertificateBuilder()
        .subject_name(issuer.subject)
        .issuer_name(issuer.subject)
        .public_key(public.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=2))
        .not_valid_after(now + timedelta(days=-1 if defect == "expired" else 365))
    )
    if defect != "basic":
        builder = builder.add_extension(
            x509.BasicConstraints(ca=defect != "not-ca", path_length=None),
            critical=defect != "noncritical",
        )
    if defect != "usage":
        builder = builder.add_extension(
            x509.KeyUsage(
                False,
                False,
                False,
                False,
                False,
                defect != "no-sign",
                True,
                False,
                False,
            ),
            critical=True,
        )
    path = tmp_path / "outbound.crt"
    path.write_bytes(
        builder.sign(key, hashes.SHA256()).public_bytes(serialization.Encoding.PEM)
    )
    path.chmod(0o644)
    runner = CliRunner()
    arguments = ["validate", "--cert", str(path), "--format", "json", "--kind"]
    outbound = runner.invoke(main, [*arguments, "outbound-ca"])
    assert outbound.exit_code == 0, outbound.output
    result = json.loads(outbound.output)
    assert result["warnings"]
    assert result["checks"] == ["outbound-ca-policy-inspection"]
    strict = runner.invoke(main, [*arguments, "ca"])
    assert strict.exit_code != 0
    assert "error" in json.loads(strict.output)


def test_outbound_ca_inspection_rejects_malformed_pem(tmp_path):
    """Refuse unreadable certificate data even when CA policy is warning-only."""
    path = tmp_path / "broken.crt"
    path.write_text("not a PEM certificate")
    path.chmod(0o644)
    result = CliRunner().invoke(
        main,
        ["validate", "--cert", str(path), "--kind", "outbound-ca", "--format", "json"],
    )
    assert result.exit_code != 0
    assert "malformed certificate PEM" in json.loads(result.output)["error"]


def test_generated_profile_and_identity():
    """Generate separate CA/server keys that satisfy the requested RSA/SHA-256 profile.

    A CA and server certificate are generated with DNS and IPv6 names. Validation
    must accept the resulting chain and matching server key, while the two private
    keys remain distinct. This protects usable server issuance, not PEM appearance.
    """
    key, issuer, _ = certs.create_ca("Deployment", 3072, 1825, None)
    names = certs.identities(("localhost",), ("::1",))
    server_key, server, _ = certs.issue(issuer, key, names, 3072, 365, None)
    result = certs.validate_server([server], [issuer], names, key=server_key)
    assert key.key_size == server_key.key_size == 3072
    assert key.private_numbers() != server_key.private_numbers()
    issuer_digest = issuer.signature_hash_algorithm
    server_digest = server.signature_hash_algorithm
    assert issuer_digest is not None and server_digest is not None
    assert issuer_digest.name == server_digest.name == "sha256"
    assert set(result["certificate"]["identities"]) == {"localhost", "::1"}
    assert "key-match" in result["checks"]


@pytest.mark.parametrize(
    "defect", ["identity", "key", "trust", "leaf-anchor", "deadline"]
)
def test_invalid_server_material(ca, pair, defect):
    """Reject each distinct certificate, trust, identity or expiration mismatch.

    Starting from a valid pair, each case changes one input: requested name, private
    key, root, use of the leaf as a root, or expiration cap. Validation must fail
    for that defect instead of accepting a seemingly valid but unusable server pair.
    """
    key, server, names = pair
    roots = [ca[1]]
    maximum = None
    if defect == "identity":
        names = certs.identities(("other.test",), ())
    elif defect == "key":
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    elif defect == "trust":
        roots = [certs.create_ca("Other", 2048, 10, None)[1]]
    elif defect == "leaf-anchor":
        roots = [server]
    else:
        maximum = certs.utc_now() + timedelta(days=1)
    with pytest.raises(
        ValueError, match="verification|mismatch|authorized CA|CA requires|limit"
    ):
        certs.validate_server([server], roots, names, key=key, maximum=maximum)


@pytest.mark.parametrize(
    "key",
    [
        rsa.generate_private_key(public_exponent=65537, key_size=1024).public_key(),
        ec.generate_private_key(ec.SECP224R1()).public_key(),
        ed25519.Ed25519PrivateKey.generate().public_key(),
    ],
)
def test_unsupported_public_keys(key):
    """Reject weak or unsupported certificate authentication keys.

    The inputs are RSA-1024, an unapproved ECDSA curve and Ed25519. Each must be
    rejected by the configured certificate policy. Hybrid key exchange is a separate
    requirement and does not make these certificate keys acceptable.
    """
    with pytest.raises(ValueError, match="unsupported public key"):
        certs.check_public_key(key)


@pytest.mark.parametrize("curve", [ec.SECP256R1, ec.SECP384R1, ec.SECP521R1])
def test_supported_ecdsa_issuer(ca, curve):
    """Allow an approved ECDSA CA to sign a generated RSA server key.

    Each supported ECDSA curve signs a new RSA server certificate. Trust-chain
    validation must succeed even though the signing key differs from the generated
    RSA profile. This preserves support for externally supplied issuers.
    """
    issuer_key = ec.generate_private_key(curve())
    template = ca[1]
    issuer = (
        x509.CertificateBuilder()
        .subject_name(template.subject)
        .issuer_name(template.subject)
        .public_key(issuer_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(template.not_valid_before_utc)
        .not_valid_after(template.not_valid_after_utc)
        .add_extension(x509.BasicConstraints(True, None), True)
        .add_extension(
            x509.KeyUsage(False, False, False, False, False, True, True, False, False),
            True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(issuer_key.public_key()), False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()),
            False,
        )
        .sign(issuer_key, hashes.SHA384())
    )
    names = certs.identities(("mixed.test",), ())
    key, server, _ = certs.issue(issuer, issuer_key, names, 2048, 30, None)
    result = certs.validate_server([server], [issuer], names, key=key)
    assert result["certificate"]["public_key_algorithm"] == "RSA"
    assert result["certificate"]["signature_hash"] == "sha256"


def test_expiry_shortening_and_no_remaining_validity(ca, monkeypatch):
    """Shorten a server lifetime at issuer expiry and refuse an unusable deadline.

    The verification clock is moved close to CA expiration without changing the
    host clock. A requested longer lifetime must stop at issuer expiry and warn;
    a deadline with no time remaining must fail instead of issuing an expired pair.
    """
    key, issuer = ca
    near_end = issuer.not_valid_after_utc - timedelta(hours=1)
    with monkeypatch.context() as patch:
        patch.setattr(certs, "utc_now", lambda: near_end)
        _, server, warnings = certs.issue(
            issuer, key, certs.identities(("short.test",), ()), 2048, 365, None
        )
        assert server.not_valid_after_utc == issuer.not_valid_after_utc
        assert any("shortened" in item for item in warnings)
        with pytest.raises(ValueError, match="no usable validity"):
            certs._expiry(365, near_end, issuer)


def test_cli_independent_paths_and_permissions(tmp_path):
    """Create and issue protected certificate files outside a deployment directory.

    The commands run with a permissive umask and explicit temporary output paths.
    Keys must still be private and certificates public. Reusing an output name must
    fail without publishing the other file or overwriting the existing pair.
    """
    root = tmp_path.resolve()
    runner = CliRunner()
    old_mask = os.umask(0)
    try:
        created = runner.invoke(
            main,
            [
                "create-ca",
                "--common-name",
                "Standalone",
                "--key-out",
                str(root / "ca.key"),
                "--cert-out",
                str(root / "ca.crt"),
                "--format",
                "json",
            ],
        )
        issued = runner.invoke(
            main,
            [
                "issue",
                "--ca-cert",
                str(root / "ca.crt"),
                "--ca-key",
                str(root / "ca.key"),
                "--dns",
                "localhost",
                "--key-out",
                str(root / "server.key"),
                "--cert-out",
                str(root / "server.crt"),
                "--format",
                "json",
            ],
        )
    finally:
        os.umask(old_mask)
    assert created.exit_code == issued.exit_code == 0, (created.output, issued.output)
    assert stat.S_IMODE((root / "server.key").stat().st_mode) == 0o600
    assert stat.S_IMODE((root / "server.crt").stat().st_mode) == 0o644
    retry = runner.invoke(
        main,
        [
            "create-ca",
            "--common-name",
            "Other",
            "--key-out",
            str(root / "ca.key"),
            "--cert-out",
            str(root / "unused.crt"),
            "--format",
            "json",
        ],
    )
    assert retry.exit_code != 0
    assert "already exists" in json.loads(retry.output)["error"]
    assert not (root / "unused.crt").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ["validate", "--unknown"],
        ["create-ca", "--rsa-bits", "1024"],
        ["issue", "--valid-days", "bad"],
        ["validate", "--kind", "other"],
    ],
)
def test_cli_parse_errors_are_structured(arguments):
    """Report invalid CLI arguments as one machine-readable JSON error.

    Click rejects an unknown option, weak key size, malformed lifetime or unknown
    kind before certificate work starts. With --format json, automation must still
    receive the same structured failure interface as an operation-time error.
    """
    result = CliRunner().invoke(main, [*arguments, "--format", "json"])
    assert result.exit_code != 0
    error = json.loads(result.output)
    assert error["schema_version"] == 1
    assert error["error"]


@pytest.mark.parametrize("defect", ["symlink", "hardlink", "fifo", "mode"])
def test_private_file_safety(tmp_path, ca, defect):
    """Reject linked, nonregular or public-readable private-key inputs without repair.

    Each case presents a symlink, hard link, FIFO or wrong-mode file. Reading the
    key must fail safely without following links, blocking on the FIFO, changing
    permissions or modifying the underlying private-key bytes.
    """
    root = tmp_path.resolve()
    key, _ = save_pair(root, ca[0], ca[1], "issuer")
    target = root / "input.key"
    if defect == "symlink":
        target.symlink_to(key)
    elif defect == "hardlink":
        os.link(key, target)
    elif defect == "fifo":
        os.mkfifo(target)
    else:
        target = key
        target.chmod(0o644)
    before = key.read_bytes()
    with pytest.raises((ValueError, OSError)):
        certs.load_key(target)
    assert key.read_bytes() == before


def test_interrupted_publication_retains_pair(tmp_path, ca, pair, monkeypatch):
    """Preserve the staged matching pair after the certificate-output write fails.

    A scoped replacement injects a disk error after private-key publication. The
    error must identify the retained pair and which output exists. A blind retry
    must refuse the existing key rather than combine it with a newly generated pair.
    """
    root = tmp_path.resolve()
    key, server, _ = pair
    original = files.write_new
    key_out, cert_out = root / "server.key", root / "server.crt"

    def interrupted(path, content, mode):
        """Inject failure after private-key publication to test retained-pair diagnostics."""
        if path == cert_out:
            raise OSError("injected disk failure")
        original(path, content, mode)

    with monkeypatch.context() as patch:
        patch.setattr(files, "write_new", interrupted)
        with pytest.raises(publication.PublicationError) as failure:
            publication.publish("issue", key, server, key_out, cert_out, issuer=ca[1])
    recovery = failure.value.recovery
    assert recovery["key_output"]["state"] == "identical"
    assert recovery["certificate_output"]["state"] == "absent"
    assert Path(recovery["saved_key"]).read_bytes() == key_out.read_bytes()
    assert stat.S_IMODE(Path(recovery["directory"]).stat().st_mode) == 0o700
    with pytest.raises(ValueError, match="already exists"):
        publication.publish("issue", key, server, key_out, cert_out, issuer=ca[1])


@pytest.mark.parametrize(
    "defect",
    [
        "schema-bool",
        "id",
        "issuer",
        "serial",
        "names",
        "dates",
        "algorithm",
        "signature",
    ],
)
def test_malformed_json_history_is_not_appended(tmp_path, ca, pair, defect):
    """Reject invalid signing-history fields without changing history or final outputs.

    A valid record is altered into invalid schema, identity, date or algorithm data
    while retaining parseable JSON. Logged publication must fail, preserve those
    bytes and avoid publishing either requested output; it must not repair history.
    """
    root = tmp_path.resolve()
    log = root / "issuance.jsonl"
    publication.append_log(log, ca[1], pair[1])
    record = json.loads(log.read_text())
    replacements = {
        "schema-bool": (record, "schema_version", True),
        "id": (record, "issuance_id", ""),
        "issuer": (record, "issuer_fingerprint_sha256", 4),
        "serial": (record["certificate"], "serial", "-1"),
        "names": (record["certificate"], "identities", [2]),
        "dates": (record["certificate"], "not_after", "bad"),
        "algorithm": (record["certificate"], "public_key_algorithm", "Ed25519"),
        "signature": (record["certificate"], "signature_hash", "sha1"),
    }
    selected, field, value = replacements[defect]
    selected[field] = value
    content = (json.dumps(record) + "\n").encode()
    log.write_bytes(content)
    with pytest.raises(
        publication.PublicationError, match="malformed issuance log"
    ) as failure:
        publication.publish(
            "issue",
            pair[0],
            pair[1],
            root / "new.key",
            root / "new.crt",
            issuer=ca[1],
            log=log,
        )
    assert log.read_bytes() == content
    assert failure.value.recovery["issuance_log"]["status"] == "unconfirmed"
    assert not (root / "new.key").exists()
    assert not (root / "new.crt").exists()


def certificate(
    key: certs.PrivateKey,
    subject: x509.Name,
    issuer: x509.Name,
    signer: certs.PrivateKey,
    end: datetime,
    *,
    ca: bool,
    digest: hashes.SHA256 | hashes.SHA384 | hashes.SHA512 | None = None,
    pss: padding.PSS | None = None,
) -> x509.Certificate:
    """Build independent supplied-certificate fixtures with explicit chain constraints."""
    from cryptography.x509.oid import ExtendedKeyUsageOID

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(certs.utc_now() - timedelta(minutes=1))
        .not_valid_after(end)
        .add_extension(x509.BasicConstraints(ca, None), True)
        .add_extension(
            x509.KeyUsage(not ca, False, False, False, False, ca, ca, False, False),
            True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(signer.public_key()),
            False,
        )
    )
    if not ca:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName("service.test")]), False
        ).add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
    return builder.sign(signer, digest or hashes.SHA256(), rsa_padding=pss)


@pytest.mark.parametrize("pss", [False, True])
def test_supplied_intermediate_and_ecdsa_leaf(ca, pss):
    """Verify a supplied ECDSA server through an RSA intermediate and explicit root.

    Both RSA PKCS#1 and RSA-PSS signatures are exercised on the supplied path.
    Validation must accept the proper leaf-first chain but reject selecting its
    intermediate as the root, preserving the distinction between chain and trust.
    """
    from cryptography.hazmat.primitives.asymmetric import padding

    root_key, root = ca
    intermediate_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "Intermediate")])
    parameters = (
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA384()), salt_length=padding.PSS.DIGEST_LENGTH
        )
        if pss
        else None
    )
    intermediate = certificate(
        intermediate_key,
        name,
        root.subject,
        root_key,
        root.not_valid_after_utc,
        ca=True,
        digest=hashes.SHA384(),
        pss=parameters,
    )
    key = ec.generate_private_key(ec.SECP384R1())
    server = certificate(
        key,
        name,
        intermediate.subject,
        intermediate_key,
        certs.utc_now() + timedelta(days=30),
        ca=False,
        digest=hashes.SHA512(),
        pss=padding.PSS(
            mgf=padding.MGF1(hashes.SHA512()), salt_length=padding.PSS.DIGEST_LENGTH
        )
        if pss
        else None,
    )
    result = certs.validate_server(
        [server, intermediate], [root], certs.identities(("service.test",), ()), key=key
    )
    assert result["certificate"]["public_key_algorithm"] == "ECDSA"
    with pytest.raises(ValueError, match="root CA"):
        certs.validate_server(
            [server], [intermediate], certs.identities(("service.test",), ())
        )


def test_external_ca_cutoff_is_warning_only(monkeypatch):
    """Apply the supplied endpoint deadline without imposing it on an external root.

    At a controlled 2033 time, a 2034 endpoint under a 2040 root must pass with a
    CA-expiration warning. A 2036 endpoint must fail the 2035 endpoint cap. The
    scenarios separate a required endpoint limit from warning-only CA policy.
    """
    now = datetime(2033, 1, 1, tzinfo=timezone.utc)
    limit = datetime(2035, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [x509.NameAttribute(x509.NameOID.COMMON_NAME, "Long-lived root")]
    )
    with monkeypatch.context() as patch:
        patch.setattr(certs, "utc_now", lambda: now)
        root = certificate(
            key,
            subject,
            subject,
            key,
            datetime(2040, 1, 1, tzinfo=timezone.utc),
            ca=True,
        )
        server = certificate(
            key,
            subject,
            subject,
            key,
            datetime(2034, 1, 1, tzinfo=timezone.utc),
            ca=False,
        )
        result = certs.validate_server(
            [server],
            [root],
            certs.identities(("service.test",), ()),
            maximum=limit,
            warn_ca=limit,
        )
        assert any("2040" in warning for warning in result["warnings"])
        late = certificate(
            key,
            subject,
            subject,
            key,
            datetime(2036, 1, 1, tzinfo=timezone.utc),
            ca=False,
        )
        with pytest.raises(ValueError, match="exceeds caller limit"):
            certs.validate_server(
                [late],
                [root],
                certs.identities(("service.test",), ()),
                maximum=limit,
                warn_ca=limit,
            )


def test_optional_key_dates_and_readonly_validation(tmp_path, ca, pair):
    """Validate using explicit trust and identity without optional key or date limits.

    A CLI server check omits those optional inputs and must report no key-match
    check, preserve file bytes/metadata and succeed. Omitting the required identity
    must fail, so optional settings do not make trust or hostname checks optional.
    """
    root = tmp_path.resolve()
    _, trust = save_pair(root, ca[0], ca[1], "ca")
    _, server = save_pair(root, pair[0], pair[1], "server")
    before = {
        path: (
            path.read_bytes(),
            path.stat().st_mode,
            path.stat().st_uid,
            path.stat().st_gid,
        )
        for path in (trust, server)
    }
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "validate",
            "--cert",
            str(server),
            "--trust",
            str(trust),
            "--dns",
            "service.test",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "key-match" not in json.loads(result.output)["checks"]
    for path, expected in before.items():
        assert (
            path.read_bytes(),
            path.stat().st_mode,
            path.stat().st_uid,
            path.stat().st_gid,
        ) == expected
    missing_identity = runner.invoke(
        main, ["validate", "--cert", str(server), "--trust", str(trust)]
    )
    assert missing_identity.exit_code != 0


def test_current_validity_boundaries(ca, pair, monkeypatch):
    """Reject a server certificate before its validity begins and after it expires.

    Only the verification/issuance clock is controlled. The CA remains valid so
    each failure must concern the endpoint rather than its issuer. These ordinary
    validity checks must apply even without a separate calendar-policy deadline.
    """
    key, server, names = pair
    with monkeypatch.context() as patch:
        patch.setattr(
            certs, "utc_now", lambda: server.not_valid_after_utc + timedelta(seconds=1)
        )
        with pytest.raises(ValueError, match="verification"):
            certs.validate_server([server], [ca[1]], names, key=key)
    future = certs.utc_now() + timedelta(days=1)
    with monkeypatch.context() as patch:
        patch.setattr(certs, "utc_now", lambda: future)
        _, not_yet, _ = certs.issue(ca[1], ca[0], names, 2048, 30, None)
    with pytest.raises(ValueError, match="verification"):
        certs.validate_server([not_yet], [ca[1]], names)


def test_concurrent_publication_never_mixes_pairs(tmp_path, ca):
    """Let only one competing writer publish to the same unused output paths.

    Two independently generated pairs compete for one key/certificate destination.
    Exactly one publication may succeed, and the resulting key must match the
    certificate under the selected root. This protects against mixed-pair output.
    """
    from concurrent.futures import ThreadPoolExecutor

    root = tmp_path.resolve()
    names = certs.identities(("concurrent.test",), ())
    pairs = [certs.issue(ca[1], ca[0], names, 2048, 30, None) for _ in range(2)]

    def publish_pair(pair):
        """Compete to publish one independent pair at the same protected output paths."""
        try:
            publication.publish(
                "issue",
                pair[0],
                pair[1],
                root / "server.key",
                root / "server.crt",
                issuer=ca[1],
            )
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as writers:
        results = list(writers.map(publish_pair, pairs))
    assert results.count(True) == 1
    certs.validate_server(
        certs.load_certificates(root / "server.crt"),
        [ca[1]],
        names,
        key=certs.load_key(root / "server.key"),
    )


def test_concurrent_history_writers_are_serialized(tmp_path, ca):
    """Keep complete distinct signing-history records when cooperating writers overlap.

    Concurrent writers append certificates to the same protected JSON-lines file.
    All certificate fingerprints and unique issuance IDs must remain present with
    private permissions; no append may interleave with or replace another record.
    """
    from concurrent.futures import ThreadPoolExecutor

    root = tmp_path.resolve()
    names = certs.identities(("history.test",), ())
    certificates = [
        certs.issue(ca[1], ca[0], names, 2048, 30, None)[1] for _ in range(3)
    ]

    def append(certificate):
        """Append one fixture certificate while competing with other cooperating writers."""
        publication.append_log(root / "issuance.jsonl", ca[1], certificate)

    with ThreadPoolExecutor(max_workers=3) as writers:
        list(writers.map(append, certificates))
    records = [
        json.loads(line) for line in (root / "issuance.jsonl").read_text().splitlines()
    ]
    assert len({record["issuance_id"] for record in records}) == 3
    assert {record["certificate"]["fingerprint_sha256"] for record in records} == {
        certificate.fingerprint(hashes.SHA256()).hex() for certificate in certificates
    }
    assert stat.S_IMODE((root / "issuance.jsonl").stat().st_mode) == 0o600


def test_long_dns_identity_uses_full_san(ca):
    """Preserve a valid DNS identity longer than the certificate subject-name limit.

    A long DNS name is issued and verified through its subject-alternative-name
    extension. It must remain untruncated even though the descriptive Common Name
    is bounded, preventing identity checks from accidentally depending on the subject.
    """
    identity = "a" * 63 + "." + "b" * 63 + ".example"
    names = certs.identities((identity,), ())
    key, server, _ = certs.issue(ca[1], ca[0], names, 2048, 30, None)
    result = certs.validate_server([server], [ca[1]], names, key=key)
    assert result["certificate"]["identities"] == [identity]
    assert (
        len(server.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value)
        <= 64
    )


@pytest.mark.parametrize("legacy_digest", ["sha1", "md5"])
def test_historical_root_self_signature_and_weak_intermediate(
    tmp_path, ca, legacy_digest
):
    """Trust a historical root's self-signature but reject a weak intermediate.

    OpenSSL creates deliberately old SHA-1/MD5 root self-signatures for isolated
    fixtures because cryptography refuses to create them. The chosen root may
    anchor a valid server path, but a new SHA-1 intermediate on the path must fail.
    No deployment or workstation trust is involved.
    """
    import subprocess

    root = tmp_path.resolve()
    ca_key, _ = save_pair(root, ca[0], ca[1], "issuer")
    root_cert = root / "historical-root.crt"
    command = [
        "openssl",
        "req",
        "-new",
        "-x509",
        "-key",
        str(ca_key),
        "-" + legacy_digest,
        "-days",
        "365",
        "-subj",
        "/CN=Historical test root",
        "-addext",
        "basicConstraints=critical,CA:TRUE",
        "-addext",
        "keyUsage=critical,keyCertSign,cRLSign",
        "-out",
        str(root_cert),
    ]
    subprocess.run(command, check=True, capture_output=True)
    issuer = certs.load_certificates(root_cert)[0]
    names = certs.identities(("service.test",), ())
    key, server, _ = certs.issue(issuer, ca[0], names, 2048, 7, None)
    certs.validate_server([server], [issuer], names, key=key)
    signature_digest = issuer.signature_hash_algorithm
    assert signature_digest is not None
    assert signature_digest.name == legacy_digest
    intermediate_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private, _ = save_pair(root, intermediate_key, ca[1], "intermediate")
    request = root / "intermediate.csr"
    subprocess.run(
        [
            "openssl",
            "req",
            "-new",
            "-key",
            str(private),
            "-subj",
            "/CN=Weak intermediate",
            "-out",
            str(request),
        ],
        check=True,
        capture_output=True,
    )
    extensions = root / "ca-extensions.cnf"
    extensions.write_text(
        "basicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,cRLSign\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid\n"
    )
    weak_path = root / "weak-intermediate.crt"
    subprocess.run(
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            str(request),
            "-CA",
            str(root_cert),
            "-CAkey",
            str(ca_key),
            "-set_serial",
            "42",
            "-days",
            "30",
            "-sha1",
            "-extfile",
            str(extensions),
            "-out",
            str(weak_path),
        ],
        check=True,
        capture_output=True,
    )
    intermediate = certs.load_certificates(weak_path)[0]
    _, issued, _ = certs.issue(intermediate, intermediate_key, names, 2048, 7, None)
    with pytest.raises(ValueError, match="verification|unsupported path signature"):
        certs.validate_server([issued, intermediate], [issuer], names)


def test_history_records_signing_time_before_publication_delay(tmp_path, ca, pair):
    """Retain the caller-captured signing time rather than substituting logging time.

    The history writer receives a fixed earlier signing instant. Its record must
    contain that instant and the issued certificate fingerprint, so delayed output
    or lock acquisition does not change when the signing operation is reported.
    """
    instant = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    log = tmp_path.resolve() / "issuance.jsonl"
    publication.append_log(log, ca[1], pair[1], signed_at=instant)
    record = json.loads(log.read_text())
    assert datetime.fromisoformat(record["signing_time"]) == instant
    assert (
        record["certificate"]["fingerprint_sha256"]
        == certs.metadata(pair[1])["fingerprint_sha256"]
    )
