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

import pytest
import structlog
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from sqlalchemy import select
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import MultiDict

from dioptra.restapi.models import User, UserRegistrationForm, UserRegistrationFormData
from dioptra.restapi.shared.password.service import PasswordService
from dioptra.restapi.user.errors import UsernameNotAvailableError
from dioptra.restapi.user.service import UserService

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
def user_registration_form_data() -> UserRegistrationFormData:
    return UserRegistrationFormData(
        username="test_name",
        password="insecure-password",
        email_address="test_name@example.org",
    )


@pytest.fixture
def password_service(dependency_injector) -> PasswordService:
    return dependency_injector.get(PasswordService)


@pytest.fixture
def user_service(dependency_injector) -> UserService:
    return dependency_injector.get(UserService)


@freeze_time("2020-08-17T18:46:28.717559")
def test_create(
    db: SQLAlchemy,
    user_service: UserService,
    user_registration_form_data: UserRegistrationFormData,
):
    user: User = user_service.create(
        user_registration_form_data=user_registration_form_data
    )

    assert user.user_id == 1
    assert user.username == "test_name"
    assert user.password == "insecure-password"
    assert user.email_address == "test_name@example.org"
    assert user.created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert user.last_modified_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert user.last_login_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert user.user_expire_on == datetime.datetime(9999, 12, 31, 23, 59, 59)
    assert user.password_expire_on == datetime.datetime(2021, 8, 17, 18, 46, 28, 717559)

    with pytest.raises(UsernameNotAvailableError):
        user_service.create(user_registration_form_data=user_registration_form_data)


@freeze_time("2020-08-17T18:46:28.717559")
def test_delete(
    db: SQLAlchemy,
    user_service: UserService,
    user_registration_form_data: UserRegistrationFormData,
):
    user_service.create(user_registration_form_data=user_registration_form_data)

    assert user_service.get_by_id(1).user_id == 1

    deleted_user_ids: list[int] = user_service.delete(1)

    assert deleted_user_ids[0] == 1
    assert user_service.get_by_id(1) is None

    deleted_user: User = db.session.scalars(select(User).filter_by(user_id=1)).one()

    assert deleted_user.user_id == 1
    assert deleted_user.is_deleted


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_by_id(db: SQLAlchemy, user_service: UserService):
    timestamp: datetime.datetime = datetime.datetime.now()
    user_expire_on = datetime.datetime(9999, 12, 31, 23, 59, 59)
    password_expire_on = timestamp.replace(year=timestamp.year + 1)

    new_user: User = User(
        username="test_name",
        password="insecure-password",
        email_address="test_name@example.org",
        created_on=timestamp,
        last_modified_on=timestamp,
        last_login_on=timestamp,
        user_expire_on=user_expire_on,
        password_expire_on=password_expire_on,
    )

    db.session.add(new_user)
    db.session.commit()

    user: User = user_service.get_by_id(1)

    assert user == new_user


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_by_username(db: SQLAlchemy, user_service: UserService):
    timestamp: datetime.datetime = datetime.datetime.now()
    user_expire_on = datetime.datetime(9999, 12, 31, 23, 59, 59)
    password_expire_on = timestamp.replace(year=timestamp.year + 1)

    new_user: User = User(
        username="test_name",
        password="insecure-password",
        email_address="test_name@example.org",
        created_on=timestamp,
        last_modified_on=timestamp,
        last_login_on=timestamp,
        user_expire_on=user_expire_on,
        password_expire_on=password_expire_on,
    )

    db.session.add(new_user)
    db.session.commit()

    user: User = user_service.get_by_username("test_name")

    assert user == new_user


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_all(db: SQLAlchemy, user_service: UserService):
    timestamp: datetime.datetime = datetime.datetime.now()
    user_expire_on = datetime.datetime(9999, 12, 31, 23, 59, 59)
    password_expire_on = timestamp.replace(year=timestamp.year + 1)

    new_user1: User = User(
        username="test_name1",
        password="insecure-password1",
        email_address="test_name1@example.org",
        created_on=timestamp,
        last_modified_on=timestamp,
        last_login_on=timestamp,
        user_expire_on=user_expire_on,
        password_expire_on=password_expire_on,
    )

    new_user2: User = User(
        username="test_name2",
        password="insecure-password2",
        email_address="test_name2@example.org",
        created_on=timestamp,
        last_modified_on=timestamp,
        last_login_on=timestamp,
        user_expire_on=user_expire_on,
        password_expire_on=password_expire_on,
    )

    db.session.add(new_user1)
    db.session.add(new_user2)
    db.session.commit()

    results: list[User] = user_service.get_all()

    assert len(results) == 2
    assert new_user1 in results and new_user2 in results
    assert new_user1.user_id == 1
    assert new_user2.user_id == 2


def test_extract_data_from_form(
    password_service: PasswordService,
    user_service: UserService,
    user_registration_form: UserRegistrationForm,
):
    user_registration_form_data: UserRegistrationFormData = (
        user_service.extract_data_from_form(
            user_registration_form=user_registration_form
        )
    )

    assert user_registration_form_data["username"] == "test_name"
    assert user_registration_form_data["email_address"] == "test_name@example.org"

    assert user_registration_form_data["password"] != "insecure-password"
    assert password_service.verify(
        "insecure-password", user_registration_form_data["password"]
    )
