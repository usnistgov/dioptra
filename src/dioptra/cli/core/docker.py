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
"""Wrappers around docker and docker compose for the Dioptra CLI.

Most functions are wrappers around shell commands, with a few patterns:

* compose_* functions resolve `docker compose` vs `docker-compose`
* *_exists functions check for existing resources.
* remove_* functions ignore missing resources.

DIOPTRA_IMAGE_PREFIX defines which images count as "internal" (built by
Dioptra) vs "external" (third-party images like postgres, redis).
"""

import shlex
import shutil

import yaml

from dioptra.cli.core import process

DIOPTRA_IMAGE_PREFIX = "ghcr.io/usnistgov/dioptra"

# --- Compose command resolution -------------------------------------------


def resolve_compose_cmd(compose_str: str | None) -> tuple[str, list[str]]:
    """Resolve the docker-compose invocation to use.

    If compose_str is provided (from --docker-compose-path), it's split
    via shlex. Otherwise, prefer modern `docker compose` over legacy
    `docker-compose` if available.

    Returns a tuple of (string form for manifest storage, list form for
    subprocess invocation).

    Raises RuntimeError if neither docker compose nor docker-compose is found.
    """
    if compose_str:
        parts = shlex.split(compose_str)
        return compose_str, parts

    if shutil.which("docker"):
        return "docker compose", ["docker", "compose"]

    if shutil.which("docker-compose"):
        return "docker-compose", ["docker-compose"]

    raise RuntimeError("Neither docker-compose nor docker compose is available.")


# --- Compose operations ---------------------------------------------------


def compose_up(path, compose_str: str | None = None, verbose: bool = False) -> None:
    """Run `docker compose up -d` in the given path."""
    _, compose_cmd = resolve_compose_cmd(compose_str)
    process.run(
        compose_cmd + ["up", "-d"],
        cwd=path,
        verbose=verbose,
        stream_output=verbose,
    )


def compose_down(path, compose_str: str | None = None, verbose: bool = False) -> None:
    """Run `docker compose down --remove-orphans` in the given path."""
    _, compose_cmd = resolve_compose_cmd(compose_str)
    process.run(
        compose_cmd + ["down", "--remove-orphans"],
        cwd=path,
        verbose=verbose,
    )


def compose_pull(
    path,
    compose_str: str | None = None,
    verbose: bool = False,
    env: dict | None = None,
):
    """Run `docker compose pull` in the given path."""
    _, compose_cmd = resolve_compose_cmd(compose_str)
    process.run(
        compose_cmd + ["pull"],
        cwd=path,
        env=env,
        verbose=verbose,
        stream_output=verbose,
    )


def compose_config(
    path,
    compose_str: str | None = None,
    verbose: bool = False,
    env: dict | None = None,
) -> dict:
    """Run `docker compose config` and return the parsed YAML as a dict.

    Checks a compose config with the environment already applied.

    Raises RuntimeError if the output isn't a YAML mapping.
    """
    _, compose_cmd = resolve_compose_cmd(compose_str)

    result = process.run(
        compose_cmd + ["config"],
        cwd=path,
        env=env,
        verbose=verbose,
        capture_output=True,
    )

    config = yaml.safe_load(result.stdout)
    if not isinstance(config, dict):
        raise RuntimeError(f"Invalid docker compose config in {path}")
    return config


# --- Status reporting ------------------------------------------------------


def get_status(path, compose_str: str | None = None) -> str:
    """Return the runtime status of a deployment's containers.

    Returns one of:
      "docker_unavailable" - docker daemon not reachable
      "stopped"            - compose has no containers, or none are running
      "running"            - all containers are running
      "partially running"  - some containers are running, others are not
      "unknown"            - couldn't determine (compose query failed)
    """
    if not is_docker_available():
        return "docker_unavailable"

    _, compose_cmd = resolve_compose_cmd(compose_str)

    try:
        all_result = process.run(
            compose_cmd + ["ps", "-a", "-q"],
            cwd=path,
            capture_output=True,
        )
        all_containers = [c for c in all_result.stdout.strip().splitlines() if c]

        if not all_containers:
            return "stopped"

        running_result = process.run(
            compose_cmd + ["ps", "--status", "running", "-q"],
            cwd=path,
            capture_output=True,
        )
        running_containers = [
            c for c in running_result.stdout.strip().splitlines() if c
        ]

        if len(running_containers) == len(all_containers):
            return "running"
        if running_containers:
            return "partially running"
        return "stopped"

    except Exception:
        return "unknown"


# --- Resource enumeration -------------------------------------------------


def get_compose_resources(
    path,
    compose_str: str | None = None,
    env: dict | None = None,
) -> dict:
    """Enumerate the images, volumes, and networks declared in a compose file.

    Reads the rendered compose config and pulls out:
      - images:   service image references, split into internal/external
                  via DIOPTRA_IMAGE_PREFIX
      - volumes:  named volumes only (bind mounts are ignored), resolved
                  through any 'name:' aliases in the top-level volumes block
      - networks: resolved through 'name:' aliases similarly
    """
    config = compose_config(path, compose_str, env=env)

    images: set[str] = set()
    service_volumes: set[str] = set()

    for service in config.get("services", {}).values():
        if "image" in service:
            images.add(service["image"])

        for vol in service.get("volumes", []):
            if isinstance(vol, dict):
                if vol.get("type") == "volume":
                    source = vol.get("source")
                    if source:
                        service_volumes.add(source)
            elif isinstance(vol, str):
                source = vol.split(":")[0]
                # Skip bind mounts; only track named volumes
                if source.startswith(".") or source.startswith("/"):
                    continue
                if source:
                    service_volumes.add(source)

    # Resolve logical volume names -> actual docker volume names via any
    # 'name:' overrides in the top-level volumes definitions.
    volume_aliases = {
        name: data.get("name", name) for name, data in config.get("volumes", {}).items()
    }
    resolved_volumes = {volume_aliases.get(v, v) for v in service_volumes}

    # Same alias-resolution pattern for networks.
    networks = {
        data.get("name", name) for name, data in config.get("networks", {}).items()
    }

    internal_images, external_images = split_images(images)

    return {
        "images": {
            "internal": sorted(internal_images),
            "external": sorted(external_images),
        },
        "volumes": sorted(resolved_volumes),
        "networks": sorted(networks),
    }


def split_images(images: set[str]) -> tuple[list[str], list[str]]:
    """Partition images into (internal, external) based on DIOPTRA_IMAGE_PREFIX.

    Internal images are those built and signed by Dioptra; external are third-party
    (postgres, redis, etc) installed alongside.
    """
    internal = []
    external = []
    for img in images:
        if img.startswith(DIOPTRA_IMAGE_PREFIX):
            internal.append(img)
        else:
            external.append(img)
    return internal, external


def get_image_digests(images: list[str]) -> dict[str, str]:
    """Return {image_ref: digest} for each image, looked up locally.

    Reads the digest each image was pulled with via `docker image inspect`.
    Images that aren't pulled locally (or can't be inspected) get a value of
    "unavailable" so callers can show what's known.

    The digest format is the full RepoDigest reference:
    "ghcr.io/usnistgov/dioptra/nginx@sha256:abc123...". Callers wanting
    just the sha256 portion can split on "@".
    """
    digests = {}
    for image in images:
        try:
            result = process.run(
                [
                    "docker",
                    "image",
                    "inspect",
                    image,
                    "--format",
                    "{{if .RepoDigests}}{{index .RepoDigests 0}}{{end}}",
                ],
                capture_output=True,
                suppress_output=True,
            )
            digest = (result.stdout or "").strip()
            digests[image] = digest if digest else "unavailable"
        except Exception:
            digests[image] = "unavailable"
    return digests


def format_image_digests(digests: dict[str, str]) -> str:
    """Format a digest dict as a multi-line string for display."""
    lines = []
    for image, digest in digests.items():
        sha = digest.split("@")[1] if "@sha256:" in digest else digest
        lines.append(f"  {image}\n    {sha}")
    return "\n".join(lines)


# --- Existence checks -----------------------------------------------------


def is_docker_available() -> bool:
    """Return True if the docker daemon is reachable."""
    try:
        process.run(["docker", "info"], suppress_output=True)
        return True
    except Exception:
        return False


def volume_exists(volume: str) -> bool:
    """Return True if a docker volume with the given name exists."""
    try:
        process.run(
            ["docker", "volume", "inspect", volume],
            suppress_output=True,
        )
        return True
    except Exception:
        return False


def network_exists(network: str) -> bool:
    """Return True if a docker network with the given name exists."""
    try:
        process.run(
            ["docker", "network", "inspect", network],
            suppress_output=True,
        )
        return True
    except Exception:
        return False


def image_exists(image: str) -> bool:
    """Return True if a docker image with the given tag is present locally."""
    try:
        process.run(
            ["docker", "image", "inspect", image],
            suppress_output=True,
        )
        return True
    except Exception:
        return False


# --- Resource removal -----------------------------------------------------


def remove_volume(volume: str, verbose: bool = False) -> None:
    """Remove a docker volume if it exists; no-op otherwise.

    Silent when verbose is False. Volume removal can fail at the docker
    level (e.g., if a container still uses it) - those errors propagate.
    """
    if not volume_exists(volume):
        if verbose:
            print(f"Cannot delete {volume} - volume does not exist")
        return

    process.run(["docker", "volume", "rm", volume])
    if verbose:
        print(f"Successfully deleted volume: {volume}")


def remove_network(network: str, verbose: bool = False) -> None:
    """Remove a docker network if it exists; no-op otherwise.

    Silent when verbose is False.
    """
    if not network_exists(network):
        if verbose:
            print(f"Cannot delete {network} - network does not exist")
        return

    process.run(["docker", "network", "rm", network])
    if verbose:
        print(f"Successfully deleted network: {network}")


def remove_image(image: str, verbose: bool = False) -> None:
    """Remove a docker image if it exists locally; no-op otherwise.

    Silent when verbose is False.
    """
    if not image_exists(image):
        if verbose:
            print(f"Cannot delete {image} - image does not exist")
        return

    process.run(["docker", "image", "rm", image])
    if verbose:
        print(f"Successfully deleted image: {image}")
