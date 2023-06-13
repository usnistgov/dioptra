from urllib.parse import quote
import pytest
import requests
import responses
from dioptra.task_engine.completion import complete, CompletionPolicy
from dioptra.task_engine.validation import is_valid

_DIOPTRA_RESTAPI_BASE_URL = "http://restapi:5000/"


class DummyDioptraClient:
    # Required to distinguish a null type definition (for a simple type)
    # from type-not-found.  Retain None as a not-found value; use this as a
    # null definition return value.
    NULL_TYPE_DEFINITION = object()

    def __init__(self, base_url):
        self.api_url = base_url + "api/"

    @property
    def task_plugin_endpoint(self):
        return self.api_url + "taskPlugin/"

    @property
    def task_plugin_definitions_endpoint(self):
        return self.task_plugin_endpoint + "definitions/"

    @property
    def task_plugin_definitions_builtins_endpoint(self):
        return self.task_plugin_definitions_endpoint + "dioptra_builtins/"

    @property
    def task_plugin_definitions_custom_endpoint(self):
        return self.task_plugin_definitions_endpoint + "dioptra_custom/"

    @property
    def types_endpoint(self):
        return self.api_url + "types/"

    def get_task_definition(self, task_id, allow_custom_task_plugins=True):
        """
        Get a task definition from the REST API.

        Args:
            task_id: The task identifier to look up
            allow_custom_task_plugins: A boolean flag which determines whether
                the custom task plugin collection is searched.  The builtins
                collection is always searched first; if this flag is True,
                the custom collection is searched as a fallback.

        Returns:
            A task definition if one was found, None if one was not found.
        """
        url = self.task_plugin_definitions_builtins_endpoint + quote(task_id)
        definition = None

        resp = requests.get(url)

        if resp.status_code == 404:
            if allow_custom_task_plugins:
                url = self.task_plugin_definitions_custom_endpoint \
                    + quote(task_id)
                resp = requests.get(url)

                if resp.status_code != 404:
                    definition = resp.json()
        else:
            definition = resp.json()

        return definition

    def get_type_definition(self, type_name):
        """
        Get a type definition from the REST API.

        Args:
            type_name: The name of the type to look up

        Returns:
            A type definition, or None if one was not found.  None happens
            also to be a valid type definition (for simple types), so to
            disambiguate the null type definition from the not-found condition,
            a null type definition is returned as a special value,
            DioptraClient.NULL_TYPE_DEFINITION.
        """
        url = self.types_endpoint + quote(type_name)
        resp = requests.get(url)

        if resp.status_code == 404:
            definition = None
        else:
            definition = resp.json()
            if definition is None:
                definition = self.NULL_TYPE_DEFINITION

        return definition


@pytest.fixture
def dioptra_client():
    dummy_client = DummyDioptraClient(_DIOPTRA_RESTAPI_BASE_URL)
    return dummy_client


def test_schema_validation(dioptra_client):
    # Just ensure we get validation issues if an experiment description is
    # invalid, not a crash.
    invalid_experiment_desc = {
        "foo": 1
    }

    issues = complete(invalid_experiment_desc, dioptra_client)

    assert issues


@responses.activate
def test_complete_task_builtins_ok(dioptra_client):
    url = dioptra_client.task_plugin_definitions_builtins_endpoint + "foo"
    responses.get(
        url,
        json={
            "plugin": "org.example.foo",
            "inputs": [
                {"in": "string"}
            ],
            "outputs": {"out": "string"}
        }
    )

    experiment_desc = {
        "graph": {
            "step1": {
                "foo": "hello"
            }
        }
    }

    issues = complete(experiment_desc, dioptra_client)

    responses.assert_call_count(url, 1)

    assert not issues
    assert experiment_desc == {
        "tasks": {
            "foo": {
                "plugin": "org.example.foo",
                "inputs": [
                    {"in": "string"}
                ],
                "outputs": {"out": "string"}
            }
        },
        "graph": {
            "step1": {
                "foo": "hello"
            }
        }
    }

    assert is_valid(experiment_desc)


@responses.activate
def test_complete_task_custom_ok(dioptra_client):
    builtin_url = dioptra_client.task_plugin_definitions_builtins_endpoint + "foo"
    custom_url = dioptra_client.task_plugin_definitions_custom_endpoint + "foo"

    responses.get(builtin_url, status=404)

    responses.get(
        custom_url,
        json={
            "plugin": "org.example.foo",
            "inputs": [
                {"in": "string"}
            ],
            "outputs": {"out": "string"}
        }
    )

    experiment_desc = {
        "tasks": {},
        "graph": {
            "step1": {
                "foo": "hello"
            }
        }
    }

    issues = complete(experiment_desc, dioptra_client)

    responses.assert_call_count(builtin_url, 1)
    responses.assert_call_count(custom_url, 1)

    assert not issues
    assert experiment_desc == {
        "tasks": {
            "foo": {
                "plugin": "org.example.foo",
                "inputs": [
                    {"in": "string"}
                ],
                "outputs": {"out": "string"}
            }
        },
        "graph": {
            "step1": {
                "foo": "hello"
            }
        }
    }

    assert is_valid(experiment_desc)


@responses.activate
def test_complete_task_not_found_allow_custom(dioptra_client):
    builtin_url = dioptra_client.task_plugin_definitions_builtins_endpoint + "foo"
    custom_url = dioptra_client.task_plugin_definitions_custom_endpoint + "foo"

    responses.get(builtin_url, status=404)
    responses.get(custom_url, status=404)

    experiment_desc = {
        "tasks": {
            "bar": {
                "plugin": "org.example.bar"
            }
        },
        "graph": {
            "step1": {
                "foo": "hello"
            },
            "step2": {
                "bar": []
            }
        }
    }

    issues = complete(experiment_desc, dioptra_client, CompletionPolicy.ENRICH)

    responses.assert_call_count(builtin_url, 1)
    responses.assert_call_count(custom_url, 1)

    assert issues
    assert not is_valid(experiment_desc)

    # ensure the description has not changed
    assert experiment_desc == {
        "tasks": {
            "bar": {
                "plugin": "org.example.bar"
            }
        },
        "graph": {
            "step1": {
                "foo": "hello"
            },
            "step2": {
                "bar": []
            }
        }
    }


@responses.activate
def test_complete_task_not_found_no_custom(dioptra_client):
    builtin_url = dioptra_client.task_plugin_definitions_builtins_endpoint + "foo"

    responses.get(builtin_url, status=404)

    experiment_desc = {
        "tasks": {
            "bar": {
                "plugin": "org.example.bar"
            }
        },
        "graph": {
            "step1": {
                "foo": "hello"
            },
            "step2": {
                "bar": []
            }
        }
    }

    issues = complete(
        experiment_desc, dioptra_client, CompletionPolicy.ENRICH,
        allow_custom_task_plugins=False
    )

    responses.assert_call_count(builtin_url, 1)

    assert issues
    assert not is_valid(experiment_desc)

    # ensure the description has not changed
    assert experiment_desc == {
        "tasks": {
            "bar": {
                "plugin": "org.example.bar"
            }
        },
        "graph": {
            "step1": {
                "foo": "hello"
            },
            "step2": {
                "bar": []
            }
        }
    }


@responses.activate
def test_complete_type_from_task_io_ok(dioptra_client):
    experiment_desc = {
        "parameters": {
            # Easy way to produce an "in_type" type inference so that type
            # validation succeeds.
            "value_with_in_type": {
                "type": "in_type"
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [
                    {"in": "in_type"}
                ],
                "outputs": {
                    "out": "out_type"
                }
            }
        },
        "graph": {
            "step1": {
                "task1": "$value_with_in_type"
            }
        }
    }

    in_url = dioptra_client.types_endpoint + "in_type"
    out_url = dioptra_client.types_endpoint + "out_type"
    responses.get(
        in_url,
        # json=None  # does not work; responses interprets as empty body.
        # The below is a workaround.
        body="null",
        content_type="application/json"
    )
    responses.get(
        out_url,
        body="null",
        content_type="application/json"
    )

    issues = complete(experiment_desc, dioptra_client, CompletionPolicy.ENRICH)

    assert not issues
    assert responses.assert_call_count(in_url, 1)
    assert responses.assert_call_count(out_url, 1)

    assert experiment_desc == {
        "types": {
            "in_type": None,
            "out_type": None
        },
        "parameters": {
            "value_with_in_type": {
                "type": "in_type"
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [
                    {"in": "in_type"}
                ],
                "outputs": {
                    "out": "out_type"
                }
            }
        },
        "graph": {
            "step1": {
                "task1": "$value_with_in_type"
            }
        }
    }

    assert is_valid(experiment_desc)


@responses.activate
def test_complete_type_from_param_ok(dioptra_client):
    url = dioptra_client.types_endpoint + "foo"
    responses.get(
        url,
        json={
            "list": "string"
        }
    )

    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.task1"
            }
        },
        "parameters": {
            "param1": {
                "type": "foo"
            }
        },
        "graph": {
            "step1": {
                "task1": []
            }
        }
    }

    issues = complete(experiment_desc, dioptra_client, CompletionPolicy.ENRICH)

    responses.assert_call_count(url, 1)

    assert not issues
    assert experiment_desc == {
        "types": {
            "foo": {
                "list": "string"
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1"
            }
        },
        "parameters": {
            "param1": {
                "type": "foo"
            }
        },
        "graph": {
            "step1": {
                "task1": []
            }
        }
    }

    assert is_valid(experiment_desc)


@responses.activate
def test_complete_type_nested_ok(dioptra_client):

    experiment_desc = {
        "types": {
            "out_type": {
                "union": ["string", "nested_type"]
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": [
                    {"out": "out_type"}
                ]
            }
        },
        "graph": {
            "step1": {
                "task1": []
            }
        }
    }

    nested_url = dioptra_client.types_endpoint + "nested_type"
    nested2_url = dioptra_client.types_endpoint + "nested_type2"

    responses.get(
        nested_url,
        json={
            # should trigger a second type definition query
            "list": "nested_type2"
        }
    )

    responses.get(
        nested2_url,
        json={
            "mapping": ["string", "boolean"]
        }
    )

    issues = complete(experiment_desc, dioptra_client, CompletionPolicy.ENRICH)

    responses.assert_call_count(nested_url, 1)
    responses.assert_call_count(nested2_url, 1)

    assert not issues

    assert experiment_desc == {
        "types": {
            "out_type": {
                "union": ["string", "nested_type"]
            },
            "nested_type": {
                "list": "nested_type2"
            },
            "nested_type2": {
               "mapping": ["string", "boolean"]
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": [
                    {"out": "out_type"}
                ]
            }
        },
        "graph": {
            "step1": {
                "task1": []
            }
        }
    }

    assert is_valid(experiment_desc)


@responses.activate
def test_complete_type_not_found(dioptra_client):

    experiment_desc = {
        "parameters": {
            "param1": {
                "type": "in_type"
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [
                    {"in": "in_type"}
                ]
            }
        },
        "graph": {
            "step1": {
                "task1": "$param1"
            }
        }
    }

    in_type_url = dioptra_client.types_endpoint + "in_type"
    nested_type_url = dioptra_client.types_endpoint + "nested_type"

    responses.get(
        in_type_url,
        json={
            "list": "nested_type"
        }
    )

    responses.get(nested_type_url, status=404)

    issues = complete(experiment_desc, dioptra_client, CompletionPolicy.ENRICH)

    responses.assert_call_count(in_type_url, 1)
    responses.assert_call_count(nested_type_url, 1)
    assert issues

    assert experiment_desc == {
        "types": {
            # Completion currently adds the types it can find, and omits
            # those it can't.
            "in_type": {
                "list": "nested_type"
            }
        },
        "parameters": {
            "param1": {
                "type": "in_type"
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [
                    {"in": "in_type"}
                ]
            }
        },
        "graph": {
            "step1": {
                "task1": "$param1"
            }
        }
    }


@responses.activate
def test_complete_type_cycle(dioptra_client):

    experiment_desc = {
        "graph": {
            "step1": {
                "task1": []
            }
        }
    }

    task1_url = dioptra_client.task_plugin_definitions_builtins_endpoint + "task1"
    out_type_url = dioptra_client.types_endpoint + "out_type"

    responses.get(
        task1_url,
        json={
            "plugin": "org.example.task1",
            "outputs": {
                "out": "out_type"
            }
        }
    )

    responses.get(
        out_type_url,
        json={
            # this causes a type reference cycle
            "list": "out_type"
        }
    )

    issues = complete(
        experiment_desc, dioptra_client, policy=CompletionPolicy.ENRICH
    )

    responses.assert_call_count(task1_url, 1)
    responses.assert_call_count(out_type_url, 1)

    # A type reference cycle is not an error at this stage.  The validation
    # module will pick up that error.
    assert not issues

    assert experiment_desc == {
        "types": {
            "out_type": {
                "list": "out_type"
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": {
                    "out": "out_type"
                }
            }
        },
        "graph": {
            "step1": {
                "task1": []
            }
        }
    }

    # The cycle issue is detected here.
    assert not is_valid(experiment_desc)


def test_remove_unused_tasks(dioptra_client):
    experiment_desc = {
        "tasks": {
            "unused1": {
                "plugin": "org.example.unused1"
            },
            "unused2": {
                "plugin": "org.example.unused2"
            },
            "used": {
                "plugin": "org.example.used"
            }
        },
        "graph": {
            "step1": {
                "used": []
            }
        }
    }

    issues = complete(experiment_desc, dioptra_client, CompletionPolicy.ENRICH)

    assert not issues

    assert experiment_desc == {
        "tasks": {
            "used": {
                "plugin": "org.example.used"
            }
        },
        "graph": {
            "step1": {
                "used": []
            }
        }
    }

    assert is_valid(experiment_desc)


def test_remove_unused_types(dioptra_client):
    experiment_desc = {
        "types": {
            # This type will be considered unused because it is referred to
            # from an unused task.
            "unused_type": {
                "tuple": ["string", "integer"]
            }
        },
        "tasks": {
            "unused1": {
                "plugin": "org.example.unused1",
                "inputs": [
                    {"in": "unused_type"}
                ]
            },
            "unused2": {
                "plugin": "org.example.unused2"
            },
            "used": {
                "plugin": "org.example.used",
                "inputs": [
                    {"in": "integer"}
                ]
            }
        },
        "graph": {
            "step1": {
                "used": 1
            }
        }
    }

    issues = complete(experiment_desc, dioptra_client, CompletionPolicy.ENRICH)

    assert not issues

    assert experiment_desc == {
        "tasks": {
            "used": {
                "plugin": "org.example.used",
                "inputs": [
                    {"in": "integer"}
                ]
            }
        },
        "graph": {
            "step1": {
                "used": 1
            }
        }
    }

    assert is_valid(experiment_desc)


@responses.activate
def test_policy_override_ok(dioptra_client):

    type1_url = dioptra_client.types_endpoint + "type1"
    type2_url = dioptra_client.types_endpoint + "type2"
    task1_url_builtin = dioptra_client.task_plugin_definitions_builtins_endpoint + "task1"
    task2_url_builtin = dioptra_client.task_plugin_definitions_builtins_endpoint + "task2"
    task2_url_custom = dioptra_client.task_plugin_definitions_custom_endpoint + "task2"

    # These will be our overrides
    responses.get(
        type1_url,
        json={
            "list": "number"
        }
    )

    responses.get(
        task1_url_builtin,
        json={
            "plugin": "org.example.override.task1",
            "inputs": [
                {
                    "name": "in1",
                    "type": "type1",
                    "required": False
                }
            ]
        }
    )

    # Type/task2 are not overridden, but the completion module must check
    # to be sure, so we have to mock them.
    responses.get(type2_url, status=404)
    responses.get(task2_url_builtin, status=404)
    responses.get(task2_url_custom, status=404)

    experiment_desc = {
        "types": {
            "type1": {
                "tuple": ["number", "number"]
            },
            "type2": {
                "mapping": {
                    "name": "string",
                    "age": "integer"
                }
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [
                    {
                        "name": "in1",
                        "type": "type1",
                        "required": False
                    }
                ]
            },
            "task2": {
                "plugin": "org.example.task2",
                "inputs": [
                    {"in1": "type2"}
                ]
            }
        },
        "graph": {
            "step1": {
                "task1": [[12, 34.5]]
            },
            "step2": {
                "task2": {
                    "in1": {
                        "name": "alice",
                        "age": 55
                    }
                }
            }
        }
    }

    issues = complete(
        experiment_desc, dioptra_client, CompletionPolicy.OVERRIDE
    )

    assert responses.assert_call_count(type1_url, 1)
    assert responses.assert_call_count(type2_url, 1)
    assert responses.assert_call_count(task1_url_builtin, 1)
    assert responses.assert_call_count(task2_url_builtin, 1)
    assert responses.assert_call_count(task2_url_custom, 1)

    assert not issues

    # Ensure the required overrides happened for type1 and task1, and type2
    # and task2 were left alone.
    assert experiment_desc == {
        "types": {
            "type1": {
                "list": "number"
            },
            "type2": {
                "mapping": {
                    "name": "string",
                    "age": "integer"
                }
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.override.task1",
                "inputs": [
                    {
                        "name": "in1",
                        "type": "type1",
                        "required": False
                    }
                ]
            },
            "task2": {
                "plugin": "org.example.task2",
                "inputs": [
                    {"in1": "type2"}
                ]
            }
        },
        "graph": {
            "step1": {
                "task1": [[12, 34.5]]
            },
            "step2": {
                "task2": {
                    "in1": {
                        "name": "alice",
                        "age": 55
                    }
                }
            }
        }
    }

    assert is_valid(experiment_desc)


@responses.activate
def test_policy_strict_ok(dioptra_client):

    type1_url = dioptra_client.types_endpoint + "type1"
    task1_url_builtins = dioptra_client.task_plugin_definitions_builtins_endpoint + "task1"

    responses.get(
        type1_url,
        json={
            "list": "number"
        }
    )

    responses.get(
        task1_url_builtins,
        json={
            "plugin": "org.example.server_task1",
            "inputs": [
                {"in1": "type1"}
            ]
        }
    )

    # there will be no queries for unused_type or unused_task because in
    # "strict" mode, the task/type definitions are all deleted.  So the
    # presence of extraneous definitions has no effect.

    experiment_desc = {
        "types": {
            "type1": {
                "list": "integer"
            },
            "unused_type": None
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [
                    {"in1": "type1"}
                ]
            },
            "unused_task": {
                "plugin": "org.example.unused"
            }
        },
        "parameters": {
            "param1": {
                "type": "type1"
            }
        },
        "graph": {
             "step1": {
                 "task1": "$param1"
             }
        }
    }

    issues = complete(experiment_desc, dioptra_client, CompletionPolicy.STRICT)

    assert not issues
    responses.assert_call_count(type1_url, 1)
    responses.assert_call_count(task1_url_builtins, 1)

    assert experiment_desc == {
        "types": {
            "type1": {
                "list": "number"
            }
        },
        "tasks": {
            "task1": {
                "plugin": "org.example.server_task1",
                "inputs": [
                    {"in1": "type1"}
                ]
            }
        },
        "parameters": {
            "param1": {
                "type": "type1"
            }
        },
        "graph": {
             "step1": {
                 "task1": "$param1"
             }
        }
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "completion_policy", [
        CompletionPolicy.ENRICH,
        CompletionPolicy.OVERRIDE,
        CompletionPolicy.STRICT
    ]
)
@responses.activate
def test_task_not_found_all_policies(dioptra_client, completion_policy):

    experiment_desc = {
        "tasks": {
            "unused_task": {
                "plugin": "org.example.unused"
            }
        },
        "graph": {
            "step1": {
                "unknown_task": []
            }
        }
    }

    unknown_task_url_builtin = dioptra_client.task_plugin_definitions_builtins_endpoint + "unknown_task"
    unknown_task_url_custom = dioptra_client.task_plugin_definitions_custom_endpoint + "unknown_task"

    responses.get(unknown_task_url_builtin, status=404)
    responses.get(unknown_task_url_custom, status=404)

    issues = complete(experiment_desc, dioptra_client, completion_policy)

    responses.assert_call_count(unknown_task_url_builtin, 1)
    responses.assert_call_count(unknown_task_url_custom, 1)

    assert issues
    assert experiment_desc == {
        "graph": {
            "step1": {
                "unknown_task": []
            }
        }
    }


def test_policy_none(dioptra_client):

    # With NONE completion policy, the experiment is ignored altogether, so it
    # doesn't matter what it is.
    experiment_desc = 1

    issues = complete(
        experiment_desc, dioptra_client, policy=CompletionPolicy.NONE
    )

    assert not issues
