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
"""Update command support for the Dioptra CLI."""

import click

from dioptra.cli.core import deployments, updater


@click.command()
@click.argument("name", required=False)
@click.option(
    "--ref",
    default=None,
    help="Override the git ref used to fetch update metadata. "
    f"Defaults to '{updater.DEFAULT_UPDATE_REF}'.",
)
@click.option("--verbose", is_flag=True, help="Print detailed output.")
@click.pass_context
def update(context, name, ref, verbose):
    """Check for available updates without applying anything.

    NAME may be omitted if exactly one deployment is registered.

    Reports both container build updates (applicable via `upgrade`) and
    Python package updates (which require reinstalling dioptra-platform
    and the deployment).
    """
    try:
        name = deployments.resolve_existing_deployment_name(name)
        status = updater.check_update(name, ref=ref)
    except Exception as e:
        raise click.ClickException(str(e)) from None

    if not status["supported"]:
        click.echo(status["supported_reason"])
        return

    click.echo(f"Deployment: {status['name']}\n")

    click.echo(f"Container build: {status['current_container']}")
    if status["container_update_available"]:
        click.echo(
            f"  Update available: {status['latest_container']}\n"
            f"  Apply with: dioptra-platform upgrade {status['name']}"
        )
    else:
        click.echo("  Up to date.")

    click.echo(f"\nPython package: {status['current_python']}")
    if status["python_update_available"]:
        click.echo(
            f"  Update available: {status['latest_python']}\n"
            f"  Apply with: pip install --upgrade dioptra-platform\n"
            f"  Note: Python updates only affect the CLI and future installs.\n"
            f"  Existing deployments continue running with their current setup."
        )
    else:
        click.echo("  Up to date.")
