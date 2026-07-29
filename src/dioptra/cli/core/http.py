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

"""HTTP fetch helpers for retrieving release metadata from GitHub.

Centralizes the patterns used to fetch verify.json, cosign keys, and
latest_build.json: URL construction, curl invocation, retry on transient
network errors, and JSON parsing.
"""

import json
import os
import time
from pathlib import Path
from urllib.parse import quote

from dioptra.cli.core import process

# Configurable via env vars for testing against a fork; production usage
# always leaves the defaults in place
GITHUB_ORG = os.environ.get("DIOPTRA_GITHUB_ORG", "usnistgov")
GITHUB_REPO = os.environ.get("DIOPTRA_GITHUB_REPO", "dioptra")
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com"

# Error message fragments indicating a network problem worth retrying.
# Matched case-insensitively against the str() of the exception.
TRANSIENT_ERROR_MARKERS = (
    "socket is not connected",
    "connection refused",
    "connection reset",
    "no such host",
    "i/o timeout",
    "tls handshake timeout",
    "temporary failure",
    "eof",
    "could not resolve host",
    "operation timed out",
    "ssl connect error",
    "empty reply from server",
)


def github_raw_url(ref: str, path: str) -> str:
    """Build a raw.githubusercontent.com URL for the given ref and path.

    Works with branches, tags, and commit SHAs in the ref position.
    URL-encodes the ref since branch names can contain slashes.
    """
    safe_ref = quote(ref.strip("/"), safe="/")
    safe_path = path.strip("/")
    return f"{GITHUB_RAW_BASE_URL}/{GITHUB_ORG}/{GITHUB_REPO}/{safe_ref}/{safe_path}"


def fetch_json(ref: str, path: str, verbose: bool = False) -> dict:
    """Fetch a JSON file from GitHub raw, returning the parsed dict.

    Retries on transient network failures. Raises RuntimeError with
    branch and URL context for fetch failures, empty responses, and
    JSON-decode errors.
    """
    url = github_raw_url(ref, path)

    def _curl():
        return process.run(
            ["curl", "--fail", "--silent", "--show-error", "--location", url],
            verbose=verbose,
            capture_output=True,
            suppress_output=True,
        )

    try:
        result = retry(_curl, verbose=verbose)
    except RuntimeError as e:
        raise RuntimeError(
            f"Failed to fetch {path} from ref '{ref}'.\nURL: {url}\n{e}"
        ) from e

    body = result.stdout if result else ""
    if not body.strip():
        raise RuntimeError(
            f"Fetched {path} from ref '{ref}', but the response was empty."
        )

    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Fetched {path} from ref '{ref}', but it was not valid JSON."
        ) from e


def fetch_to_file(
    ref: str,
    path: str,
    dest: Path,
    verbose: bool = False,
) -> None:
    """Fetch a file from GitHub raw and write it to dest.

    Retries on transient network failures. Raises RuntimeError with
    branch and URL context on failure; leaves dest in whatever state
    curl left it (caller should clean up on error).
    """
    url = github_raw_url(ref, path)

    def _curl():
        return process.run(
            [
                "curl",
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--output",
                str(dest),
                url,
            ],
            verbose=verbose,
        )

    try:
        retry(_curl, verbose=verbose)
    except RuntimeError as e:
        raise RuntimeError(
            f"Failed to fetch {path} from ref '{ref}'.\nURL: {url}\n{e}"
        ) from e


def retry(fn, attempts: int = 3, base_delay: float = 1.0, verbose: bool = False):
    """Call fn(); retry on transient errors with exponential backoff.

    Up to `attempts` (default 3). Delays double each attempt starting from base_delay
    (1s → 2s → 4s by default). Non-transient RuntimeErrors propagate immediately.
    """
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except RuntimeError as e:
            if not _is_transient_error(e):
                raise
            if attempt == attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            if verbose:
                print(
                    f"Transient error (attempt {attempt}/{attempts}), "
                    f"retrying in {delay:.1f}s..."
                )
            time.sleep(delay)


def _is_transient_error(err: Exception) -> bool:
    """True if an exception's message looks like a transient network failure."""
    msg = str(err).lower()
    return any(marker in msg for marker in TRANSIENT_ERROR_MARKERS)
