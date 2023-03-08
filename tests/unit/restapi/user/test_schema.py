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
from flask import Flask
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import MultiDict

from dioptra.restapi.models import User, UserRegistrationForm
from dioptra.restapi.user.schema import UserRegistrationFormSchema, UserSchema

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def user_registration_form(app: Flask) -> UserRegistrationForm:
    with app.test_request_context():
        form = UserRegistrationForm(
            formdata=MultiDict(
                [
                    ("username", "test_name"),
                    ("password", "insecure-password"),
                    ("password_confirm", "insecure-password"),
                    ("email_address", "test_name@example.org"),
                ]
            ),
        )

    return form


@pytest.fixture
def user_schema() -> UserSchema:
    return UserSchema()


@pytest.fixture
def user_registration_form_schema() -> UserRegistrationFormSchema:
    return UserRegistrationFormSchema()


def test_UserSchema_create(user_schema: UserSchema) -> None:
    assert isinstance(user_schema, UserSchema)


def test_UserRegistrationFormSchema_create(
    user_registration_form_schema: UserRegistrationFormSchema,
) -> None:
    assert isinstance(user_registration_form_schema, UserRegistrationFormSchema)


def test_UserSchema_load_works(user_schema: UserSchema) -> None:
    user: User = user_schema.load(
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
    )

    assert user["user_id"] == 1
    assert user["username"] == "test_name"
    assert user["email_address"] == "test_name@example.org"
    assert user["created_on"] == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert user["last_modified_on"] == datetime.datetime(
        2020, 8, 17, 18, 46, 28, 717559
    )
    assert user["last_login_on"] == datetime.datetime(2022, 8, 23, 16, 0, 0, 0)
    assert user["user_expire_on"] == datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)
    assert user["password_expire_on"] == datetime.datetime(
        2022, 12, 31, 23, 59, 59, 999999
    )


def test_UserSchema_dump_works(user_schema: UserSchema) -> None:
    user: User = User(
        user_id=1,
        username="test_name",
        password="insecure-password",
        email_address="test_name@example.org",
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_login_on=datetime.datetime(2022, 8, 23, 16, 0, 0, 0),
        user_expire_on=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999),
        password_expire_on=datetime.datetime(2022, 12, 31, 23, 59, 59, 999999),
    )
    user_serialized: dict[str, Any] = user_schema.dump(user)

    assert user_serialized["userId"] == 1
    assert user_serialized["username"] == "test_name"
    assert user_serialized["emailAddress"] == "test_name@example.org"
    assert user_serialized["createdOn"] == "2020-08-17T18:46:28.717559"
    assert user_serialized["lastModifiedOn"] == "2020-08-17T18:46:28.717559"
    assert user_serialized["lastLoginOn"] == "2022-08-23T16:00:00"
    assert user_serialized["userExpireOn"] == "9999-12-31T23:59:59.999999"
    assert user_serialized["passwordExpireOn"] == "2022-12-31T23:59:59.999999"

    with pytest.raises(KeyError, match=r".*?'password'.*?"):
        assert user_serialized["password"] == "insecure-password"


def test_UserRegistrationFormSchema_dump_works(
    user_registration_form: UserRegistrationForm,
    user_registration_form_schema: UserRegistrationFormSchema,
) -> None:
    user_serialized: dict[str, Any] = user_registration_form_schema.dump(
        user_registration_form
    )

    assert user_serialized["username"] == "test_name"
    assert user_serialized["password"] == "insecure-password"
    assert user_serialized["email_address"] == "test_name@example.org"

    with pytest.raises(KeyError, match=r".*?'password_confirm'.*?"):
        assert user_serialized["password_confirm"] == "insecure-password"


def test_UserRegistrationForm_password_confirm(app: Flask) -> None:
    with app.test_request_context():
        form_confirm_correct = UserRegistrationForm(
            formdata=MultiDict(
                [
                    ("username", "test_name"),
                    ("password", "insecure-password"),
                    ("password_confirm", "insecure-password"),
                    ("email_address", "test_name@example.org"),
                ]
            ),
        )
        form_confirm_error = UserRegistrationForm(
            formdata=MultiDict(
                [
                    ("username", "test_name"),
                    ("password", "insecure-password"),
                    ("password_confirm", "insecure-password-typo"),
                    ("email_address", "test_name@example.org"),
                ]
            ),
        )

    assert form_confirm_correct.validate()
    assert not form_confirm_error.validate()
