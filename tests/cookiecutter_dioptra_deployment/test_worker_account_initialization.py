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

import json
import os
import subprocess

import pytest

WORKER_USERNAME = "dioptra-worker"
WORKER_PASSWORD = "worker-password-sentinel"
USERS_URL = "http://restapi:5000/api/v1/users/"

# Stand-in for curl that records its arguments and prints a canned response in the
# layout produced by the script's --write-out format: the body, a newline, the status.
CURL_STUB = """#!/bin/sh
printf '%s\\0' "$@" > "$CURL_ARGUMENTS_FILE"
if [ "$CURL_EXIT_STATUS" -ne 0 ]; then
  echo "curl: (7) Failed to connect to restapi port 5000" 1>&2
  exit "$CURL_EXIT_STATUS"
fi
printf '%s\\n%s' "$CURL_RESPONSE_BODY" "$CURL_HTTP_STATUS"
"""


def run_init_worker_account(
    result, tmp_path, http_status="200", body="{}", curl_exit_status=0
):
    commands = tmp_path / "bin"
    commands.mkdir()
    curl = commands / "curl"
    curl.write_text(CURL_STUB)
    curl.chmod(0o755)
    arguments = tmp_path / "curl-arguments"
    environment = {
        **os.environ,
        "PATH": str(commands) + os.pathsep + os.environ["PATH"],
        "CURL_ARGUMENTS_FILE": str(arguments),
        "CURL_EXIT_STATUS": str(curl_exit_status),
        "CURL_HTTP_STATUS": http_status,
        "CURL_RESPONSE_BODY": body,
        "DIOPTRA_WORKER_USERNAME": WORKER_USERNAME,
        "DIOPTRA_WORKER_PASSWORD": WORKER_PASSWORD,
    }
    environment.pop("DEBUG", None)
    completed = subprocess.run(
        ["bash", str(result.project_path / "scripts" / "init-worker-account.sh")],
        env=environment,
        capture_output=True,
        text=True,
    )
    return completed, arguments.read_bytes().split(b"\0")[:-1]


@pytest.mark.skipif(
    os.name != "posix", reason="deployment scripts require a POSIX shell"
)
def test_worker_account_request_matches_user_schema(result, tmp_path):
    """Send only the fields that the users endpoint accepts.

    The endpoint rejects unknown fields with a 400 response, so the request body must
    hold exactly the username, password and password confirmation.
    """
    completed, arguments = run_init_worker_account(result, tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert USERS_URL.encode() in arguments
    payload = json.loads(arguments[arguments.index(b"-d") + 1])
    assert payload == {
        "username": WORKER_USERNAME,
        "password": WORKER_PASSWORD,
        "confirmPassword": WORKER_PASSWORD,
    }


@pytest.mark.skipif(
    os.name != "posix", reason="deployment scripts require a POSIX shell"
)
@pytest.mark.parametrize(
    "http_status, message",
    [
        ("200", "Registered the worker account"),
        ("409", "already exists"),
    ],
)
def test_worker_account_registration_succeeds(result, tmp_path, http_status, message):
    """Accept a new account and an account left over from an earlier initialization."""
    completed, _ = run_init_worker_account(result, tmp_path, http_status=http_status)

    assert completed.returncode == 0, completed.stderr
    assert message in completed.stdout
    assert WORKER_USERNAME in completed.stdout
    assert WORKER_PASSWORD not in completed.stdout + completed.stderr


@pytest.mark.skipif(
    os.name != "posix", reason="deployment scripts require a POSIX shell"
)
@pytest.mark.parametrize("http_status", ["400", "401", "500"])
def test_worker_account_registration_failure_stops_initialization(
    result, tmp_path, http_status
):
    """Exit with an error that shows the status and response body of a failed request."""
    body = '{"message": "Input validation failed"}'
    completed, _ = run_init_worker_account(
        result, tmp_path, http_status=http_status, body=body
    )

    assert completed.returncode == 1
    assert f"HTTP status {http_status}" in completed.stderr
    assert body in completed.stderr
    assert WORKER_PASSWORD not in completed.stdout + completed.stderr


@pytest.mark.skipif(
    os.name != "posix", reason="deployment scripts require a POSIX shell"
)
def test_unreachable_restapi_stops_initialization(result, tmp_path):
    """Exit with an error when curl cannot connect to the REST API."""
    completed, _ = run_init_worker_account(result, tmp_path, curl_exit_status=7)

    assert completed.returncode == 1
    assert "Could not reach the REST API" in completed.stderr
    assert WORKER_PASSWORD not in completed.stdout + completed.stderr
