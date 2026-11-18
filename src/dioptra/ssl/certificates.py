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
"""Construct and validate RSA/ECDSA certificates with explicit caller policy."""

import ipaddress
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from cryptography.x509.verification import PolicyBuilder, Store, VerificationError
from dateutil.parser import parse as parse_datetime

from .files import read

PrivateKey = rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time, rounded down to whole seconds.

    Returns:
        The time used by certificate validity checks and issuance. Keeping the clock
        in one function also allows tests to select a fixed verification time.
    """
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_date(value: str | None) -> datetime | None:
    """Parse an optional UTC certificate-policy deadline.

    Args:
        value: A timestamp in YYYY-MM-DDTHH:MM:SSZ format, or None for no deadline.

    Returns:
        A timezone-aware UTC datetime, or None when no value was supplied.

    Raises:
        ValueError: The value has another format or is not a valid calendar time.
    """
    if value is None:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is None:
        raise ValueError(f"{value!r}: expected UTC date YYYY-MM-DDTHH:MM:SSZ")
    return parse_datetime(value)


def identities(
    dns: tuple[str, ...], ips: tuple[str, ...]
) -> list[x509.DNSName | x509.IPAddress]:
    """Build the explicit DNS and IP names a server certificate must cover.

    Args:
        dns: Concrete DNS hostnames. International names are converted to ASCII IDNA;
            wildcard names and invalid DNS labels are rejected.
        ips: IPv4 or IPv6 address strings, without URL brackets or port numbers.

    Returns:
        Certificate subject-alternative-name objects in DNS-then-IP input order.

    Raises:
        ValueError: Both inputs are empty or a DNS/IP identity is invalid.
        UnicodeError: A DNS name cannot be converted to IDNA.
    """
    names: list[x509.DNSName | x509.IPAddress] = []
    for name in dns:
        normalized = name.encode("idna").decode("ascii")
        if len(normalized) > 253 or any(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", part) is None
            for part in normalized.split(".")
        ):
            raise ValueError(f"{name!r}: invalid concrete DNS identity")
        names.append(x509.DNSName(normalized))
    names.extend(x509.IPAddress(ipaddress.ip_address(value)) for value in ips)
    if not names:
        raise ValueError(
            "server validation and issuance require at least one --dns or --ip identity"
        )
    return names


def load_certificates(path: Path) -> list[x509.Certificate]:
    """Read PEM-encoded certificates from a protected input path.

    Args:
        path: PEM file containing one or more certificates, normally ordered with the
            server certificate first, followed by its issuing intermediates.

    Returns:
        Parsed certificates in file order, without establishing their trust.

    Raises:
        ValueError: The PEM data or the file safety checks are invalid.
        OSError: The file cannot be read.
    """
    try:
        return x509.load_pem_x509_certificates(read(path))
    except ValueError as exc:
        raise ValueError(f"{path}: malformed certificate PEM: {exc}") from exc


def load_key(path: Path) -> PrivateKey:
    """Read an unencrypted RSA or ECDSA private key from a protected file.

    Args:
        path: PEM private-key file owned by the effective user, with mode 0400 or 0600,
            one hard link and no symbolic links in the path.

    Returns:
        An RSA key of at least 2048 bits or an ECDSA key on P-256, P-384 or P-521.

    Raises:
        ValueError: The file is unsafe, encrypted, malformed or uses an unsupported key.
        OSError: The file cannot be read.
    """
    try:
        key = serialization.load_pem_private_key(
            read(path, private=True), password=None
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"{path}: unreadable or malformed unencrypted private key: {exc}"
        ) from exc
    if not isinstance(key, (rsa.RSAPrivateKey, ec.EllipticCurvePrivateKey)):
        raise ValueError(f"{path}: unsupported private key algorithm")
    check_public_key(key.public_key())
    return key


def check_public_key(key: Any) -> None:
    """Require a public key supported by the certificate policy.

    Args:
        key: Public key to check. RSA needs at least 2048 bits; ECDSA must use P-256,
            P-384 or P-521.

    Returns:
        None. The key is not modified.

    Raises:
        ValueError: The key's algorithm, size or curve is unsupported.
    """
    if isinstance(key, rsa.RSAPublicKey) and key.key_size >= 2048:
        return
    if isinstance(key, ec.EllipticCurvePublicKey) and key.curve.name in {
        "secp256r1",
        "secp384r1",
        "secp521r1",
    }:
        return
    raise ValueError(
        "unsupported public key: require RSA >=2048 or ECDSA P-256/P-384/P-521"
    )


def check_signature(cert: x509.Certificate) -> None:
    """Check a certificate's signature algorithm, without verifying the signature.

    Check the algorithm only. The certificate-path verifier is responsible for verifying
    the signature bytes against the issuing certificate.

    Args:
        cert: Server or intermediate certificate from a verified chain. Do not pass a
            trust anchor solely to check its self-signature.

    Returns:
        None.

    Raises:
        ValueError: The signature is not RSA PKCS#1 v1.5, RSA-PSS or ECDSA using
            SHA-256, SHA-384 or SHA-512.
    """
    digest = cert.signature_hash_algorithm
    parameters = cert.signature_algorithm_parameters
    if not isinstance(
        digest, (hashes.SHA256, hashes.SHA384, hashes.SHA512)
    ) or not isinstance(parameters, (padding.PKCS1v15, padding.PSS, ec.ECDSA)):
        raise ValueError(
            f"{cert.subject.rfc4514_string()}: unsupported path signature {cert.signature_algorithm_oid.dotted_string}"
        )


def check_current(cert: x509.Certificate, now: datetime) -> None:
    """Require a certificate to be valid at the selected time.

    Args:
        cert: Certificate whose validity interval is checked.
        now: Timezone-aware verification time. The lower validity bound is inclusive;
            the expiration bound is exclusive.

    Returns:
        None.

    Raises:
        ValueError: The time falls outside the certificate's validity interval.
    """
    if not cert.not_valid_before_utc <= now < cert.not_valid_after_utc:
        raise ValueError(
            f"{cert.subject.rfc4514_string()}: not currently valid; validity {cert.not_valid_before_utc.isoformat()} to {cert.not_valid_after_utc.isoformat()}, checked {now.isoformat()}"
        )


def check_match(cert: x509.Certificate, key: PrivateKey) -> None:
    """Require a certificate and private key to have the same public key.

    Matching public keys establishes that the pair belongs together; it does not check
    certificate trust, identities or expiration.

    Args:
        cert: Certificate to match.
        key: RSA or ECDSA private key expected to belong to the certificate.

    Returns:
        None.

    Raises:
        ValueError: The encoded public keys differ.
    """
    if cert.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    ) != key.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    ):
        raise ValueError(
            f"{cert.subject.rfc4514_string()}: certificate/private key mismatch"
        )


def validate_ca(
    cert: x509.Certificate,
    key: PrivateKey | None = None,
    *,
    now: datetime | None = None,
) -> None:
    """Check that a certificate can act as a certificate authority.

    Check whether the certificate is suitable for signing, without establishing trust in
    its issuer. A root CA is trusted by explicit selection, not by its self-signature.
    That self-signature is therefore exempt from the signature policy applied to server
    and intermediate certificates.

    Args:
        cert: CA certificate requiring a supported public key, current validity, a
            critical CA Basic Constraints extension and keyCertSign permission.
        key: Optional private key to match against the certificate.
        now: Verification time, or None to use the current UTC time.

    Returns:
        None.

    Raises:
        ValueError: Validity, CA constraints, key policy or optional key matching fails.
    """
    check_current(cert, now or utc_now())
    check_public_key(cert.public_key())
    try:
        constraints = cert.extensions.get_extension_for_class(x509.BasicConstraints)
        usage = cert.extensions.get_extension_for_class(x509.KeyUsage)
    except x509.ExtensionNotFound as exc:
        raise ValueError(
            f"{cert.subject.rfc4514_string()}: CA requires basic constraints and signing key usage"
        ) from exc
    if (
        not constraints.value.ca
        or not constraints.critical
        or not usage.value.key_cert_sign
    ):
        raise ValueError(
            f"{cert.subject.rfc4514_string()}: certificate is not an authorized CA"
        )
    if key is not None:
        check_match(cert, key)


def inspect_outbound_ca(
    cert: x509.Certificate, *, warn_after: datetime | None = None
) -> dict[str, Any]:
    """Report deployment CA policy differences for an outbound-only trust certificate.

    This inspection permits additional trust inputs for external HTTPS resources. It
    does not authorize a CA to issue or verify deployment service certificates and does
    not replace the outbound client's certificate verification. File safety and PEM
    parsing remain the caller's responsibility.

    Args:
        cert: Parsed certificate used only for outbound trust.
        warn_after: Optional aware CA expiration threshold, or None.

    Returns:
        Public certificate identity, completed inspection checks and policy warnings.
        Deployment CA policy differences are reported without raising ValueError.
    """
    warnings = []
    try:
        validate_ca(cert)
    except (ValueError, UnsupportedAlgorithm) as exc:
        warnings.append(f"Outbound-only CA does not meet deployment CA policy: {exc}")
    if cert.subject != cert.issuer:
        warnings.append("Outbound-only trust certificate is not a self-issued root CA")
    if warn_after is not None and cert.not_valid_after_utc > warn_after:
        warnings.append(
            f"CA expires {cert.not_valid_after_utc.isoformat()} after {warn_after.isoformat()}"
        )
    return {
        "certificate": {
            "fingerprint_sha256": cert.fingerprint(hashes.SHA256()).hex(),
            "subject": cert.subject.rfc4514_string(),
        },
        "checks": ["outbound-ca-policy-inspection"],
        "warnings": warnings,
    }


def metadata(cert: x509.Certificate) -> dict[str, Any]:
    """Describe a certificate using public values suitable for JSON output.

    Args:
        cert: Supported RSA/ECDSA certificate whose public metadata is required.

    Returns:
        A dictionary containing the SHA-256 fingerprint, decimal serial number,
        subject-alternative names, UTC validity timestamps, public-key algorithm,
        signature algorithm OID and signature hash name. No private-key data is used.
    """
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        names = [str(name.value) for name in san]
    except x509.ExtensionNotFound:
        names = []
    key = cert.public_key()
    algorithm = "RSA" if isinstance(key, rsa.RSAPublicKey) else "ECDSA"
    return {
        "fingerprint_sha256": cert.fingerprint(hashes.SHA256()).hex(),
        "serial": str(cert.serial_number),
        "identities": names,
        "not_before": cert.not_valid_before_utc.isoformat(),
        "not_after": cert.not_valid_after_utc.isoformat(),
        "public_key_algorithm": algorithm,
        "signature_algorithm": cert.signature_algorithm_oid.dotted_string,
        "signature_hash": cert.signature_hash_algorithm.name
        if cert.signature_hash_algorithm
        else "unsupported",
    }


def validate_server(
    chain: list[x509.Certificate],
    roots: list[x509.Certificate],
    names: list[x509.DNSName | x509.IPAddress],
    *,
    key: PrivateKey | None = None,
    maximum: datetime | None = None,
    warn_ca: datetime | None = None,
) -> dict[str, Any]:
    """Verify a server certificate's trust chain, identities and key policy.

    Verify at the current UTC time. Apply signature policy only to certificates on the
    verified paths, excluding a trusted root's self-signature. This validates the
    supplied files; revocation checks and a live TLS connection are outside this
    function's scope.

    Args:
        chain: Server certificate first, followed by available intermediate CAs.
        roots: Explicitly trusted root CAs. Intermediates are not accepted as roots.
        names: Nonempty DNS/IP identities; the server must be valid for every name.
        key: Optional private key to match against the server certificate.
        maximum: Optional latest permitted server expiration, as an aware datetime.
        warn_ca: Optional CA expiration threshold. Certificates in a verified issuer
            path that expire later add warnings without failing for that reason.

    Returns:
        A JSON-compatible dictionary with server metadata, its issuer's SHA-256
        fingerprint, names of the checks performed and sorted warning messages.

    Raises:
        ValueError: Inputs are missing, a chain/identity/key check fails, an algorithm
            is unsupported, or the server expiration exceeds maximum.
    """
    if not names or not roots or not chain:
        raise ValueError(
            "server validation requires a leaf, explicit trust roots and identities"
        )
    if key is not None:
        check_match(chain[0], key)
    now = utc_now()
    for root in roots:
        validate_ca(root, now=now)
        if root.subject != root.issuer:
            raise ValueError(
                "explicit trust inputs must be root CA certificates, not intermediates"
            )
    builder = PolicyBuilder().store(Store(roots)).time(now)
    paths = []
    for name in names:
        try:
            paths.append(
                builder.build_server_verifier(name).verify(chain[0], chain[1:])
            )
        except VerificationError as exc:
            raise ValueError(
                f"chain/identity verification failed for {name.value}: {exc}"
            ) from exc
    if any(len(path) < 2 for path in paths):
        raise ValueError(
            "server certificate cannot be its own trust anchor; provide its root CA"
        )
    warnings = _check_paths(paths, now, warn_ca)
    if maximum is not None and chain[0].not_valid_after_utc > maximum:
        raise ValueError(
            f"endpoint expiration {chain[0].not_valid_after_utc.isoformat()} exceeds caller limit {maximum.isoformat()}"
        )
    return {
        "certificate": metadata(chain[0]),
        "issuer_fingerprint_sha256": paths[0][1].fingerprint(hashes.SHA256()).hex(),
        "checks": [
            "current-validity",
            "server-chain",
            "identities",
            "supported-algorithms",
        ]
        + (["key-match"] if key is not None else []),
        "warnings": sorted(warnings),
    }


def _check_paths(
    paths: list[list[x509.Certificate]], now: datetime, warn_ca: datetime | None
) -> set[str]:
    """Apply key/signature policy to verified certificate paths.

    A trusted root's self-signature does not establish its trust. Exclude that
    self-signature when applying the server and intermediate signature policy, while
    still checking the root's key and validity.

    Args:
        paths: Verified paths in leaf-to-root order, one per required server identity.
        now: Aware verification time used for every path certificate.
        warn_ca: Optional aware CA-expiration threshold.

    Returns:
        Deduplicated warning strings for CAs beyond the threshold.

    Raises:
        ValueError: A path certificate is expired or has unsupported key/signature
            policy.
    """
    warnings = set()
    for path in paths:
        for index, cert in enumerate(path):
            check_current(cert, now)
            check_public_key(cert.public_key())
            if index < len(path) - 1:
                check_signature(cert)
            if index and warn_ca is not None and cert.not_valid_after_utc > warn_ca:
                warnings.add(
                    f"CA {cert.subject.rfc4514_string()} expires {cert.not_valid_after_utc.isoformat()} after warning threshold {warn_ca.isoformat()}"
                )
    return warnings


def _expiry(
    days: int, limit: datetime | None, issuer: x509.Certificate | None
) -> tuple[datetime, list[str]]:
    """Bound requested certificate expiry by an issuer and optional caller deadline.

    Args:
        days: Requested positive lifetime in days from utc_now().
        limit: Optional aware absolute expiration cap.
        issuer: Optional issuing certificate whose validity must not be exceeded.

    Returns:
        Tuple of the selected aware expiration and shortening-warning messages.

    Raises:
        ValueError: The resulting expiration is not after the current time.
    """
    now = utc_now()
    requested = now + timedelta(days=days)
    bounds = [requested]
    if limit is not None:
        bounds.append(limit)
    if issuer is not None:
        bounds.append(issuer.not_valid_after_utc)
    end = min(bounds)
    if end <= now:
        raise ValueError(
            "no usable validity remains; replace the expired issuer or correct the caller deadline; the issuer will not be extended"
        )
    warnings = (
        []
        if end == requested
        else [
            f"shortened requested {days}-day lifetime; actual expiration {end.isoformat()}"
        ]
    )
    return end, warnings


def _builder(
    key: PrivateKey,
    subject: x509.Name,
    issuer: x509.Name,
    end: datetime,
    authority_key: Any,
) -> x509.CertificateBuilder:
    """Create the common certificate fields before adding CA/server extensions.

    Args:
        key: New private key whose public key belongs in the certificate.
        subject: Certificate subject name.
        issuer: Signing CA name, or subject for a self-signed root.
        end: Selected aware expiration.
        authority_key: Issuer public key used to derive Authority Key Identifier.

    Returns:
        CertificateBuilder with serial, validity, public key and key identifiers.
        The caller adds role-specific extensions and signs it.
    """
    now = utc_now()
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(end)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(authority_key),
            critical=False,
        )
    )


def create_ca(
    common_name: str, bits: int, days: int, limit: datetime | None
) -> tuple[PrivateKey, x509.Certificate, list[str]]:
    """Create a self-signed RSA certificate authority in memory.

    Return the generated objects without writing files. Use publication.publish to save
    the certificate and private key with the required file protections.

    Args:
        common_name: Nonblank descriptive CA name placed in its subject.
        bits: RSA key size, at least 2048 bits.
        days: Requested lifetime in days, measured from the current UTC time.
        limit: Optional aware expiration deadline that can shorten the lifetime.

    Returns:
        A tuple containing the new private key, CA certificate and lifetime warning
        messages. The certificate uses SHA-256 and permits certificate signing.

    Raises:
        ValueError: The name, key size or resulting validity interval is invalid.
    """
    if not common_name.strip():
        raise ValueError("CA common name must not be empty")
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    end, warnings = _expiry(days, limit, None)
    key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    cert = (
        _builder(key, subject, subject, end, key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(False, False, False, False, False, True, True, False, False),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    validate_ca(cert, key)
    # Generated roots use the known SHA-256 profile, so their construction can
    # additionally verify the self-signature without constraining external roots.
    cert.verify_directly_issued_by(cert)
    return key, cert, warnings


def issue(
    ca: x509.Certificate,
    ca_key: PrivateKey,
    names: list[x509.DNSName | x509.IPAddress],
    bits: int,
    days: int,
    limit: datetime | None,
) -> tuple[PrivateKey, x509.Certificate, list[str]]:
    """Sign a new RSA server certificate using an existing certificate authority.

    Create the new pair in memory. The caller must separately validate the resulting
    chain against its chosen trust roots and publish the files; issuing a certificate
    does not perform either step.

    Args:
        ca: Current CA certificate authorized for certificate signing.
        ca_key: Matching RSA or ECDSA CA private key.
        names: Server DNS/IP subject-alternative names, normally from identities().
        bits: New server RSA key size, at least 2048 bits.
        days: Requested server lifetime in days from the current UTC time.
        limit: Optional aware expiration deadline. The issuer's expiration also limits
            the lifetime; this function never extends the issuer.

    Returns:
        A tuple of the new server private key, server certificate and any warnings about
        a shortened lifetime. The certificate permits TLS server authentication.

    Raises:
        ValueError: Issuer/key checks, key generation or the validity interval fails.
    """
    validate_ca(ca, ca_key)
    end, warnings = _expiry(days, limit, ca)
    key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Server certificate")])
    cert = (
        _builder(key, subject, ca.subject, end, ca.public_key())
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(True, False, False, False, False, False, False, False, False),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .add_extension(x509.SubjectAlternativeName(names), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    return key, cert, warnings
