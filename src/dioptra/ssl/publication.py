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
"""Publish independent PEM files and optional signing history without overwriting."""

import json
import os
import re
import secrets
import stat
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import serialization

from . import files
from .certificates import PrivateKey, metadata, utc_now


class PublicationError(ValueError):
    """Report a publication failure together with retained recovery information.

    Args:
        reason: Explanation of the failed write or validation.
        recovery: JSON-compatible description of staging paths, output states and
            whether the signing-history append was confirmed.

    Attributes:
        recovery: The supplied recovery dictionary, available without parsing the
            exception message. Files named there remain for operator inspection.
    """

    def __init__(self, reason: str, recovery: dict[str, Any]):
        """Store the failure and include its recovery details in the error message.

        Args:
            reason: Description of the operation that failed.
            recovery: Retained paths and output/log status for manual recovery.
        """
        self.recovery = recovery
        super().__init__(
            f"{reason}; retained files and output states: {json.dumps(recovery, sort_keys=True)}"
        )


def check_outputs(key_out: Path, cert_out: Path) -> None:
    """Require distinct, unused certificate and private-key output paths.

    Inspect the requested paths without creating files. The later writes must still use
    exclusive creation, because another process can claim a name after this check.

    Args:
        key_out: Intended private-key path in an existing caller-owned directory.
        cert_out: Intended certificate path in an existing caller-owned directory.

    Returns:
        None.

    Raises:
        ValueError: Paths coincide, either name exists, or a parent directory permits
            other users to write to it or is not owned by the caller.
        OSError: A parent cannot be opened safely without following symbolic links.
    """
    if key_out == cert_out:
        raise ValueError("key and certificate destinations must differ")
    for path in (key_out, cert_out):
        with files.directory(path.parent) as parent:
            files.owned(os.fstat(parent), path.parent)
            try:
                os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise ValueError(
                f"{path}: output already exists; select unused output paths"
            )


def _timestamp(value: object) -> datetime:
    """Parse signing-history timestamps without accepting an unknown time zone.

    Args:
        value: Expected ISO timestamp string with a zero UTC offset.

    Returns:
        Aware UTC datetime.

    Raises:
        ValueError: The value is not a timestamp string or does not use UTC.
    """
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("timestamp must be UTC")
    return parsed


def _hex(value: object, length: int) -> bool:
    """Recognize an exact-length lowercase hexadecimal record identifier.

    Args:
        value: Untrusted JSON field value.
        length: Required hexadecimal character count.

    Returns:
        True only for a string with the required lowercase hexadecimal spelling.
    """
    return (
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", value) is not None
    )


def _certificate_record_valid(cert: object) -> bool:
    """Check the public certificate metadata stored in an issuance record.

    Args:
        cert: Untrusted JSON value expected to match metadata() fields.

    Returns:
        True for valid field names, SHA-256 fingerprint, positive serial, names,
        increasing validity bounds and supported algorithm descriptors; False for
        ordinary field mismatches.

    Raises:
        ValueError: A timestamp is malformed. The outer record validator catches it.
    """
    required = {
        "fingerprint_sha256",
        "serial",
        "identities",
        "not_before",
        "not_after",
        "public_key_algorithm",
        "signature_algorithm",
        "signature_hash",
    }
    if not isinstance(cert, dict) or set(cert) != required:
        return False
    serial = cert["serial"]
    names = cert["identities"]
    return (
        _hex(cert["fingerprint_sha256"], 64)
        and isinstance(serial, str)
        and serial.isdecimal()
        and 0 < int(serial) < 2**160
        and isinstance(names, list)
        and bool(names)
        and all(isinstance(n, str) and bool(n.strip()) for n in names)
        and _timestamp(cert["not_before"]) < _timestamp(cert["not_after"])
        and cert["public_key_algorithm"] in {"RSA", "ECDSA"}
        and isinstance(cert["signature_algorithm"], str)
        and re.fullmatch(r"[0-2](?:\.[0-9]+)+", cert["signature_algorithm"]) is not None
        and cert["signature_hash"] in {"sha256", "sha384", "sha512"}
    )


def _record_valid(record: object) -> bool:
    """Validate a full schema-1 issuance-history record before accepting an append.

    Args:
        record: Untrusted JSON value from one history line.

    Returns:
        True only for a complete supported record with valid IDs, issuer fingerprint,
        UTC signing time and certificate metadata. Invalid values return False.
        Existing history is never modified by this check.
    """
    required = {
        "schema_version",
        "issuance_id",
        "signing_time",
        "issuer_fingerprint_sha256",
        "certificate",
    }
    if not isinstance(record, dict) or set(record) != required:
        return False
    try:
        return (
            type(record["schema_version"]) is int
            and record["schema_version"] == 1
            and _hex(record["issuance_id"], 32)
            and bool(_timestamp(record["signing_time"]))
            and _hex(record["issuer_fingerprint_sha256"], 64)
            and _certificate_record_valid(record["certificate"])
        )
    except (ValueError, TypeError, OverflowError):
        return False


def append_log(
    path: Path,
    issuer: x509.Certificate,
    cert: x509.Certificate,
    *,
    signed_at: datetime | None = None,
) -> None:
    """Append one certificate issuance to a protected JSON-lines history file.

    Require existing entries to be complete, valid JSON lines before appending.
    Synchronize the appended record and its directory before returning. A failed append
    may leave an incomplete trailing record; retain that history for inspection rather
    than truncate or silently repair it before retrying.

    Args:
        path: Caller-owned history path, created with mode 0600 if absent. A separate
            adjacent .lock file serializes cooperating writers.
        issuer: CA certificate used to sign cert; its public fingerprint is recorded.
        cert: Issued certificate whose public metadata is recorded.
        signed_at: UTC signing time supplied by the caller, or None for the current
            logging time. It must have a zero UTC offset.

    Returns:
        None after the history file and its directory have been synchronized.

    Raises:
        ValueError: Existing history, timestamps or file protections are invalid.
        OSError: Reading, appending, locking or synchronization fails.
    """
    signing_time = _timestamp((signed_at or utc_now()).isoformat()).isoformat()
    record = {
        "schema_version": 1,
        "issuance_id": secrets.token_hex(16),
        "signing_time": signing_time,
        "issuer_fingerprint_sha256": metadata(issuer)["fingerprint_sha256"],
        "certificate": metadata(cert),
    }
    with files.lock(path.with_name(path.name + ".lock")):
        with files.directory(path.parent) as parent:
            fd = os.open(
                path.name,
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                0o600,
                dir_fd=parent,
            )
            with os.fdopen(fd, "rb+") as stream:
                info = files.confirm(fd, path)
                if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
                    raise ValueError(
                        f"{path}: issuance log requires caller ownership and mode 0600"
                    )
                _inspect_log(stream.read())
                stream.seek(0, os.SEEK_END)
                line = (json.dumps(record, sort_keys=True) + "\n").encode()
                if stream.write(line) != len(line):
                    raise OSError(f"{path}: incomplete log append; commit unconfirmed")
                stream.flush()
                os.fsync(fd)
                files.confirm(fd, path)
            os.fsync(parent)


def _inspect_log(content: bytes) -> None:
    """Check every existing JSON-lines issuance record before appending.

    Args:
        content: Complete history bytes. An empty history is permitted; a nonempty
            history must end with a newline and each line must match the supported
            schema, including meaningful timestamps and certificate metadata.

    Returns:
        None. The supplied history bytes are not changed or repaired.

    Raises:
        ValueError: A record is malformed, incomplete or uses unsupported fields.
    """
    if content and not content.endswith(b"\n"):
        raise ValueError(
            "malformed issuance log: incomplete trailing record; preserve it and select a new log"
        )
    for line in content.splitlines():
        try:
            record = json.loads(line)
        except (ValueError, UnicodeError) as exc:
            raise ValueError(
                "malformed issuance log: preserve it and select a new log"
            ) from exc
        if not _record_valid(record):
            raise ValueError(
                "malformed issuance log record: unsupported fields or schema"
            )


def _output_state(path: Path, expected: bytes) -> str:
    """Describe one final output after a failed publication.

    Args:
        path: Requested output path.
        expected: Bytes that this publication intended to save.

    Returns:
        identical, conflicting, absent, or an unreadable diagnostic. Reading uses
        file-safety checks and does not repair or remove the output.
    """
    try:
        return "identical" if files.read(path) == expected else "conflicting"
    except FileNotFoundError:
        return "absent"
    except (OSError, ValueError) as exc:
        return f"unreadable: {exc}"


def publish(
    operation: str,
    key: PrivateKey,
    cert: x509.Certificate,
    key_out: Path,
    cert_out: Path,
    *,
    issuer: x509.Certificate | None = None,
    chain: Sequence[x509.Certificate] = (),
    log: Path | None = None,
    signed_at: datetime | None = None,
) -> dict[str, Any]:
    """Save a certificate/key pair and optional issuance history without overwriting.

    The key and certificate are separate files, so they cannot be published as one
    atomic change. Save a protected staged pair first, append any requested history
    entry, then write each final output. If a later step fails, preserve the reported
    files and history and inspect the recovery information before retrying over existing
    paths.

    Args:
        operation: Operation name included in failure diagnostics, such as issue.
        key: Private key to serialize as an unencrypted PKCS#8 PEM file.
        cert: Certificate to serialize first in the certificate output.
        key_out: Unused key destination in a protected caller-owned directory.
        cert_out: Distinct unused certificate destination in a protected directory.
        issuer: Signing certificate, required when log is requested.
        chain: Additional certificates to append after cert, in chain order.
        log: Optional protected signing-history path; None omits the log append.
        signed_at: Optional UTC signing time forwarded to append_log.

    Returns:
        A dictionary containing saved_pair_directory, the key/certificate output paths
        under outputs, and issuance_log_status. The staging directory remains available
        after success and contains a mode-0600 key and mode-0644 certificate.

    Raises:
        ValueError: Output preflight rejects an existing name or unsafe directory.
        OSError: Creating the staging directory fails.
        PublicationError: A later save, history append or output write fails. Its
            recovery attribute identifies retained paths and per-output state.
    """
    check_outputs(key_out, cert_out)
    staging = key_out.parent / (".dioptra-ssl-" + secrets.token_hex(16))
    with files.directory(staging.parent) as parent:
        os.mkdir(staging.name, 0o700, dir_fd=parent)
        os.fsync(parent)
    key_bytes = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    cert_bytes = cert.public_bytes(serialization.Encoding.PEM) + b"".join(
        c.public_bytes(serialization.Encoding.PEM) for c in chain
    )
    saved_key, saved_cert = staging / "private.key", staging / "certificate.crt"
    log_status = "not-requested" if log is None else "unconfirmed"
    try:
        files.write_new(saved_key, key_bytes, 0o600)
        files.write_new(saved_cert, cert_bytes, 0o644)
        if log is not None:
            if issuer is None:
                raise ValueError("issuance log requires an issuing certificate")
            append_log(log, issuer, cert, signed_at=signed_at)
            log_status = "durably-saved"
        files.write_new(key_out, key_bytes, 0o600)
        files.write_new(cert_out, cert_bytes, 0o644)
    except BaseException as exc:
        recovery = {
            "operation": operation,
            "directory": str(staging),
            "saved_key": str(saved_key),
            "saved_certificate": str(saved_cert),
            "key_output": {
                "path": str(key_out),
                "state": _output_state(key_out, key_bytes),
            },
            "certificate_output": {
                "path": str(cert_out),
                "state": _output_state(cert_out, cert_bytes),
            },
            "issuance_log": {"path": str(log) if log else None, "status": log_status},
        }
        raise PublicationError(str(exc), recovery) from exc
    return {
        "saved_pair_directory": str(staging),
        "outputs": {"key": str(key_out), "certificate": str(cert_out)},
        "issuance_log_status": log_status,
    }
