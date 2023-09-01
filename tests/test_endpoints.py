from __future__ import annotations

import pytest
from flask.testing import FlaskClient


@pytest.mark.parametrize("method", ["get", "put", "post"])
def test_hello_endpoint(client: FlaskClient, method: str) -> None:
    response = getattr(client, method)("/api/hello", follow_redirects=True)
    assert response.json == "Hello, World!"


@pytest.mark.parametrize("endpoint", ["/api/test", "/api/world", "/api/foo"])
def test_endpoints_before_login(client: FlaskClient, endpoint: str) -> None:
    response = client.get(endpoint, follow_redirects=True)
    assert response.status_code == 401


@pytest.mark.parametrize("method", ["get", "put", "post"])
def test_test_endpoint_after_login(
    client: FlaskClient, login: None, method: str
) -> None:
    response = getattr(client, method)("/api/test", follow_redirects=True)
    assert response.json == "dev"


@pytest.mark.parametrize("method", ["get", "put", "post"])
def test_world_endpoint_after_login(
    client: FlaskClient, login: None, method: str
) -> None:
    response = getattr(client, method)("/api/world", follow_redirects=True)
    expected_response = {"id": 1, "name": "test_user", "deleted": False}
    actual_response = {
        "id": response.json["id"],
        "name": response.json["name"],
        "deleted": response.json["deleted"],
    }
    assert expected_response == actual_response


@pytest.mark.parametrize("method", ["get", "put"])
def test_foo_endpoint_after_login(
    client: FlaskClient, login: None, method: str
) -> None:
    response = getattr(client, method)("/api/foo", follow_redirects=True)
    assert response.json == "bar"


def test_post_foo_endpoint_after_login(client: FlaskClient, login: None) -> None:
    response = client.post("/api/foo", json={"baz": "thud"}, follow_redirects=True)
    assert response.json == {"baz": "thud"}
