import pytest

from dioptra.task_engine.validation import is_valid


@pytest.mark.parametrize("experiment_desc", [
    None,
    1,
    True,
    "foo",
    {},
    [],
    {"graph": {}},
    {"tasks": {}},
    {"foo": "bar"},
    ["foo"],
    {
        "parameters": ["param1"],
        "tasks": {
            "add": {
                "plugin": "org.example.add"
            }
        },
        "graph": {
            "step1": {
                "add": [1, 2, 3]
            }
        },
        "extra": "property"
    }
])
def test_invalid_description(experiment_desc):
    # I don't test the error messages; they are just prose-y strings, and
    # we should be able to change wording without breaking a bunch of unit
    # tests, right?
    assert not is_valid(experiment_desc)


@pytest.mark.parametrize("parameters", [
    [],
    ["arg1"],
    ["arg1", "arg2"],
    {},
    {"arg1": None},
    {"arg1": "default_value"},
    {"arg1": {"default": None}},
    {"arg1": {"default": "default_value"}}
])
def test_valid_parameters(parameters):

    # Since we are strictly testing the parameters part, we just parameterize
    # that part, and insert it into an otherwise valid description.
    experiment_desc = {
        "parameters": parameters,
        "tasks": {
            "add": {
                "plugin": "org.example.add"
            }
        },
        "graph": {
            "step1": {
                "add": [1, 2, 3]
            }
        }
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize("parameters", [
    None,
    1,
    [1],
    "foo",
    ["foo.bar"],
    {"arg1": {"foo": 1}},
    {1: {"default": "foo"}},
])
def test_invalid_parameters(parameters):
    experiment_desc = {
        "parameters": parameters,
        "tasks": {
            "add": {
                "plugin": "org.example.add"
            }
        },
        "graph": {
            "step1": {
                "add": [1, 2, 3]
            }
        }
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize("tasks", [
    {
        "add": {
            "plugin": "org.example.add"
        }
    },
    {
        "add": {
            "plugin": "org.example.add",
            "outputs": "foo"
        }
    },
    {
        "add": {
            "plugin": "org.example.add",
            "outputs": ["foo", "bar"]
        }
    },
    {
        "add": {
            "plugin": "org.example.add"
        },
        "sub": {
            "plugin": "org.example.sub"
        }
    }
])
def test_valid_tasks(tasks):
    experiment_desc = {
        "tasks": tasks,
        "graph": {
            "step1": {
                "add": [1, 2, 3]
            }
        }
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize("tasks", [
    None,
    1,
    "foo",
    [],
    {},
    {
        "add": 1
    },
    {
        1: "add"
    },
    {
        "add": []
    },
    {
        "add": {}
    },
    {
        "add": {
            "foo": True
        }
    },
    {
        "add": {
            True: "foo"
        }
    },
    {
        "add": {
            "plugin": ""
        }
    },
    {
        "add": {
            "plugin": "abc"
        }
    },
    {
        "add": {
            "plugin": "org.example.add."
        }
    },
    {
        "add": {
            "plugin": "org.example.add",
            "foo": 123
        }
    },
    {
        "add": {
            "plugin": "org.example.add",
            "outputs": "value",
            "foo": 123
        }
    }
])
def test_invalid_tasks(tasks):
    experiment_desc = {
        "tasks": tasks,
        "graph": {
            "step1": {
                "add": [1, 2, 3]
            }
        }
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize("graph", [
    {
        "step1": {
            "add": 1
        }
    },
    {
        "step1": {
            "add": [1]
        }
    },
    {
        "step1": {
            "add": {
                "a": 1,
                "b": 2
            }
        }
    },
    {
        "step1": {
            "task": "add"
        }
    },
    {
        "step1": {
            "task": "add",
            "args": [1, 2]
        }
    },
    {
        "step1": {
            "task": "add",
            "kwargs": {
                "b": 2
            }
        }
    },
    {
        "step1": {
            "task": "add",
            "args": 1,
            "kwargs": {
                "b": 2
            }
        }
    },
    {
        "add1": {
            "add": [1, 2]
        },
        "add2": {
            "add": [3, 4]
        }
    }
])
def test_valid_graph(graph):
    experiment_desc = {
        "tasks": {
            "add": {
                "plugin": "org.example.add"
            }
        },
        "graph": graph
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize("graph", [
    None,
    1,
    "foo",
    [],
    {},
    {"step1": 1},
    {1: "step1"},
    {"step1": [1]},
    {"step1": {"sub": 1}},
    {"step1": {"task": "sub"}},
    {
        "step1": {
            # missing task short name
            "dependencies": ["step2"]
        },
        "step2": {
            "add": 1
        }
    },
    {
        "step1": {
            "task": "add",
            "foo": "bar"
        }
    }
])
def test_invalid_graph(graph):
    experiment_desc = {
        "tasks": {
            "add": {
                "plugin": "org.example.add"
            }
        },
        "graph": graph
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize("graph", [
    {
        "step1": {
            "task1": 1
        },
        "step2": {
            "task2": "$step1"
        }
    },
    {
        "step1": {
            "task1": 1
        },
        "step2": {
            "task2": ["$step1", "$step3.value2"]
        },
        "step3": {
            "task3": 123
        }
    },
    {
        "step1": {
            "task1": 1
        },
        "step2": {
            "task2": "abc"
        },
        "step3": {
            "task3": [
                "$step1",
                {"arg1": "$step2"}
            ]
        }
    },
    {
        "step1": {
            "task1": 1
        },
        "step2": {
            "task2": {
                "arg1": "$step1",
                "arg3": {"subarg1": ["$step3.value2"]}
            }
        },
        "step3": {
            "task3": 1
        }
    },
    {
        "step1": {
            "task1": 1
        },
        "step2": {
            "task": "task2",
            "args": ["$step1.value"],
            "kwargs": {
                "subarg": "$step3.value1"
            }
        },
        "step3": {
            "task3": 1
        }
    },
])
def test_valid_step_references(graph):
    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": "value"
            },
            "task2": {
                "plugin": "org.example.task2",
                "outputs": ["value"]
            },
            "task3": {
                "plugin": "org.example.task3",
                "outputs": ["value1", "value2"]
            },
        },

        "graph": graph
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize("graph", [
    {
        "step1": {
            "task1": "$param1"
        }
    },
    {
        "step1": {
            "task1": {
                "foo": [{
                    "bar": ["$param2"]
                }]
            }
        }
    }
])
def test_valid_parameter_references(graph):
    experiment_desc = {
        "parameters": [
            "param1",
            "param2"
        ],
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": "value"
            }
        },
        "graph": graph
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize("graph", [
    {
        "step1": {
            "task1": "$step2"
        }
    },
    {
        "step1": {
            "task1": 1
        },
        "step2": {
            "task2": "$step1.foo"
        }
    },
    {
        "step1": {
            "task1": {
                "arg1": "$step3"
            }
        },
        "step3": {
            "task3": 1
        }
    },
    {
        "step1": {
            "task1": "$param3"
        }
    },
    {
        "step1": {
            "task1": "$param1.value"
        }
    }
])
def test_invalid_references(graph):
    experiment_desc = {
        "parameters": [
            "param1",
            "param2"
        ],
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": "value"
            },
            "task2": {
                "plugin": "org.example.task2",
                "outputs": ["value"]
            },
            "task3": {
                "plugin": "org.example.task3",
                "outputs": ["value1", "value2"]
            },
        },

        "graph": graph
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize("graph", [
    {
        "step1": {
            "task1": "$step1"
        }
    },
    {
        "step1": {
            "task1": ["$step2"]
        },
        "step2": {
            "task2": {
                "arg1": ["$step1.value"]
            }
        }
    },
    {
        "step1": {
            "task": "task1",
            "args": ["$step3.value2"]
        },
        "step2": {
            "task2": [{"foo": "$step1"}]
        },
        "step3": {
            "task3": {
                "bar": {
                    "baz": ["$step2.value"]
                }
            }
        }
    },
    {
        "step1": {
            "task1": 1,
            "dependencies": ["step1"]
        }
    },
    {
        "step1": {
            "task1": 1,
            "dependencies": ["step3"]
        },
        "step2": {
            "task2": 2,
            "dependencies": ["step1"]
        },
        "step3": {
            "task3": 3,
            "dependencies": ["step2"]
        }
    }
])
def test_step_cycle(graph):
    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": "value"
            },
            "task2": {
                "plugin": "org.example.task2",
                "outputs": ["value"]
            },
            "task3": {
                "plugin": "org.example.task3",
                "outputs": ["value1", "value2"]
            },
        },

        "graph": graph
    }

    assert not is_valid(experiment_desc)


def test_name_collision():
    # parameter name collides with a step name
    experiment_desc = {
        "parameters": [
            "foo"
        ],
        "tasks": {
            "task1": {
                "plugin": "org.example.foo"
            }
        },
        "graph": {
            "foo": {
                "task1": 1
            }
        }
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize("graph", [
    {
        "step1": {
            "task1": 1,
            "dependencies": ["step2"]
        },
        "step2": {
            "task1": 1
        }
    },
    {
        "step1": {
            "task1": 1,
            "dependencies": ["step2", "step3"]
        },
        "step2": {
            "task1": 1,
            "dependencies": ["step3"]
        },
        "step3": {
            "task1": 1
        }
    },
    {
        "step1": {
            "task1": 1,
            "dependencies": "step2"
        },
        "step2": {
            "task1": 1
        }
    }
])
def test_valid_dependencies(graph):
    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.foo"
            }
        },
        "graph": graph
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize("graph", [
    {
        "step1": {
            "task1": 1,
            "dependencies": ["step2"]
        }
    },
    {
        "step1": {
            "task1": 1,
            "dependencies": ["step2", "step3"]
        },
        "step2": {
            "task1": 1
        }
    },
    {
        "step1": {
            "task1": 1,
            "dependencies": 1
        }
    }
])
def test_invalid_dependencies(graph):
    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.foo"
            }
        },
        "graph": graph
    }

    assert not is_valid(experiment_desc)
