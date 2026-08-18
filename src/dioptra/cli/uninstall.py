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
"""Uninstall command support for the Dioptra CLI."""

import click

from dioptra.cli.core import deployments, uninstaller


@click.command()
@click.argument("name", required=False)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option(
    "--force",
    is_flag=True,
    help="Override safety checks.",
)
@click.option("--verbose", is_flag=True, help="Print detailed output.")
@click.option(
    "--remove-images",
    is_flag=True,
    help="Remove Dioptra images that are no longer in use after uninstall.",
)
@click.option(
    "--include-external",
    is_flag=True,
    help="Also remove non-Dioptra images (postgres, redis, etc.) "
    "used by this deployment. These may be shared with other tools on the host.",
)
@click.pass_context
def uninstall(
    context,
    name,
    yes,
    force,
    verbose,
    remove_images,
    include_external,
):
    """Remove a Dioptra deployment.

    NAME may be omitted if exactly one deployment is registered.

    Always removes: the deployment's docker compose stack, its registration,
    its on-disk directory, and its named volumes (which are deployment-scoped
    and cannot be reused by other deployments).

    Optionally removes: images, with --remove-images. External images (postgres, redis, etc)
    additionally require --include-external since they may be shared.
    """
    force = force or context.obj["FORCE"]
    verbose = verbose or context.obj["VERBOSE"]

    try:
        name = deployments.resolve_existing_deployment_name(name)
    except ValueError as e:
        click.echo(e)
        return

    plan = uninstaller.plan_uninstall(
        name,
        remove_images=remove_images,
        include_external=include_external,
        verbose=verbose,
    )
    if not plan:
        return

    click.echo(f"Dioptra deployment '{name}' will be removed.\n")

    _print_plan_section("Networks that will be removed", plan["remove_networks"])
    _print_plan_section("Images that will be removed", plan["remove_images"])
    _print_plan_section("Images skipped (still in use)", plan["skip_images"])
    _print_plan_section("Volumes that will be removed", plan["remove_volumes"])
    _print_plan_section("Volumes skipped (still in use)", plan["skip_volumes"])

    if not yes:
        confirm = click.confirm("Continue?", default=False)
        if not confirm:
            click.echo("Uninstall aborted.")
            return

    uninstaller.execute_uninstall(plan, verbose=verbose, force=force)
    click.echo(f"\nDeployment '{name}' uninstalled.")


def _print_plan_section(label: str, items: list[str]) -> None:
    """Print a section of the uninstall plan, skipping empty sections."""
    if not items:
        return
    click.echo(f"{label}:")
    for item in items:
        click.echo(f"  - {item}")
    click.echo()
