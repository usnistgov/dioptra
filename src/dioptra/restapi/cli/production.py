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
"""Keep Gunicorn's native lifecycle with a fixed, resolved Dioptra factory."""

import sys
from pathlib import Path

from flask import Flask
from gunicorn.app.base import Application
from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.errors import ConfigError

from dioptra.restapi import create_app
from dioptra.restapi.config import BaseConfig


class DioptraApplication(WSGIApplication):
    """Run Gunicorn with settings shared by its ordinary worker forks.

    Native options and config files remain available except replacement WSGI or
    Paste applications. Factory loading stays in the worker unless Gunicorn's
    preload option is explicitly selected. Re-execution repeats the complete
    launcher command from its original invocation directory, so relative paths
    and the default database keep their meaning after a native chdir.

    Args:
        settings: Validated application configuration passed to the factory.
        arguments: Gunicorn options supplied to the production launcher.
    """

    def __init__(self, settings: BaseConfig, arguments: list[str]) -> None:
        self.settings = settings
        self.arguments = arguments
        self.invocation_directory = Path.cwd()
        super().__init__(usage="%(prog)s [GUNICORN OPTIONS]", prog="dioptra-api prod")

    def load_default_config(self) -> None:
        """Keep native default chdir tied to this launch's invocation directory."""
        super().load_default_config()
        self.cfg.set("chdir", str(self.invocation_directory))

    def init(self, parser, opts, args):
        """Reject native positional or Paste application dispatch.

        Args:
            parser: Gunicorn's argument parser.
            opts: Parsed Gunicorn options.
            args: Positional arguments remaining after parsing.

        Raises:
            ConfigError: If positional application or Paste dispatch was requested.
        """
        if args or opts.paste:
            raise ConfigError(
                "Dioptra fixes the application; positional apps and Paste are unsupported."
            )

    def load_config(self) -> None:
        """Parse native configuration while preserving launcher restart arguments.

        Reject WSGI application and Paste overrides, and arrange for re-exec
        to use the launch directory after the configured pre-exec hook.

        Raises:
            ConfigError: If a replacement application or Paste configuration
                is selected.
        """
        original_arguments = sys.argv
        try:
            sys.argv = [original_arguments[0], *self.arguments]
            # WSGIApplication.load_config requires an import string. The native
            # base performs the same parsing without selecting a replacement app.
            Application.load_config(self)
        finally:
            sys.argv = original_arguments
        inherited = self.cfg.parser().parse_args(self.cfg.get_cmd_args_from_env())
        if (
            self.cfg.paste is not None
            or self.cfg.wsgi_app is not None
            or inherited.args
        ):
            raise ConfigError(
                "Dioptra fixes the application; WSGI app and Paste overrides are unsupported."
            )
        configured_pre_exec = self.cfg.pre_exec

        def pre_exec(server):
            """Run the configured hook before restoring the invocation directory for exec."""
            configured_pre_exec(server)
            # Gunicorn captures cwd after --chdir. Restore invocation semantics
            # for its exec, without changing master/worker operating directories.
            server.START_CTX["cwd"] = str(self.invocation_directory)

        self.cfg.set("pre_exec", pre_exec)

    def load(self) -> Flask:
        """Construct the fixed Dioptra application.

        Returns:
            A Flask application built with the launcher's resolved settings.
        """
        return create_app(settings=self.settings)
