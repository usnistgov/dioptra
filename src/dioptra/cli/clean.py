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
"""Clean command support for the Dioptra CLI.

Handles missing deployments and orphaned resources."""

import click

from dioptra.cli.core import deployments, docker, uninstaller


@click.command()
@click.option(
    "--include-external",
    is_flag=True,
    help="Also clean external images (postgres, redis, etc). Off by default "
    "since these may be used by other tools on this host.",
)
@click.option("--verbose", is_flag=True, help="Print detailed output.")
@click.pass_context
def clean(context, verbose, include_external):
    """Clean up Dioptra resources that are no longer in use.

    Identifies two categories:

    1. Missing deployments - registered in Dioptra but whose deployment
       directory has been removed. Their images, volumes, and networks
       will be removed.

    2. Orphaned resources - docker resources Dioptra previously knew about
       but that no current deployment manifest references.

    By default, only Dioptra's own images (those under ghcr.io/usnistgov/dioptra/)
    are eligible for removal. Pass --include-external to also remove third-party
    images Dioptra installed (postgres, redis, minio, pgadmin); however it is possible
    these may be in use by other tools on the host.
    """
    if not docker.is_docker_available():
        click.echo("Error: Docker is not running. Resources cannot be removed.")
        return

    # Gather all cleanup work upfront
    missing_plans = _gather_missing_deployment_plans(
        verbose=verbose,
        include_external=include_external,
    )

    orphans = deployments.find_orphaned_resources(verbose=verbose)
    internal_orphans, external_orphans = docker.split_images(set(orphans["images"]))
    orphan_images = sorted(internal_orphans)
    if include_external:
        orphan_images.extend(sorted(external_orphans))
    orphan_volumes = orphans["volumes"]
    orphan_networks = orphans["networks"]

    have_missing = bool(missing_plans)
    have_orphans = bool(orphan_images or orphan_volumes or orphan_networks)

    if not have_missing and not have_orphans:
        click.echo("No unused Dioptra resources found.")
        if external_orphans and not include_external:
            click.echo(
                f"({len(external_orphans)} external image(s) ignored. "
                "Pass --include-external to clean them.)"
            )
        return

    # Present the plan
    if have_missing:
        click.echo("Missing deployments to remove:")
        for name, plan in missing_plans:
            click.echo(f"  - {name}")
            _print_plan_counts(plan)

    if have_orphans:
        _print_resource_list("Orphaned images", orphan_images)
        _print_resource_list("Orphaned volumes", orphan_volumes)
        _print_resource_list("Orphaned networks", orphan_networks)

    if external_orphans and not include_external:
        click.echo(
            f"\n(Skipping {len(external_orphans)} external image(s). "
            "Pass --include-external to clean them too.)"
        )

    if not click.confirm("\nContinue?", default=False):
        click.echo("Clean aborted.")
        return

    # Execute
    for _name, plan in missing_plans:
        uninstaller.execute_uninstall(plan, verbose=verbose)

    _remove_resources(
        orphan_images,
        orphan_volumes,
        orphan_networks,
        verbose=verbose,
    )


def _gather_missing_deployment_plans(
    verbose: bool,
    include_external: bool,
) -> list[tuple[str, dict]]:
    """Build uninstall plans for every deployment in 'missing' state."""
    missing = [d for d in deployments.list_deployments() if d["status"] == "missing"]
    plans = []
    for deployment in missing:
        name = deployment["name"]
        plan = uninstaller.plan_uninstall(
            name,
            remove_images=True,
            include_external=include_external,
            verbose=verbose,
        )
        if plan:
            plans.append((name, plan))
        else:
            click.echo(f"Unable to build uninstall plan for '{name}'; skipping.")
    return plans


def _print_plan_counts(plan: dict) -> None:
    """Print a short count summary of what an uninstall plan will remove."""
    parts = []
    if plan.get("remove_images"):
        parts.append(f"images: {len(plan['remove_images'])}")
    if plan.get("remove_volumes"):
        parts.append(f"volumes: {len(plan['remove_volumes'])}")
    if plan.get("remove_networks"):
        parts.append(f"networks: {len(plan['remove_networks'])}")
    if parts:
        click.echo(f"      ({', '.join(parts)})")


def _print_resource_list(label: str, items: list[str]) -> None:
    """Print a labeled list of resources, skipping empty sections."""
    if not items:
        return
    click.echo(f"\n{label}:")
    for item in items:
        click.echo(f"  - {item}")


def _remove_resources(
    images: list[str],
    volumes: list[str],
    networks: list[str],
    verbose: bool,
) -> None:
    """Remove the given resources, reporting per-item success or failure."""
    for img in images:
        try:
            docker.remove_image(img)
            click.echo(f"Removed image: {img}")
        except Exception as e:
            click.echo(f"Failed to remove image {img}: {e}")

    for vol in volumes:
        try:
            docker.remove_volume(vol, verbose=verbose)
            click.echo(f"Removed volume: {vol}")
        except Exception as e:
            click.echo(f"Failed to remove volume {vol}: {e}")

    for net in networks:
        try:
            docker.remove_network(net, verbose=verbose)
            click.echo(f"Removed network: {net}")
        except Exception as e:
            click.echo(f"Failed to remove network {net}: {e}")
