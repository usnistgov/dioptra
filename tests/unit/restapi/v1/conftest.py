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
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from injector import Injector

from ..lib import actions


@pytest.fixture
def app(dependency_modules: list[Any]) -> Flask:
    from dioptra.restapi import create_app

    injector = Injector(dependency_modules)
    app = create_app(env="test_v1", injector=injector)

    yield app


@pytest.fixture
def registered_users(client: FlaskClient, db: SQLAlchemy) -> dict[str, Any]:
    password = "supersecurepassword"
    user1_response = actions.register_user(
        client, "user1", "user1@example.org", password
    ).get_json()
    user2_response = actions.register_user(
        client, "user2", "user2@example.net", password
    ).get_json()
    user3_response = actions.register_user(
        client, "name", "user3@example.org", password
    ).get_json()
    users_info = {
        "user1": user1_response,
        "user2": user2_response,
        "user3": user3_response,
    }

    for _, user_info in users_info.items():
        user_info["password"] = password
        user_info["default_group_id"] = user_info["groups"][0]["id"]

    return users_info


@pytest.fixture
def auth_account(
    client: FlaskClient,
    db: SQLAlchemy,
    registered_users: dict[str, Any],  # noqa: F811
) -> dict[str, Any]:
    user_info = registered_users["user1"]
    login_response = actions.login(
        client, username=user_info["username"], password=user_info["password"]
    )
    if login_response.status_code != 200:
        raise ValueError("User login failed.")
    return user_info


@pytest.fixture
def registered_tags(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
) -> dict[str, Any]:
    tag1_response = actions.register_tag(
        client,
        name="tag_one",
        group_id=auth_account["default_group_id"],
    ).get_json()
    tag2_response = actions.register_tag(
        client,
        name="tag_two",
        group_id=auth_account["default_group_id"],
    ).get_json()
    tag3_response = actions.register_tag(
        client,
        name="name",
        group_id=auth_account["default_group_id"],
    ).get_json()
    return {
        "tag1": tag1_response,
        "tag2": tag2_response,
        "tag3": tag3_response,
    }


@pytest.fixture
def registered_plugins(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
) -> dict[str, Any]:
    plugin1_response = actions.register_plugin(
        client,
        name="plugin_one",
        description="The first plugin.",
        group_id=auth_account["groups"][0]["id"],
    ).get_json()
    plugin2_response = actions.register_plugin(
        client,
        name="plugin_two",
        description="The second plugin.",
        group_id=auth_account["groups"][0]["id"],
    ).get_json()
    plugin3_response = actions.register_plugin(
        client,
        name="plugin_three",
        description="Not retrieved.",
        group_id=auth_account["groups"][0]["id"],
    ).get_json()
    return {
        "plugin1": plugin1_response,
        "plugin2": plugin2_response,
        "plugin3": plugin3_response,
    }


@pytest.fixture
def registered_queues(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
) -> dict[str, Any]:
    queue1_response = actions.register_queue(
        client,
        name="tensorflow_cpu",
        description="The first queue.",
        group_id=auth_account["groups"][0]["id"],
    ).get_json()
    queue2_response = actions.register_queue(
        client,
        name="tensorflow_gpu",
        description="The second queue.",
        group_id=auth_account["groups"][0]["id"],
    ).get_json()
    queue3_response = actions.register_queue(
        client,
        name="pytorch_cpu",
        description="Not retrieved.",
        group_id=auth_account["groups"][0]["id"],
    ).get_json()
    return {
        "queue1": queue1_response,
        "queue2": queue2_response,
        "queue3": queue3_response,
    }


@pytest.fixture
def registered_groups(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
) -> dict[str, Any]:
    public_response = actions.get_public_group(client).get_json()
    # group1_response = actions.register_group(
    # client,
    #  name="group_one",
    # ).get_json()
    # group2_response = actions.register_group(
    # client,
    # name="group_two",
    # ).get_json()
    # group3_response = actions.register_group(
    # client,
    # name="group_three",
    # ).get_json()
    return {
        "public": public_response,
        # "group1": group1_response,
        # "group2": group2_response,
        # "group3": group3_response,
    }


@pytest.fixture
def registered_plugin_parameter_types(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
) -> dict[str, Any]:
    plugin_param_type1_response = actions.register_plugin_parameter_type(
        client,
        name="int",
        group_id=auth_account["groups"][0]["id"],
        structure=dict(),
        description="The first parameter type.",
    ).get_json()
    plugin_param_type2_response = actions.register_plugin_parameter_type(
        client,
        name="integer",
        group_id=auth_account["groups"][0]["id"],
        structure=dict(),
        description="The second parameter type.",
    ).get_json()
    # This is intentionally named using a different pattern for search query testing
    plugin_param_type3_response = actions.register_plugin_parameter_type(
        client,
        name="string",
        group_id=auth_account["groups"][0]["id"],
        structure=dict(),
        description="Not retrieved.",
    ).get_json()
    return {
        "plugin_param_type1": plugin_param_type1_response,
        "plugin_param_type2": plugin_param_type2_response,
        "plugin_param_type3": plugin_param_type3_response,
    }


@pytest.fixture
def registered_experiments(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
) -> dict[str, Any]:
    experiment1_response = actions.register_experiment(
        client,
        name="experiment1",
        group_id=auth_account["default_group_id"],
        description="test description",
        entrypoint_ids=list(),
    ).get_json()
    experiment2_response = actions.register_experiment(
        client,
        name="experiment2",
        group_id=auth_account["default_group_id"],
        description="test description",
        entrypoint_ids=list(),
    ).get_json()
    experiment3_response = actions.register_experiment(
        client,
        name="experiment3",
        group_id=auth_account["default_group_id"],
        description="test description",
        entrypoint_ids=list(),
    ).get_json()
    return {
        "experiment1": experiment1_response,
        "experiment2": experiment2_response,
        "experiment3": experiment3_response,
    }
