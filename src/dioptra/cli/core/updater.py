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

"""Container update detection and application for Dioptra deployments.

Reads each deployment's current container build from its .env file,
compares against the latest published build (latest_build.json fetched
from GitHub), and either reports the status (update) or applies it
(upgrade) by editing .env and deploying new container versions.

This module depends on a deployment template with container_tag in .env.
"""

from pathlib import Path

from dioptra.cli.core import deployments, docker, http, versions

LATEST_BUILD_FILENAME = "latest_build.json"
ENV_FILENAME = ".env"
CONTAINER_TAG_KEY = "CONTAINER_TAG"

DEFAULT_UPDATE_REF = "main"


def check_update(name: str, ref: str | None = None) -> dict:
    """Check for available updates without applying anything.

    Returns a dict with current state, available state, and a status flag:
      {
        "name": <deployment name>,
        "current_container": <tag from .env, or None>,
        "latest_container": <tag from latest_build.json>,
        "current_python": <installed dioptra-platform version>,
        "latest_python": <python version from latest_build.json>,
        "container_update_available": bool,
        "python_update_available": bool,
        "supported": bool,           # False if .env mechanism not present
        "supported_reason": str,     # explanation when supported=False
      }
    """
    record = deployments.get_deployment_record(name)
    deployment_path = Path(record["path"]).expanduser()

    update_ref = ref or DEFAULT_UPDATE_REF

    current_container = _read_container_tag(deployment_path)
    if current_container is None:
        return {
            "name": name,
            "supported": False,
            "supported_reason": (
                "This deployment was installed before .env-based container "
                "tagging was supported. Reinstall to enable updates."
            ),
        }

    latest = _fetch_latest_build(update_ref)
    latest_container = latest["container_build"]
    latest_python = latest["python_version"]
    current_python = _get_installed_python_version()

    return {
        "name": name,
        "current_container": current_container,
        "latest_container": latest_container,
        "current_python": current_python,
        "latest_python": latest_python,
        "container_update_available": versions.is_newer(
            current_container,
            latest_container,
        ),
        "python_update_available": versions.is_newer(current_python, latest_python),
        "supported": True,
    }


def apply_update(
    name: str,
    ref: str | None = None,
    verbose: bool = False,
) -> dict:
    """Apply an available container update.

    Edits .env with the new container tag, pulls new images, and (if the
    deployment is currently running) recreates containers with the new
    images. Stopped deployments stay stopped; they'll pick up new images
    on the next `dioptra-platform start`. Volumes are preserved regardless.

    On any failure during pull or recreate, the .env is rolled back to
    its previous tag so subsequent operations see a consistent state.

    Does not handle Python-version upgrades; caller should detect that
    case and suggest `pip install --upgrade dioptra-platform`.

    Returns the same dict as check_update, after updating.
    """
    status = check_update(name, ref=ref)
    if not status["supported"]:
        raise RuntimeError(status["supported_reason"])
    if not status["container_update_available"]:
        return status

    record = deployments.get_deployment_record(name)
    deployment_path = Path(record["path"]).expanduser()
    compose_str = record.get("docker_compose_path")

    # Preserve pre-upgrade runtime state
    runtime_status = docker.get_status(deployment_path, compose_str)
    was_running = runtime_status in ("running", "partially running")

    old_tag = status["current_container"]
    new_tag = status["latest_container"]

    _write_container_tag(deployment_path, new_tag)

    try:
        print("Pulling updated images...")
        docker.compose_pull(deployment_path, compose_str, verbose=verbose)

        if was_running:
            print("Recreating containers with new images...")
            docker.compose_up(deployment_path, compose_str, verbose=verbose)
        else:
            print(
                "Deployment was stopped; skipping container start. "
                "Run `dioptra-platform start` to launch with new images."
            )
    except Exception:
        # roll back .env
        _write_container_tag(deployment_path, old_tag)
        raise

    # Capture and show new digests so the user can verify
    resources = docker.get_compose_resources(deployment_path, compose_str)
    all_images = resources["images"]["internal"] + resources["images"]["external"]
    image_digests = docker.get_image_digests(all_images)

    print("\nPost-upgrade image digests:")
    print(docker.format_image_digests(image_digests))

    try:
        _update_manifest_and_registry(
            name,
            deployment_path,
            new_tag,
            resources=resources,
            image_digests=image_digests,
        )
    except Exception as e:
        print(
            f"Warning: containers updated to {new_tag} but registry/manifest "
            f"update failed: {e}. Run `dioptra-platform update` again to refresh."
        )

    return check_update(name, ref=ref)


def _update_manifest_and_registry(
    name: str,
    deployment_path: Path,
    new_tag: str,
    resources: dict,
    image_digests: dict[str, str],
) -> None:
    """Update the manifest and registry to reflect a new container tag.

    Rewrites image tags in both stores so `list` and `status` show the
    current version.
    """
    record = deployments.get_deployment_record(name)

    # Update registry record
    record["image_tag"] = new_tag
    record["resources"] = resources
    if "context" in record and "container_tag" in record["context"]:
        record["context"]["container_tag"] = new_tag
    deployments.update_deployment_record(name, record)

    # Update manifest.
    manifest = deployments.read_manifest(deployment_path)
    if manifest:
        manifest["deployment"]["image_tag"] = new_tag
        manifest["resources"] = resources
        manifest["resources"]["image_digests"] = image_digests
        deployments.write_manifest(deployment_path, manifest)


# --- .env file handling ---------------------------------------------------


def _read_container_tag(deployment_path: Path) -> str | None:
    """Read CONTAINER_TAG from the deployment's .env, or None if absent."""
    env_path = deployment_path / ENV_FILENAME
    if not env_path.exists():
        return None

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == CONTAINER_TAG_KEY:
            return value.strip().strip('"').strip("'")
    return None


def _write_container_tag(deployment_path: Path, new_tag: str) -> None:
    """Update CONTAINER_TAG in the deployment's .env, preserving other lines.

    Use a temp file so we can't corrupt .env with partial state.
    """
    env_path = deployment_path / ENV_FILENAME
    if not env_path.exists():
        raise RuntimeError(f".env not found at {env_path}")

    lines = env_path.read_text().splitlines(keepends=True)
    new_lines = []
    updated = False

    for line in lines:
        stripped = line.strip()
        if (
            not updated
            and stripped
            and not stripped.startswith("#")
            and stripped.split("=", 1)[0].strip() == CONTAINER_TAG_KEY
        ):
            # Preserve trailing newline if original had one
            newline = "\n" if line.endswith("\n") else ""
            new_lines.append(f"{CONTAINER_TAG_KEY}={new_tag}{newline}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        raise RuntimeError(
            f"{CONTAINER_TAG_KEY} not found in {env_path}; cannot update."
        )

    tmp_path = env_path.with_suffix(env_path.suffix + ".tmp")
    tmp_path.write_text("".join(new_lines))
    tmp_path.replace(env_path)


# --- Remote fetch ---------------------------------------------------------


def _fetch_latest_build(ref: str) -> dict:
    """Fetch and validate latest_build.json from the given ref on GitHub.

    Raises RuntimeError if the file is missing required fields.
    """
    data = http.fetch_json(ref, LATEST_BUILD_FILENAME)

    required = ("container_build", "python_version")
    missing = [f for f in required if f not in data]
    if missing:
        raise RuntimeError(
            f"{LATEST_BUILD_FILENAME} from ref '{ref}' missing required "
            f"field(s): {', '.join(missing)}"
        )
    return data


# --- Version comparison ---------------------------------------------------


def _get_installed_python_version() -> str:
    """Return the currently installed dioptra-platform package version."""
    from dioptra.cli.core.installer import get_version

    return get_version()
