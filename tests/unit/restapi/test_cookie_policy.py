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
"""Authentication cookie behavior under explicitly resolved application modes."""

from http import HTTPStatus
from http.cookies import SimpleCookie

import pytest

from dioptra.restapi.config import _is_windows
from dioptra.restapi.db import db

from .lib.db import setup_ontology


@pytest.fixture
def flask_app(request, app_factory):
    """Use shared API construction with login enabled in the selected mode.

    Each case owns an in-memory database so dev/prod cookie policy is resolved
    independently. The ordinary shared Flask app disables authentication and
    cannot exercise remember-cookie login, but its construction is reused here.
    """
    app = app_factory(
        request.param,
        DIOPTRA_TLS_ALLOWED_AUTHORITIES=["localhost"],
        MLFLOW_TRACKING_URI="file:///unused-cookie-test-mlruns",
    )
    with app.app_context():
        db.create_all()
        setup_ontology(db.session())
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.mark.parametrize(
    "flask_app,base_url,secure",
    [
        ("dev", "http://localhost", False),
        pytest.param(
            "prod",
            "https://localhost",
            True,
            marks=pytest.mark.skipif(
                _is_windows(), reason="Production startup requires a POSIX host."
            ),
        ),
    ],
    indirect=["flask_app"],
)
def test_login_sets_both_cookie_flags_and_preserves_remember_authentication(
    flask_app, client, dioptra_client, base_url, secure
):
    """Emit mode-appropriate cookies and authenticate again from the remember token.

    Real login must set both cookies using the resolved mode's security flags.
    Removing only the session cookie then checks the existing remember-cookie
    authentication path. Development performs the same flow over HTTP. These
    in-process requests inspect WSGI behavior and do not qualify a TLS listener.
    """
    username, password = "cookie-user", "cookie-test-password"
    registered = dioptra_client.users.create(username=username, password=password)
    assert registered.status_code == HTTPStatus.OK
    response = client.post(
        "/api/v1/auth/login",
        base_url=base_url,
        json={"username": username, "password": password},
    )
    assert response.status_code == HTTPStatus.OK
    cookies = SimpleCookie()
    for header in response.headers.getlist("Set-Cookie"):
        cookies.load(header)
    session_name = flask_app.config["SESSION_COOKIE_NAME"]
    remember_name = flask_app.config["REMEMBER_COOKIE_NAME"]
    assert bool(cookies[session_name]["secure"]) is secure
    assert bool(cookies[remember_name]["secure"]) is secure
    client.delete_cookie(session_name)
    restored = client.get("/api/v1/users/current", base_url=base_url)
    assert restored.status_code == HTTPStatus.OK
    assert restored.get_json()["username"] == username
