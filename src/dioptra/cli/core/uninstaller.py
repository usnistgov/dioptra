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
"""Uninstall planning and execution for Dioptra deployments.

Uninstall is split into two phases for safety:

* plan_uninstall builds a description of what would be removed (which
  images, volumes, networks; which are skipped because other deployments
  reference them) without taking any destructive action. Callers show this
  to the user and prompt for confirmation.

* execute_uninstall performs the actual removal based on a plan: stops the
  compose stack, removes resources, deletes the deployment directory, and
  unregisters from the registry.
"""

import shutil
from pathlib import Path

from dioptra.cli.core import deployments, docker


def plan_uninstall(
    name: str,
    remove_images: bool,
    include_external: bool,
    verbose: bool = False,
) -> dict | None:
    """Build a plan describing what would be removed by uninstalling `name`.

    Reads the deployment's manifest (preferred), or falls back to docker
    compose, or further to the registry's recorded resources.
    Compares against other deployments' manifests so that any resources
    shared with another deployment are added to skip lists rather than
    remove lists.

    Returns None if the deployment isn't registered (and prints the error).
    Other failures are caught and logged.

    The returned plan structure:
      {
        "name", "path", "compose_str",
        "remove_images", "skip_images": list[str],
        "remove_volumes", "skip_volumes": list[str],
        "remove_networks", "skip_networks": list[str],
      }
    """
    try:
        record = deployments.get_deployment_record(name)
    except Exception as e:
        print(e)
        return None

    path = Path(record["path"]).expanduser()
    compose_str = record.get("docker_compose_path")

    plan: dict = {
        "name": name,
        "path": path,
        "compose_str": compose_str,
        "remove_images": [],
        "remove_volumes": [],
        "remove_networks": [],
        "skip_images": [],
        "skip_volumes": [],
        "skip_networks": [],
    }

    internal, external, volumes, networks = _discover_resources(
        path,
        compose_str,
        record,
        verbose,
    )

    refs = deployments.get_resource_references(exclude_deployment=name)

    if remove_images:
        candidates = internal + (external if include_external else [])
        for img in candidates:
            if img in refs["images"]:
                plan["skip_images"].append(img)
            else:
                plan["remove_images"].append(img)

    for vol in volumes:
        if vol in refs["volumes"]:
            plan["skip_volumes"].append(vol)
        else:
            plan["remove_volumes"].append(vol)

    for net in networks:
        if net in refs["networks"]:
            plan["skip_networks"].append(net)
        else:
            plan["remove_networks"].append(net)

    return plan


def execute_uninstall(  # noqa: C901 — complex structure; branch count is due to verbose logging
    plan: dict,
    verbose: bool = False,
    force: bool = False,
) -> None:
    """Carry out an uninstall plan: stop, remove, unregister.

    Phases:
      1. validate_deployment_removal sanity check (refuses symlinks and
         non-Dioptra paths unless force is set)
      2. docker compose down to stop and clean up the running stack
      3. remove volumes, networks, and images per the plan
      4. remove the deployment directory
      5. unregister from the registry

    Failures during resource removal are logged and don't abort the rest of
    the uninstall. Failures removing the directory or unregistering are raised.
    """
    name = plan["name"]
    path = plan["path"]
    compose_str = plan.get("compose_str")

    if verbose:
        print(f"Uninstalling '{name}' from {path}")

    deployments.validate_deployment_removal(path, force)

    # Stop the running stack. Catch any exceptions and make a best effort
    # to uninstall.
    if path.exists():
        if verbose:
            print("Stopping containers...")
        try:
            docker.compose_down(path, compose_str, verbose=verbose)
        except Exception as e:
            print(f"Warning: Failed to stop containers: {e}")
    elif verbose:
        print(f"Path missing, skipping container shutdown: {path}")

    _remove_resources(
        volumes=plan.get("remove_volumes", []),
        networks=plan.get("remove_networks", []),
        images=plan.get("remove_images", []),
        verbose=verbose,
    )

    if path.exists():
        if verbose:
            print(f"Removing directory: {path}")
        try:
            shutil.rmtree(path)
        except Exception as e:
            raise RuntimeError(f"Failed to remove deployment directory: {e}") from e
    elif verbose:
        print(f"Directory already removed: {path}")

    try:
        deployments.unregister_deployment(name)
        if verbose:
            print(f"Unregistered deployment '{name}'")
    except Exception as e:
        raise RuntimeError(f"Failed to unregister deployment: {e}") from e

    if verbose:
        print("Uninstall complete.")


def _discover_resources(
    path: Path,
    compose_str: str | None,
    record: dict,
    verbose: bool,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Discover internal_images, external_images, volumes, networks.

    Prefers the deployment's manifest. Falls back to compose-config, then
    lastly to the registry's recorded resources. Returns empty lists if all
    three sources fail.
    """
    manifest = deployments.read_manifest(path)
    if manifest:
        resources = manifest["resources"]
        return (
            resources["images"]["internal"],
            resources["images"]["external"],
            resources["volumes"],
            resources.get("networks", []),
        )

    if verbose:
        print(
            f"Warning: No manifest found in {path}. "
            "Attempting to discover docker resources."
        )

    try:
        resources = docker.get_compose_resources(path, compose_str)
        return (
            resources["images"]["internal"],
            resources["images"]["external"],
            resources["volumes"],
            resources["networks"],
        )
    except Exception:
        if verbose:
            print(
                f"Could not read docker compose at {path}. "
                "Falling back to the deployment registry."
            )

    normalized = deployments.normalize_resources(record.get("resources", {}))
    return (
        normalized["internal"],
        normalized["external"],
        normalized["volumes"],
        normalized["networks"],
    )


def _remove_resources(
    volumes: list[str],
    networks: list[str],
    images: list[str],
    verbose: bool,
) -> None:
    """Remove the planned resources and log any failures.

    Volumes and networks are removed first (which may be holding
    references to images via stopped containers), then images. Each
    docker.remove_* call is independent so one failure doesn't block
    the rest.
    """
    for vol in volumes:
        try:
            docker.remove_volume(vol, verbose=verbose)
        except Exception as e:
            print(f"Warning: Failed to remove volume {vol}: {e}")

    for net in networks:
        try:
            docker.remove_network(net, verbose=verbose)
        except Exception as e:
            print(f"Warning: Failed to remove network {net}: {e}")

    for img in images:
        try:
            docker.remove_image(img, verbose=verbose)
        except Exception as e:
            print(f"Warning: Failed to remove image {img}: {e}")
