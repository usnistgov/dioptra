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
"""Runtime command support for the Dioptra CLI: start, stop, status."""

import click

from dioptra.cli.core import docker, runtime


@click.command()
@click.argument("name", required=False)
@click.option("--verbose", is_flag=True, help="Print detailed output.")
@click.pass_context
def start(context, name, verbose):
    """Start a deployment.

    NAME may be omitted if exactly one deployment is registered; the lone
    deployment will be started.
    """
    verbose = verbose or context.obj["VERBOSE"]
    try:
        runtime.start(name, verbose=verbose)
    except Exception as e:
        raise click.ClickException(f"Unable to start deployment: {e}") from None

    click.echo(
        "Deployment start requested. Use `dioptra-platform status` to check progress."
    )


@click.command()
@click.argument("name", required=False)
@click.option("--verbose", is_flag=True, help="Print detailed output.")
@click.pass_context
def stop(context, name, verbose):
    """Stop a deployment.

    NAME may be omitted if exactly one deployment is registered; the lone
    deployment will be stopped.
    """
    verbose = verbose or context.obj["VERBOSE"]
    try:
        runtime.stop(name, verbose=verbose)
    except Exception as e:
        raise click.ClickException(f"Unable to stop deployment: {e}") from None

    click.echo("Deployment stopped.")


@click.command()
@click.argument("name", required=False)
@click.option("--verbose", is_flag=True, help="Print detailed output.")
@click.pass_context
def status(context, name, verbose):
    """Show deployment status.

    NAME may be omitted if exactly one deployment is registered; status
    for the lone deployment will be shown.
    """
    verbose = verbose or context.obj["VERBOSE"]
    try:
        info = runtime.status(name)
    except Exception as e:
        raise click.ClickException(f"Unable to get status: {e}") from None

    _print_status(info, verbose=verbose)


def _print_status(info: dict, verbose: bool) -> None:
    """Print a deployment's status info, with detail when verbose."""
    click.echo(f"Name:   {info['name']}")
    click.echo(f"Path:   {info['path']}")
    click.echo(f"Status: {info['status']}\n")

    if not verbose:
        return

    _print_section_split(
        "Images",
        info.get("internal", []),
        info.get("external", []),
    )

    digests = info.get("image_digests") or {}
    if digests:
        click.echo("\nImage digests:")
        click.echo(docker.format_image_digests(digests))

    _print_section("Volumes", info.get("volumes", []))
    _print_section("Networks", info.get("networks", []))


def _print_section(label: str, items: list[str]) -> None:
    """Print a labeled list, skipping empty sections."""
    if not items:
        return
    click.echo(f"\n{label}:")
    for item in items:
        click.echo(f"  - {item}")


def _print_section_split(
    label: str,
    internal: list[str],
    external: list[str],
) -> None:
    """Print images as two grouped sublists (internal vs external)."""
    if not (internal or external):
        return
    click.echo(f"\n{label}:")
    if internal:
        click.echo("  Internal:")
        for img in internal:
            click.echo(f"    - {img}")
    if external:
        click.echo("  External:")
        for img in external:
            click.echo(f"    - {img}")
