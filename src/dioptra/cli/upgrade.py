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
"""Upgrade command support for the Dioptra CLI."""

import click

from dioptra.cli.core import deployments, updater


@click.command()
@click.argument("name", required=False)
@click.option(
    "--ref",
    default=None,
    help="Override the git ref used to fetch update metadata.",
)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--verbose", is_flag=True, help="Print detailed output.")
@click.pass_context
def upgrade(context, name, ref, yes, verbose):
    """Apply available container updates to a deployment.

    NAME may be omitted if exactly one deployment is registered.

    Updates the deployment's container_tag in .env and recreates containers
    with the new images. Volumes (user data) are preserved.

    Python package upgrades are not handled by this command; if a Python
    update is available, run `dioptra-platform update` for instructions.
    """
    try:
        name = deployments.resolve_existing_deployment_name(name)
        status = updater.check_update(name, ref=ref)
    except Exception as e:
        raise click.ClickException(str(e)) from None

    if not status["supported"]:
        raise click.ClickException(status["supported_reason"])

    if not status["container_update_available"]:
        click.echo(f"Deployment '{name}' is up to date.")
        if status["python_update_available"]:
            click.echo(
                f"\nA Python package update is available "
                f"({status['current_python']} -> {status['latest_python']}). "
                "Run `pip install --upgrade dioptra-platform` to update the CLI. "
                "Existing deployments will keep running with their current setup."
            )
        return

    click.echo(
        f"Upgrade '{name}': container "
        f"{status['current_container']} -> {status['latest_container']}"
    )

    if not yes:
        if not click.confirm("Continue?", default=False):
            click.echo("Upgrade aborted.")
            return

    try:
        updater.apply_update(name, ref=ref, verbose=verbose)
    except Exception as e:
        raise click.ClickException(f"Upgrade failed: {e}") from None

    click.echo(
        f"Upgrade complete: {status['current_container']} -> "
        f"{status['latest_container']}"
    )
