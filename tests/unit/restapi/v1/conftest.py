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
"""Fixtures representing resources needed for test suites"""

from typing import Any

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from ..lib import actions


@pytest.fixture
def registered_users(client: FlaskClient, db: SQLAlchemy) -> dict[str, Any]:
    user1_response = actions.register_user(client, "user1", "user1@example.org")
    user2_response = actions.register_user(client, "user2", "user2@example.org")
    user3_response = actions.register_user(client, "user3", "user3@example.org")
    return {
        "user1": user1_response,
        "user2": user2_response,
        "user3": user3_response,
    }


@pytest.fixture
def auth_account(
    client: FlaskClient,
    db: SQLAlchemy,
    registered_users: dict[str, Any],  # noqa: F811
) -> dict[str, Any]:
    user_info = registered_users["user1"].json()
    actions.login(
        client, username=user_info["username"], password=user_info["password"]
    )
    return user_info


@pytest.fixture
def registered_queues(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
) -> dict[str, Any]:
    queue1_response = actions.register_queue(
        client,
        name="tensorflow_cpu",
        description="The first queue.",
        group_id=auth_account["default_group_id"],
    )
    queue2_response = actions.register_queue(
        client,
        name="tensorflow_gpu",
        description="The second queue.",
        group_id=auth_account["default_group_id"],
    )
    queue3_response = actions.register_queue(
        client,
        name="pytorch_cpu",
        description="Not retrieved.",
        group_id=auth_account["default_group_id"],
    )
    return {
        "queue1": queue1_response,
        "queue2": queue2_response,
        "queue3": queue3_response,
    }
