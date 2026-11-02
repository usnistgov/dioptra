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
"""Exercise the requests client's multipart uploads against the REST API."""

import tarfile
from contextlib import ExitStack, contextmanager
from functools import partial
from http import HTTPStatus
from io import BytesIO
from threading import Thread

import pytest
from werkzeug.serving import make_server

from dioptra.client import DioptraClient, DioptraFile
from dioptra.client.sessions import DioptraRequestsSession


@pytest.fixture
def requests_client(flask_app, db_session, monkeypatch):
    """Use a loopback server, the real multipart encoder, and real login cookies."""
    monkeypatch.setitem(flask_app.config, "LOGIN_DISABLED", False)
    # The db_session fixture owns cleanup of its plain SQLAlchemy Session.
    monkeypatch.setattr(db_session, "remove", lambda: None, raising=False)
    server = make_server("127.0.0.1", 0, flask_app)

    def serve():
        with flask_app.app_context():
            server.serve_forever(poll_interval=0.01)

    thread = Thread(target=serve)
    session = DioptraRequestsSession(f"http://127.0.0.1:{server.server_port}/api/v1")
    session.connect()
    http = session._get_requests_session()
    http.trust_env = False
    http.request = partial(http.request, timeout=5)
    client = DioptraClient(session)
    thread.start()
    try:
        username, password = "upload-user", "upload-password"
        response = client.users.create(username, password)
        assert response.status_code == HTTPStatus.OK, response.text
        group_id = response.json()["groups"][0]["id"]
        response = client.auth.login(username, password)
        assert response.status_code == HTTPStatus.OK, response.text
        yield client, group_id
    finally:
        session.close()
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        assert not thread.is_alive()


@contextmanager
def upload_source(kind, contents):
    """Keep caller-owned streams open until the HTTP request has completed."""
    with ExitStack() as stack:
        if kind == "files":
            yield [
                DioptraFile(name, stack.enter_context(BytesIO(data)), None)
                for name, data in contents.items()
            ]
        else:
            stream = stack.enter_context(BytesIO())
            with tarfile.open(fileobj=stream, mode="w:gz") as archive:
                for name, data in contents.items():
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    archive.addfile(info, BytesIO(data))
            stream.seek(0)
            yield DioptraFile("resources.tar.gz", stream, "application/gzip")


@pytest.mark.parametrize("kind", ["files", "archive"])
@pytest.mark.parametrize("config_path", ["dioptra.toml", "configs/import.toml"])
def test_requests_upload_imports_every_file(requests_client, kind, config_path):
    client, group_id = requests_client
    prefix = "../" if config_path.startswith("configs/") else ""
    contents = {
        config_path: (
            f'[[plugins]]\npath = "{prefix}first"\n'
            f'[[plugins]]\npath = "{prefix}second"\n'
        ).encode(),
        "first/tasks.py": '# UTF-8: caf\u00e9\nVALUE = "first"\n'.encode(),
        "first/empty.py": b"",
        "second/tasks.py": b'VALUE = "second"\n',
    }
    with upload_source(kind, contents) as source:
        response = client.workflows.import_resources(
            group_id, source, config_path=config_path
        )
    assert response.status_code == HTTPStatus.OK, response.text
    plugins = response.json()["resources"]["plugins"]
    assert set(plugins) == {"first", "second"}
    for name, plugin_id in plugins.items():
        response = client.plugins.files.get(plugin_id)
        assert response.status_code == HTTPStatus.OK, response.text
        actual = {}
        for file in response.json()["data"]:
            response = client.plugins.files.get_by_id(plugin_id, file["id"])
            assert response.status_code == HTTPStatus.OK, response.text
            actual[file["filename"]] = response.json()["contents"].encode()
        assert actual == {
            path.removeprefix(f"{name}/"): data
            for path, data in contents.items()
            if path.startswith(f"{name}/")
        }


def test_requests_upload_reports_invalid_manifest_without_importing(
    requests_client,
):
    client, group_id = requests_client
    with upload_source("files", {"dioptra.toml": b"[[plugins"}) as source:
        response = client.workflows.import_resources(group_id, source)
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.text
    response = client.plugins.get()
    assert response.status_code == HTTPStatus.OK, response.text
    assert response.json()["data"] == []


def test_requests_upload_requires_login(requests_client):
    client, group_id = requests_client
    response = client.auth.logout()
    assert response.status_code == HTTPStatus.OK, response.text
    with upload_source("files", {"dioptra.toml": b""}) as source:
        response = client.workflows.import_resources(group_id, source)
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text
