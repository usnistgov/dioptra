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
"""Run the production API with Gunicorn's native configuration and process lifecycle.

Dioptra fixes which Flask application is served while preserving native server
options, worker reload and master re-execution. This module validates the final
certificate/key selection, enforces TLS policy on custom SSL-context hooks and
keeps relative launch paths usable when Gunicorn changes its working directory.
"""

import os
import ssl
import sys
from pathlib import Path

from flask import Flask
from gunicorn.app.base import Application
from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.errors import ConfigError
from gunicorn.sock import ssl_context

from dioptra.restapi import create_app
from dioptra.restapi.config import BaseConfig
from dioptra.sdk.utilities.tls import enforce_tls, validate_key_exchange


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
        """Resolve production server settings for the Dioptra application.

        Parse Gunicorn configuration and validate TLS before constructing the fixed
        Dioptra application. Save the original invocation directory and arguments so
        server re-execution can resolve relative paths in the same way.

        Args:
            settings: Validated Dioptra settings passed to the Flask factory.
            arguments: Gunicorn options following the production launcher command.
        """
        self.settings = settings
        self.arguments = arguments
        self.invocation_directory = Path.cwd()
        self.invocation_arguments = sys.orig_argv.copy()
        super().__init__(usage="%(prog)s [GUNICORN OPTIONS]", prog="dioptra-api prod")

    def load_default_config(self) -> None:
        """Load Gunicorn defaults with chdir tied to the original launch directory.

        Returns:
            None. The native configuration is updated before explicit settings are read.
        """
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
            ConfigError: If a replacement application or Paste configuration is
                selected.
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
        self.configure_tls()
        configured_pre_exec = self.cfg.pre_exec

        def pre_exec(server):
            """Run the configured hook before restoring the invocation directory for exec."""
            # Gunicorn rebuilds argv from sys.argv, which loses interpreter flags
            # such as -m. Keep the original module or installed-command form.
            server.START_CTX["args"] = self.invocation_arguments.copy()
            configured_pre_exec(server)
            # Gunicorn captures cwd after --chdir. Restore invocation semantics
            # for its exec, without changing master/worker operating directories.
            server.START_CTX["cwd"] = str(self.invocation_directory)

        self.cfg.set("pre_exec", pre_exec)

    def configure_tls(self) -> None:
        """Apply production TLS policy after Gunicorn resolves its final settings.

        Gunicorn accepts certificate paths from command options, environment or a
        configuration file. An ssl_context hook can also construct a context
        instead of using the provided default factory. This method wraps that hook
        so every returned context uses the final configured certificate/key pair
        and TLS policy, including during worker startup and reload.

        Returns:
            None. The configured ssl_context hook is replaced with the enforcing
            wrapper.

        Raises:
            ConfigError: Certificate/key settings, the custom context or forwarding
                settings violate production requirements.
        """
        self.reject_forwarding_overrides()
        if not self.cfg.certfile or not self.cfg.keyfile:
            raise ConfigError("Production requires Gunicorn certfile and keyfile.")
        try:
            exchange = validate_key_exchange(
                os.environ.get("DIOPTRA_TLS_KEY_EXCHANGE", "default")
            )
            configured_context = self.cfg.ssl_context

            def context(conf, factory):
                """Preserve the selected hook and enforce policy for each native context."""
                selected = configured_context(conf, factory)
                if not isinstance(selected, ssl.SSLContext):
                    raise ValueError("Gunicorn ssl_context hook must return SSLContext")
                if (
                    selected.protocol == ssl.PROTOCOL_TLS_CLIENT
                    or selected.check_hostname
                ):
                    raise ValueError(
                        "Gunicorn ssl_context hook must return a server context"
                    )
                selected.load_cert_chain(conf.certfile, conf.keyfile)
                return enforce_tls(selected, exchange)

            self.cfg.set("ssl_context", context)
            ssl_context(self.cfg)
        except (OSError, ValueError, ssl.SSLError) as exc:
            raise ConfigError(f"Production TLS configuration failed: {exc}") from exc

    def reject_forwarding_overrides(self) -> None:
        """Reject native options that would trust client-supplied proxy identity.

        Keep the request scheme tied to native TLS and the Host header subject to the
        application's permitted-host check. Reject settings that would instead accept a
        client-supplied scheme, host or proxy-protocol identity.

        Returns:
            None. Accepted native forwarding settings are cleared.

        Raises:
            ConfigError: A setting permits forwarded identity or proxy-protocol
                metadata.
        """
        defaults = {
            "secure_scheme_headers": {
                "X-FORWARDED-PROTOCOL": "ssl",
                "X-FORWARDED-PROTO": "https",
                "X-FORWARDED-SSL": "on",
            },
            "forwarded_allow_ips": ["127.0.0.1", "::1"],
            "forwarder_headers": ["SCRIPT_NAME", "PATH_INFO"],
        }
        for name in (
            "secure_scheme_headers",
            "forwarded_allow_ips",
            "forwarder_headers",
        ):
            value = getattr(self.cfg, name)
            if value and value != defaults[name]:
                raise ConfigError(
                    f"Production forbids unsafe Gunicorn {name} overrides."
                )
            self.cfg.set(name, {} if name == "secure_scheme_headers" else "")
        if self.cfg.proxy_protocol != "off":
            raise ConfigError("Production forbids Gunicorn proxy_protocol.")

    def load(self) -> Flask:
        """Create the Flask application using the already resolved Dioptra settings.

        Returns:
            The Flask WSGI application for the current worker, or for the master when
            Gunicorn preload is explicitly enabled.
        """
        return create_app(settings=self.settings)
