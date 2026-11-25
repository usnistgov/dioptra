#!/usr/bin/env python3
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
"""Manage recorded deployment certificate generations using Python 3.11 or newer.

A generation is one validated set of endpoint certificates, keys, distributed
trust roots and transport policy. Each mutation records an operation before
staging files and retains its exact candidate for interrupted-operation recovery.
The state points to the installed generation only after its required checks pass.

Init installs offline without starting or stopping normal services. Validate
checks the installed state read-only, including live HTTPS. Maintenance replacement
coordinates affected services and verifies live HTTPS before reporting success.
Cryptographic operations run in the configured API image; host code uses only the
standard library. Workstation trust is never changed automatically.
"""

import argparse
import json
import os
import secrets
import shlex
import sys
import tempfile
import time
from pathlib import Path

from ssl_support import config as config
from ssl_support import files as files
from ssl_support import install as installation
from ssl_support import probe as ssl_probe
from ssl_support import state as records
from ssl_support import transport as transport
from ssl_support.runtime import API_INTERNAL_PORT, Runtime, require_offline, run

COMPOSE_COMMAND = {{cookiecutter.docker_compose_path | tojson}}


def directories(root: Path, *, repair: bool) -> None:
    """Check state directories and TLS environment permissions before accessing inputs.

    With repair enabled, create missing directories and correct permitted mode
    differences. Otherwise, inspect without changes. Incorrect ownership, symbolic links
    and unexpected file types are rejected in either mode; repairs never take over
    another user's files. The derived envs/tls.env file requires mode 0640; permission
    repair preserves its contents and ownership.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        repair: Allow directory creation and safe permission corrections when True.

    Returns:
        None.
    """
    required = (".ssl-private", ".ssl-private/operations", "ssl/restapi", "ssl/nginx")
    files.read(root / transport.ENVIRONMENT, 0o640, repair=repair)
    for name in required:
        if repair:
            files.ensure_directory(root / name)
        else:
            with files.directory(root / name) as fd:
                files.mode(fd, root / name, 0o700, repair=False)
    for current, folders, filenames in os.walk(
        root / ".ssl-private", followlinks=False
    ):
        for folder in folders:
            files.ensure_directory(Path(current) / folder, repair=repair)
        for filename in filenames:
            path = Path(current) / filename
            expected = 0o644 if path == root / records.CA_FILES[0] else 0o600
            files.read(path, expected, repair=repair)


def public_names(root: Path, *, repair: bool) -> list[str]:
    """Collect and check all distributed public CA certificate files.

    Inspect every distributed CA certificate, including roots not selected by either
    server. Files must have mode 0644 and neither files nor directories may be symbolic
    links. Correct modes only when repair is enabled.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        Sorted relative .crt paths under ssl/ca-certificates, including roots not
        selected by either endpoint for its own validation.
    """
    base = root / "ssl/ca-certificates"
    files.ensure_directory(base, 0o755, repair=repair)
    names = []
    for current, folders, filenames in os.walk(base, followlinks=False):
        for folder in folders:
            with files.directory(Path(current) / folder):
                pass
        for name in filenames:
            if name.endswith(".crt"):
                path = Path(current) / name
                files.read(path, 0o644, repair=repair)
                names.append(str(path.relative_to(root)))
    return sorted(names)


def host_names(root: Path, selected: dict, *, repair: bool) -> list[str]:
    """List existing CA, server-certificate and public-trust files.

    Inspect both server endpoints, the local CA files and distributed public roots.
    Check each file's safety and permissions before including it. Finding a
    certificate/key pair does not authorize reuse or replacement; later checks must
    match it to the saved installation record.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        selected: Certificate and TLS settings loaded by config.load.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        Sorted relative member paths that currently exist. Missing optional members are
        omitted; operation-specific code separately decides what must be present.
    """
    names = public_names(root, repair=repair)
    for name in (
        *records.CA_FILES,
        *(
            f"ssl/{endpoint}/server.{suffix}"
            for endpoint in config.ENDPOINTS
            for suffix in ("crt", "key")
        ),
    ):
        try:
            files.read(root / name, records.mode(name), repair=repair)
        except FileNotFoundError:
            continue
        names.append(name)
    return sorted(names)


def current_manifest(root: Path, selected: dict, *, repair: bool = False) -> dict:
    """Hash the currently selected deployment inputs after safety checks.

    Args:
        root: Deployment root containing config/, ssl/ and .ssl-private/.
        selected: Normalized certificate and transport configuration returned by
            config.load.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        Mapping of relative input paths to SHA-256 digests, suitable for comparing
        current inputs with a protected generation record.
    """
    return records.manifest(
        root, host_names(root, selected, repair=repair), repair=repair
    )


def snapshot_path(root: Path, operation: str, kind: str = "candidate") -> Path:
    """Locate a protected operation snapshot without accepting arbitrary paths.

    Args:
        root: Deployment root containing config/, ssl/ and .ssl-private/.
        operation: Validated 32-character hexadecimal operation ID.
        kind: candidate for proposed bytes, or previous for the retained rollback copy.

    Returns:
        Path below .ssl-private/operations/<id>/. It is not created.

    Raises:
        ValueError: The operation ID or snapshot kind is invalid.
    """
    records.operation_id(operation)
    if kind not in {"candidate", "previous"}:
        raise ValueError("invalid generation snapshot kind")
    return root / ".ssl-private/operations" / operation / kind


def recovery_message(operation: dict) -> str:
    """Describe explicit recovery for the recorded interrupted operation.

    Args:
        operation: Recorded operation dictionary with its ID, phase, selected
            configuration and recovery information.

    Returns:
        Diagnostic identifying the operation ID/phase and exact resume command,
        with rollback restricted to an available still-valid prior generation.
    """
    return (
        f"operation {operation['id']} is {operation['phase']}; retain its files. "
        f"Reconcile the reported failure, then run python3 scripts/manage_ssl.py recover --operation {operation['id']} --action resume. "
        "Use --action rollback only when a prior complete still-valid generation exists."
    )


def fresh_state() -> dict:
    """Build a new deployment record without claiming that certificates are installed.

    Returns:
        Schema-1 state with a random deployment_id and empty installed, active and
        previous generation pointers. Nothing is saved until the caller writes it.
    """
    return {
        "schema_version": 1,
        "deployment_id": secrets.token_hex(16),
        "installed_generation": None,
        "installed": None,
        "active_operation": None,
        "previous_generation": None,
    }


def check_intent(state: dict, selected: dict, command: str, targets: list[str]) -> None:
    """Check that configuration changes are allowed by the selected command.

    Compare the selected settings with the installed configuration. Ordinary init must
    not adopt changed server settings, and replacement must not change an unselected
    endpoint. Valid certificates do not exempt a configuration change from these rules.
    The supplied state is not modified.

    Args:
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        selected: Certificate and TLS settings loaded by config.load.
        command: Selected lifecycle command: init, replace or replace-ca.
        targets: Selected endpoint names, restapi and/or nginx.

    Returns:
        None.

    Raises:
        ValueError: Init changes server settings or replacement changes an unselected
            endpoint.
    """
    prior = state["installed"]
    if prior is None:
        if command != "init":
            raise ValueError(
                "replacement requires a recorded installed generation; initialize explicitly first"
            )
        return
    old = prior["configuration"]
    if old == selected:
        return
    if command == "init" and {k: v for k, v in old.items() if k != "transport"} == {
        k: v for k, v in selected.items() if k != "transport"
    }:
        return
    if command != "replace":
        raise ValueError(
            "configuration differs from installed state; use explicit targeted replacement and reconcile intent"
        )
    for key in old:
        allowed = key in targets or (key == "public" and "nginx" in targets)
        if not allowed and old[key] != selected[key]:
            raise ValueError(
                f"configuration {key} changed outside selected replacement targets"
            )


def check_inputs(
    state: dict, selected: dict, observed: dict, command: str, targets: list[str]
) -> None:
    """Check certificate-file changes against the selected operation.

    Compare the observed file digests with the installed record and the selected
    replacement targets. Changed supplied server pairs require explicit replacement.
    Files generated by this deployment must remain accounted for; init cannot silently
    adopt or lose them. Changes limited to public trust roots may use init. Run this
    check before installation or service interruption.

    Args:
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        selected: Certificate and TLS settings loaded by config.load.
        observed: Mapping of current deployment-relative input paths to their SHA-256
            digests.
        command: Selected lifecycle command: init, replace or replace-ca.
        targets: Selected endpoint names, restapi and/or nginx.

    Returns:
        None.

    Raises:
        ValueError: File changes are not permitted by the command or recorded
            installation.
    """
    prior = state["installed"]
    if prior is None:
        _check_fresh_inputs(selected, observed)
        return
    changed = {
        name
        for name in observed.keys() | prior["manifest"].keys()
        if observed.get(name) != prior["manifest"].get(name)
    }
    if not changed:
        return
    if command == "init" and all(
        name.startswith("ssl/ca-certificates/")
        and name != "ssl/ca-certificates/dioptra-local-ca.crt"
        for name in changed
    ):
        return
    if command != "replace":
        raise ValueError(
            f"host inputs differ from installed generation: {sorted(changed)}; explicit replacement is required"
        )
    for name in changed:
        supplied_target = _supplied_input(name, selected, targets)
        if not supplied_target and not name.startswith("ssl/ca-certificates/"):
            raise ValueError(
                f"{name}: unexplained host change outside supplied replacement input"
            )


def _check_fresh_inputs(selected: dict, observed: dict) -> None:
    """Reject unrecorded generated-source files in a fresh deployment.

    A fresh deployment has no record proving that existing CA or server files were
    generated by this tool. Refuse those files when their source is configured as
    generated. Files explicitly configured as supplied can proceed to certificate
    validation and installation.

    Args:
        selected: Certificate and TLS settings loaded by config.load.
        observed: Mapping of current deployment-relative input paths to their SHA-256
            digests.

    Returns:
        None.

    Raises:
        ValueError: A generated-source endpoint or local issuer already has unrecorded
            files.
    """
    generated = [name for name in observed if _generated_input(name, selected)]
    if generated:
        raise ValueError(
            f"missing generated ownership record for existing certificates or keys: {generated}; reconcile rather than adopt"
        )


def _generated_input(name: str, selected: dict) -> bool:
    """Classify a recorded path as generated-source input.

    Args:
        name: Relative certificate/key or public local-CA path.
        selected: Normalized certificate and transport configuration returned by
            config.load.

    Returns:
        True if ownership must be preserved as part of a generated endpoint/issuer.
    """
    if name in records.CA_FILES or name == "ssl/ca-certificates/dioptra-local-ca.crt":
        return True
    return any(
        name.startswith(f"ssl/{endpoint}/")
        and selected[endpoint]["source"] == "generated"
        for endpoint in config.ENDPOINTS
    )


def _supplied_input(name: str, selected: dict, targets: list[str]) -> bool:
    """Classify a path as supplied input owned by the selected replacement target.

    Args:
        name: Relative live-host member path.
        selected: Normalized certificate and transport configuration returned by
            config.load.
        targets: Selected endpoint names, restapi and/or nginx.

    Returns:
        True only for serving inputs of a supplied endpoint included in targets.
    """
    return any(
        name.startswith(f"ssl/{endpoint}/")
        and selected[endpoint]["source"] == "supplied"
        for endpoint in targets
    )


def start_operation(
    root: Path,
    runtime: Runtime,
    state: dict,
    selected: dict,
    command: str,
    targets: list[str],
    observed: dict,
) -> dict:
    """Record a certificate operation before preparing its files.

    Save the input file digests, Compose configuration, affected services and previous
    certificate installation before generating or replacing files. Create private
    storage for the operation and its backups. If a later step fails, these records
    allow recovery to use the same inputs and previous installation.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        selected: Certificate and TLS settings loaded by config.load.
        command: Selected lifecycle command: init, replace or replace-ca.
        targets: Selected endpoint names, restapi and/or nginx.
        observed: Mapping of current deployment-relative input paths to their SHA-256
            digests.

    Returns:
        Active operation dictionary also stored in state and synchronized to disk.
    """
    identifier = secrets.token_hex(16)
    operation = {
        "id": identifier,
        "type": command,
        "targets": targets,
        "configuration_digest": config.digest(selected),
        "configuration": selected,
        "expected_prior_generation": state["installed_generation"],
        "candidate_generation": identifier,
        "phase": "preparing",
        "staged_file_digests": {},
        "input_digests": observed,
        "initialization_volume": runtime.project + "-ssl-" + identifier,
        "affected_services": runtime.affected(targets),
        "runtime_intent": transport.intent(runtime.config),
        "transport_input": files.read(root / transport.ENVIRONMENT, 0o640).decode(),
        "candidate": None,
        "previous": state["installed"],
    }
    if state["installed"] is None or state["installed"].get(
        "transport_policy"
    ) != transport.prepare(root, runtime, selected):
        operation["affected_services"] = sorted(
            set(operation["affected_services"]) | set(runtime.affected(["restapi"]))
        )
    state["active_operation"] = operation
    trust_changed = (
        state["installed"] is None
        or command == "replace-ca"
        or any(
            name.startswith("ssl/ca-certificates/")
            and observed.get(name) != state["installed"]["manifest"].get(name)
            for name in observed.keys()
            | (state["installed"]["manifest"].keys() if state["installed"] else set())
        )
    )
    if trust_changed:
        operation["affected_services"] = sorted(
            set(operation["affected_services"]) | installation.trust_consumers(runtime)
        )
    operation["trust_changed"] = trust_changed
    records.save(root, state)
    for kind in ("candidate", "previous"):
        path = snapshot_path(root, identifier, kind)
        files.ensure_directory(path.parent)
        files.ensure_directory(path)
    if state["installed"]:
        prior = state["installed"]
        source = snapshot_path(
            root, prior["snapshot_operation"], prior.get("snapshot_kind", "candidate")
        )
        records.check_snapshot(source, prior["manifest"])
        records.copy(
            source,
            snapshot_path(root, identifier, "previous"),
            list(prior["manifest"]),
            source_snapshot=True,
        )
    return operation


def prepare(root: Path, runtime: Runtime, state: dict, operation: dict) -> None:
    """Prepare and validate the files for one certificate installation.

    Copy the selected inputs into private storage and create only the missing or
    replacement files permitted by this operation. Validate both server endpoints and
    the public CA roots, then save their file digests and validation results with phase
    prepared. Recheck the host inputs before accepting the copy. This preparation does
    not yet replace active files or stop application services.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.

    Returns:
        None.
    """
    selected = operation["configuration"]
    targets, generated, new_ca, omitted = generation_inputs(state, operation)
    operation["generation_targets"] = targets
    snapshot = snapshot_path(root, operation["id"])
    imported = [name for name in operation["input_digests"] if name not in omitted]
    records.copy(root, snapshot, imported)
    runtime.create_operation_volume(operation["initialization_volume"], operation["id"])
    names, results = construct(
        runtime, operation, snapshot, imported, omitted, generated, new_ca
    )
    expected = records.manifest(snapshot, names, snapshot=True)
    if current_manifest(root, selected) != operation["input_digests"]:
        raise ValueError(
            "host inputs changed during import; retain candidate and reconcile digests before recovery"
        )
    operation["staged_file_digests"] = expected
    operation["candidate"] = {
        "generation": operation["candidate_generation"],
        "transport_policy": transport.prepare(root, runtime, selected),
        "manifest": expected,
        "configuration": selected,
        "results": results,
        "snapshot_operation": operation["id"],
        "snapshot_kind": "candidate",
        "prior_generation": state["installed_generation"],
        "volumes": [],
        "previous_volumes": state["installed"]["volumes"] if state["installed"] else [],
        "previous_bundle_volumes": state["installed"].get("bundle_volumes", [])
        if state["installed"]
        else [],
        "install_prefixes": [
            prefix
            for service, prefix in installation.services(runtime)
            if service in operation["affected_services"]
        ],
        "trust_changed": operation["trust_changed"],
    }
    operation["phase"] = "prepared"
    records.save(root, state)


def generation_inputs(
    state: dict, operation: dict
) -> tuple[list[str], list[str], bool, set[str]]:
    """Choose which issuer and endpoint files an operation may generate.

    Args:
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        operation: Recorded operation dictionary with its ID, phase, selected
            configuration and recovery information.

    Returns:
        Tuple of target endpoints, all generated-source endpoints, whether a new CA
        is required, and relative file names excluded from import because they will
        be regenerated. An installed trust-only init generates no replacement pairs.
    """
    selected, targets = operation["configuration"], operation["targets"]
    if operation["type"] == "init" and state["installed"] is not None:
        targets = []
    generated = [
        name for name in config.ENDPOINTS if selected[name]["source"] == "generated"
    ]
    new_ca = bool(generated) and (
        state["installed"] is None or operation["type"] == "replace-ca"
    )
    omitted = {
        f"ssl/{name}/server.{suffix}"
        for name in targets
        if name in generated
        for suffix in ("crt", "key")
    }
    if new_ca:
        omitted.update(records.CA_FILES)
        omitted.add("ssl/ca-certificates/dioptra-local-ca.crt")
    return targets, generated, new_ca, omitted


def construct(
    runtime: Runtime,
    operation: dict,
    snapshot: Path,
    imported: list[str],
    omitted: set[str],
    generated: list[str],
    new_ca: bool,
) -> tuple[list[str], dict]:
    """Generate and validate certificate files in a temporary container.

    Transfer the CA private key only when certificates must be signed. A deployment
    using only supplied certificates needs no locally generated CA. Copy newly generated
    public CA certificates back to the snapshot for distribution to clients. Remove the
    helper container when finished, while retaining the operation's saved files for
    recovery.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        imported: Relative input names already copied into snapshot.
        omitted: Relative names reserved for newly generated files.
        generated: All endpoints configured to use the deployment-local issuer.
        new_ca: Create a local issuer only when True.

    Returns:
        Tuple of complete member names and cryptographic validation results keyed by
        endpoint and optional ca.
    """
    selected, targets = operation["configuration"], operation["generation_targets"]
    with runtime.helper(
        runtime.image, [(operation["initialization_volume"], "/private", False)]
    ) as container:
        issuing = new_ca or any(
            selected[name]["source"] == "generated" for name in targets
        )
        container_names = installation.validation_inputs(imported, issuing=issuing)
        installation.import_snapshot(container, snapshot, container_names)
        installation.generate(container, snapshot, selected, targets, new_ca=new_ca)
        if generated:
            public_ca = "ssl/ca-certificates/dioptra-local-ca.crt"
            records.parents(snapshot, public_ca)
            if not (snapshot / public_ca).exists():
                files.write(
                    snapshot / public_ca,
                    files.read(snapshot / records.CA_FILES[0], 0o600),
                )
                installation.import_snapshot(container, snapshot, [public_ca])
        names = sorted(
            set(imported)
            | omitted
            | ({"ssl/ca-certificates/dioptra-local-ca.crt"} if generated else set())
        )
        # No local CA exists or is constructed in a fully supplied deployment.
        results = installation.validate(
            container, selected, installation.validation_inputs(names, issuing=issuing)
        )
    return names, results


def reconcile_host(root: Path, operation: dict, candidate: dict) -> None:
    """Check host files before resuming an interrupted installation.

    An interrupted write may leave either the original file or the prepared replacement
    in place. Require every affected path to match one of those recorded versions. A
    removed file may instead have the archive recorded during rollback. Inspect only; do
    not replace or repair host inputs here.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.
        candidate: Prepared installation record identifying the new generation and its
            files.

    Returns:
        None.

    Raises:
        ValueError: A host file is missing or changed without a matching operation
            record or rollback archive.
    """
    actual = current_manifest(root, operation["configuration"])
    initial, desired = operation["input_digests"], candidate["manifest"]
    for name in actual.keys() | initial.keys() | desired.keys():
        if actual.get(name) is None and name in operation.get(
            "rollback_archived_inputs", {}
        ):
            archived = (
                snapshot_path(root, operation["id"]).parent
                / "rollback-inputs"
                / records.member(name)
            )
            if (
                files.digest(files.read(archived, 0o600))
                != operation["rollback_archived_inputs"][name]
            ):
                raise ValueError(f"{name}: archived rollback input changed")
            continue
        if actual.get(name) not in {initial.get(name), desired.get(name)}:
            raise ValueError(
                f"{name}: host digest differs from both recorded input and candidate; recovery refused"
            )
        if operation["phase"] == "prepared" and actual.get(name) != initial.get(name):
            raise ValueError(f"{name}: input changed after preparation")


def validate_snapshot(
    runtime: Runtime, snapshot: Path, candidate: dict, volume: str, identifier: str
) -> dict:
    """Validate a saved certificate set against its recorded contents.

    Compare the saved files with their recorded digests before copying them into a
    validation volume. Leave out signing keys that validation does not need.
    Certificate-tool failures are returned to the caller. The caller must remove
    disposable validation storage or retain an operation's storage for recovery, as
    appropriate.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        candidate: Prepared installation record identifying the new generation and its
            files.
        volume: Exact validation/construction volume name for this invocation.
        identifier: Operation ID used to label the volume.

    Returns:
        Fresh certificate-tool results for both endpoints and applicable issuer.
    """
    records.check_snapshot(snapshot, candidate["manifest"])
    runtime.create_operation_volume(volume, identifier)
    with runtime.helper(runtime.image, [(volume, "/private", False)]) as container:
        names = installation.validation_inputs(list(candidate["manifest"]))
        installation.import_snapshot(container, snapshot, names)
        return installation.validate(container, candidate["configuration"], names)


def publish_host(root: Path, snapshot: Path, candidate: dict) -> None:
    """Publish candidate certificate and trust bytes into their live host paths.

    Copy files from the prepared snapshot with their required permissions, skipping
    files whose bytes already match so their inodes remain unchanged. Each file is
    published separately. If publication stops partway through, use the saved operation
    to reconcile the partially written set before continuing.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        candidate: Prepared installation record identifying the new generation and its
            files.

    Returns:
        None.
    """
    for name in candidate["manifest"]:
        if not name.startswith("ssl/ca-certificates/"):
            files.ensure_directory((root / name).parent)
        else:
            files.ensure_directory(root / "ssl/ca-certificates", 0o755)
        desired = files.read(snapshot / name, 0o600)
        try:
            current = files.read(root / name, records.mode(name), repair=True)
        except FileNotFoundError:
            current = None
        if current != desired:
            files.write(root / name, desired, records.mode(name), replace=True)


def archive_extra_inputs(
    root: Path, state: dict, operation: dict, candidate: dict
) -> None:
    """Back up certificate files that rollback will remove.

    Rollback can remove files that were introduced after the previous installation.
    While holding the deployment lock, save those files and their digests in a private
    archive before removing their active names. Check the bytes again before removal so
    recovery can recognize either the original path or its saved archive.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.
        candidate: Prepared installation record identifying the new generation and its
            files.

    Returns:
        None.
    """
    actual = current_manifest(root, operation["configuration"])
    extra = sorted(actual.keys() - candidate["manifest"].keys())
    archive = snapshot_path(root, operation["id"]).parent / "rollback-inputs"
    files.ensure_directory(archive)
    archived = operation.setdefault("rollback_archived_inputs", {})
    for name in extra:
        records.parents(archive, records.member(name))
        content = files.read(root / name, records.mode(name))
        destination = archive / name
        if destination.exists():
            if files.read(destination, 0o600) != content:
                raise ValueError(
                    f"{name}: retained rollback input conflicts with host input"
                )
        else:
            files.write(destination, content)
        archived[name] = files.digest(content)
    records.save(root, state)
    for name in extra:
        files.remove_verified(root / name, files.read(archive / name, 0o600))


def check_published_host(root: Path, candidate: dict) -> None:
    """Require the published host files to match the prepared certificate set.

    Compare the complete active file set with the prepared installation record. Report
    differences without repairing files or generating replacements.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        candidate: Prepared installation record identifying the new generation and its
            files.

    Returns:
        None.

    Raises:
        ValueError: A file is extra, missing, changed or unsafe to read.
    """
    if current_manifest(root, candidate["configuration"]) != candidate["manifest"]:
        raise ValueError(
            "host inputs differ from the selected complete generation after publication"
        )


def verify_live(
    root: Path, runtime: Runtime, snapshot: Path, candidate: dict
) -> list[dict]:
    """Check the API and public nginx endpoint over verified HTTPS.

    Verify each server against the selected trust roots, identity and expected
    certificate fingerprint. Reach the API through its Compose network and nginx through
    its published address and port. The probes send no login credentials. Connection,
    certificate and HTTP-response failures are returned to the caller.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        candidate: Prepared installation record identifying the new generation and its
            files.

    Returns:
        List of successful TLS/HTTP probe dictionaries for both endpoints.
    """
    selected = candidate["configuration"]
    results = []
    for endpoint in config.ENDPOINTS:
        roots = (
            [records.CA_FILES[0]]
            if selected[endpoint]["source"] == "generated"
            else selected[endpoint]["trust_files"]
        )
        bundle = snapshot / ("live-" + endpoint + ".crt")
        files.write(
            bundle,
            b"".join(files.read(snapshot / name, 0o600) for name in roots),
            replace=True,
        )
        fingerprint = candidate["results"][endpoint]["certificate"][
            "fingerprint_sha256"
        ]
        if endpoint == "nginx":
            results.append(
                ssl_probe.verify(
                    runtime.public_connect(),
                    runtime.public_port(),
                    selected["public"]["host"],
                    bundle,
                    fingerprint,
                    hybrid=selected["transport"]["key_exchange"] == "hybrid-required",
                    path="/",
                )
            )
        else:
            results.append(
                _verify_api(root, runtime, snapshot, bundle, fingerprint, selected)
            )
    return results


def _verify_api(
    root: Path,
    runtime: Runtime,
    snapshot: Path,
    bundle: Path,
    fingerprint: str,
    selected: dict,
) -> dict:
    """Probe the candidate API on its Compose network without transferring private keys.

    Run the standalone probe on the API's Docker network, supplying only the probe
    script and public trust bundle. Remove the helper container when the request
    finishes or fails. Trust, server-identity and fingerprint mismatches fail the check.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        bundle: Protected host bundle containing the explicit API validation roots.
        fingerprint: Expected candidate API certificate SHA-256 fingerprint.
        selected: Certificate and TLS settings loaded by config.load.

    Returns:
        Successful standalone-probe TLS/HTTP result dictionary.
    """
    probe = snapshot / "ssl_probe.py"
    files.write(
        probe, (root / "scripts/ssl_support/probe.py").read_bytes(), replace=True
    )
    # This network helper sees selected public trust only. No issuer volume or
    # private CA key is mounted for a live connection check.
    with runtime.helper(runtime.image, [], network=runtime.network) as container:
        container.put(probe, "/ssl_probe.py", 0o600)
        container.put(bundle, "/trust.crt", 0o600)
        arguments = [
            "python3",
            "/ssl_probe.py",
            "--connect",
            runtime.api,
            "--identity",
            runtime.api,
            "--port",
            str(API_INTERNAL_PORT),
            "--trust",
            "/trust.crt",
            "--fingerprint",
            fingerprint,
        ]
        if selected["transport"]["key_exchange"] == "hybrid-required":
            arguments.append("--hybrid")
        result: dict = json.loads(container.exec(*arguments))
        return result


def complete(
    root: Path,
    runtime: Runtime,
    state: dict,
    operation: dict,
    candidate: dict,
    snapshot: Path,
) -> None:
    """Install a prepared certificate set and record successful completion.

    The caller must hold the deployment lock. For init, keep services stopped and record
    completion of file validation and installation. Live HTTPS checks run separately
    after startup. For maintenance, stop the affected services, install the prepared
    files and settings, restart them and require verified HTTPS. Save progress as
    installation proceeds; a failure leaves the operation active for recovery.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.
        candidate: Prepared installation record identifying the new generation and its
            files.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.

    Returns:
        None.
    """
    volume = operation["initialization_volume"]
    if candidate["generation"] != operation["candidate_generation"]:
        volume += "-rollback"
        operation["rollback_volume"] = volume
    candidate["results"] = validate_snapshot(
        runtime, snapshot, candidate, volume, operation["id"]
    )
    check_transport(root, runtime, candidate["configuration"], snapshot)
    candidate["runtime_trust_digests"] = {
        name: files.digest(
            installation.trust_bundle(snapshot, candidate["configuration"][name])
        )
        for name in config.ENDPOINTS
    }
    reconcile_host(root, operation, operation.get("candidate") or candidate)
    transport.preflight(root, runtime, candidate["transport_policy"], snapshot)
    transport.reconcile(root, runtime, operation, candidate)
    if operation["type"] == "init":
        require_offline(root, runtime.compose)
    else:
        runtime.stop(operation["affected_services"])
    operation["phase"] = "installing"
    records.save(root, state)
    publish_host(root, snapshot, candidate)
    if candidate["generation"] != operation["candidate_generation"]:
        archive_extra_inputs(root, state, operation, candidate)
    check_published_host(root, candidate)
    transport.publish(root, runtime, candidate["transport_policy"], snapshot)
    installation.install(
        runtime,
        snapshot,
        candidate,
        allow_empty=operation["type"] == "init",
        record_progress=lambda: records.save(root, state),
    )
    check_published_host(root, candidate)
    installation.inspect(runtime, candidate)
    transport.inspect(root, runtime, candidate, candidate["configuration"])
    operation["phase"] = "installed"
    records.save(root, state)
    if operation["type"] == "init":
        candidate.pop("live_checks", None)
    else:
        runtime.start(operation["affected_services"])
        candidate["live_checks"] = wait_live(root, runtime, snapshot, candidate)
        check_published_host(root, candidate)
        operation["phase"] = "ready"
    operation["completed_generation"] = candidate["generation"]
    records.write_operation(root, operation)
    if state["installed_generation"] != candidate["generation"]:
        state["previous_generation"] = state["installed"]
    state["installed"] = candidate
    state["installed_generation"] = candidate["generation"]
    state["active_operation"] = None
    records.save(root, state)
    report(candidate, runtime, live_verified=operation["type"] != "init")


def wait_live(
    root: Path, runtime: Runtime, snapshot: Path, candidate: dict
) -> list[dict]:
    """Wait for restarted API and nginx services to pass HTTPS checks.

    Retry failed HTTPS probes while restarted services become ready. Check the 60-second
    retry deadline between attempts; each in-flight probe has its own connection or
    command timeout. Return only after both endpoints verify successfully.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        candidate: Prepared installation record identifying the new generation and its
            files.

    Returns:
        Successful API/nginx probe results from verify_live.

    Raises:
        ValueError: Verification still fails after the bounded startup window.
    """
    deadline = time.monotonic() + 60
    while True:
        try:
            return verify_live(root, runtime, snapshot, candidate)
        except (OSError, ValueError) as exc:
            if time.monotonic() >= deadline:
                raise ValueError(f"verified HTTPS readiness failed: {exc}") from exc
            time.sleep(2)


def report(installed: dict, runtime: Runtime, *, live_verified: bool = True) -> None:
    """Print certificate details and instructions for configuring client trust.

    Show the public HTTPS URL, certificate expirations and fingerprints, backup
    locations and public CA export instructions. Explain whether live verification ran.
    Do not expose private-key digests or modify the user's workstation or browser trust
    settings.

    Args:
        installed: Installation record describing files on the host and in Docker
            volumes.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        live_verified: True only after this invocation passed live checks; False reports
            offline installation and tells the operator to start services and validate.

    Returns:
        None.
    """
    public_host = installed["configuration"]["public"]["host"]
    authority = f"[{public_host}]" if ":" in public_host else public_host
    outcome = (
        "passed verified HTTPS readiness"
        if live_verified
        else "was validated and installed offline"
    )
    print(f"Installed generation {installed['generation']} {outcome}.")
    if not live_verified:
        print(
            "Normal deployment services remain stopped. Start them with Compose, then run python3 scripts/manage_ssl.py validate for live HTTPS checks."
        )
    print(
        f"Public HTTPS URL is https://{authority}:{runtime.public_port()}. Clients must reach this Docker host using the configured hostname or IP address."
    )
    print(
        "Configure DNS or client hosts-file resolution for a selected hostname. Keep a protected backup of .ssl-private/, ssl/ and config/ssl.toml; retained recovery files remain under .ssl-private/operations/."
    )
    for endpoint in config.ENDPOINTS:
        cert = installed["results"][endpoint]["certificate"]
        print(
            f"{endpoint}: identities {cert['identities']}, expires {cert['not_after']}, SHA-256 {cert['fingerprint_sha256']}"
        )
    if "ca" in installed["results"]:
        print(
            "Public CA export: ssl/ca-certificates/dioptra-local-ca.crt; SHA-256 "
            + installed["results"]["ca"]["certificate"]["fingerprint_sha256"]
        )
        if installed["configuration"]["nginx"]["source"] == "generated":
            print(
                "Import only this public CA into your chosen browser or operating-system trust store before browser access."
            )
    print("Workstation trust was not changed.")


def validation_checks() -> dict[str, str]:
    """Initialize independent validation groups before any checks run.

    Returns:
        Ordered mapping of check-group names to unavailable. Callers replace each
        status only after actually attempting or completing that group.
    """
    return dict.fromkeys(
        (
            "compose",
            "permissions",
            "configuration-and-state",
            "host-material",
            "cryptography",
            "runtime-volumes",
            "live-https",
        ),
        "unavailable",
    )


def print_validation(checks: dict[str, str]) -> None:
    """Print every validation group, including failures and unavailable checks.

    Args:
        checks: Mutable mapping of validation group names to their reported outcomes.

    Returns:
        None.
    """
    for check, result in checks.items():
        print(f"{check}: {result}")


def inspect_readonly(
    root: Path,
    runtime: Runtime,
    state: dict | None,
    selected: dict,
    checks: dict[str, str] | None = None,
    *,
    live: bool = True,
) -> None:
    """Validate the recorded installation without changing its files or services.

    Require a completed installation with no interrupted operation. Check the host
    files, TLS configuration, certificates and installed Docker volumes, then verify
    HTTPS unless live is disabled for an offline init rerun. Record which checks could
    not run after a prerequisite failure and return that failure to the caller.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        state: Installed deployment record, or None when no record exists.
        selected: Certificate and TLS settings loaded by config.load.
        checks: Optional outcome mapping to update; when omitted a local report is
            printed.
        live: Require a fresh verified HTTPS connection when True; False explicitly
            reports it as not performed.

    Returns:
        None.
    """
    own_report = checks is None
    checks = validation_checks() if checks is None else checks
    if own_report:
        checks.update({"compose": "passed", "permissions": "passed"})
    try:
        checks["configuration-and-state"] = "failed"
        if (
            state is None
            or state["installed"] is None
            or state["active_operation"] is not None
        ):
            raise ValueError(
                "validation incomplete: no installed recorded generation, or an interrupted operation requires recovery"
            )
        check_intent(state, selected, "init", [])
        transport.inspect(root, runtime, state["installed"], selected)
        checks["configuration-and-state"] = "passed"
        checks["host-material"] = "failed"
        observed = current_manifest(root, selected)
        if observed != state["installed"]["manifest"]:
            raise ValueError(
                "host inputs differ from the installed generation; use init for a public-trust-only update or explicit replacement for serving certificates or keys"
            )
        checks["host-material"] = "passed"
        inspect_runtime_snapshot(
            root, runtime, state["installed"], observed, checks, live=live
        )
    finally:
        if own_report:
            print_validation(checks)


def inspect_runtime_snapshot(
    root: Path,
    runtime: Runtime,
    installed: dict,
    observed: dict,
    checks: dict[str, str],
    *,
    live: bool = True,
) -> None:
    """Validate installed volumes using temporary copies of host certificate files.

    Check certificate validity and recorded volume contents, updating the result for
    each validation group. Optionally verify the live HTTPS endpoints. Remove this
    call's helper and temporary validation volume on success or failure; leave the saved
    installation files and normal service state unchanged.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        installed: Installation record describing files on the host and in Docker
            volumes.
        observed: Mapping of current deployment-relative input paths to their SHA-256
            digests.
        checks: Mutable mapping of validation group names to their reported outcomes.
        live: Require a fresh verified HTTPS connection when True; False explicitly
            reports it as not performed.

    Returns:
        None.
    """
    identifier = secrets.token_hex(16)
    volume = runtime.project + "-ssl-validation-" + identifier
    with tempfile.TemporaryDirectory(prefix="dioptra-ssl-validation-") as temporary:
        snapshot = Path(temporary).resolve()
        records.copy(root, snapshot, list(observed))
        try:
            checks["cryptography"] = "failed or unavailable"
            validate_snapshot(runtime, snapshot, installed, volume, identifier)
            checks["cryptography"] = "passed"
            checks["runtime-volumes"] = "failed or unavailable"
            installation.inspect(runtime, installed)
            checks["runtime-volumes"] = "passed"
            if live:
                checks["live-https"] = "failed or unavailable"
                verify_live(root, runtime, snapshot, installed)
                checks["live-https"] = "passed"
            else:
                checks["live-https"] = "not performed (offline installation)"
        except BaseException as primary:
            remove_validation_volume(runtime, volume, primary)
            raise
        else:
            remove_validation_volume(runtime, volume)


def remove_validation_volume(
    runtime: Runtime, volume: str, primary: BaseException | None = None
) -> None:
    """Remove a temporary certificate-validation volume.

    If validation has already failed, add a cleanup failure to that exception as a note
    instead of replacing it. Otherwise, let a removal failure reach the caller. The
    supplied name must identify this call's disposable volume, not a service's installed
    storage.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        volume: Exact temporary volume name, never an installed service volume.
        primary: Existing failure to annotate if cleanup also fails, or None.

    Returns:
        None.
    """
    try:
        run([*runtime.docker, "volume", "rm", volume], root=runtime.root)
    except (OSError, ValueError) as cleanup:
        if primary is None:
            raise
        primary.add_note(f"validation volume {volume} removal also failed: {cleanup}")


def validate_deployment(root: Path, compose: list[str]) -> None:
    """Print the results of read-only deployment validation.

    Resolve the deployment configuration and installation record, inspect permissions
    without repair and run the read-only validation groups. Print the collected results
    even if a check fails, including checks that could not run. Let the command wrapper
    report a nonzero exit on failure. Normal services are not started or stopped.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        compose: Configured split Compose command selecting the deployment and engine.

    Returns:
        None.
    """
    checks = validation_checks()
    try:
        checks["compose"] = "failed or unavailable"
        runtime = Runtime(root, compose)
        checks["compose"] = "passed"
        checks["permissions"] = "failed"
        directories(root, repair=False)
        checks["permissions"] = "passed"
        checks["configuration-and-state"] = "failed"
        selected = config.load(root, runtime.api)
        state = records.load(root)
        inspect_readonly(root, runtime, state, selected, checks)
    finally:
        print_validation(checks)


def recover(
    root: Path,
    runtime: Runtime,
    state: dict,
    selected: dict,
    identifier: str,
    action: str,
) -> None:
    """Resume or roll back the recorded interrupted certificate operation.

    Require the requested ID, selected settings and Compose configuration to match the
    saved operation. Resume uses its exact prepared certificate set rather than
    generating another. Init recovery stays offline; maintenance recovery controls the
    affected services and verifies HTTPS. Save further progress so another interruption
    can also be recovered.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        selected: Certificate and TLS settings loaded by config.load.
        identifier: Recorded 32-character hexadecimal operation ID.
        action: resume uses the exact candidate; rollback requires a valid prior
            generation.

    Returns:
        None.
    """
    records.operation_id(identifier)
    operation = recovery_operation(state, identifier)
    prior = operation.get("previous") or state["installed"]
    rolling_back = (
        action == "rollback" or operation.get("recovery_action") == "rollback"
    )
    intent = (
        prior["configuration"] if rolling_back and prior else operation["configuration"]
    )
    expected_runtime = (
        prior.get("transport_policy", {}).get("runtime_intent")
        if rolling_back and prior
        else operation["runtime_intent"]
    )
    if selected != intent or transport.intent(runtime.config) != expected_runtime:
        raise ValueError(
            "recovery intent or effective Compose configuration changed; restore the prior Compose mapping for rollback, or the recorded candidate mapping for resume"
        )
    if state["installed_generation"] != operation["expected_prior_generation"]:
        raise ValueError("recorded prior generation changed; recovery refused")
    candidate = operation["candidate"]
    if rolling_back:
        restore_prior(root, runtime, state, operation, candidate, prior)
        return
    if candidate is None:
        raise ValueError(
            "preparation did not retain a complete recorded candidate; inspect retained files and reconcile before recovery; no replacement is generated automatically"
        )
    complete(
        root, runtime, state, operation, candidate, snapshot_path(root, identifier)
    )


def recovery_operation(state: dict, identifier: str) -> dict:
    """Select only the explicitly identified active interrupted operation.

    Args:
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        identifier: Recorded 32-character hexadecimal operation ID.

    Returns:
        The matching active operation dictionary.

    Raises:
        ValueError: No active operation exists or the ID does not match.
    """
    operation: dict | None = state["active_operation"]
    if operation is None or operation["id"] != identifier:
        raise ValueError("operation is not the recorded interrupted operation")
    return operation


def restore_prior(
    root: Path,
    runtime: Runtime,
    state: dict,
    operation: dict,
    candidate: dict | None,
    prior: dict | None,
) -> None:
    """Validate and reinstall the certificate set saved before an operation.

    Check the previous certificates, including their current validity, before
    interrupting services. Record the rollback choice and reinstall the exact saved
    files. The saved progress also supports resuming a rollback interrupted before or
    during publication.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.
        candidate: Interrupted candidate record, or None before preparation completes.
        prior: Recorded previous complete generation, or None when rollback is
            unavailable.

    Returns:
        None.
    """
    if prior is None:
        raise ValueError(
            "first initialization has no prior complete generation; rollback is unavailable"
        )
    if candidate is None:
        raise ValueError(
            "operation lacks a complete candidate for runtime reconciliation"
        )
    rollback = dict(
        prior,
        snapshot_operation=operation["id"],
        snapshot_kind="previous",
        previous_volumes=candidate.get("volumes") or prior["volumes"],
        previous_bundle_volumes=candidate.get("bundle_volumes")
        or prior.get("bundle_volumes", []),
        install_prefixes=candidate["install_prefixes"],
        trust_changed=candidate["trust_changed"],
    )
    validate_snapshot(
        runtime,
        snapshot_path(root, operation["id"], "previous"),
        rollback,
        operation["initialization_volume"] + "-rollback",
        operation["id"],
    )
    # Retain the publication origin when rollback itself advances the phase.
    # Prepared candidates have not changed serving volumes and may lack digests.
    operation.setdefault("rollback_prepublication", operation["phase"] == "prepared")
    if not operation["rollback_prepublication"]:
        rollback["recovery_source"] = {
            "generation": candidate["generation"],
            "transport_policy": candidate.get("transport_policy"),
            "manifest": candidate["manifest"],
            "runtime_trust_digests": candidate["runtime_trust_digests"],
            "bundle_volumes": candidate.get("bundle_volumes", []),
        }
    operation["recovery_action"] = "rollback"
    state["active_operation"] = operation
    records.save(root, state)
    complete(
        root,
        runtime,
        state,
        operation,
        rollback,
        snapshot_path(root, operation["id"], "previous"),
    )


def check_transport(
    root: Path, runtime: Runtime, selected: dict, snapshot: Path
) -> None:
    """Check runtime support for the selected TLS key exchange.

    The default selection needs no capability probe. For hybrid TLS, check local Python
    and each participating image, including real curl and nginx connections using the
    selected trust roots. Remove the temporary test servers and helpers afterward.
    Unsupported hybrid exchange fails before service interruption rather than selecting
    a different exchange.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        selected: Certificate and TLS settings loaded by config.load.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.

    Returns:
        None.
    """
    if selected["transport"]["key_exchange"] != "hybrid-required":
        return
    ssl_probe.hybrid_context()
    with tempfile.TemporaryDirectory(prefix="dioptra-ssl-capability-") as temporary:
        probe = Path(temporary).resolve() / "ssl_probe.py"
        files.write(probe, (root / "scripts/ssl_support/probe.py").read_bytes())
        images = {
            runtime.services[service]["image"]
            for service in runtime.affected(["restapi"])
            if service != runtime.nginx
        }
        for image in images:
            with runtime.helper(image, []) as container:
                container.put(probe, "/ssl_probe.py", 0o600)
                container.exec("python3", "/ssl_probe.py", "--check-hybrid")
                if image == runtime.image:
                    transport.curl_trust(container, snapshot, selected, "restapi")
                    container.put(
                        snapshot / "ssl/restapi/server.crt", "/curl-server.crt", 0o644
                    )
                    container.put(
                        snapshot / "ssl/restapi/server.key", "/curl-server.key", 0o600
                    )
                    run(
                        [
                            *runtime.docker,
                            "exec",
                            "--detach",
                            container.name,
                            "python3",
                            "/ssl_probe.py",
                            "--serve-hybrid",
                            "--certificate",
                            "/curl-server.crt",
                            "--key",
                            "/curl-server.key",
                            "--port",
                            str(ssl_probe.HYBRID_PROBE_PORT),
                        ],
                        root=root,
                    )
                    transport.curl_handshake(container, runtime.api)
        with runtime.helper(runtime.services[runtime.nginx]["image"], []) as container:
            # Test the image's listener and proxy SSL contexts with validated candidate
            # certificates or keys. The minimal config does not need running service DNS records.
            probe_config = Path(temporary).resolve() / "capability.conf"
            files.write(
                probe_config, (root / "scripts/ssl_hybrid_nginx.conf").read_bytes()
            )
            container.put(probe_config, "/capability.conf", 0o644)
            container.put(snapshot / "ssl/nginx/server.crt", "/candidate.crt", 0o644)
            container.put(snapshot / "ssl/nginx/server.key", "/candidate.key", 0o600)
            container.exec("nginx", "-t", "-c", "/capability.conf")
            transport.curl_trust(container, snapshot, selected, "nginx")
            container.exec("nginx", "-c", "/capability.conf")
            transport.curl_handshake(container, selected["public"]["host"])


def require_offline_command(args, root: Path, compose: list[str]) -> None:
    """Check offline prerequisites for init and init recovery.

    Init and recovery of an init operation require normal services to be stopped before
    host files can be created or repaired. Read only the state needed to identify that
    case. Other maintenance commands keep their own service stop/start behavior.

    Args:
        args: Parsed manager arguments identifying init or an init recovery.
        root: Deployment directory containing SSL configuration and certificate files.
        compose: Configured split Compose command.

    Returns:
        None.

    Raises:
        ValueError: Init or its recovery would run while normal services are active.
    """
    if args.command == "init":
        require_offline(root, compose)
    elif args.command == "recover":
        retained = records.load(root)
        operation = recovery_operation(retained or fresh_state(), args.operation)
        if operation["type"] == "init":
            require_offline(root, compose)


def execute(args) -> None:
    """Run the requested certificate management command.

    Send validate through its read-only inspection path. For commands that change the
    deployment, check offline prerequisites first, inspect or repair permitted file
    modes, load the settings and saved state, then execute under the deployment lock.
    Failures reach main for reporting.

    Args:
        args: Namespace returned by parser(), including command and deployment_root.

    Returns:
        None.
    """
    root = files.absolute(args.deployment_root)
    compose = shlex.split(COMPOSE_COMMAND)
    if not compose:
        raise ValueError("Compose executable is required")
    if args.command == "validate":
        validate_deployment(root, compose)
        return
    require_offline_command(args, root, compose)
    runtime = Runtime(root, compose)
    files.ensure_directory(root / ".ssl-private")
    with files.lock(root / ".ssl-private/operation.lock"):
        directories(root, repair=True)
        public_names(root, repair=True)
        selected = config.load(root, runtime.api)
        state = records.load(root) or fresh_state()
        try:
            mutate(args, root, runtime, state, selected)
        except BaseException:
            if state["active_operation"]:
                print(recovery_message(state["active_operation"]), file=sys.stderr)
            raise


def check_existing_issuer(state: dict, selected: dict) -> None:
    """Require the recorded CA before reusing generated server certificates.

    An existing generated-certificate installation must retain its complete recorded CA
    before a rerun or replacement can reuse it. Do not silently generate a different
    issuer if those files are missing. A deployment using only supplied certificates
    does not need a local CA.

    Args:
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        selected: Certificate and TLS settings loaded by config.load.

    Returns:
        None.

    Raises:
        ValueError: The installed generated-certificate record does not include its
            complete local issuer.
    """
    if state["installed"] is None or not any(
        selected[name]["source"] == "generated" for name in config.ENDPOINTS
    ):
        return
    if not set(records.CA_FILES).issubset(state["installed"]["manifest"]):
        raise ValueError(
            "no complete deployment CA is recorded; generated replacement requires the existing CA. Use supplied certificates or initialize a fresh deployment with generated certificates"
        )


def mutate(args, root: Path, runtime: Runtime, state: dict, selected: dict) -> None:
    """Run certificate initialization, replacement or recovery under the lock.

    The caller holds the deployment lock throughout. Check settings and file ownership
    before creating an operation. An unchanged init validates the existing installation
    offline; a changed installation is recorded, prepared and then completed. Handle an
    interrupted operation through the explicit recover command.

    Args:
        args: Parsed manager command, including target or recovery choices.
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        state: Mutable deployment record containing installed, installed_generation and
            active_operation.
        selected: Certificate and TLS settings loaded by config.load.

    Returns:
        None.
    """
    if args.command == "recover":
        recover(root, runtime, state, selected, args.operation, args.action)
        return
    if state["active_operation"]:
        raise ValueError(recovery_message(state["active_operation"]))
    targets = (
        [args.target]
        if args.command == "replace" and args.target != "all"
        else list(config.ENDPOINTS)
    )
    if args.command == "replace-ca":
        targets = [
            name for name in config.ENDPOINTS if selected[name]["source"] == "generated"
        ]
        if not targets:
            raise ValueError(
                "replace-ca requires at least one endpoint using the deployment-local CA; it accepts no target"
            )
    observed = current_manifest(root, selected, repair=True)
    check_intent(state, selected, args.command, targets)
    check_inputs(state, selected, observed, args.command, targets)
    check_existing_issuer(state, selected)
    if args.command == "init" and state["installed"]:
        installation.inspect(runtime, state["installed"], repair=True)
    if (
        args.command == "init"
        and state["installed"]
        and observed == state["installed"]["manifest"]
        and state["installed"].get("transport_policy")
        == transport.prepare(root, runtime, selected)
    ):
        inspect_readonly(root, runtime, state, selected, live=False)
        report(state["installed"], runtime, live_verified=False)
        return
    if state["installed"]:
        installation.inspect(runtime, state["installed"])
    operation = start_operation(
        root, runtime, state, selected, args.command, targets, observed
    )
    prepare(root, runtime, state, operation)
    complete(
        root,
        runtime,
        state,
        operation,
        operation["candidate"],
        snapshot_path(root, operation["id"]),
    )


def parser() -> argparse.ArgumentParser:
    """Build the manager's explicit initialization, inspection and maintenance commands.

    Returns:
        ArgumentParser with init, validate, replace-ca, targeted replace, and
        recover with an operation ID and resume/rollback action. Building it has no
        deployment side effects.
    """
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--deployment-root", type=Path, default=Path(__file__).resolve().parent.parent
    )
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for command in ("init", "validate", "replace-ca"):
        commands.add_parser(command, parents=[shared])
    replacement = commands.add_parser("replace", parents=[shared])
    replacement.add_argument(
        "--target", choices=[*config.ENDPOINTS, "all"], required=True
    )
    recovery = commands.add_parser("recover", parents=[shared])
    recovery.add_argument("--operation", required=True)
    recovery.add_argument("--action", choices=["resume", "rollback"], required=True)
    return result


def main() -> int:
    """Run the selected lifecycle command and report failures without discarding state.

    Returns:
        Zero on success, or one after reporting an operation failure to stderr.
        Argument parsing also exits nonzero for invalid command-line input.
    """
    args = parser().parse_args()
    try:
        execute(args)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print(f"Certificate operation failed: {exc}", file=sys.stderr)
        for note in getattr(exc, "__notes__", []):
            print(note, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
