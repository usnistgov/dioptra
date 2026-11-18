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
"""Install verified generation files into service-owned Docker volumes.

The host snapshot contains private copies of selected input bytes. An installed
generation adds per-volume completion markers and file metadata (sha256, mode,
owner). A serving volume contains its endpoint pair plus public trust; clients
receive only public trust. A completion marker is written last so service startup
can reject partial installation. This module does not own normal service startup
or shutdown; its caller stops affected services before mutation.
"""

import json
import sys
from collections.abc import Callable
from pathlib import Path

from . import config, files
from . import state as records
from .runtime import Runtime, run

MATERIAL = "/private/material/"
MARKER = "/etc/ssl/dioptra-complete.json"
CHECKSUMS = "/etc/ssl/dioptra-complete.sha256"


def tool(container, *arguments: str) -> dict:
    """Run dioptra-ssl in the helper and decode its structured result.

    Args:
        container: Running temporary Container used for explicit command execution and
            checked file transfers.
        arguments: Certificate-tool command and options, excluding --format which is set
            to json.

    Returns:
        JSON result dictionary. Reported warnings are also printed.

    Raises:
        ValueError: The command fails or its output is not valid JSON.
    """
    result: dict = json.loads(
        container.exec("dioptra-ssl", *arguments, "--format", "json")
    )
    for warning in result.get("warnings", []):
        print("WARNING: " + warning)
    return result


def validation_inputs(names: list[str], *, issuing: bool = False) -> list[str]:
    """Select inputs for validation without unnecessarily transferring a signing key.

    Args:
        names: Deployment-relative certificate/key paths selected for this operation.
        issuing: Include the deployment CA private key only when signing is required.

    Returns:
        Selected relative input names, excluding the issuer key unless issuing=True.
    """
    return [name for name in names if name != records.CA_FILES[1] or issuing]


def import_snapshot(container, snapshot: Path, names: list[str]) -> None:
    """Copy selected snapshot members into the operation's private helper volume.

    Create private parent directories and copy missing files into the helper volume. If
    a destination already exists, require its digest and permissions to match the saved
    host copy. A transfer failure must not cause an existing file with different
    contents to be overwritten.

    Args:
        container: Running helper container used to inspect or install certificate
            files.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        names: Deployment-relative certificate/key paths selected for this operation.

    Returns:
        None.
    """
    for name in names:
        records.member(name)
        destination = MATERIAL + name
        container.private_directory(str(Path(destination).parent))
        if container.exists(destination):
            container.check(
                destination, files.digest(files.read(snapshot / name, 0o600)), 0o600
            )
        else:
            container.put(snapshot / name, destination, 0o600)


def generate(
    container, snapshot: Path, selected: dict, targets: list[str], *, new_ca: bool
) -> None:
    """Generate only selected endpoint pairs and export them to the protected snapshot.

    Use the local signing CA only for endpoints configured as generated; supplied
    endpoint certificates are not reissued. Cap generated-certificate expiration at
    GENERATED_LIMIT. Export the generated files into the private snapshot with mode
    0600. File or certificate-tool failures reach the caller.

    Args:
        container: Running helper container used to inspect or install certificate
            files.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        selected: Certificate and TLS settings loaded by config.load.
        targets: Selected endpoint names, restapi and/or nginx.
        new_ca: Create a new local CA at unused private paths when True.

    Returns:
        None.
    """
    if new_ca:
        container.private_directory(MATERIAL + ".ssl-private/ca")
        tool(
            container,
            "create-ca",
            "--key-out",
            MATERIAL + records.CA_FILES[1],
            "--cert-out",
            MATERIAL + records.CA_FILES[0],
            "--common-name",
            "Dioptra deployment CA",
            "--not-after-limit",
            config.GENERATED_LIMIT,
        )
    for name in targets:
        if selected[name]["source"] == "generated":
            _issue(container, selected, name)
    export = list(records.CA_FILES) if new_ca else []
    export.extend(
        f"ssl/{name}/server.{suffix}"
        for name in targets
        if selected[name]["source"] == "generated"
        for suffix in ("crt", "key")
    )
    if new_ca:
        container.exec("chmod", "0600", MATERIAL + records.CA_FILES[0])
    for name in export:
        records.parents(snapshot, name)
        container.get(MATERIAL + name, snapshot / name)


def _issue(container, selected: dict, name: str) -> None:
    """Issue one generated endpoint with its concrete DNS and IP identities."""
    destination = MATERIAL + f"ssl/{name}/"
    container.private_directory(destination)
    tool(
        container,
        "issue",
        "--ca-cert",
        MATERIAL + records.CA_FILES[0],
        "--ca-key",
        MATERIAL + records.CA_FILES[1],
        "--key-out",
        destination + "server.key",
        "--cert-out",
        destination + "server.crt",
        "--rsa-bits",
        "3072",
        "--valid-days",
        "365",
        "--not-after-limit",
        config.GENERATED_LIMIT,
        *config.identities(selected[name]),
    )
    # General publication uses 0644 for public files. Retained private construction
    # and recovery copies deliberately tighten every member to 0600.
    container.exec("chmod", "0600", destination + "server.crt")


def validate(container, selected: dict, names: list[str]) -> dict:
    """Validate service certificates and inspect additional outbound trust inputs.

    Check each server's trust chain, required identities, private-key match and
    expiration. Generated certificates use GENERATED_LIMIT and supplied server
    certificates use SUPPLIED_LIMIT. Roots selected for services retain strict CA
    validation. Additional outbound trust inputs produce policy warnings, including
    expiration beyond SUPPLIED_LIMIT.

    Args:
        container: Running helper container used to inspect or install certificate
            files.
        selected: Certificate and TLS settings loaded by config.load.
        names: Deployment-relative certificate/key paths selected for this operation.

    Returns:
        Certificate-tool results keyed by restapi, nginx and, when a local issuer is
        present, ca.

    Raises:
        ValueError: Certificate-tool validation or required root selection fails.
    """
    results = {}
    if records.CA_FILES[0] in names:
        key = (
            ["--key", MATERIAL + records.CA_FILES[1]]
            if records.CA_FILES[1] in names
            else []
        )
        results["ca"] = tool(
            container,
            "validate",
            "--kind",
            "ca",
            "--cert",
            MATERIAL + records.CA_FILES[0],
            *key,
            "--max-not-after",
            config.GENERATED_LIMIT,
        )
    _validate_roots(container, names, selected)
    for name in config.ENDPOINTS:
        spec = selected[name]
        roots = (
            [records.CA_FILES[0]]
            if spec["source"] == "generated"
            else spec["trust_files"]
        )
        trust = [part for root in roots for part in ("--trust", MATERIAL + root)]
        limit = (
            config.GENERATED_LIMIT
            if spec["source"] == "generated"
            else config.SUPPLIED_LIMIT
        )
        results[name] = tool(
            container,
            "validate",
            "--cert",
            MATERIAL + f"ssl/{name}/server.crt",
            "--key",
            MATERIAL + f"ssl/{name}/server.key",
            *trust,
            *config.identities(spec),
            "--max-not-after",
            limit,
            "--warn-ca-not-after",
            config.SUPPLIED_LIMIT,
        )
    return results


def _validate_roots(container, names: list[str], selected: dict) -> None:
    """Check distributed CAs according to their configured trust roles.

    Roots selected by supplied service certificates must satisfy deployment CA policy.
    Other distributed certificates are inspected with policy warnings for outbound
    HTTPS use. Unsafe files, malformed PEM and tool failures remain errors in both
    cases. Generated service certificates use the separately validated local issuer.

    Args:
        container: Helper containing the public certificates under MATERIAL.
        names: Deployment-relative certificate paths present in the helper.
        selected: Normalized endpoint configuration, including supplied trust_files.

    Returns:
        None. The tool prints any reported policy warnings.

    Raises:
        ValueError: A selected service root violates policy, or an input/tool fails.
    """
    service_roots = {
        str(Path(name))
        for endpoint in config.ENDPOINTS
        if selected[endpoint]["source"] == "supplied"
        for name in selected[endpoint]["trust_files"]
    }
    for name in names:
        if name.startswith("ssl/ca-certificates/"):
            strict = name in service_roots
            result = tool(
                container,
                "validate",
                "--kind",
                "ca" if strict else "outbound-ca",
                "--cert",
                MATERIAL + name,
                "--warn-ca-not-after",
                config.SUPPLIED_LIMIT,
            )
            if strict and "self-issued-root" not in result["checks"]:
                raise ValueError(
                    f"{name}: public trust inputs must contain root CA certificates"
                )


BUNDLE_TARGETS = {
    "rc-ca-certificates": "ca-certificates.crt",
    "rustfs-certs": "ca-certificates.crt",
    "dbadmin-ca-certificates": "cacert.pem",
}


def trust_consumers(runtime: Runtime) -> set[str]:
    """Select normal services affected by a public trust-bundle change.

    Include services with system trust stores and services that mount only a CA bundle,
    such as the configured RustFS or dbadmin consumers. Exclude one-shot initialization
    helpers, which use their separate setup trust volumes.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.

    Returns:
        Set of effective service names whose public trust bundle is managed by the
        deployment.
    """
    selected = {service for service, _ in services(runtime)}
    for name, service in runtime.services.items():
        if any(
            mount.get("type") == "volume" and mount.get("source") in BUNDLE_TARGETS
            for mount in service.get("volumes", [])
        ):
            selected.add(name)
    return selected


def services(runtime: Runtime) -> list[tuple[str, str]]:
    """Find the services that own each shared system trust-store volume pair.

    Several workers can share the same trust-store volume pair. Return one
    representative service for each logical volume prefix so installation does not write
    the same shared store repeatedly.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.

    Returns:
        List of (effective service name, logical volume prefix) tuples, with each shared
        prefix represented once.
    """
    found: dict[str, tuple[str, str]] = {}
    for name, service in runtime.services.items():
        for mount in service.get("volumes", []):
            source = mount.get("source", "")
            if mount.get("type") == "volume" and source.endswith("-etc-ssl"):
                found.setdefault(source, (name, source.removesuffix("-etc-ssl")))
    return list(found.values())


def _owner(runtime: Runtime, service: str, container) -> str:
    """Resolve the configured runtime UID and GID through the selected service image."""
    selected = runtime.services[service]
    user = selected.get("user")
    if user is None:
        inspected = json.loads(
            run(
                [*runtime.docker, "image", "inspect", selected["image"]],
                root=runtime.root,
            )
        )[0]
        user = inspected["Config"].get("User") or "0:0"
    account, _, group = str(user).partition(":")
    uid = (
        account
        if account.isdecimal()
        else container.exec("id", "-u", account).decode().strip()
    )
    gid = group or container.exec("id", "-g", account).decode().strip()
    if not gid.isdecimal():
        gid = container.exec("getent", "group", gid).decode().split(":")[2]
    return uid + ":" + gid


def trust_bundle(snapshot: Path, spec: dict) -> bytes:
    """Build only the roots selected for one endpoint's certificate validation.

    Args:
        snapshot: Protected directory holding a generation copy with deployment-relative
            paths.
        spec: Normalized endpoint configuration; generated selects the local CA,
            supplied selects its explicit trust_files.

    Returns:
        Concatenated PEM root bytes read from the protected snapshot. These are
        distinct from the service-wide trust store containing all distributed roots.
    """
    roots = (
        [records.CA_FILES[0]] if spec["source"] == "generated" else spec["trust_files"]
    )
    return b"".join(files.read(snapshot / name, 0o600) for name in roots)


def serving_directory(endpoint: str) -> str:
    """Choose the dedicated container directory for an endpoint's certificate and key.

    Args:
        endpoint: restapi or nginx.

    Returns:
        /etc/dioptra/tls for the API, otherwise /etc/ssl for nginx.
    """
    return "/etc/dioptra/tls" if endpoint == "restapi" else "/etc/ssl"


def _mounts(runtime: Runtime, prefix: str, *, readonly: bool) -> list:
    """Keep API serving keys separate from public trust and make runtime reads explicit."""
    mounts = [
        (runtime.volume(prefix + "-etc-ssl"), "/etc/ssl", readonly),
        (
            runtime.volume(prefix + "-ca-certificates"),
            "/usr/local/share/ca-certificates",
            readonly,
        ),
    ]
    if prefix == "restapi":
        mounts.append((runtime.volume("restapi-tls"), "/etc/dioptra/tls", readonly))
    return mounts


def inspect(runtime: Runtime, installed: dict, *, repair: bool = False) -> None:
    """Inspect installed certificate files and public CA bundles.

    Compare completion records, file digests and metadata, checksum lists and the API
    certificate directory with the saved installation. Mount volumes read-only unless
    permission repair is requested. Correct modes only for files whose contents match
    the record; reject a changed or unrecognized certificate set. Normal service state
    is unchanged.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        installed: Installation record describing files on the host and in Docker
            volumes.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        None.
    """
    for entry in installed["volumes"]:
        with runtime.helper(
            entry["image"], _mounts(runtime, entry["prefix"], readonly=not repair)
        ) as container:
            actual = inspect_record(container, MARKER, entry["marker"], repair=repair)
            for path, item in actual["files"].items():
                inspect_file(container, path, item, repair=repair)
            if entry["prefix"] == "restapi":
                inspect_api_directory(container, actual, repair=repair)
            inspect_checksums(container, actual, repair=repair)
            container.exec("sha256sum", "-c", CHECKSUMS)
    inspect_bundles(runtime, installed, repair=repair)


def inspect_record(container, path: str, expected: dict, *, repair: bool) -> dict:
    """Check a known JSON completion record before accepting its parsed contents.

    Args:
        container: Running temporary Container used for explicit command execution and
            checked file transfers.
        path: Container completion-record path.
        expected: Exact record dictionary retained in protected host state.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        Parsed record equal to expected.

    Raises:
        ValueError: Safe metadata, digest or JSON equality checks fail.
    """
    container.safe_destination(path)
    inspect_file(
        container,
        path,
        {
            "sha256": files.digest(files.json_bytes(expected)),
            "mode": 0o644,
            "owner": "0:0",
        },
        repair=repair,
    )
    actual: dict = json.loads(container.exec("cat", path))
    if actual != expected:
        raise ValueError(
            f"{container.name}:{path}: completion record differs from the protected generation"
        )
    return actual


def inspect_checksums(container, marker: dict, *, repair: bool) -> None:
    """Require checksum records to match a known generation, allowing member reordering.

    Check root ownership and single-link file metadata before reading the checksum
    record. Require its generation header first and exactly the recorded files
    afterward, without missing, extra or duplicate lines. File-entry order may vary.
    Repair permissions only if the contents already match the expected installation.

    Args:
        container: Running helper container used to inspect or install certificate
            files.
        marker: Expected completion dictionary with generation ID and file metadata.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        None.

    Raises:
        ValueError: The checksum record or its metadata does not match the expected
            installation.
    """
    container.safe_destination(CHECKSUMS)
    observed = (
        container.exec("stat", "-c", "%F:%h:%a:%u:%g", CHECKSUMS).decode().strip()
    )
    kind, links, mode, uid, gid = observed.split(":")
    if (kind, links, uid, gid) != ("regular file", "1", "0", "0"):
        raise ValueError(
            f"{container.name}:{CHECKSUMS}: unsafe completion metadata {observed}"
        )
    if mode != "644" and not repair:
        raise ValueError(f"{container.name}:{CHECKSUMS}: mode {mode}; expected 0644")
    content = container.exec("cat", CHECKSUMS)
    expected = completion_checks(marker)
    if content.partition(b"\n")[0] != expected.partition(b"\n")[0] or sorted(
        content.split(b"\n")
    ) != sorted(expected.split(b"\n")):
        raise ValueError(
            f"{container.name}:{CHECKSUMS}: checksum record differs from the protected generation"
        )
    inspect_file(
        container,
        CHECKSUMS,
        {"sha256": files.digest(content), "mode": 0o644, "owner": "0:0"},
        repair=repair,
    )


def inspect_file(container, path: str, item: dict, *, repair: bool) -> None:
    """Check a recorded runtime file and optionally repair only its permissions.

    Check type, link count and ownership before hashing the file. Repair a mode
    difference only when the bytes match the installation record. Never rewrite file
    contents or change ownership as part of inspection.

    Args:
        container: Running helper container used to inspect or install certificate
            files.
        path: Container file path.
        item: Expected sha256, mode and numeric uid:gid owner fields.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        None.

    Raises:
        ValueError: Metadata is unsafe, contents differ, or a mode mismatch cannot be
            repaired.
    """
    old = int(container.exec("stat", "-c", "%a", path).decode().strip(), 8)
    if old != item["mode"] and not repair:
        raise ValueError(
            f"{container.name}:{path}: mode {old:04o}; expected {item['mode']:04o}"
        )
    container.check(path, item["sha256"], old, item["owner"])
    if old != item["mode"]:
        container.safe_destination(path)
        container.exec("chmod", f"{item['mode']:04o}", path)
        container.check(path, item["sha256"], item["mode"], item["owner"])
        print(
            f"WARNING: repaired permissions for {container.name}:{path} from {old:04o} to {item['mode']:04o}",
            file=sys.stderr,
        )


def inspect_api_directory(container, marker: dict, *, repair: bool) -> None:
    """Check or repair the dedicated API serving directory.

    The API key directory must be a real directory owned by the recorded serving account
    with mode 0700. Inspection reports an incorrect mode; repair may correct that mode
    only after the directory's type and owner have been checked. Container and
    validation failures reach the caller.

    Args:
        container: Running helper container used to inspect or install certificate
            files.
        marker: Completion record whose server-key file metadata identifies the API
            owner.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        None.
    """
    path = "/etc/dioptra/tls"
    owner = marker["files"][path + "/server.key"]["owner"]
    observed = container.exec("stat", "-c", "%F:%a:%u:%g", path).decode().strip()
    kind, mode, uid, gid = observed.split(":")
    if kind != "directory" or uid + ":" + gid != owner:
        raise ValueError(
            f"{path}: unsafe serving-directory type or ownership {observed}"
        )
    if mode != "700":
        if not repair:
            raise ValueError(f"{path}: mode {mode}; expected 0700")
        container.exec("chmod", "0700", path)
        confirmed = container.exec("stat", "-c", "%F:%a:%u:%g", path).decode().strip()
        if confirmed != "directory:700:" + owner:
            raise ValueError(f"{path}: could not confirm safe directory repair")
        print(
            f"WARNING: repaired permissions for {container.name}:{path} from {int(mode, 8):04o} to 0700",
            file=sys.stderr,
        )


def install(
    runtime: Runtime,
    snapshot: Path,
    installed: dict,
    *,
    allow_empty: bool = False,
    record_progress: Callable[[], None] | None = None,
) -> None:
    """Install a recorded generation into stopped services' trust and serving volumes.

    The caller must hold the deployment lock and manage service shutdown and restart.
    Update installed with completion records for each volume and public CA bundle.
    Publish a volume's completion marker only after its files verify. Save newly
    determined digests through record_progress before publication so an interruption can
    be recovered. Failed installation leaves partial files and saved progress for
    explicit recovery.

    Args:
        installed: Mutable installation record updated with per-volume completion data
            and public-bundle records.

    Returns:
        None.
    """
    selected_prefixes = set(installed["install_prefixes"])
    previous = {
        entry["prefix"]: entry for entry in installed.get("previous_volumes", [])
    }
    volumes = [
        entry for prefix, entry in previous.items() if prefix not in selected_prefixes
    ]
    for service, prefix in services(runtime):
        if prefix not in selected_prefixes:
            continue
        volumes.append(
            install_volume(
                runtime,
                service,
                prefix,
                snapshot,
                installed,
                previous.get(prefix),
                allow_empty,
            )
        )
    installed["volumes"] = volumes
    if installed.get("trust_changed"):
        _export_other_bundles(
            runtime, snapshot, installed, allow_empty, record_progress
        )
    else:
        installed["bundle_volumes"] = installed.get("previous_bundle_volumes", [])


def install_volume(
    runtime: Runtime,
    service: str,
    prefix: str,
    snapshot: Path,
    installed: dict,
    previous: dict | None,
    allow_empty: bool,
) -> dict:
    """Install and verify one stopped service's complete certificate/trust set.

    Require existing files to match the previous or prepared installation, or allow an
    uninitialized volume when explicitly permitted. Install trust, any server pair and
    the TLS settings, then publish checksums and the completion record after
    verification. On failure, retain the partial files so recovery can compare them with
    the saved records.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        service: Effective service name selecting image and runtime ownership.
        prefix: Logical volume prefix identifying the trust-store pair.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        installed: Installation record describing files on the host and in Docker
            volumes.
        previous: Prior generation metadata, or None when installing the first
            generation.
        allow_empty: Permit a volume without a completed generation only when True.

    Returns:
        Dictionary identifying the prefix/image and newly verified completion marker.
    """
    with runtime.helper(
        runtime.services[service]["image"], _mounts(runtime, prefix, readonly=False)
    ) as container:
        endpoint = (
            "restapi"
            if service == runtime.api
            else "nginx"
            if service == runtime.nginx
            else None
        )
        _begin_volume(container, previous, installed, endpoint, allow_empty)
        tracked = _install_trust(container, snapshot, installed["manifest"])
        if endpoint:
            tracked.update(
                _install_pair(
                    container,
                    runtime,
                    service,
                    snapshot,
                    endpoint,
                    installed["configuration"][endpoint],
                )
            )
        if installed.get("transport_policy") and service in runtime.affected(
            ["restapi"]
        ):
            tracked.update(_install_transport(container, snapshot, installed, endpoint))
        tracked.update(_bundle(container))
        marker = {
            "schema_version": 1,
            "generation": installed["generation"],
            "files": tracked,
        }
        if endpoint:
            marker["serving"] = {
                "certificate": serving_directory(endpoint) + "/server.crt",
                "trust": serving_directory(endpoint) + "/dioptra-server-trust.crt",
                "dns": installed["configuration"][endpoint]["dns_sans"],
                "ip": installed["configuration"][endpoint]["ip_sans"],
            }
        _complete(container, snapshot, marker)
        return {
            "image": runtime.services[service]["image"],
            "prefix": prefix,
            "marker": marker,
        }


def _begin_volume(
    container,
    previous: dict | None,
    candidate: dict,
    endpoint: str | None,
    allow_empty: bool,
) -> None:
    """Reconcile complete or interrupted known members before invalidating markers."""
    known = previous["marker"]["files"] if previous else {}
    container.safe_destination(MARKER)
    if container.exists(MARKER):
        marker = json.loads(container.exec("cat", MARKER))
        accepted = {candidate["generation"]}
        if candidate.get("recovery_source"):
            accepted.add(candidate["recovery_source"]["generation"])
        if previous:
            accepted.add(previous["marker"]["generation"])
        if marker.get("generation") not in accepted:
            raise ValueError(
                f"{container.name}: unexplained installed generation; reconcile before installation"
            )
    # A missing marker is expected only during a recorded installing phase. Every
    # managed input still has to match the old or exact candidate digest. The
    # system bundle is reconstructed by the distribution updater from those roots.
    _reconcile_runtime(container, known, candidate, endpoint)
    if not previous and not allow_empty and not container.exists(MARKER):
        raise ValueError(f"{container.name}: missing complete-generation marker")
    for path in (MARKER, CHECKSUMS):
        container.safe_destination(path)
        container.exec("rm", "-f", path)


def _reconcile_runtime(
    container, known: dict, candidate: dict, endpoint: str | None
) -> None:
    """Allow only recorded old or candidate public roots and endpoint pair members."""
    desired = _generation_files(candidate, endpoint)
    source = (
        _generation_files(candidate["recovery_source"], endpoint)
        if candidate.get("recovery_source")
        else {}
    )
    existing = (
        container.exec(
            "find",
            "/usr/local/share/ca-certificates",
            "-maxdepth",
            "1",
            "-name",
            "dioptra-*.crt",
            "-print",
        )
        .decode()
        .splitlines()
    )
    if endpoint:
        serving = "/etc/dioptra/tls" if endpoint == "restapi" else "/etc/ssl"
        existing += [
            f"{serving}/server.{suffix}"
            for suffix in ("crt", "key")
            if container.exists(f"{serving}/server.{suffix}")
        ]
        trust = serving_directory(endpoint) + "/dioptra-server-trust.crt"
        if container.exists(trust):
            existing.append(trust)
    if container.exists(TRANSPORT):
        existing.append(TRANSPORT)
    for path in existing:
        container.safe_destination(path)
        actual = container.exec("sha256sum", path).decode().split()[0]
        accepted = {
            desired.get(path),
            source.get(path),
            known.get(path, {}).get("sha256"),
        }
        if actual not in accepted:
            raise ValueError(
                f"{container.name}:{path}: unexplained runtime digest; recovery refused"
            )


TRANSPORT = "/etc/ssl/dioptra-transport.env"


def transport_bytes(generation: dict, endpoint: str | None) -> bytes:
    """Serialize the transport settings bound to one service generation.

    Args:
        generation: Generation containing transport_policy.
        endpoint: restapi/nginx for a serving service, or None for a trust-only
            consumer.

    Returns:
        Public policy bytes with environment fields and, for nginx, its configuration
        hash. The generation must include transport_policy.
    """
    policy = generation["transport_policy"]
    content = "".join(
        f"{name}={value}\n" for name, value in sorted(policy["environment"].items())
    )
    if endpoint == "nginx":
        content += (
            "NGINX_CONFIG_SHA256=" + files.digest(policy["nginx"].encode()) + "\n"
        )
    return content.encode()


def _install_transport(
    container, snapshot: Path, generation: dict, endpoint: str | None
) -> dict:
    """Publish public policy as a checksum-bound member before completing a volume."""
    content = transport_bytes(generation, endpoint)
    source = snapshot / ("transport-" + (endpoint or "client") + ".env")
    files.write(source, content, replace=True)
    container.put(source, TRANSPORT, 0o644)
    return {TRANSPORT: {"sha256": files.digest(content), "mode": 0o644, "owner": "0:0"}}


def _generation_files(generation: dict, endpoint: str | None) -> dict:
    """Identify one recorded generation's public trust and serving members."""
    expected = _desired_files(generation["manifest"], endpoint)
    if generation.get("transport_policy"):
        expected[TRANSPORT] = files.digest(transport_bytes(generation, endpoint))
    if endpoint:
        expected[serving_directory(endpoint) + "/dioptra-server-trust.crt"] = (
            generation["runtime_trust_digests"][endpoint]
        )
    return expected


def _desired_files(manifest: dict, endpoint: str | None) -> dict:
    """Describe the complete expected runtime members before publication starts."""
    desired = {}
    for name, digest in manifest.items():
        if name.startswith("ssl/ca-certificates/"):
            desired[
                "/usr/local/share/ca-certificates/dioptra-"
                + files.digest(name.encode())
                + ".crt"
            ] = digest
        elif endpoint and name.startswith("ssl/" + endpoint + "/"):
            serving = "/etc/dioptra/tls/" if endpoint == "restapi" else "/etc/ssl/"
            desired[serving + Path(name).name] = digest
    return desired


def _install_trust(container, snapshot: Path, manifest: dict) -> dict:
    """Install every validated public root and rebuild the distribution trust bundle."""
    tracked = {}
    for name in manifest:
        if name.startswith("ssl/ca-certificates/"):
            filename = "dioptra-" + files.digest(name.encode()) + ".crt"
            destination = "/usr/local/share/ca-certificates/" + filename
            container.put(snapshot / name, destination, 0o644)
            tracked[destination] = {
                "sha256": manifest[name],
                "mode": 0o644,
                "owner": "0:0",
            }
    # Remove only managed old public anchors. Unmanaged distribution trust remains.
    existing = (
        container.exec(
            "find",
            "/usr/local/share/ca-certificates",
            "-maxdepth",
            "1",
            "-name",
            "dioptra-*.crt",
            "-print",
        )
        .decode()
        .splitlines()
    )
    for path in existing:
        if path not in tracked:
            container.safe_destination(path)
            container.exec("rm", path)
    updater = "/usr/sbin/update-ca-certificates"
    if not container.exists(updater):
        updater = "/usr/bin/update-ca-trust"
    container.exec(updater)
    return tracked


def _install_pair(
    container, runtime: Runtime, service: str, snapshot: Path, endpoint: str, spec: dict
) -> dict:
    """Copy a selected endpoint pair with runtime ownership and a private key mode."""
    owner = _owner(runtime, service, container)
    directory = serving_directory(endpoint)
    if endpoint == "restapi":
        container.exec("chown", owner, directory)
        container.exec("chmod", "0700", directory)
    tracked = {}
    for suffix, mode in (("crt", 0o644), ("key", 0o600)):
        name = f"ssl/{endpoint}/server.{suffix}"
        destination = f"{directory}/server.{suffix}"
        container.put(snapshot / name, destination, mode, owner)
        tracked[destination] = {
            "sha256": files.digest(files.read(snapshot / name, 0o600)),
            "mode": mode,
            "owner": owner,
        }
    trust = trust_bundle(snapshot, spec)
    source = snapshot / ("server-trust-" + endpoint + ".crt")
    files.write(source, trust, replace=True)
    destination = directory + "/dioptra-server-trust.crt"
    container.put(source, destination, 0o644)
    tracked[destination] = {
        "sha256": files.digest(trust),
        "mode": 0o644,
        "owner": "0:0",
    }
    return tracked


def _bundle(container) -> dict:
    """Export and record the installed public system trust bundle."""
    path = "/etc/ssl/certs/ca-certificates.crt"
    digest = container.exec("sha256sum", path).decode().split()[0]
    container.check(path, digest, 0o644)
    return {path: {"sha256": digest, "mode": 0o644, "owner": "0:0"}}


def completion_checks(marker: dict) -> bytes:
    """Describe every byte and identity check required before service startup.

    Args:
        marker: Completion record containing generation, files and optional serving
            metadata.

    Returns:
        Checksum-file bytes with generation/count metadata, optional certificate
        identity/trust records, and hashes binding each member plus the JSON marker.
    """
    checks: str = "# generation " + marker["generation"] + "\n"
    checks += "# count " + str(len(marker["files"]) + 1) + "\n"
    if "serving" in marker:
        serving = marker["serving"]
        checks += (
            "# certificate "
            + serving["certificate"]
            + "\n# trust "
            + serving["trust"]
            + "\n"
        )
        for kind in ("dns", "ip"):
            checks += "".join("# " + kind + " " + name + "\n" for name in serving[kind])
    checks += "".join(
        value["sha256"] + "  " + path + "\n"
        for path, value in sorted(marker["files"].items())
    )
    checks += files.digest(files.json_bytes(marker)) + "  " + MARKER + "\n"
    return checks.encode()


def _complete(container, snapshot: Path, marker: dict) -> None:
    """Bind the complete member set and JSON generation record with checksums before sync."""
    marker_file = snapshot / ("marker-" + marker["generation"] + ".json")
    checks_file = snapshot / ("marker-" + marker["generation"] + ".sha256")
    files.write(marker_file, files.json_bytes(marker), replace=True)
    files.write(checks_file, completion_checks(marker), replace=True)
    container.put(checks_file, CHECKSUMS, 0o644)
    container.put(marker_file, MARKER, 0o644)
    container.exec("sha256sum", "-c", CHECKSUMS)
    container.exec("sync")


def _export_other_bundles(
    runtime: Runtime,
    snapshot: Path,
    installed: dict,
    allow_empty: bool,
    record_progress: Callable[[], None] | None,
) -> None:
    """Record intended bundle digests before publishing any bundle-only volume."""
    targets = [
        (volume, filename)
        for volume, filename in BUNDLE_TARGETS.items()
        if volume in runtime.volumes
    ]
    if not targets:
        installed["bundle_volumes"] = []
        return
    bundle = snapshot / "system-bundle.crt"
    image = runtime.services[runtime.nginx]["image"]
    with runtime.helper(
        image, [(runtime.volume("nginx-etc-ssl"), "/etc/ssl", True)]
    ) as container:
        container.get("/etc/ssl/certs/ca-certificates.crt", bundle)
    digest = files.digest(files.read(bundle, 0o600))
    installed["bundle_volumes"] = [
        {
            "volume": volume,
            "filename": filename,
            "image": image,
            "marker": {
                "schema_version": 1,
                "generation": installed["generation"],
                "sha256": digest,
            },
        }
        for volume, filename in targets
    ]
    if record_progress:
        record_progress()
    previous = {
        entry["volume"]: entry for entry in installed.get("previous_bundle_volumes", [])
    }
    recovery = {
        entry["volume"]: entry
        for entry in installed.get("recovery_source", {}).get("bundle_volumes", [])
    }
    for entry in installed["bundle_volumes"]:
        publish_bundle(
            runtime,
            snapshot,
            bundle,
            entry,
            previous.get(entry["volume"]),
            recovery.get(entry["volume"]),
            allow_empty,
        )


def publish_bundle(
    runtime: Runtime,
    snapshot: Path,
    bundle: Path,
    entry: dict,
    previous: dict | None,
    recovery: dict | None,
    allow_empty: bool,
) -> None:
    """Install one bundle-only consumer's recorded public trust file.

    Require the existing bundle to match a permitted previous or prepared version,
    unless an empty volume is explicitly allowed. Write the bundle and its completion
    record with root ownership. Do not adopt or overwrite a bundle whose contents are
    absent from the operation's records.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        bundle: Protected host PEM bundle file.
        entry: Candidate bundle-volume name, filename, digest and completion metadata.
        previous: Prior generation metadata, or None when installing the first
            generation.
        recovery: Interrupted candidate bundle metadata, or None if not recovering.
        allow_empty: Permit a volume without a completed generation only when True.

    Returns:
        None.
    """
    with runtime.helper(
        entry["image"], [(runtime.volume(entry["volume"]), "/target", False)]
    ) as container:
        path = "/target/" + entry["filename"]
        allowed = {
            item["marker"]["sha256"]
            for item in (entry, previous, recovery)
            if item is not None
        }
        if container.exists(path):
            container.safe_destination(path)
            current = container.exec("sha256sum", path).decode().split()[0]
            if current not in allowed and not (allow_empty and previous is None):
                raise ValueError(f"{entry['volume']}: unexplained public bundle digest")
        marker = "/target/dioptra-complete.json"
        container.safe_destination(marker)
        container.exec("rm", "-f", marker)
        container.put(bundle, path, 0o644)
        source = snapshot / ("bundle-marker-" + entry["volume"] + ".json")
        files.write(source, files.json_bytes(entry["marker"]), replace=True)
        container.put(source, marker, 0o644)
        container.exec("sync")


def inspect_bundles(runtime: Runtime, installed: dict, *, repair: bool) -> None:
    """Check all recorded bundle-only volumes without accepting changed generations.

    Check each public CA bundle's digest, root ownership, permissions and completion
    record. Permission repair is allowed only when requested and the contents match the
    installation record. Report validation or Docker failures without changing normal
    service state.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        installed: Installation record describing files on the host and in Docker
            volumes.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        None.
    """
    expected = {volume for volume in BUNDLE_TARGETS if volume in runtime.volumes}
    if {entry["volume"] for entry in installed.get("bundle_volumes", [])} != expected:
        raise ValueError(
            "bundle-only volume inventory differs from the installed record"
        )
    for entry in installed.get("bundle_volumes", []):
        with runtime.helper(
            entry["image"], [(runtime.volume(entry["volume"]), "/target", not repair)]
        ) as container:
            actual = inspect_record(
                container,
                "/target/dioptra-complete.json",
                entry["marker"],
                repair=repair,
            )
            inspect_file(
                container,
                "/target/" + entry["filename"],
                {"sha256": actual["sha256"], "mode": 0o644, "owner": "0:0"},
                repair=repair,
            )
