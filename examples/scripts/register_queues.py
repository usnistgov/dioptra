#!/usr/bin/env python
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
"""Register the queues used in Dioptra's examples and demos.

Functions:
    register_queues: The Click command for registering the queues used in Dioptra's
        examples and demos.
"""
from __future__ import annotations

import click
from rich.console import Console

# The try/except ImportError blocks allow this script to be invoked using:
#     python ./scripts/register_task_plugins.py  # OR
#     python -m scripts.register_task_plugins
try:
    from .client import DioptraClient

except ImportError:
    from client import DioptraClient

try:
    from .utils import RichConsole

except ImportError:
    from utils import RichConsole

_CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
    show_default=True,
)


@click.command(context_settings=_CONTEXT_SETTINGS)
@click.option(
    "--queue",
    multiple=True,
    type=click.STRING,
    default=["tensorflow_cpu", "tensorflow_gpu", "pytorch_cpu", "pytorch_gpu"],
    help="The queue name to register.",
)
@click.option(
    "--api-url",
    type=click.STRING,
    default="http://localhost",
    help="The url to the Dioptra REST API.",
)
def register_queues(queue, api_url):
    """Register the queues used in Dioptra's examples and demos."""

    console = RichConsole(Console())
    client = DioptraClient(address=api_url)

    console.print_title("Dioptra Examples - Register Queues")
    console.print_parameter("queue", value=f"[default not bold]{', '.join(queue)}[/]")
    console.print_parameter("api_url", value=f"[default not bold]{api_url}[/]")

    for name in queue:
        response = client.get_queue_by_name(name=name)

        if response is None or "Not Found" in response.get("message", []):
            response = client.register_queue(name=name)
            response_after = client.get_queue_by_name(name=name)

            if response_after is None or "Not Found" in response_after.get("message", []):
                raise RuntimeError(
                    f"Failed to register the queue {name!r}. Is the API URL correct?"
                )

            console.print_success(
                "[bold green]Success![/] [default not bold]Registered the queue "
                f"{name!r}.[/]"
            )

        else:
            console.print_info(
                f"[bold white]Skipped.[/] [default not bold]The queue {name!r} is "
                "already registered.[/]"
            )

    console.print_success("[default no bold]Queue registration is complete.[/]")


if __name__ == "__main__":
    register_queues()
