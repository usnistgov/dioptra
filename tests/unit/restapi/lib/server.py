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
"""A context manager for a Flask test server.

This module provides a context manager for a Flask test server. This can be used in
combination with a requests Session as an alternative to the Flask test client for
testing the REST API.
"""
from __future__ import annotations

import os
import platform
import shutil
import signal
import subprocess
import time
from pathlib import Path
from subprocess import PIPE, CompletedProcess, Popen


class FlaskTestServer(object):
    """A context manager for a Flask test server.

    This class provides a convenient way to start and stop a Flask server process
    for testing purposes. The server process runs in a subprocess and uses an SQLite
    database for storage.
    """

    def __init__(
        self, sqlite_path: str | Path, extra_env: dict[str, str] | None = None
    ) -> None:
        """Initialize the FlaskTestServer object.

        Args:
            sqlite_path: The path to the SQLite database file.
            extra_env: A dictionary of additional environment variables to set for the
                server process.
        """
        self._process: Popen | None = None
        self._sqlite_uri: str = f"sqlite:///{Path(sqlite_path).resolve()}"
        self._extra_env: dict[str, str] = extra_env or {}

    def __enter__(self) -> FlaskTestServer:
        """Start the Flask server process and enter the runtime context.

        Returns:
            The FlaskTestServer object.
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Stop the Flask server process and exit the runtime context.

        Args:
            exc_type: The type of the exception raised in the runtime context. None if
                no exception was raised.
            exc_value: The value of the exception raised in the runtime context. None
                if no exception was raised.
            traceback: The traceback of the exception raised in the runtime context.
                None if no exception was raised.
        """
        self.stop()

    @property
    def env(self) -> dict[str, str]:
        """A dictionary containing the server's environment variables."""
        return (
            os.environ
            | {
                "DIOPTRA_RESTAPI_DEV_DATABASE_URI": self._sqlite_uri,
                "DIOPTRA_RESTAPI_ENV": "dev",
            }
            | self._extra_env
        )

    @property
    def dioptra_db_cmd(self) -> str:
        """The path to the dioptra-db command.

        Raises:
            RuntimeError: If the dioptra-db command is not found.
        """
        cmd = shutil.which("dioptra-db")

        if cmd is None:
            raise RuntimeError("dioptra-db command not found.")

        return cmd

    @property
    def flask_cmd(self) -> str:
        """The path to the Flask command.

        Raises:
            RuntimeError: If the Flask command is not found.
        """
        cmd = shutil.which("flask")

        if cmd is None:
            raise RuntimeError("Flask command not found.")

        return cmd

    def start(self) -> Popen:
        """Start the Flask server process.

        Returns:
            The Flask server process.
        """
        self._process = Popen(
            args=[self.flask_cmd, "run", "--port", "5000", "--no-reload"],
            env=self.env,
            stdout=PIPE,
            stderr=PIPE,
        )
        return self._process

    def stop(self) -> int | None:
        """Stop the Flask server process.

        Returns:
            The return code of the Flask server process. If the process is not running,
            returns None.
        """
        if self._process is None:
            return None

        stop_attempts = 0
        while (return_code := self._process.poll()) is None:
            if stop_attempts <= 2:
                self._send_interrupt_signal()

            elif stop_attempts <= 4:
                self._process.terminate()

            else:
                self._process.kill()

            stop_attempts += 1
            time.sleep(1)

        self._process = None
        return return_code

    def upgrade_db(self, *args) -> CompletedProcess:
        """Run the Flask database upgrade command in a subprocess.

        Args:
            *args: Additional arguments to pass to the Flask database upgrade command.

        Returns:
            The result of the database upgrade command.
        """
        return subprocess.run(
            args=[self.dioptra_db_cmd, "autoupgrade", *args],
            env=self.env,
            capture_output=True,
            text=True,
        )

    def _send_interrupt_signal(self) -> None:
        """Send OS-dependent interrupt signal to the Flask server process."""
        if platform.system() == "Windows":
            self._process.send_signal(signal.CTRL_C_EVENT)

        if platform.system() in {"Linux", "Darwin"}:
            self._process.send_signal(signal.SIGINT)
