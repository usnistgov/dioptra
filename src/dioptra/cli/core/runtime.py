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
"""Runtime operations on installed deployments: start, stop, status.

These functions sit between the CLI and the docker/deployments layers,
resolving deployment names, looking up paths and compose overrides, and
invoke docker compose commands.
"""

from dioptra.cli.core import deployments, docker


def start(name: str | None, verbose: bool = False) -> None:
    """Start a deployment via `docker compose up -d`.

    Name may be None if exactly one deployment is registered. Honors the
    docker_compose_path override stored at install time.
    """
    name = deployments.resolve_existing_deployment_name(name)
    record = deployments.get_deployment_record(name)
    path = deployments.get_deployment_path(name, override=None)
    compose_str = record.get("docker_compose_path")

    docker.compose_up(path, compose_str=compose_str, verbose=verbose)


def stop(name: str | None, verbose: bool = False) -> None:
    """Stop a deployment via `docker compose down --remove-orphans`.

    Name may be None if exactly one deployment is registered. Honors the
    docker_compose_path override stored at install time.
    """
    name = deployments.resolve_existing_deployment_name(name)
    record = deployments.get_deployment_record(name)
    path = deployments.get_deployment_path(name, override=None)
    compose_str = record.get("docker_compose_path")

    docker.compose_down(path, compose_str=compose_str, verbose=verbose)


def status(name: str | None) -> dict:
    """Return detailed status info for a deployment.

    Resolves the name (single-deployment shortcut allowed), then returns
    the dict produced by deployments.get_detailed_status. Caller handles
    formatting and presentation.

    Raises if the deployment isn't registered or can't be queried.
    """
    name = deployments.resolve_existing_deployment_name(name)
    return deployments.get_detailed_status(name)
