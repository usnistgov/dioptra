"""Focused downloader tests, independent of Flask requests and database fixtures."""

import importlib
from io import BytesIO

import pytest
import requests

downloader = importlib.import_module(
    "dioptra.restapi.v1.workflows.lib.download_repository_archive"
)
BASE = "https://api.github.com/repos/owner/project"
COMMIT = "a" * 40
ARCHIVE_URL = f"{BASE}/tarball/{COMMIT}"
CODELOAD_URL = f"https://codeload.github.com/owner/project/legacy.tar.gz/{COMMIT}"
HOSTS = {"api.github.com", "codeload.github.com"}


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("ext::echo ignored", "approved HTTPS host"),
        ("https://github.com.attacker.example/owner/project", "approved HTTPS host"),
        ("https://user:password@github.com/owner/project", "approved HTTPS host"),
        ("https://github.com/owner/project;plugins#main", ";path selections"),
    ],
)
def test_invalid_repository_url_makes_no_request(url, message, repository_http):
    with pytest.raises(ValueError, match=message):
        downloader.download_repository_archive(url, BytesIO())
    repository_http.get.assert_not_called()


def test_download_returns_commit_and_rewound_archive_without_extracting(
    repository_http, repository_response
):
    repository_http.get.side_effect = [
        repository_response({"private": False, "default_branch": "main"}),
        repository_response({"sha": COMMIT}),
        repository_response(status=302, headers={"Location": CODELOAD_URL}),
        # Deliberately not a valid tar: the downloader must not attempt extraction.
        repository_response(b"archive bytes"),
    ]
    output = BytesIO()
    commit = downloader.download_repository_archive(
        "https://github.com/owner/project#feature/import",
        output,
    )
    assert commit == COMMIT
    assert not output.closed
    assert output.tell() == 0
    assert output.read() == b"archive bytes"
    assert [request.args[0] for request in repository_http.get.call_args_list] == [
        BASE,
        f"{BASE}/commits/feature%2Fimport",
        ARCHIVE_URL,
        CODELOAD_URL,
    ]
    assert repository_http.get.call_args.kwargs["timeout"] == (5, 30)


@pytest.mark.parametrize(
    ("host", "metadata"),
    [("github.com", {"private": True}), ("gitlab.com", {"visibility": "private"})],
)
def test_private_repository_rejected(
    host, metadata, repository_http, repository_response
):
    repository_http.get.return_value = repository_response(metadata)
    with pytest.raises(ValueError, match="Only public repositories"):
        downloader.download_repository_archive(
            f"https://{host}/owner/project", BytesIO()
        )
    assert repository_http.get.call_count == 1


@pytest.mark.parametrize(
    "location", ["https://localhost/internal", "http://codeload.github.com/archive"]
)
def test_download_rejects_redirect_before_following(
    location, repository_http, repository_response
):
    repository_http.get.return_value = repository_response(
        status=302, headers={"Location": location}
    )
    with pytest.raises(ValueError, match="approved HTTPS host"):
        downloader._download(repository_http, ARCHIVE_URL, HOSTS, BytesIO(), 100)
    assert repository_http.get.call_count == 1


def test_redirect_loop_is_bounded(repository_http, repository_response):
    repository_http.get.side_effect = [
        repository_response(status=302, headers={"Location": ARCHIVE_URL})
        for _ in range(6)
    ]
    with pytest.raises(ValueError, match="too many redirects"):
        downloader._download(repository_http, ARCHIVE_URL, HOSTS, BytesIO(), 100)
    assert repository_http.get.call_count == 6


def test_network_error_preserves_cause(repository_http):
    error = requests.Timeout("timeout")
    repository_http.get.side_effect = error
    with pytest.raises(ValueError, match="Unable to download") as caught:
        downloader.download_repository_archive(
            "https://github.com/owner/project", BytesIO()
        )
    assert caught.value.__cause__ is error


def test_session_uses_explicit_ca_bundle_without_ambient_credentials(
    monkeypatch,
    repository_http,
    repository_response,
):
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/requests.pem")
    monkeypatch.setenv("CURL_CA_BUNDLE", "/curl.pem")
    repository_http.get.return_value = repository_response(status=404)
    with pytest.raises(ValueError, match="HTTP 404"):
        downloader.download_repository_archive(
            "https://github.com/owner/project", BytesIO()
        )
    assert repository_http.trust_env is False
    assert repository_http.verify == "/requests.pem"
    assert "Authorization" not in repository_http.headers


def test_download_limit_counts_streamed_bytes(
    monkeypatch, repository_http, repository_response
):
    monkeypatch.setattr(downloader, "CHUNK_SIZE", 2)
    repository_http.get.return_value = repository_response(b"123456")
    output = BytesIO()
    with pytest.raises(ValueError, match="download exceeds the size limit"):
        downloader._download(repository_http, ARCHIVE_URL, HOSTS, output, 4)
    assert output.getvalue() == b"1234"


@pytest.mark.parametrize("host", ["gitlab.com", "gitlab.research.example"])
@pytest.mark.parametrize(
    ("ref", "encoded_ref"), [("", "main"), ("feature/import", "feature%2Fimport")]
)
def test_gitlab_resolution_keeps_requests_on_supplied_host(
    host, ref, encoded_ref, repository_http, repository_response
):
    # Exercise the resolver contract without adding a host to the public allowlist.
    base = f"https://{host}/api/v4/projects/group%2Fsubgroup%2Fproject"
    repository_http.get.side_effect = [
        repository_response({"visibility": "public", "default_branch": "main"}),
        repository_response({"id": COMMIT}),
        repository_response(b"gitlab archive bytes"),
    ]

    commit, archive_url, hosts = downloader._resolve_archive(
        repository_http, host, "group/subgroup/project", ref
    )
    output = BytesIO()
    downloader._download(repository_http, archive_url, hosts, output, 100)

    assert commit == COMMIT
    assert hosts == {host}
    assert archive_url == (
        f"{base}/repository/archive.tar.gz?sha={COMMIT}&include_lfs_blobs=false"
    )
    assert [request.args[0] for request in repository_http.get.call_args_list] == [
        base,
        f"{base}/repository/commits/{encoded_ref}",
        archive_url,
    ]
    assert all(
        request.kwargs["allow_redirects"] is False
        for request in repository_http.get.call_args_list
    )
    assert output.tell() == 0
    assert output.read() == b"gitlab archive bytes"


def test_public_importer_still_rejects_unapproved_gitlab_host(repository_http):
    with pytest.raises(ValueError, match="approved HTTPS host"):
        downloader.download_repository_archive(
            "https://gitlab.research.example/group/project", BytesIO()
        )
    repository_http.get.assert_not_called()


def test_gitlab_metadata_redirect_cannot_cross_supplied_host(
    repository_http, repository_response
):
    repository_http.get.side_effect = [
        repository_response(
            status=302,
            headers={"Location": "https://gitlab.com/api/v4/projects/group%2Fproject"},
        ),
        repository_response({"visibility": "public", "default_branch": "main"}),
        repository_response({"id": COMMIT}),
    ]

    with pytest.raises(ValueError, match="approved HTTPS host"):
        downloader._resolve_archive(
            repository_http, "gitlab.research.example", "group/project", ""
        )

    assert repository_http.get.call_count == 1
    assert repository_http.get.call_args.args[0] == (
        "https://gitlab.research.example/api/v4/projects/group%2Fproject"
    )
