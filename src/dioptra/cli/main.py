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
"""Command-line entry point for installing and managing Dioptra deployments."""

from __future__ import annotations

import click

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "--force",
    is_flag=True,
    help="Attempt to force [un]install operations regardless of current deployment state. "
    "Ignored by read-only commands.",
)
@click.pass_context
def cli(context, verbose, force):
    """Install, manage, and remove Dioptra deployments.

    Run `dioptra-platform <command> --help` for details on each command.
    Start with `dioptra-platform install` to set up a new deployment.
    """
    context.ensure_object(dict)
    context.obj["VERBOSE"] = verbose
    context.obj["FORCE"] = force


# Commands are imported after `cli` is defined so they can reference it
# without circular import
from .clean import clean  # noqa: E402
from .install import install  # noqa: E402
from .list import list_deployments  # noqa: E402
from .runtime import start, status, stop  # noqa: E402
from .uninstall import uninstall  # noqa: E402
from .update import update  # noqa: E402
from .upgrade import upgrade  # noqa: E402

cli.add_command(install)
cli.add_command(start)
cli.add_command(stop)
cli.add_command(clean)
cli.add_command(status)
cli.add_command(update)
cli.add_command(upgrade)
cli.add_command(uninstall)
cli.add_command(list_deployments, name="list")
