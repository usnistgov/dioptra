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
"""Retain deployment generations and recovery operations in protected host records.

A generation describes one certificate/key/trust file set by relative path and
SHA-256 digest. A state record points to the installed generation and optionally
an interrupted active operation. Operation snapshots use the same relative layout
as the deployment but keep every copied file private. Saving state never implies
that unperformed live HTTPS checks passed.
"""

import json
import re
from pathlib import Path

from . import files

CA_FILES = (".ssl-private/ca/ca.crt", ".ssl-private/ca/ca.key")


def operation_id(value: str) -> str:
    """Validate a recorded identifier before using it in paths or Docker labels.

    Args:
        value: Expected 32-character lowercase hexadecimal operation/deployment ID.

    Returns:
        The unchanged identifier.

    Raises:
        ValueError: The value is not a valid identifier.
    """
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{32}", value) is None:
        raise ValueError(f"{value!r}: invalid operation ID")
    return value


def member(value: str) -> str:
    """Accept only known relative certificate or issuer file names.

    Args:
        value: Deployment-relative path from a record or selected input list.

    Returns:
        The unchanged path after rejecting traversal and unknown locations.

    Raises:
        ValueError: The name is absolute, escapes a directory or is outside the layout.
    """
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{value!r}: unsafe recorded certificate path")
    if value in CA_FILES or value in {
        f"ssl/{endpoint}/server.{suffix}"
        for endpoint in ("restapi", "nginx")
        for suffix in ("crt", "key")
    }:
        return value
    if path.parts[:2] == ("ssl", "ca-certificates") and path.suffix == ".crt":
        return value
    raise ValueError(f"{value!r}: unknown recorded certificate path")


def mode(name: str) -> int:
    """Select the required live-host permissions for a certificate member.

    Args:
        name: Validated member path; .key identifies a private key.

    Returns:
        0600 for a private key and 0644 for a public certificate.
    """
    return 0o600 if name.endswith(".key") else 0o644


def parents(root: Path, relative: str, *, repair: bool = True) -> None:
    """Create or inspect each directory needed for a relative snapshot member.

    Each required directory must be private with mode 0700. Create missing directories
    or repair permitted mode differences only when repair is enabled. Unsafe file types,
    ownership and access errors are returned to the caller.

    Args:
        root: Base directory beneath which the relative path is resolved.
        relative: Validated relative path of the file whose parent directories are
            needed.
        repair: Allow directory creation and safe permission corrections when True.

    Returns:
        None.
    """
    for parent in reversed(Path(relative).parents):
        if str(parent) != ".":
            files.ensure_directory(root / parent, repair=repair)


def manifest(
    root: Path, names: list[str], *, snapshot: bool = False, repair: bool = False
) -> dict:
    """Hash a selected host or snapshot file set after file-safety checks.

    Args:
        root: Deployment root containing config/, ssl/ and .ssl-private/.
        names: Deployment-relative certificate/key paths selected for this operation.
        snapshot: Expect mode 0600 for every snapshot file, including public
            certificates.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        Dictionary mapping each validated relative member path to its SHA-256 digest.

    Raises:
        ValueError: Names, ownership, permissions or read stability fail.
        OSError: A selected file is missing or inaccessible.
    """
    return {
        member(name): files.digest(
            files.read(root / name, 0o600 if snapshot else mode(name), repair=repair)
        )
        for name in sorted(names)
    }


def copy(
    source: Path, destination: Path, names: list[str], *, source_snapshot: bool = False
) -> dict:
    """Copy selected inputs into a protected generation directory without overwrite.

    Store every copied file with mode 0600, including public certificates. This keeps
    the entire saved file set private while an operation is being prepared or recovered.

    Args:
        names: File paths relative to source to copy into destination.

    Returns:
        Manifest of the protected destination copy.

    Raises:
        ValueError: File safety or content checks fail.
        OSError: Input access or exclusive destination publication fails.
    """
    for name in names:
        member(name)
        parents(destination, name)
        content = files.read(source / name, 0o600 if source_snapshot else mode(name))
        files.write(destination / name, content)
    return manifest(destination, names, snapshot=True)


def check_snapshot(root: Path, expected: dict) -> None:
    """Require a retained snapshot to contain the exact previously recorded bytes.

    Read the explicitly recorded files and compare their SHA-256 digests. Do not repair
    files or regenerate certificates while checking a saved set.

    Args:
        root: Directory containing the saved files at their recorded relative paths.
        expected: Mapping of relative file paths to expected SHA-256 digests.

    Returns:
        None.

    Raises:
        ValueError: A file is unsafe or its digest differs.
        OSError: A recorded file is missing or unreadable.
    """
    if manifest(root, list(expected), snapshot=True) != expected:
        raise ValueError(
            f"{root}: retained generation digest mismatch; reconcile exact files before recovery"
        )


def load(root: Path) -> dict | None:
    """Read and validate the protected deployment-state record.

    Args:
        root: Deployment root containing config/, ssl/ and .ssl-private/.

    Returns:
        The schema-1 state dictionary, or None if the state file does not exist.

    Raises:
        ValueError: File safety, JSON/schema, generation pointers or active operation
            fields are invalid.
        OSError: An existing record cannot be read safely.
    """
    path = root / ".ssl-private/deployment-state.json"
    try:
        value = json.loads(files.read(path, 0o600))
    except FileNotFoundError:
        return None
    required = {
        "schema_version",
        "deployment_id",
        "installed_generation",
        "installed",
        "active_operation",
        "previous_generation",
    }
    if (
        not isinstance(value, dict)
        or set(value) != required
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 1
    ):
        raise ValueError(f"{path}: unsupported or malformed deployment record")
    operation_id(value["deployment_id"])
    if (value["installed_generation"] is None) != (value["installed"] is None):
        raise ValueError(
            f"{path}: installed generation and certificate record must both be present or absent"
        )
    if value["installed_generation"] is not None:
        operation_id(value["installed_generation"])
        if (
            not isinstance(value["installed"], dict)
            or value["installed"].get("generation") != value["installed_generation"]
        ):
            raise ValueError(f"{path}: installed generation contradicts record")
    if value["active_operation"] is not None:
        try:
            validate_operation(value["active_operation"])
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"{path}: malformed active operation: {exc}") from exc
    return value


def validate_operation(operation: dict) -> None:
    """Validate operation fields that control paths, resources and recovery.

    Check the operation type, progress phase, selected endpoints, identifiers and
    saved-file digests before these values are used to choose paths or Docker resources.
    The supplied record is not changed.

    Args:
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.

    Returns:
        None.

    Raises:
        ValueError: An operation field has an unsupported or unsafe value.
        KeyError: A required field is missing.
    """
    if not isinstance(operation, dict):
        raise ValueError("operation must be a JSON object")
    operation_id(operation["id"])
    operation_id(operation["candidate_generation"])
    if operation["type"] not in {"init", "replace", "replace-ca"} or operation[
        "phase"
    ] not in {"preparing", "prepared", "installing", "installed", "ready"}:
        raise ValueError("unsupported operation type or phase")
    if not operation["targets"] or set(operation["targets"]) - {"restapi", "nginx"}:
        raise ValueError("invalid recorded operation targets")
    for name, digest in operation.get("staged_file_digests", {}).items():
        member(name)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("invalid recorded member digest")


def save(root: Path, state: dict) -> None:
    """Synchronize current state and, when present, its active operation record.

    The caller must hold the deployment lock. Write .ssl-private/deployment-state.json
    and, if an operation is active, its operation.json record. The operation's directory
    must already exist. Each file is replaced atomically, but the two writes are not a
    single transaction. A filesystem failure can leave temporary output for inspection.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.

    Returns:
        None.
    """
    files.write(
        root / ".ssl-private/deployment-state.json",
        files.json_bytes(state),
        replace=True,
    )
    operation = state["active_operation"]
    if operation is not None:
        path = root / ".ssl-private/operations" / operation_id(operation["id"])
        if path.exists():
            write_operation(root, operation)


def write_operation(root: Path, operation: dict) -> None:
    """Save an operation record independently of the active-state pointer.

    Write .ssl-private/operations/<id>/operation.json with mode 0600 without changing
    the active-operation pointer. Its directory must already exist, and the caller must
    hold the deployment lock. File-check or publication failures leave recovery files
    available for inspection.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.

    Returns:
        None.
    """
    path = (
        root
        / ".ssl-private/operations"
        / operation_id(operation["id"])
        / "operation.json"
    )
    files.write(path, files.json_bytes(operation), replace=True)
