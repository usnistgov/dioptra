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
"""Registry, manifest, and status tracking for Dioptra deployments.

This module is the source of truth for "what deployments does Dioptra know
about." It manages two stores:

* The registry (~/.config/dioptra-platform/deployments.yml): a single YAML
  file mapping deployment names to their metadata (path, image tag,
  resources, etc.). Read on every CLI command that needs to list, find, or
  identify deployments.

* The per-deployment manifest (<deployment>/manifest.json): a snapshot of
  what was installed, written at install time and read for detailed
  status, resource enumeration, and orphan detection.

Status is reported in two layers:

* Lifecycle status answers "does this deployment look properly installed
  on disk" - checks for the registry entry, marker file, manifest, and
  compose file.

* Deployment status combines lifecycle with runtime info from docker
  (running, stopped, degraded) when the lifecycle is healthy.
"""

import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict

import yaml

from dioptra.cli.core import docker

DEFAULT_BASE_DIR = Path.home() / ".config" / "dioptra-platform" / "deployments"
CONFIG_DIR = Path.home() / ".config" / "dioptra-platform"
REGISTRY_FILE = CONFIG_DIR / "deployments.yml"

MANIFEST_SCHEMA_VERSION = 1

# Registry record schema (per deployment):
#   path:                str         - deployment directory
#   image_tag:           str         - Docker tag pulled and verified
#   release_version:     str | None  - release the user requested, if any
#   docker_compose_path: str | None  - override for docker compose command
#   resources:           dict        - images, volumes, networks (no digests)
#   context:             dict        - cookiecutter render context
#
# Manifest schema (per deployment, at manifest.json):
#   schema_version:      int         - MANIFEST_SCHEMA_VERSION
#   deployment:          dict        - name, path, template_ref, image_tag,
#                                       validation_ref, release_version
#   compose:             dict        - path, command
#   resources:           dict        - images, image_digests, volumes, networks


def get_default_deployments_dir() -> Path:
    """Return the default parent directory for new deployments."""
    return DEFAULT_BASE_DIR


def get_default_config_dir() -> Path:
    """Return the directory holding Dioptra's CLI configuration and registry."""
    return CONFIG_DIR


# --- Registry I/O -----------------------------------------------------------


def _ensure_registry() -> None:
    """Create the config dir and an empty registry file if neither exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "w") as f:
            yaml.safe_dump({"deployments": {}}, f)


def _read_registry() -> dict[str, Any]:
    """Load and return the registry, initializing it if needed."""
    _ensure_registry()
    with open(REGISTRY_FILE) as f:
        data: dict[str, Any] = yaml.safe_load(f) or {"deployments": {}}
        return data


def _write_registry(data: Dict[str, Any]) -> None:
    """Write the registry to disk."""
    with open(REGISTRY_FILE, "w") as f:
        yaml.safe_dump(data, f)


# --- Deployment registration -----------------------------------------------


def deployment_exists(name: str) -> bool:
    """Return True if a deployment with this name is registered."""
    registry = _read_registry()
    return name in registry["deployments"]


def get_deployment_record(name: str) -> dict:
    """Return the full registry record for a deployment.

    Raises ValueError if the deployment isn't registered.
    """
    record: dict[str, Any] = _read_registry()["deployments"].get(name)
    if not record:
        raise ValueError(f"Deployment '{name}' is not registered.")
    return record


def get_deployment_path(name: str, override: str | None = None) -> Path:
    """Return the on-disk path of a deployment.

    If override is provided, returns it (expanded) without consulting the
    registry - useful for commands that take a --dir flag and don't need a
    registered deployment. Otherwise, looks up the deployment by name and
    returns its registered path.
    """
    if override:
        return Path(override).expanduser()

    record = get_deployment_record(name)
    return Path(record["path"]).expanduser()


def register_deployment(
    name: str,
    path: Path,
    image_tag: str,
    release_version: str | None,
    resources: dict,
    docker_compose_path: str | None = None,
    context: dict | None = None,
) -> None:
    """Add a new deployment to the registry and write its on-disk marker.

    Raises ValueError if a deployment with this name is already registered.
    The marker file (.dioptra-deployment) is what later commands use to
    distinguish a Dioptra-managed directory from arbitrary user files.
    """
    registry = _read_registry()

    if name in registry["deployments"]:
        raise ValueError(f"Deployment '{name}' already exists.")

    registry["deployments"][name] = {
        "path": str(path),
        "image_tag": image_tag,
        "release_version": release_version,
        "docker_compose_path": docker_compose_path,
        "resources": resources,
        "context": context or {},
    }

    (path / ".dioptra-deployment").write_text(
        json.dumps(
            {
                "name": name,
                "image_tag": image_tag,
                "release_version": release_version,
                "installed_at": datetime.datetime.now(datetime.UTC).isoformat(),
            }
        )
    )

    _write_registry(registry)


def update_deployment_record(name: str, record: dict) -> None:
    """Update an existing deployment's registry record in place.

    Used by the updater when a container upgrade changes the image_tag
    or resource set. Raises ValueError if the deployment isn't registered.
    """
    registry = _read_registry()
    if name not in registry["deployments"]:
        raise ValueError(f"Deployment '{name}' not found.")
    registry["deployments"][name] = record
    _write_registry(registry)


def unregister_deployment(name: str) -> None:
    """Remove a deployment from the registry.

    Raises ValueError if the deployment isn't registered.
    """
    registry = _read_registry()

    if name not in registry["deployments"]:
        raise ValueError(f"Deployment '{name}' not found.")

    del registry["deployments"][name]
    _write_registry(registry)


# --- Name resolution -------------------------------------------------------


def resolve_new_deployment_name(name: str | None, force: bool) -> str:
    """Resolve a deployment name for a new install.

    If name is given, returns it stripped. If omitted, falls back to:
      - "default" when no deployments exist
      - the lone existing deployment's name (when --force is set, for overwrite)
      - raises ValueError otherwise
    """
    if name:
        return name.strip()

    registry = _read_registry()
    deployments = registry["deployments"]

    if not deployments:
        return "default"

    if force and len(deployments) == 1:
        return str(next(iter(deployments.keys())))

    raise ValueError(
        "A deployment already exists. Please specify a name for the new deployment."
    )


def resolve_existing_deployment_name(name: str | None) -> str:
    """Resolve an existing deployment name.

    If name is given, returns it. If omitted and exactly one deployment is
    registered, returns that one's name. Raises ValueError if there are
    none, or if there are multiple and no name was specified.
    """
    if name:
        return name

    registry = _read_registry()
    deployments = registry["deployments"]

    if not deployments:
        raise ValueError("No deployments found.")

    if len(deployments) == 1:
        return str(next(iter(deployments.keys())))

    raise ValueError("Multiple deployments exist. Please specify a deployment name.")


def normalize_deployment_slug(name: str) -> str:
    """Convert a deployment name into a filesystem-safe slug.

    Collapses whitespace to hyphens.
    """
    name = name.strip()
    name = re.sub(r"\s+", "-", name)
    return name


def deployment_slug_exists(slug: str) -> bool:
    """Return True if any registered deployment uses this directory slug.

    Used during install to detect collisions where two different deployment
    names would collapse to the same on-disk directory name.
    """
    registry = _read_registry()
    for record in registry["deployments"].values():
        deployment_path = record.get("path")
        if deployment_path and Path(deployment_path).name == slug:
            return True
    return False


# --- Status reporting ------------------------------------------------------


def list_deployments() -> list[dict]:
    """Return a summary of every registered deployment.

    Each entry has: name, path, status, version. Status errors out as
    "error" rather than propagating exceptions so the listing doesn't
    fail on a bad deployment.
    """
    registry = _read_registry()
    found = []

    for name, record in registry["deployments"].items():
        path = Path(record["path"])
        try:
            status = get_deployment_status(name)
        except Exception:
            status = "error"

        version = record.get("image_tag", "-")

        found.append(
            {
                "name": name,
                "path": path,
                "status": status,
                "version": version,
            }
        )

    return found


def get_deployment_status(name: str) -> str:
    """Return the combined lifecycle + runtime status of a deployment.

    If lifecycle status indicates the deployment isn't fully installed,
    returns that lifecycle state. Otherwise, queries docker for runtime
    state and maps it to user-facing labels ('running', 'stopped',
    'degraded', or 'unknown').
    """
    lifecycle = get_lifecycle_status(name)
    if lifecycle != "installed":
        return lifecycle

    record = get_deployment_record(name)
    path = Path(record["path"]).expanduser()
    compose_str = record.get("docker_compose_path")

    runtime = docker.get_status(path, compose_str)

    if runtime == "running":
        return "running"
    if runtime == "partially running":
        return "degraded"
    if runtime == "stopped":
        return "stopped"
    if not path.exists():
        return "missing"
    return "unknown"


def get_lifecycle_status(name: str) -> str:
    """Return the on-disk lifecycle state of a deployment.

    Walks a series of expected artifacts and returns the first thing that's
    missing or wrong:
      - "missing":    deployment directory doesn't exist
      - "unmanaged":  directory exists but isn't a Dioptra deployment
      - "partial":    marker present but manifest is missing
      - "broken":     manifest present but compose file is missing
      - "installed":  all expected artifacts present
    """
    record = get_deployment_record(name)
    path = Path(record["path"]).expanduser()

    if not path.exists():
        return "missing"
    if not (path / ".dioptra-deployment").exists():
        return "unmanaged"
    if not (path / "manifest.json").exists():
        return "partial"
    if not (path / "docker-compose.yml").exists():
        return "broken"
    return "installed"


def get_detailed_status(name: str) -> dict:
    """Return detailed info about a deployment for the `status` command.

    Includes the basic status plus resource enumeration (images split into
    internal/external, volumes, networks). Resources are sourced from the
    manifest if available, falling back to live docker compose or additionally
    to the registry record.
    """
    record = get_deployment_record(name)
    path = Path(record["path"]).expanduser()
    compose_str = record.get("docker_compose_path")

    status = get_deployment_status(name)

    result = {
        "name": name,
        "path": path,
        "status": status,
    }

    if status == "missing":
        return result

    resources = None
    image_digests = None

    manifest = read_manifest(path)
    if manifest:
        resources = manifest.get("resources")
        image_digests = (manifest.get("resources") or {}).get("image_digests")
    if not resources:
        try:
            resources = docker.get_compose_resources(path, compose_str)
        except Exception:
            pass
    if not resources:
        resources = record.get("resources", {})

    normalized = normalize_resources(resources)
    result.update(
        {
            "images": normalized["images"],
            "internal": normalized["internal"],
            "external": normalized["external"],
            "volumes": normalized["volumes"],
            "networks": normalized["networks"],
            "image_digests": image_digests or {},
        }
    )
    return result


# --- Manifest I/O ----------------------------------------------------------


def write_manifest(path: Path, data: dict) -> None:
    """Write the deployment manifest into the deployment directory."""
    manifest_path = path / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def read_manifest(path: Path) -> dict | None:
    """Read the deployment manifest, returning None if it doesn't exist."""
    manifest_file = path / "manifest.json"
    if not manifest_file.exists():
        return None
    with open(manifest_file) as f:
        manifest: dict = json.load(f)
        return manifest


def get_all_manifests() -> list[dict]:
    """Read every deployment's manifest, skipping those that fail to load."""
    manifests = []
    for deployment in list_deployments():
        path = deployment["path"]
        try:
            manifest = read_manifest(path)
            if manifest:
                manifests.append(manifest)
        except Exception:
            continue
    return manifests


# --- Resource enumeration --------------------------------------------------


def normalize_resources(resources: dict) -> dict:
    """Flatten the nested 'resources' dict into a uniform structure.

    Input shape:  {images: {internal: [...], external: [...]}, volumes: [...], networks: [...]}
    Output shape: {internal: [...], external: [...], images: [...combined...],
                   volumes: [...], networks: [...]}

    Tolerates missing keys at any level by returning empty lists.
    """
    images = resources.get("images", {})
    internal = images.get("internal", [])
    external = images.get("external", [])

    return {
        "internal": internal,
        "external": external,
        "images": internal + external,
        "volumes": resources.get("volumes", []),
        "networks": resources.get("networks", []),
    }


def get_manifest_resources(path: Path) -> dict:
    """Return the resources block from a deployment's manifest.

    Returns an empty structure if the manifest is missing. The returned
    shape matches what's stored in the manifest (nested 'images') - pass
    through normalize_resources for a flattened structure.
    """
    manifest = read_manifest(path)
    if not manifest:
        return {
            "images": {"internal": [], "external": []},
            "volumes": [],
            "networks": [],
        }
    return {
        "images": manifest["resources"].get("images", []),
        "volumes": manifest["resources"].get("volumes", []),
        "networks": manifest["resources"].get("networks", []),
    }


def get_registry_resources() -> dict:
    """Return the union of all resources known to the registry.

    Combines images, volumes, and networks across every registered
    deployment. Used by orphan-detection to compare what the registry
    thinks exists against what the live manifests reference.
    """
    registry = _read_registry()
    all_resources: dict[str, set[str]] = {
        "images": set(),
        "volumes": set(),
        "networks": set(),
    }

    for record in registry["deployments"].values():
        normalized = normalize_resources(record.get("resources", {}))
        all_resources["images"].update(normalized["images"])
        all_resources["volumes"].update(normalized["volumes"])
        all_resources["networks"].update(normalized["networks"])

    return {k: sorted(v) for k, v in all_resources.items()}


def get_all_manifest_resources(verbose: bool = False) -> dict:
    """Return the union of all resources referenced by deployment manifests.

    Skips deployments whose on-disk state is invalid (no manifest or marker).
    Used together with get_registry_resources to find orphans.
    """
    registry = _read_registry()
    all_resources: dict[str, set[str]] = {
        "images": set(),
        "volumes": set(),
        "networks": set(),
    }

    for name, record in registry["deployments"].items():
        path = Path(record["path"]).expanduser()
        if not is_deployment_valid(path):
            if verbose:
                print(f"Found invalid deployment: {name}")
            continue

        normalized = normalize_resources(get_manifest_resources(path))
        all_resources["images"].update(normalized["images"])
        all_resources["volumes"].update(normalized["volumes"])
        all_resources["networks"].update(normalized["networks"])

    return {k: sorted(v) for k, v in all_resources.items()}


def find_orphaned_resources(verbose: bool = False) -> dict:
    """Return resources known to the registry but not referenced by any manifest.

    A resource becomes orphaned when its deployment's directory has been
    removed (leaving the registry entry without a referencing manifest).
    """
    registry_resources = get_registry_resources()
    manifest_resources = get_all_manifest_resources(verbose=verbose)

    return {
        "images": sorted(
            set(registry_resources["images"]) - set(manifest_resources["images"])
        ),
        "volumes": sorted(
            set(registry_resources["volumes"]) - set(manifest_resources["volumes"])
        ),
        "networks": sorted(
            set(registry_resources["networks"]) - set(manifest_resources["networks"])
        ),
    }


def get_resource_references(
    exclude_deployment: str | None = None,
) -> dict[str, dict[str, set[str]]]:
    """Build a reverse-lookup of which deployments reference each resource.

    Returns {"images": {image: {deployment_names}}, "volumes": {...}, "networks": {...}}.
    Used by the uninstaller to determine which resources are safe to remove
    versus which are still in use by other deployments. Pass exclude_deployment
    to skip the deployment being uninstalled.
    """
    registry = _read_registry()
    refs: dict[str, dict[str, set[str]]] = {
        "images": {},
        "volumes": {},
        "networks": {},
    }

    for name, record in registry["deployments"].items():
        if exclude_deployment and name == exclude_deployment:
            continue

        path = Path(record["path"]).expanduser()
        if not is_deployment_valid(path):
            continue

        normalized = normalize_resources(get_manifest_resources(path))

        for img in normalized["internal"] + normalized["external"]:
            refs["images"].setdefault(img, set()).add(name)
        for vol in normalized["volumes"]:
            refs["volumes"].setdefault(vol, set()).add(name)
        for net in normalized["networks"]:
            refs["networks"].setdefault(net, set()).add(name)

    return refs


# --- Validation ------------------------------------------------------------


def is_deployment_valid(path: Path) -> bool:
    """Return True if path looks like a complete Dioptra deployment.

    Requires the directory to exist with both the marker file and a manifest.
    """
    return (
        path.exists()
        and (path / ".dioptra-deployment").exists()
        and (path / "manifest.json").exists()
    )


def validate_deployment_removal(path: Path, force: bool = False) -> None:
    """Raise if removing path looks risky, unless force is set.

    Don't proceed if the path is a symlink or if there's no .dioptra-deployment
    marker.
    """
    if not path.exists():
        return  # caller handles missing path

    if path.is_symlink() and not force:
        raise RuntimeError(f"{path} is a symlink. Aborting. Use --force to override.")

    if not (path / ".dioptra-deployment").exists() and not force:
        raise RuntimeError(
            f"{path} does not appear to be a dioptra deployment. Aborting. "
            "Use --force to delete anyways."
        )
