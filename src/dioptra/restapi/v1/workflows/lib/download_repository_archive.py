"""Download public repository snapshots without invoking Git or remote helpers."""

import json
import os
import re
from tempfile import TemporaryFile
from typing import BinaryIO
from urllib.parse import quote, unquote, urljoin, urlparse

from requests import RequestException, Session

from dioptra.restapi.v1.shared.io_file_service import MAX_ARCHIVE_BYTES

MAX_METADATA_BYTES = 1024 * 1024
CHUNK_SIZE = 64 * 1024


def _validate_https_url(url: str, hosts: set[str]) -> None:
    parsed = urlparse(url)
    if (
        any(ord(char) < 32 or ord(char) == 127 for char in url)
        or "\\" in url
        or parsed.scheme != "https"
        or parsed.netloc not in hosts
    ):
        raise ValueError("Repository requests must use an approved HTTPS host.")


def _parse_repository(url: str) -> tuple[str, str, str]:
    _validate_https_url(url, {"github.com", "gitlab.com"})

    parsed = urlparse(url)
    if parsed.query or parsed.params or ";" in url:
        raise ValueError("Repository URLs cannot contain queries or ;path selections.")

    repository = parsed.path.removeprefix("/").removesuffix("/").removesuffix(".git")
    parts = repository.split("/")
    if (
        len(parts) < 2
        or (parsed.hostname == "github.com" and len(parts) != 2)
        or any(
            part in {".", ".."} or not re.fullmatch(r"[\w-][\w.-]*", part, re.ASCII)
            for part in parts
        )
    ):
        raise ValueError("Expected a repository URL, not a file or archive URL.")
    ref = unquote(parsed.fragment)

    if ref and (
        ref.startswith(("-", "/"))
        or any(part in {"", ".", ".."} for part in ref.split("/"))
        or any(ord(char) < 32 or ord(char) == 127 for char in ref)
        or "\\" in ref
    ):
        raise ValueError("Invalid repository branch, tag, or commit.")

    return str(parsed.hostname), repository, ref


def _download(
    session: Session,
    url: str,
    hosts: set[str],
    output: BinaryIO,
    limit: int,
) -> None:
    for _ in range(6):
        _validate_https_url(url, hosts)
        with session.get(
            url, stream=True, allow_redirects=False, timeout=(5, 30)
        ) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                if not location:
                    raise ValueError(
                        "Repository provider returned an invalid redirect."
                    )
                url = urljoin(url, location)
                continue
            if response.status_code != 200:
                raise ValueError(
                    f"Repository provider returned HTTP {response.status_code}. "
                    "Check public visibility, the ref, and provider rate limits."
                )
            size = 0
            for chunk in response.iter_content(CHUNK_SIZE):
                size += len(chunk)
                if size > limit:
                    raise ValueError("Repository download exceeds the size limit.")
                output.write(chunk)
            output.seek(0)
            return
    raise ValueError("Repository provider returned too many redirects.")


def _metadata(session: Session, url: str, host: str) -> dict:
    with TemporaryFile() as output:
        _download(session, url, {host}, output, MAX_METADATA_BYTES)
        data = json.load(output)

    if not isinstance(data, dict):
        raise ValueError("Repository provider returned invalid metadata.")

    return data


def _resolve_archive(
    session: Session, host: str, repository: str, ref: str
) -> tuple[str, str, set[str]]:
    # New providers must define public-visibility checks, commit resolution,
    # archive endpoints, and approved redirect hosts here.
    if host == "github.com":
        api_host = "api.github.com"
        base = f"https://{api_host}/repos/{repository}"
        project = _metadata(session, base, api_host)
        public = project.get("private") is False
        commit_path, commit_key = "commits", "sha"
    else:
        api_host = "gitlab.com"
        base = f"https://{api_host}/api/v4/projects/{quote(repository, safe='')}"
        project = _metadata(session, base, api_host)
        public = project.get("visibility") == "public"
        commit_path, commit_key = "repository/commits", "id"

    if not public:
        raise ValueError("Only public repositories can be imported.")

    selected_ref = ref or project.get("default_branch")
    if (
        not isinstance(selected_ref, str)
        or not selected_ref
        or selected_ref in {".", ".."}
    ):
        raise ValueError("Repository has no valid default branch.")

    commit = _metadata(
        session,
        f"{base}/{commit_path}/{quote(selected_ref, safe='')}",
        api_host,
    ).get(commit_key)

    if not isinstance(commit, str) or not re.fullmatch(
        r"[0-9a-f]{40}|[0-9a-f]{64}", commit
    ):
        raise ValueError("Repository provider returned an invalid commit ID.")

    if host == "github.com":
        return commit, f"{base}/tarball/{commit}", {api_host, "codeload.github.com"}

    return (
        commit,
        f"{base}/repository/archive.tar.gz?sha={commit}&include_lfs_blobs=false",
        {api_host},
    )


def download_repository_archive(url: str, output: BinaryIO) -> str:
    """Download a public GitHub/GitLab archive and return its resolved commit ID.

    URLs accept an optional ``.git`` suffix and ``#branch``, ``#tag``, or
    ``#commit`` fragment. No fragment selects the repository's default branch.
    The caller supplies an empty, seekable binary stream and owns its cleanup.
    On success the stream is rewound for reading. No archive extraction is done.
    Requests have connection/read timeouts, but no overall download deadline.
    """
    host, repository, ref = _parse_repository(url)
    try:
        with Session() as session:
            # Public imports must not inherit netrc credentials or proxy settings.
            session.trust_env = False
            # Honor the deployment's explicit TLS trust configuration even though
            # requests' automatic environment handling is disabled.
            session.verify = (
                os.getenv("REQUESTS_CA_BUNDLE") or os.getenv("CURL_CA_BUNDLE") or True
            )
            session.headers.update({"User-Agent": "dioptra-repository-import"})

            commit, archive_url, hosts = _resolve_archive(
                session, host, repository, ref
            )

            _download(session, archive_url, hosts, output, MAX_ARCHIVE_BYTES)

            return commit

    except RequestException as error:
        raise ValueError("Unable to download repository archive over HTTPS.") from error
