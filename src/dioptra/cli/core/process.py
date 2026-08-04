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
"""Subprocess invocation for the Dioptra CLI.

All shell-outs go through this module to get consistent behavior:

* Non-zero exit codes raise RuntimeError with the command, exit code,
  working directory, and captured output.
* Captured output is the default (so failures are diagnosable) but can be
  streamed directly to the terminal for long-running operations.
* KeyboardInterrupt is converted to RuntimeError so caller cleanup paths
  run on Ctrl-C; without this, BaseException would bypass them.
"""

import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any


def run(
    cmd: list,
    cwd: Path | None = None,
    verbose: bool = False,
    env: dict | None = None,
    suppress_output: bool = False,
    capture_output: bool = False,
    stream_output: bool = False,
    timeout: float | None = None,
) -> CompletedProcess:
    """Run a subprocess, raising on failure.

    Parameters
    ----------
    cmd : list[str]
        Command and arguments to execute.
    cwd : str | Path | None
        Working directory for the subprocess.
    verbose : bool
        Print the command before executing.
    env : dict | None
        Environment variables. If None, the parent process's env is used.
    suppress_output : bool
        When the command fails, do not print captured stdout/stderr to the
        terminal. The output is still included in the raised exception
        message. Useful for "does X exist" checks where failure is expected.
    capture_output : bool
        Capture stdout and stderr into the returned CompletedProcess.
        Mutually exclusive with stream_output. Default behavior (neither
        flag set) also captures output, but the result fields may be
        consumed by the failure paths.
    stream_output : bool
        Stream stdout and stderr directly to the terminal as the command
        runs. Use for long-running commands where seeing progress matters
        (cruft, docker compose pull, etc). Mutually exclusive with
        capture_output: streamed output cannot be retrieved afterward.
    timeout : float | None
        Maximum seconds to allow the command to run. None means no limit.

    Returns
    -------
    CompletedProcess
        The completed subprocess. Its stdout/stderr will be populated only
        if capture_output was True or stream_output was False.

    Raises
    ------
    RuntimeError
        If the command exits non-zero, times out, or is interrupted.
    ValueError
        If capture_output and stream_output are both set.
    """
    if capture_output and stream_output:
        raise ValueError("capture_output and stream_output cannot both be true.")
    cmd_str = " ".join(map(str, cmd))

    if verbose:
        print(f"Running {cmd_str}")

    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "env": env,
        "text": True,
        "timeout": timeout,
    }

    # Capture by default so failures are diagnosable; only skip capture
    # when the caller explicitly asked for streamed output
    if not stream_output:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    try:
        result = subprocess.run(cmd, **kwargs)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"Command timed out after {timeout} seconds:\n{cmd_str}"
        ) from e
    except KeyboardInterrupt as e:
        # Convert to RuntimeError so caller cleanup runs on Ctrl-C.
        # BaseException would bypass `except Exception` cleanup blocks.
        raise RuntimeError(f"Command interrupted:\n{cmd_str}") from e

    if result.returncode != 0:
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if not suppress_output:
            if stdout:
                print(stdout)

            if stderr:
                print(stderr)

        raise RuntimeError(
            f"Command failed ({result.returncode}):\n"
            f"{cmd_str}\n"
            f"CWD: {cwd}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}\n"
        )

    return result
