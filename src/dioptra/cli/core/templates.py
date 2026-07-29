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
"""Template path resolution and cookiecutter context construction.

Two installation modes are supported, each with a different path-resolution
strategy:

* Dev checkout: the templates live in the local git repo at
  TEMPLATE_SUBDIR_IN_REPO, and cruft renders them after a `git checkout`
  of the desired ref. is_dev_checkout() detects this case.

* Pip-installed package: the templates ship as package data under
  dioptra/cli/cookiecutter-templates/, and cookiecutter renders them
  directly from the installed location.

The TEMPLATE_* constants distinguish these locations:

* TEMPLATE_PACKAGE         - Python package that contains the data dir
                              (used by importlib.resources lookups)
* TEMPLATE_DATA_DIR        - name of the data directory within that package
* TEMPLATE_DIRNAME         - the specific cookiecutter template directory
                              within the data dir
* TEMPLATE_SUBDIR_IN_REPO  - path from the repo root to the same template,
                              used in dev mode where the repo layout matters
"""

from contextlib import contextmanager
from importlib import resources
from pathlib import Path

from dioptra.cli.core import docker, process

TEMPLATE_PACKAGE = "dioptra.cli"
TEMPLATE_DATA_DIR = "cookiecutter-templates"
TEMPLATE_DIRNAME = "cookiecutter-dioptra-deployment"
TEMPLATE_SUBDIR_IN_REPO = (
    "src/dioptra/cli/cookiecutter-templates/cookiecutter-dioptra-deployment"
)


def get_repo_root() -> Path:
    """Return the path to the repository root in dev mode.

    Computed by walking up from this file:
      parents[0] = src/dioptra/cli/core/   (this file's directory)
      parents[1] = src/dioptra/cli/
      parents[2] = src/dioptra/
      parents[3] = src/
      parents[4] = repo root
    """
    return Path(__file__).resolve().parents[4]


def is_dev_checkout() -> bool:
    """Return True if dioptra-platform is running from a git checkout.

    Detects the presence of a .git directory at the computed repo root.
    Used throughout the install flow to choose between cruft and cookiecutter.
    """
    return (get_repo_root() / ".git").is_dir()


def get_template_subdir() -> str:
    """Return the template's subdirectory path within the repo. Dev mode only."""
    return TEMPLATE_SUBDIR_IN_REPO


def get_current_git_ref() -> str:
    """Return the current HEAD commit SHA, or 'main' if not in a git repo.

    The 'main' fallback exists so package-installed users (no git repo) get
    a default ref name when something tries to read this.
    """
    try:
        result = process.run(
            ["git", "rev-parse", "HEAD"],
            cwd=get_repo_root(),
            capture_output=True,
            suppress_output=True,
        )
        return result.stdout.strip()
    except RuntimeError:
        return "main"


@contextmanager
def get_packaged_template_path():
    """Yield a filesystem path to the bundled cookiecutter template.

    Used when running from a pip-installed package.
    """
    ref = (
        resources.files(TEMPLATE_PACKAGE)
        .joinpath(TEMPLATE_DATA_DIR)
        .joinpath(TEMPLATE_DIRNAME)
    )
    with resources.as_file(ref) as path:
        yield path


def build_context(
    name: str,
    docker_compose_path: str | None = None,
    datasets_dir: str | None = None,
    branch: str | None = None,
    container_tag: str | None = None,
) -> dict:
    """Build the cookiecutter context dict for rendering a deployment template.

    The returned dict is passed to cruft/cookiecutter as extra context to
    override cookiecutter.json defaults during template render. Keys here
    must match the variable names declared in cookiecutter.json.

    Notes on individual fields:
      - branch: defaults to "main" inside the context. This is template-side
        information (included in the generated deployment) and is independent
        of the CLI's template_ref, which controls which template version
        cruft checks out.
      - container_tag: only included in the context when the caller provides
        a value. When omitted, cookiecutter.json's default applies (currently
        "dev"). This lets release-version installs override the tag while
        dev installs fall through to the template's own default.
      - docker_compose_path: resolved to a concrete command string here so
        the deployment template can use the right docker compose
        invocation without needing to re-detect it.
    """
    resolved_compose_path, _ = docker.resolve_compose_cmd(docker_compose_path)
    context = {
        "deployment_name": name,
        "branch": branch or "main",
        "datasets_directory": datasets_dir or "",
        "docker_compose_path": resolved_compose_path,
    }
    if container_tag is not None:
        context["container_tag"] = container_tag
    return context
