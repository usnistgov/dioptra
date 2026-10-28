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
"""Launch the API or explicitly provision its persistent signing key."""

import os

import click

from dioptra.restapi import create_app
from dioptra.restapi.config import BaseConfig, DevelopmentConfig, load_config
from dioptra.restapi.key_file import initialize_key, resolve_key_file
from dioptra.sdk.utilities.logging import (
    attach_stdout_stream_handler,
    configure_structlog,
    set_logging_level,
)


def configure_logging(settings: BaseConfig) -> None:
    """Configure API logging from validated settings.

    Args:
        settings: Resolved settings containing the output format and log level.
    """
    attach_stdout_stream_handler(settings.DIOPTRA_RESTAPI_LOG_AS_JSON)
    set_logging_level(settings.DIOPTRA_RESTAPI_LOG_LEVEL)
    configure_structlog()


def run_pre_server_validation(settings: BaseConfig) -> None:
    """Provide an extension point for validation before server dispatch.

    Launchers call this after settings and key validation and before server
    dispatch. The current function performs no validation. Key initialization
    does not call it or resolve database settings.

    Args:
        settings: The validated configuration selected by the launcher.
    """


@click.group()
def main() -> None:
    """Run the Dioptra API or initialize its persistent signing key."""


@main.command("init-key")
@click.option("--key-file", type=str, help="Persistent key path.")
@click.option(
    "--development",
    is_flag=True,
    help="Permit native-Windows development without POSIX filesystem guarantees.",
)
def init_key(key_file: str | None, development: bool) -> None:
    """Initialize once; preserve valid keys and never replace existing contents.

    \f
    Args:
        key_file: Explicit key path, or None to use the environment or default.
        development: Permit native Windows development with reduced filesystem
            guarantees.

    Raises:
        click.ClickException: If key selection or initialization fails.
    """
    try:
        path = resolve_key_file(key_file)
        created = initialize_key(path, development=development)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    action = "Created" if created else "Preserved existing"
    click.echo(f"{action} signing key at {path}.")


def _resolve_debug(debug: bool | None) -> bool:
    """Select the explicit flag, FLASK_DEBUG, or the development default.

    Reject environment values other than true, false, 1 or 0.
    """
    if debug is not None:
        return debug
    if "FLASK_DEBUG" not in os.environ:
        return DevelopmentConfig.DEBUG
    values = {"true": True, "1": True, "false": False, "0": False}
    try:
        return values[os.environ["FLASK_DEBUG"].strip().lower()]
    except KeyError:
        raise ValueError("FLASK_DEBUG requires true, false, 1 or 0.") from None


@main.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.option("--key-file", type=str, help="Persistent key path.")
@click.option("--debug/--no-debug", default=None, help="Override FLASK_DEBUG.")
@click.pass_context
def dev(ctx: click.Context, key_file: str | None, debug: bool | None) -> None:
    """Run development policy with Flask's native run options.

    \f
    Args:
        ctx: Click context whose extra arguments are forwarded to Flask's run command.
        key_file: Explicit key path, or None to use the environment or default.
        debug: Explicit debug flag, or None to use FLASK_DEBUG and then the default.

    Raises:
        click.ClickException: If debug or resolved settings fail validation.
    """
    from flask.cli import ScriptInfo, run_command

    try:
        debug = _resolve_debug(debug)
        settings = load_config(
            "dev",
            overrides={"SECRET_KEY_FILE": resolve_key_file(key_file), "DEBUG": debug},
        )
        configure_logging(settings)
        run_pre_server_validation(settings)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    info = ScriptInfo(
        create_app=lambda: create_app(settings=settings), set_debug_flag=False
    )
    # Flask uses this explicit flag for both its banner and native reloader/debugger
    # defaults. Its callback also sets FLASK_DEBUG for subsequent reloader entries.
    run_command.main(
        args=["--debug" if debug else "--no-debug", *ctx.args],
        prog_name=f"{ctx.command_path} [FLASK RUN OPTIONS]",
        obj=info,
        standalone_mode=False,
    )


@main.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.option("--key-file", type=str, help="Persistent key path.")
@click.pass_context
def prod(ctx: click.Context, key_file: str | None) -> None:
    """Run production policy with Gunicorn's native options and signal handling.

    \f
    Args:
        ctx: Click context whose extra arguments are forwarded to Gunicorn.
        key_file: Explicit key path, or None to use the environment or default.

    Raises:
        click.ClickException: If resolved settings fail validation.
    """
    try:
        settings = load_config(
            "prod", overrides={"SECRET_KEY_FILE": resolve_key_file(key_file)}
        )
        configure_logging(settings)
        run_pre_server_validation(settings)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    # Gunicorn imports POSIX-only modules. Native Windows gets the configuration
    # policy error above before importing the production server.
    from dioptra.restapi.cli.production import DioptraApplication

    DioptraApplication(settings, ctx.args).run()


if __name__ == "__main__":
    main()
