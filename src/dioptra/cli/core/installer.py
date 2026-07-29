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
"""Install orchestration for Dioptra deployments.

The install flow has several phases that can each fail independently:

1. Resolve user intent into a concrete InstallSelection (refs, image tag, etc.)
2. Set up the installer venv (cruft + cookiecutter)
3. Resolve deployment naming and check for conflicts
4. Render the template via cruft (dev) or cookiecutter (package install)
5. Enumerate resources, validate images, pull
6. Register the deployment and write its on-disk marker
7. Install any cert, create the deployment venv, run init-deployment.sh
8. Write the manifest

Phases 4-7 are wrapped in a try/except that removes the deployment directory
on failure to avoid leaving partial state. Registration intentionally happens
before init-deployment.sh so that a failure during init leaves the deployment
in a queryable 'partial' or 'broken' lifecycle state.
"""

import dataclasses
import importlib.metadata
import os
import shutil
import sys
from pathlib import Path

from packaging.version import Version

from dioptra.cli.core import (
    cruft,
    deployments,
    docker,
    process,
    templates,
    uninstaller,
    validation,
)

DEFAULT_TEMPLATE_REF = None
DEFAULT_VALIDATION_REF = "main"
DEFAULT_INIT_REF = "main"

INSTALLER_VENV_NAME = "installer-venv"
INSTALLER_VENV_VERSION = "1"
CRUFT_VERSION = "2.16.0"
COOKIECUTTER_VERSION = "2.6.0"


COMPOSE_PRE_INIT_VARS = [
    "CONTAINER_TAG",
    "MINIO_ROOT_USER",
    "MINIO_ROOT_PASSWORD",
    "MINIO_KMS_SECRET_KEY",
    "MLFLOW_TRACKING_AWS_ACCESS_KEY_ID",
    "MLFLOW_TRACKING_AWS_SECRET_ACCESS_KEY",
    "DIOPTRA_MLFLOW_TRACKING_DATABASE_URI",
    "POSTGRES_USER_DIOPTRA_PASSWORD",
    "PGADMIN_DEFAULT_PASSWORD",
    "RESTAPI_AWS_ACCESS_KEY_ID",
    "RESTAPI_AWS_SECRET_ACCESS_KEY",
    "DIOPTRA_RESTAPI_DATABASE_URI",
    "DIOPTRA_WORKER_USERNAME",
    "DIOPTRA_WORKER_PASSWORD",
    "WORKER_AWS_ACCESS_KEY_ID",
    "WORKER_AWS_SECRET_ACCESS_KEY",
]


def _build_pre_init_env(image_tag: str) -> dict:
    """Environment overlay for compose commands before .env is generated.

    docker compose warns whenever it references an unset variable during
    config/pull runs. Set all known runtime variables to empty (except
    CONTAINER_TAG, which must be real for image resolution) to keep pre-init
    output clean. Values only matter at container runtime, not at pull time.
    """
    env = os.environ.copy()
    for var in COMPOSE_PRE_INIT_VARS:
        env.setdefault(var, "")
    env["CONTAINER_TAG"] = image_tag
    return env


@dataclasses.dataclass(frozen=True)
class InstallSelection:
    """Resolved set of identifiers and tags that drive a single install.

    A Dioptra install pulls from several independent sources, each with
    different constraints on what kind of reference it accepts. We keep
    them as separate fields rather than a single 'branch' because conflating
    them silently breaks dev installs (local SHAs aren't on the remote,
    git clone -b rejects SHAs, etc).
    """

    # Git ref used by cruft to render the deployment template.
    # Read from the LOCAL repo, so accepts anything `git checkout` accepts:
    # branches, tags, or SHAs. None during selection means "use current HEAD
    # if in a dev checkout, otherwise main" - resolved in install() before use.
    template_ref: str | None

    # Docker tag pulled by `docker compose pull` and verified by cosign.
    # Must correspond to a published, signed image in the registry.
    # Derived from (in order of precedence) --image-tag, --version, or the
    # dioptra-platform package version; dev package versions fall back to "dev".
    image_tag: str

    # Git ref used to fetch verify.json and the cosign public key from
    # raw.githubusercontent.com. Must exist on the REMOTE. Defaults to "main"
    # since validation artifacts are release-managed, not per-commit.
    validation_ref: str

    # Git ref passed to init-deployment.sh, which runs `git clone -b <ref>`
    # against the remote. Must be a remote-resolvable BRANCH OR TAG -
    # `git clone -b` rejects commit SHAs. Defaults to "main".
    init_ref: str

    # The --version argument, normalized. Stored separately from
    # image_tag because version is user intent ("install 1.1.0") while
    # image_tag is the concrete identifier sent to the registry.
    version: str | None


def install(
    name: str,
    directory: str | None,
    template_ref: str | None = None,
    validation_ref: str | None = None,
    init_ref: str | None = None,
    version: str | None = None,
    image_tag: str | None = None,
    skip_image_validation: bool = False,
    docker_compose_path: str | None = None,
    datasets_dir: str | None = None,
    cert: str | None = None,
    force: bool = False,
    verbose: bool = False,
):
    """Install a new Dioptra deployment end-to-end.

    Returns the resolved deployment name (which may differ from `name` if
    the user omitted it and auto-naming kicked in).

    Raises RuntimeError or ValueError if any phase fails. On failure after
    template rendering, attempts to remove the deployment directory; the
    registry entry, if written, may be left behind for the user to inspect
    or clean up via `dioptra-platform clean`.
    """
    if not docker.is_docker_available():
        raise RuntimeError(
            "Could not detect an active Docker instance. Aborting installation."
        )

    if template_ref is not None and not templates.is_dev_checkout():
        raise RuntimeError(
            "--template-ref is only supported when running dioptra-platform "
            "from a development checkout. With a pip-installed package, the "
            "templates bundled with the installed version are used."
        )

    # Validate cert before any side effects so a bad cert doesn't leave
    # a partial install behind
    cert_src = validation.validate_cert(cert) if cert else None

    selection = resolve_install_selection(
        template_ref=template_ref,
        validation_ref=validation_ref,
        init_ref=init_ref,
        version=version,
        image_tag=image_tag,
    )

    # If no template ref was specified and we're in a dev checkout, resolve
    # to the current git HEAD.
    # In package-install mode, template_ref stays None and cruft.create
    # routes through the package data path instead.
    if selection.template_ref is None and templates.is_dev_checkout():
        selection = dataclasses.replace(
            selection,
            template_ref=templates.get_current_git_ref(),
        )

    if directory:
        base_path = Path(directory).expanduser()
    else:
        base_path = deployments.get_default_deployments_dir()
    base_path.mkdir(parents=True, exist_ok=True)

    installer_venv = ensure_installer_venv(
        deployments.get_default_config_dir(),
        verbose=verbose,
    )
    cruft_bin = get_venv_bin(installer_venv, "cruft")
    cookiecutter_bin = get_venv_bin(installer_venv, "cookiecutter")

    resolved_deployment_name = deployments.resolve_new_deployment_name(
        name,
        force,
    )
    slug = deployments.normalize_deployment_slug(resolved_deployment_name)

    _check_for_name_collisions(resolved_deployment_name, slug, force, verbose)

    deployment_path = base_path / slug
    _ensure_clean_target_directory(deployment_path, force, verbose)

    context = templates.build_context(
        name=resolved_deployment_name,
        branch=selection.template_ref,
        container_tag=selection.image_tag,
        docker_compose_path=docker_compose_path,
        datasets_dir=datasets_dir,
    )

    _print_install_summary(selection, deployment_path, verbose)

    resolved_compose_path, _ = docker.resolve_compose_cmd(docker_compose_path)

    # Phases 4-7: any failure removes the deployment directory.
    try:
        cruft.create(
            output_dir=base_path,
            context=context,
            cruft_bin=cruft_bin,
            cookiecutter_bin=cookiecutter_bin,
            branch=selection.template_ref,
            verbose=verbose,
        )

        if not deployment_path.exists():
            raise RuntimeError(
                f"Expected deployment directory not found: {deployment_path}"
            )

        pull_env = _build_pre_init_env(selection.image_tag)

        resources = docker.get_compose_resources(
            deployment_path, docker_compose_path, env=pull_env
        )
        normalized = deployments.normalize_resources(resources)
        internal_images = normalized["internal"]
        external_images = normalized["external"]

        _validate_images(
            internal_images,
            external_images,
            validation_ref=selection.validation_ref,
            skip=skip_image_validation,
            verbose=verbose,
        )

        print("Running docker compose pull...")
        docker.compose_pull(
            deployment_path,
            docker_compose_path,
            verbose=verbose,
            env=pull_env,
        )

        print("\nPulled image digests:")
        image_digests = docker.get_image_digests(internal_images + external_images)
        print(docker.format_image_digests(image_digests))

        try:
            deployments.register_deployment(
                name=resolved_deployment_name,
                path=deployment_path,
                image_tag=selection.image_tag,
                release_version=selection.version,
                docker_compose_path=resolved_compose_path,
                resources=resources,
                context=context,
            )
        except Exception as e:
            if verbose:
                print(f"Registration failed, cleaning up directory: {e}")
            shutil.rmtree(deployment_path, ignore_errors=True)
            raise

        if cert_src:
            cert_dest = validation.install_cert(cert_src, deployment_path)
            if verbose:
                print(f"Installed certificate: {cert_dest}")

        deployment_venv = deployment_path / ".venv"
        create_venv(deployment_venv, verbose=verbose)

        print("Running the init-deployment script...")
        run_init_deployment(
            deployment_path,
            deployment_venv,
            selection.init_ref,
            verbose=verbose,
        )
    except Exception:
        # Cleanup leftover dir on any failure. Registry entry, if any,
        # is intentionally left for `dioptra-platform clean` to discover.
        if deployment_path.exists():
            shutil.rmtree(deployment_path, ignore_errors=True)
        raise

    manifest = _build_manifest(
        resolved_deployment_name,
        deployment_path,
        selection,
        resolved_compose_path,
        internal_images,
        external_images,
        resources,
        image_digests,
    )
    deployments.write_manifest(deployment_path, manifest)

    return resolved_deployment_name


# --- Pre-flight helpers ----------------------------------------------------


def _check_for_name_collisions(
    name: str,
    slug: str,
    force: bool,
    verbose: bool,
) -> None:
    """Reject collisions between deployment name, slug, and existing state.

    Slug collision is checked first because a name with whitespace may
    collapse onto an existing on-disk directory even if the name itself
    is unique.
    """
    slug_collision = deployments.deployment_slug_exists(
        slug
    ) and not deployments.deployment_exists(name)
    if slug_collision:
        raise RuntimeError(
            f"Deployment would use the identifier '{slug}' "
            "which conflicts with an existing deployment/path."
        )

    if not deployments.deployment_exists(name):
        return

    if not force:
        raise RuntimeError(
            f"Deployment '{name}' already exists.\n"
            "Use --force to overwrite or specify a different name."
        )

    if verbose:
        print(f"Overwriting deployment '{name}'")

    plan = uninstaller.plan_uninstall(
        name=name,
        remove_images=False,
        include_external=False,
        verbose=verbose,
    )
    if not plan:
        raise RuntimeError(
            f"Encountered an error while preparing to uninstall '{name}'. Aborting."
        )
    uninstaller.execute_uninstall(plan, verbose=verbose, force=True)


def _ensure_clean_target_directory(
    path: Path,
    force: bool,
    verbose: bool,
) -> None:
    """Make sure the target directory exists and is empty, or rejects/clears it.

    An empty existing directory is fine. A non-empty one requires --force,
    and additionally passes through validate_deployment_removal as a sanity
    check against accidentally clobbering user files.
    """
    if not path.exists():
        return
    if not any(path.iterdir()):
        return

    if not force:
        raise RuntimeError(
            f"Target deployment directory already exists and is not empty: {path}\n"
            "Use --force to overwrite or specify a different name."
        )

    deployments.validate_deployment_removal(path, force=True)

    if verbose:
        print(f"Removing existing directory: {path}")
    shutil.rmtree(path)


def _validate_images(
    internal_images: list[str],
    external_images: list[str],
    validation_ref: str,
    skip: bool,
    verbose: bool,
) -> None:
    """Run cosign verification on internal images, log external ones."""
    if not validation.is_cosign_available():
        print("Warning: cosign not found. Skipping image verification.")
        return

    if skip:
        if verbose:
            print("Skipping validation for Dioptra images")
    else:
        validation.validate_internal_images(
            internal_images,
            branch=validation_ref,
            verbose=verbose,
        )

    for img in external_images:
        if verbose:
            print(f"Using external image: {img}")


def _print_install_summary(selection, deployment_path, verbose):
    """Print a short summary of what's about to be installed."""
    print(f"Installing Dioptra to '{deployment_path}'")
    print(f"  Version:        {selection.version or selection.image_tag}")
    print(f"  Image tag:      {selection.image_tag}")
    print(f"  Init ref:       {selection.init_ref}")
    if verbose:
        print(f"  Template ref:   {selection.template_ref}")
        print(f"  Validation ref: {selection.validation_ref}")


def _build_manifest(
    name,
    deployment_path,
    selection,
    resolved_compose_path,
    internal_images,
    external_images,
    resources,
    image_digests,
) -> dict:
    """Assemble the manifest dict for a deployment directory."""
    return {
        "schema_version": deployments.MANIFEST_SCHEMA_VERSION,
        "deployment": {
            "name": name,
            "path": str(deployment_path),
            "template_ref": selection.template_ref,
            "image_tag": selection.image_tag,
            "validation_ref": selection.validation_ref,
            "release_version": selection.version,
        },
        "compose": {
            "path": "docker-compose.yml",
            "command": resolved_compose_path,
        },
        "resources": {
            "images": {
                "internal": sorted(internal_images),
                "external": sorted(external_images),
            },
            "image_digests": image_digests,
            "volumes": resources["volumes"],
            "networks": resources["networks"],
        },
    }


# --- Selection resolution --------------------------------------------------


def resolve_install_selection(
    template_ref: str | None,
    validation_ref: str | None,
    init_ref: str | None,
    version: str | None,
    image_tag: str | None,
) -> InstallSelection:
    """Convert raw CLI args into a concrete InstallSelection.

    Default-resolution rules:
      - template_ref: passes through; install() may further resolve None to
        the current git HEAD in dev mode.
      - validation_ref / init_ref: fall back to "main" if not provided.
      - image_tag: explicit --image-tag wins, else --version, else the
        installed dioptra-platform package version (with "dev" fallback for
        versions without published images).
    """
    resolved_template_ref = template_ref or DEFAULT_TEMPLATE_REF
    resolved_validation_ref = validation_ref or DEFAULT_VALIDATION_REF
    resolved_init_ref = init_ref or DEFAULT_INIT_REF
    resolved_version = (
        normalize_release_version(version) if version is not None else None
    )

    if image_tag:
        resolved_image_tag = image_tag.strip()
    elif resolved_version:
        resolved_image_tag = resolved_version
    else:
        pkg_version = get_version()
        try:
            parsed = Version(pkg_version)
        except Exception:
            parsed = None
        if parsed is not None and (parsed.is_devrelease or parsed.is_prerelease):
            resolved_image_tag = "dev"
        else:
            resolved_image_tag = pkg_version

    if not resolved_image_tag:
        raise RuntimeError(
            "Could not determine Dioptra image tag. "
            "Pass --version or --image-tag explicitly."
        )

    return InstallSelection(
        template_ref=resolved_template_ref,
        image_tag=resolved_image_tag,
        validation_ref=resolved_validation_ref,
        init_ref=resolved_init_ref,
        version=resolved_version,
    )


def normalize_release_version(version: str) -> str:
    """Validate and clean a --version argument.

    Rejects empty strings and leading 'v' prefixes, both of which are
    common user mistakes that would produce confusing downstream errors.

    Also rejects strings containing '-', which is exclusively used to denote
    container build versions.
    """
    normalized = version.strip()
    if not normalized:
        raise RuntimeError("Version cannot be empty.")
    if normalized.startswith("v"):
        raise RuntimeError(
            "Dioptra release versions should be specified without a leading 'v', "
            f"for example '1.2.3', not '{version}'."
        )
    if "-" in normalized:
        raise RuntimeError(
            f"--version is for Python release versions (e.g., '1.1.0'); "
            f"got '{version}'. Use --image-tag for specific container builds."
        )
    return normalized


# --- init-deployment.sh wrapper -------------------------------------------


def run_init_deployment(
    path: Path,
    deployment_venv: Path,
    branch: str,
    verbose: bool = False,
) -> None:
    """Run the deployment's init-deployment.sh script.

    The script expects to find a python venv with jinja2 installed on its
    PATH; we install jinja2 into the deployment's venv first. The script
    itself handles cert installation (no-op when no certs are present) and
    other one-time setup operations.
    """
    init_deployment_path = path / "init-deployment.sh"
    if not init_deployment_path.exists():
        raise RuntimeError(f"init-deployment.sh not found at {init_deployment_path}")

    env = os.environ.copy()
    venv_bin = get_venv_bin(deployment_venv, "")
    env["PATH"] = f"{venv_bin}:{env['PATH']}"
    env["VIRTUAL_ENV"] = str(deployment_venv)

    deployment_pip = get_venv_bin(deployment_venv, "pip")
    process.run(
        [str(deployment_pip), "install", "jinja2==3.1.6"],
        verbose=verbose,
        stream_output=verbose,
    )

    cmd = ["bash", str(init_deployment_path), "--branch", branch]
    process.run(
        cmd,
        cwd=path,
        env=env,
        verbose=verbose,
        stream_output=verbose,
    )


# --- Installer venv management --------------------------------------------


def get_version() -> str:
    """Return the installed version of the dioptra-platform package."""
    return importlib.metadata.version("dioptra-platform")


def get_venv_bin(venv_path: Path, executable: str) -> Path:
    """Return the path to an executable in a venv's bin/ directory."""
    return venv_path / "bin" / executable


def create_venv(path: Path, verbose: bool = False) -> None:
    """Create a fresh Python venv at the given path."""
    if verbose:
        print(f"Creating venv at {path}")
    process.run([sys.executable, "-m", "venv", str(path)], verbose=verbose)


def ensure_installer_venv(base_path: Path, verbose: bool = False) -> Path:
    """Return the installer venv path, creating or rebuilding as needed.

    The installer venv holds cruft and cookiecutter for template rendering.
    It's rebuilt automatically when INSTALLER_VENV_VERSION changes, which
    lets us bump pinned tool versions and have users pick them up on next
    install without manual cleanup.
    """
    installer_venv = base_path / INSTALLER_VENV_NAME
    version_file = installer_venv / ".installer-version"
    python_bin = get_venv_bin(installer_venv, "python")
    pip_bin = get_venv_bin(installer_venv, "pip")

    rebuild = (
        not python_bin.exists()
        or not version_file.exists()
        or version_file.read_text().strip() != INSTALLER_VENV_VERSION
    )

    if rebuild:
        if installer_venv.exists():
            shutil.rmtree(installer_venv)
        create_venv(installer_venv, verbose=verbose)
        process.run(
            [str(pip_bin), "install", "--upgrade", "pip"],
            verbose=verbose,
            stream_output=verbose,
        )
        process.run(
            [
                str(pip_bin),
                "install",
                f"cruft=={CRUFT_VERSION}",
                f"cookiecutter=={COOKIECUTTER_VERSION}",
            ],
            verbose=verbose,
            stream_output=verbose,
        )
        version_file.write_text(INSTALLER_VENV_VERSION)

    return installer_venv
