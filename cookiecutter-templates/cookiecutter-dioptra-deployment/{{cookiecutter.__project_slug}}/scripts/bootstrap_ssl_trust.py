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
"""Prepare initializer-only public trust before external Git/npm downloads.

Only existing public roots are imported. These separate volumes never contain
serving keys or generation-readiness markers. The normal manager init operation
still owns complete certificate installation and verified HTTPS readiness.
"""

import json
import re
import secrets
import shlex
import sys
import tempfile
from pathlib import Path

import manage_ssl as manager
from ssl_support.runtime import Runtime, run


def initialization_volumes(runtime: Runtime) -> dict[str, str]:
    """Find or create the CA trust volumes used during deployment setup.

    These volumes hold the CA certificates used to verify HTTPS downloads during
    setup. Keep them separate from service trust stores so setup cannot change a
    service's installed trust. Create missing volumes, and require existing volumes to
    carry this deployment's setup label before reusing them. Retain the volumes for
    subsequent initialization runs.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.

    Returns:
        Mapping from the three initialization-only Compose volume keys to their
        effective Docker volume names.

    Raises:
        ValueError: Compose resolution fails, a volume name is unsafe, a volume overlaps
            normal service storage, or an existing volume has a conflicting label.
        KeyError: The initialization configuration omits a required volume.
    """
    selected: dict = json.loads(
        run(
            [
                *runtime.compose,
                "-f",
                str(runtime.root / "docker-compose.init.yml"),
                "config",
                "--format",
                "json",
            ],
            root=runtime.root,
        )
    )
    volumes = {
        name: selected["volumes"][name]["name"]
        for name in (
            "ssl-bootstrap-ca-certificates",
            "ssl-bootstrap-etc-ssl",
            "ssl-bootstrap-rc-certificates",
        )
    }
    active = {value["name"] for value in runtime.volumes.values()}
    if active.intersection(volumes.values()):
        raise ValueError(
            "initializer-only trust volumes must not share active runtime volumes"
        )
    for name in volumes.values():
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            raise ValueError("initializer trust volume has an unsafe Docker name")
        runtime.create_operation_volume(name, "bootstrap-" + selected["name"])
    return volumes


def prepare_public_roots(root: Path, runtime: Runtime) -> list[str]:
    """Check the public CA files selected for setup downloads.

    Check the selected public CA files against the saved deployment settings and
    certificate records before using them for downloads. An interrupted certificate
    operation must be recovered first. Safe permission corrections are allowed, but this
    step does not create or replace server certificates.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.

    Returns:
        Paths to the selected public CA files, relative to the deployment directory.

    Raises:
        ValueError: An interrupted operation, changed certificate inputs, conflicting
            settings or unsafe file metadata prevents preparation.
    """
    manager.directories(root, repair=True)
    state = manager.records.load(root) or manager.fresh_state()
    if state["active_operation"]:
        raise ValueError(manager.recovery_message(state["active_operation"]))
    names = manager.public_names(root, repair=True)
    selected = manager.config.load(root, runtime.api)
    manager.check_intent(state, selected, "init", list(manager.config.ENDPOINTS))
    manager.check_inputs(
        state,
        selected,
        manager.current_manifest(root, selected, repair=True),
        "init",
        list(manager.config.ENDPOINTS),
    )
    return names


def validate_roots(runtime: Runtime, snapshot: Path, names: list[str]) -> None:
    """Check public certificates according to their service or outbound trust role.

    Use the API image's certificate tools to check copies of the selected public CA
    certificates. Private keys are not needed for this validation. The helper container
    and its temporary volume are removed when the check finishes or fails; the
    deployment's installed certificate record is not changed. Roots selected for
    services use strict CA validation; additional outbound roots report policy warnings.

    Args:
        runtime: Deployment configuration and Docker access.
        snapshot: Private directory containing copies of the CA files at
            deployment-relative paths.
        names: Paths to public CA certificate files within snapshot.

    Returns:
        None.
    """
    if not names:
        return
    identifier = secrets.token_hex(16)
    volume = runtime.project + "-ssl-bootstrap-validation-" + identifier
    runtime.create_operation_volume(volume, identifier)
    try:
        with runtime.helper(runtime.image, [(volume, "/private", False)]) as container:
            manager.installation.import_snapshot(container, snapshot, names)
            selected = manager.config.load(runtime.root, runtime.api)
            manager.installation._validate_roots(container, names, selected)
    except BaseException as primary:
        manager.remove_validation_volume(runtime, volume, primary)
        raise
    else:
        manager.remove_validation_volume(runtime, volume)


def bootstrap(root: Path, runtime: Runtime) -> None:
    """Prepare CA bundles for deployment setup downloads.

    Validate the selected public CA certificates, then build the system and
    RustFS-client CA bundles used by setup download commands. Hold the deployment lock
    while checking inputs and updating these setup-only volumes. Server certificates and
    the normal services' trust stores remain the responsibility of manage_ssl. A failure
    is reported without recording a completed certificate installation.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.

    Returns:
        None.
    """
    manager.files.ensure_directory(root / ".ssl-private")
    with manager.files.lock(root / ".ssl-private/operation.lock"):
        names = prepare_public_roots(root, runtime)
        volumes = initialization_volumes(runtime)
        with tempfile.TemporaryDirectory(prefix="dioptra-ssl-bootstrap-") as temporary:
            snapshot = Path(temporary).resolve()
            manifest = manager.records.copy(root, snapshot, names)
            validate_roots(runtime, snapshot, names)
            image = runtime.services[runtime.nginx]["image"]
            mounts = [
                (
                    volumes["ssl-bootstrap-ca-certificates"],
                    "/usr/local/share/ca-certificates",
                    False,
                ),
                (volumes["ssl-bootstrap-etc-ssl"], "/etc/ssl", False),
            ]
            bundle = snapshot / "bootstrap-bundle.crt"
            with runtime.helper(image, mounts) as container:
                if container.exists(manager.installation.MARKER) or container.exists(
                    "/etc/ssl/server.key"
                ):
                    raise ValueError(
                        "initializer trust volume unexpectedly contains serving certificates or keys"
                    )
                manager.installation._install_trust(container, snapshot, manifest)
                container.get("/etc/ssl/certs/ca-certificates.crt", bundle)
                container.exec("sync")
            with runtime.helper(
                image, [(volumes["ssl-bootstrap-rc-certificates"], "/target", False)]
            ) as container:
                container.put(bundle, "/target/ca-certificates.crt", 0o644)
                container.exec("sync")
    print("Prepared public CA trust for initialization downloads.")


def main() -> int:
    """Run CA trust preparation for deployment initialization.

    Locate the deployment using this script's directory and use the same configured
    Compose command as manage_ssl. Prepare the download trust stores without starting
    normal deployment services.

    Returns:
        Zero after successful bootstrap, or one after reporting a failure to stderr.
    """
    root = Path(__file__).resolve().parent.parent
    try:
        runtime = Runtime(root, shlex.split(manager.COMPOSE_COMMAND))
        bootstrap(root, runtime)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print(f"Initialization public-trust preparation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
