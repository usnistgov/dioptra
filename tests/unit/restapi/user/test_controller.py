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
from __future__ import annotations

import datetime
from typing import Any

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog.stdlib import BoundLogger

from dioptra.restapi.models import User
from dioptra.restapi.user.routes import BASE_ROUTE as USER_BASE_ROUTE
from dioptra.restapi.user.service import UserService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def user_registration_request() -> dict[str, Any]:
    return {
        "username": "test_name",
        "password": "insecure-password",
        "password_confirm": "insecure-password",
        "email_address": "test_name@example.org",
    }


def test_user_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetall(self, *args, **kwargs) -> list[User]:
        LOGGER.info("Mocking UserService.get_all()")
        user: User = User(
            user_id=1,
            username="test_name",
            email_address="test_name@example.org",
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_login_on=datetime.datetime(2022, 8, 23, 16, 0, 0),
            user_expire_on=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999),
            password_expire_on=datetime.datetime(2022, 12, 31, 23, 59, 59, 999999),
        )
        return [user]

    monkeypatch.setattr(UserService, "get_all", mockgetall)

    with app.test_client() as client:
        response: list[dict[str, Any]] = client.get(
            f"/api/{USER_BASE_ROUTE}/"
        ).get_json()

        expected: list[dict[str, Any]] = [
            {
                "userId": 1,
                "username": "test_name",
                "emailAddress": "test_name@example.org",
                "createdOn": "2020-08-17T18:46:28.717559",
                "lastModifiedOn": "2020-08-17T18:46:28.717559",
                "lastLoginOn": "2022-08-23T16:00:00",
                "userExpireOn": "9999-12-31T23:59:59.999999",
                "passwordExpireOn": "2022-12-31T23:59:59.999999",
            }
        ]

        assert response == expected


@freeze_time("2020-08-17T18:46:28.717559")
def test_user_resource_post(
    app: Flask,
    db: SQLAlchemy,
    user_registration_request: dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockcreate(*args, **kwargs) -> User:
        LOGGER.info("Mocking UserService.create()")
        timestamp = datetime.datetime.now()
        user_expire_on = datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)
        password_expire_on = timestamp.replace(year=timestamp.year + 1)

        return User(
            user_id=1,
            username="test_name",
            password="insecure-password",
            email_address="test_name@example.org",
            created_on=timestamp,
            last_modified_on=timestamp,
            last_login_on=timestamp,
            user_expire_on=user_expire_on,
            password_expire_on=password_expire_on,
        )

    monkeypatch.setattr(UserService, "create", mockcreate)

    with app.test_client() as client:
        response: dict[str, Any] = client.post(
            f"/api/{USER_BASE_ROUTE}/",
            content_type="multipart/form-data",
            data=user_registration_request,
            follow_redirects=True,
        ).get_json()
        LOGGER.info("Response received", response=response)

        expected: dict[str, Any] = {
            "userId": 1,
            "username": "test_name",
            "emailAddress": "test_name@example.org",
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModifiedOn": "2020-08-17T18:46:28.717559",
            "lastLoginOn": "2020-08-17T18:46:28.717559",
            "userExpireOn": "9999-12-31T23:59:59.999999",
            "passwordExpireOn": "2021-08-17T18:46:28.717559",
        }

        assert response == expected


def test_user_id_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyid(self, user_id: str, *args, **kwargs) -> User:
        LOGGER.info("Mocking UserService.get_by_id()")
        return User(
            user_id=1,
            username="test_name",
            password="insecure-password",
            email_address="test_name@example.org",
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_login_on=datetime.datetime(2022, 8, 23, 16, 0, 0),
            user_expire_on=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999),
            password_expire_on=datetime.datetime(2021, 8, 17, 18, 46, 28, 717559),
        )

    monkeypatch.setattr(UserService, "get_by_id", mockgetbyid)
    user_id: int = 1

    with app.test_client() as client:
        response: dict[str, Any] = client.get(
            f"/api/{USER_BASE_ROUTE}/{user_id}"
        ).get_json()

        expected: dict[str, Any] = {
            "userId": 1,
            "username": "test_name",
            "emailAddress": "test_name@example.org",
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModifiedOn": "2020-08-17T18:46:28.717559",
            "lastLoginOn": "2022-08-23T16:00:00",
            "userExpireOn": "9999-12-31T23:59:59.999999",
            "passwordExpireOn": "2021-08-17T18:46:28.717559",
        }

        assert response == expected
