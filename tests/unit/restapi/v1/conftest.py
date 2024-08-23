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
import textwrap
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from injector import Injector
from pytest import MonkeyPatch

from ..lib import actions, mock_rq


@pytest.fixture
def app(dependency_modules: list[Any]) -> Iterator[Flask]:
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
    user_info = cast(dict[str, Any], registered_users["user1"])
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
def registered_artifacts(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> dict[str, Any]:
    group_id = auth_account["groups"][0]["id"]
    artifact1_response = actions.register_artifact(
        client,
        uri="s3://bucket/model_v1.artifact",
        description="Model artifact.",
        job_id=registered_jobs["job1"]["id"],
        group_id=group_id,
    ).get_json()
    artifact2_response = actions.register_artifact(
        client,
        uri="s3://bucket/cnn.artifact",
        description="Trained conv net model artifact.",
        job_id=registered_jobs["job1"]["id"],
        group_id=group_id,
    ).get_json()
    artifact3_response = actions.register_artifact(
        client,
        uri="s3://bucket/model.artifact",
        description="Another model",
        job_id=registered_jobs["job2"]["id"],
        group_id=group_id,
    ).get_json()
    artifact4_response = actions.register_artifact(
        client,
        uri="s3://bucket/model_v2.artifact",
        description="Fine-tuned model.",
        job_id=registered_jobs["job3"]["id"],
        group_id=group_id,
    ).get_json()

    return {
        "artifact1": artifact1_response,
        "artifact2": artifact2_response,
        "artifact3": artifact3_response,
        "artifact4": artifact4_response,
    }


@pytest.fixture
def registered_models(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> dict[str, Any]:
    group_id = auth_account["groups"][0]["id"]
    model1_response = actions.register_model(
        client,
        name="my_tensorflow_model",
        description="Trained model",
        group_id=group_id,
    ).get_json()
    model2_response = actions.register_model(
        client,
        name="model2",
        description="Trained model",
        group_id=group_id,
    ).get_json()
    model3_response = actions.register_model(
        client,
        name="model3",
        description="",
        group_id=group_id,
    ).get_json()

    # actions.register_model_version(
    #     client,
    #     model_id=model1_response["id"],
    #     artifact_id=registered_artifacts["artifact1"]["id"],
    #     description="initial version",
    # ).get_json()
    # actions.register_model_version(
    #     client,
    #     model_id=model2_response["id"],
    #     artifact_id=registered_artifacts["artifact2"]["id"],
    #     description="initial version",
    # ).get_json()
    # actions.register_model_version(
    #     client,
    #     model_id=model3_response["id"],
    #     artifact_id=registered_artifacts["artifact3"]["id"],
    # ).get_json()
    # actions.register_model_version(
    #     client,
    #     model_id=model1_response["id"],
    #     artifact_id=registered_artifacts["artifact4"]["id"],
    #     description="new version",
    # ).get_json()

    # return {
    #     "model1": actions.get_model(client, model1_response["id"]).get_json(),
    #     "model2": actions.get_model(client, model2_response["id"]).get_json(),
    #     "model3": actions.get_model(client, model3_response["id"]).get_json(),
    # }

    return {
        "model1": model1_response,
        "model2": model2_response,
        "model3": model3_response,
    }


@pytest.fixture
def registered_model_versions(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> dict[str, Any]:
    version1_response = actions.register_model_version(
        client,
        model_id=registered_models["model1"]["id"],
        artifact_id=registered_artifacts["artifact1"]["id"],
        description="initial version",
    ).get_json()
    version2_response = actions.register_model_version(
        client,
        model_id=registered_models["model2"]["id"],
        artifact_id=registered_artifacts["artifact2"]["id"],
        description="initial version",
    ).get_json()
    version3_response = actions.register_model_version(
        client,
        model_id=registered_models["model3"]["id"],
        artifact_id=registered_artifacts["artifact3"]["id"],
        description="initial version",
    ).get_json()
    version4_response = actions.register_model_version(
        client,
        model_id=registered_models["model2"]["id"],
        artifact_id=registered_artifacts["artifact4"]["id"],
        description="Not retrieved.",
    ).get_json()
    version5_response = actions.register_model_version(
        client,
        model_id=registered_models["model1"]["id"],
        artifact_id=registered_artifacts["artifact4"]["id"],
        description="new version",
    ).get_json()

    return {
        "version1": version1_response,
        "version2": version2_response,
        "version3": version3_response,
        "version4": version4_response,
        "version5": version5_response,
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
def registered_plugin_with_files(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
) -> dict[str, Any]:
    plugin_response = actions.register_plugin(
        client,
        name="plugin",
        description="The plugin with files.",
        group_id=auth_account["default_group_id"],
    ).get_json()
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"
        """
    )

    plugin_file1_response = actions.register_plugin_file(
        client,
        plugin_id=plugin_response["id"],
        filename="plugin_file_one.py",
        description="The first plugin file.",
        contents=contents,
    ).get_json()
    plugin_file2_response = actions.register_plugin_file(
        client,
        plugin_id=plugin_response["id"],
        filename="plugin_file_two.py",
        description="The second plugin file.",
        contents=contents,
    ).get_json()
    plugin_file3_response = actions.register_plugin_file(
        client,
        plugin_id=plugin_response["id"],
        filename="plugin_file_three.py",
        description="Not Retrieved.",
        contents=contents,
    ).get_json()
    return {
        "plugin": plugin_response,
        "plugin_file1": plugin_file1_response,
        "plugin_file2": plugin_file2_response,
        "plugin_file3": plugin_file3_response,
    }


@pytest.fixture
def registered_plugin_with_file_and_tasks(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> dict[str, Any]:
    plugin_response = actions.register_plugin(
        client,
        name="plugin",
        description="The plugin with files.",
        group_id=auth_account["default_group_id"],
    ).get_json()
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"


        @pyplugs.register
        def add_one(x: int) -> int:
            return x + 1
        """
    )
    string_type_response = actions.register_plugin_parameter_type(
        client,
        name="string",
        group_id=auth_account["default_group_id"],
        structure=None,
        description="The plugin parameter string type.",
    ).get_json()
    integer_type_response = actions.register_plugin_parameter_type(
        client,
        name="integer",
        group_id=auth_account["default_group_id"],
        structure=None,
        description="The plugin parameter integer type.",
    ).get_json()
    hello_world_task = {
        "name": "hello_world",
        "inputParams": [{"name": "name", "parameterType": string_type_response["id"]}],
        "outputParams": [
            {
                "name": "hello_world_message",
                "parameterType": string_type_response["id"],
            }
        ],
    }
    add_one_task = {
        "name": "add_one",
        "inputParams": [{"name": "x", "parameterType": integer_type_response["id"]}],
        "outputParams": [
            {
                "name": "value",
                "parameterType": integer_type_response["id"],
            }
        ],
    }
    plugin_task_list = [hello_world_task, add_one_task]
    plugin_file_response = actions.register_plugin_file(
        client,
        plugin_id=plugin_response["id"],
        description="The plugin file with tasks.",
        filename="plugin_file.py",
        contents=contents,
        tasks=plugin_task_list,
    ).get_json()
    return {
        "plugin": plugin_response,
        "plugin_file": plugin_file_response,
        "string_parameter_type": string_type_response,
        "integer_parameter_type": integer_type_response,
        "tasks": plugin_task_list,
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
    built_in_types = {"any", "number", "integer", "string", "boolean", "null"}
    response = actions.get_plugin_parameter_types(client).get_json()
    built_in_types_dict = {
        param_type["name"]: param_type
        for param_type in response["data"]
        if param_type["name"] in built_in_types
    }
    plugin_param_type1_response = actions.register_plugin_parameter_type(
        client,
        name="image_shape",
        group_id=auth_account["groups"][0]["id"],
        structure={"list": ["integer"]},
        description="The dimensions of an image",
    ).get_json()
    plugin_param_type2_response = actions.register_plugin_parameter_type(
        client,
        name="model_output",
        group_id=auth_account["groups"][0]["id"],
        structure=dict({"list": ["float"]}),
        description="The softmax scores from a model",
    ).get_json()
    plugin_param_type3_response = actions.register_plugin_parameter_type(
        client,
        name="model",
        group_id=auth_account["groups"][0]["id"],
        structure=dict(),
        description="Opaque type for an ml model",
    ).get_json()
    return {
        **built_in_types_dict,
        "plugin_param_type1": plugin_param_type1_response,
        "plugin_param_type2": plugin_param_type2_response,
        "plugin_param_type3": plugin_param_type3_response,
    }


@pytest.fixture
def registered_experiments(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> dict[str, Any]:
    entrypoint_ids = [
        entrypoint["id"] for entrypoint in registered_entrypoints.values()
    ]
    experiment1_response = actions.register_experiment(
        client,
        name="experiment1",
        group_id=auth_account["default_group_id"],
        description="test description",
        entrypoint_ids=entrypoint_ids,
    ).get_json()
    experiment2_response = actions.register_experiment(
        client,
        name="experiment2",
        group_id=auth_account["default_group_id"],
        description="test description",
        entrypoint_ids=entrypoint_ids,
    ).get_json()
    experiment3_response = actions.register_experiment(
        client,
        name="experiment3",
        group_id=auth_account["default_group_id"],
        description="test description",
        entrypoint_ids=entrypoint_ids,
    ).get_json()
    return {
        "experiment1": experiment1_response,
        "experiment2": experiment2_response,
        "experiment3": experiment3_response,
    }


@pytest.fixture
def registered_entrypoints(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> dict[str, Any]:
    task_graph = textwrap.dedent(
        """# my entrypoint graph
        graph:
          message:
            my_entrypoint: $name
        """
    )
    parameters = [
        {
            "name": "entrypoint_param_1",
            "defaultValue": "default",
            "parameterType": "string",
        },
        {
            "name": "entrypoint_param_2",
            "defaultValue": "1.0",
            "parameterType": "float",
        },
        {
            "name": "entrypoint_param_3",
            "defaultValue": "/path",
            "parameterType": "path",
        },
    ]
    plugin_ids = [registered_plugin_with_files["plugin"]["id"]]
    queue_ids = [queue["id"] for queue in list(registered_queues.values())]
    entrypoint1_response = actions.register_entrypoint(
        client,
        name="entrypoint_one",
        description="The first entrypoint.",
        group_id=auth_account["groups"][0]["id"],
        task_graph=task_graph,
        parameters=parameters,
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    ).get_json()
    entrypoint2_response = actions.register_entrypoint(
        client,
        name="entrypoint_two",
        description="The second entrypoint.",
        group_id=auth_account["groups"][0]["id"],
        task_graph=task_graph,
        parameters=parameters,
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    ).get_json()
    entrypoint3_response = actions.register_entrypoint(
        client,
        name="entrypoint_three",
        description="Not retrieved.",
        group_id=auth_account["groups"][0]["id"],
        task_graph=task_graph,
        parameters=parameters,
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    ).get_json()
    return {
        "entrypoint1": entrypoint1_response,
        "entrypoint2": entrypoint2_response,
        "entrypoint3": entrypoint3_response,
    }


@pytest.fixture
def registered_jobs(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_experiments: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> dict[str, Any]:
    # Inline import necessary to prevent circular import
    import dioptra.restapi.v1.shared.rq_service as rq_service
    monkeypatch.setattr(rq_service, "RQQueue", mock_rq.MockRQQueue)

    queue_id = registered_queues["queue1"]["snapshot"]
    experiment_id = registered_experiments["experiment1"]["snapshot"]
    entrypoint_id = registered_entrypoints["entrypoint1"]["snapshot"]
    values = {
        registered_entrypoints["entrypoint1"]["parameters"][0]["name"]: "new_value",
    }
    timeout = "24h"
    job1_response = actions.register_job(
        client=client,
        queue_id=queue_id,
        experiment_id=experiment_id,
        entrypoint_id=entrypoint_id,
        description="The first job.",
        values=values,
        timeout=timeout,
    ).get_json()
    job2_response = actions.register_job(
        client=client,
        queue_id=queue_id,
        experiment_id=experiment_id,
        entrypoint_id=entrypoint_id,
        description="The second job.",
        values=values,
        timeout=timeout,
    ).get_json()
    job3_response = actions.register_job(
        client=client,
        queue_id=queue_id,
        experiment_id=experiment_id,
        entrypoint_id=entrypoint_id,
        description="Not retrieved.",
        values=values,
        timeout=timeout,
    ).get_json()
    return {
        "job1": job1_response,
        "job2": job2_response,
        "job3": job3_response,
    }
