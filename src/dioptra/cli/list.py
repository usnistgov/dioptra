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
"""List command support for the Dioptra CLI."""

import json

import click

from dioptra.cli.core import deployments, docker

COLUMNS = [
    ("name", "NAME"),
    ("status", "STATUS"),
    ("version", "VERSION"),
    ("path", "PATH"),
]
COLUMN_GAP = 2  # spaces between adjacent columns in the table


@click.command()
@click.option(
    "--json-output",
    is_flag=True,
    help="Output deployments as JSON instead of a formatted table.",
)
def list_deployments(json_output):
    """List all registered Dioptra deployments.

    Shows each deployment's name, current status (running, stopped, etc),
    installed version, and on-disk path. Column widths adjust to the data.

    With --json-output, emits the same data as a JSON array; the formatted table
    and Docker-availability warning are suppressed.
    """
    found = deployments.list_deployments()

    if not found:
        click.echo("[]" if json_output else "No deployments found.")
        return

    if json_output:
        click.echo(json.dumps(found, indent=2, default=str))
        return

    if not docker.is_docker_available():
        click.echo(
            click.style(
                "Warning: Docker is not running. Status may be inaccurate.\n",
                fg="yellow",
            )
        )

    _print_table(found)


def _print_table(deployments_list: list[dict]) -> None:
    """Render the deployments list as a formatted, colored table."""
    # Width of each column = max(header length, longest cell value).
    widths = {
        key: max(len(header), max(len(str(d[key])) for d in deployments_list))
        for key, header in COLUMNS
    }

    gap = " " * COLUMN_GAP

    header_row = gap.join(header.ljust(widths[key]) for key, header in COLUMNS)
    click.echo(header_row)

    for d in deployments_list:
        cells = []
        for key, _ in COLUMNS:
            value = str(d[key])
            if key == "status":
                # Ignore color code characters since they inflate str size
                # but not width on the screen.
                colored = colorize_status(value)
                ansi_padding = len(colored) - len(value)
                cells.append(colored.ljust(widths[key] + ansi_padding))
            else:
                cells.append(value.ljust(widths[key]))
        click.echo(gap.join(cells))


def colorize_status(status: str) -> str:
    """Return a status string wrapped in ANSI color codes for terminal display.

    Unknown statuses render as white. The returned string's len() is larger
    than the input due to ANSI escape sequences; callers padding for column
    alignment need to account for this.
    """
    colors = {
        "running": "green",
        "stopped": "yellow",
        "degraded": "bright_yellow",
        "partial": "bright_yellow",
        "broken": "red",
        "missing": "red",
        "unmanaged": "red",
        "error": "bright_red",
        "docker_unavailable": "bright_black",
        "unknown": "bright_black",
        "installed": "cyan",
    }
    return click.style(status, fg=colors.get(status, "white"))
