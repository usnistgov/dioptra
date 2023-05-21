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
import pytest

from dioptra.task_engine.issues import IssueSeverity
from dioptra.task_engine.validation import is_valid, validate


@pytest.mark.parametrize(
    "experiment_desc",
    [
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
            "tasks": {"add": {"plugin": "org.example.add"}},
            "graph": {"step1": {"add": []}},
            "extra": "property",
        },
    ],
)
def test_invalid_description(experiment_desc) -> None:
    # I don't test the error messages; they are just prose-y strings, and
    # we should be able to change wording without breaking a bunch of unit
    # tests, right?
    assert not is_valid(experiment_desc)


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"arg1": None},
        {"arg1": "default_value"},
        {"arg1": {"default": None}},
        {"arg1": {"default": "default_value"}},
        {"arg1": {"type": "integer"}},
        {"arg1": {"default": "default_value", "type": "string"}},
    ],
)
def test_valid_parameters(parameters) -> None:
    # Since we are strictly testing the parameters part, we just parameterize
    # that part, and insert it into an otherwise valid description.
    experiment_desc = {
        "parameters": parameters,
        "tasks": {
            "add": {
                "plugin": "org.example.add",
                "inputs": [
                    {"n1": "number"},
                    {"n2": "number"},
                    {"n3": "number"},
                ],
            }
        },
        "graph": {"step1": {"add": [1, 2, 3]}},
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "parameters",
    [
        None,
        1,
        [1],
        "foo",
        {"foo.bar": 1},
        {"arg1": {"foo": 1}},
        {1: {"default": "foo"}},
        {"foo": {"type": None}},
        {"foo": {"type": "badtype", "default": "value"}},
        {"foo": {"type": "integer", "default": "value"}},
        {"step1": "integer"},  # name collides with a graph step
    ],
)
def test_invalid_parameters(parameters) -> None:
    experiment_desc = {
        "parameters": parameters,
        "tasks": {"add": {"plugin": "org.example.add"}},
        "graph": {"step1": {"add": []}},
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize(
    "tasks",
    [
        {
            "add": {
                "plugin": "org.example.add",
                "inputs": [
                    {"n1": "integer"},
                    {"n2": "integer"},
                    {"n3": "integer"},
                ],
            }
        },
        {
            "add": {
                "plugin": "org.example.add",
                "inputs": [
                    {"n1": "integer"},
                    {"n2": "integer"},
                    {"n3": "integer"},
                ],
                "outputs": {"foo": "string"},
            }
        },
        {
            "add": {
                "plugin": "org.example.add",
                "inputs": [
                    {"n1": "integer"},
                    {"n2": "integer"},
                    {"name": "n3", "type": "number", "required": True},
                ],
                "outputs": [{"foo": "string"}, {"bar": "integer"}],
            }
        },
        {
            "add": {
                "plugin": "org.example.add",
                "inputs": [
                    {"n1": "integer"},
                    {"n2": "integer"},
                    {"n3": "integer"},
                ],
            },
            "sub": {"plugin": "org.example.sub"},
        },
    ],
)
def test_valid_tasks(tasks) -> None:
    experiment_desc = {"tasks": tasks, "graph": {"step1": {"add": [1, 2, 3]}}}

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "tasks",
    [
        None,
        1,
        "foo",
        [],
        {},
        {"add": 1},
        {1: "add"},
        {1: {"plugin": "org.example.add"}},
        {"add": []},
        {"add": {}},
        {"add": {"foo": True}},
        {"add": {True: "foo"}},
        {"add": {"plugin": ""}},
        {"add": {"plugin": "abc"}},
        {"add": {"plugin": "org.example.add."}},
        {"add": {"plugin": "org.example.add", "foo": 123}},
        {"add": {"plugin": "org.example.add", "outputs": {"value": "badtype"}}},
        {"add": {"plugin": "org.example.add", "inputs": [{"value": "badtype"}]}},
        {
            "add": {
                "plugin": "org.example.add",
                "outputs": [{"value": "number"}, {"value": "number"}],
            }
        },
        {
            "add": {
                "plugin": "org.example.add",
                "inputs": [{"value": "number"}, {"value": "number"}],
            }
        },
    ],
)
def test_invalid_tasks(tasks) -> None:
    experiment_desc = {"tasks": tasks, "graph": {"step1": {"add": []}}}

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {"0in": []}},
        {"step1": {"0in": {}}},
        {"step1": {"1in": 1}},
        {"step1": {"1in": [1]}},
        {"step1": {"1in": {"in1": 1}}},
        {"step1": {"2in": [1, 2]}},
        {"step1": {"2in": {"in1": 1, "in2": 2}}},
        {"step1": {"task": "0in"}},
        {"step1": {"task": "1in", "args": 1}},
        {"step1": {"task": "1in", "args": [1]}},
        {"step1": {"task": "2in", "args": [1, 2]}},
        {"step1": {"task": "2in", "kwargs": {"in1": 1, "in2": 2}}},
        {"step1": {"task": "2in", "args": 1, "kwargs": {"in2": 2}}},
        {"step1": {"1in": [1]}, "step2": {"2in": [3, 4]}},
    ],
)
def test_valid_graph(graph) -> None:
    experiment_desc = {
        "tasks": {
            "0in": {"plugin": "org.example.task0in"},
            "1in": {"plugin": "org.example.task1in", "inputs": [{"in1": "number"}]},
            "2in": {
                "plugin": "org.example.task1in",
                "inputs": [
                    {"in1": "number"},
                    {"in2": "number"},
                ],
            },
        },
        "graph": graph,
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        None,
        1,
        "foo",
        [],
        {},
        {"step1": 1},
        {1: "step1"},
        {1: {"add": []}},
        {"step1": [1]},
        {"step1": {"sub": 1}},
        {"step1": {"task": "sub"}},
        {"step1": {"add": [], "2arg": [1, "foo"]}},
        {
            "step1": {
                # missing task short name
                "dependencies": ["step2"]
            },
            "step2": {"add": 1},
        },
        {"step1": {"task": "add", "foo": "bar"}},
        {
            "step1": {
                "task": "2arg",
                "args": [1, "foo"],
                "kwargs": {
                    # arg1 set both positionally and via keyword
                    "arg1": 1
                },
            }
        },
        {
            "step1": {
                "task": "2arg",
                "args": [1, "foo"],
                "kwargs": {
                    # arg1 and arg2 set both positionally and via keyword
                    "arg1": 1,
                    "arg2": "foo",
                },
            }
        },
    ],
)
def test_invalid_graph(graph) -> None:
    experiment_desc = {
        "tasks": {
            "add": {"plugin": "org.example.add"},
            "2arg": {
                "plugin": "org.example.task2arg",
                "inputs": [{"arg1": "number"}, {"arg2": "string"}],
            },
        },
        "graph": graph,
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {"1out": []}, "step2": {"1in": "$step1"}},
        {
            "step1": {"1out": []},
            "step2": {"2in": ["$step1", "$step3.out2"]},
            "step3": {"2out": []},
        },
        {
            "step1": {"1out": []},
            "step2": {"1out": []},
            "step3": {"2inmap": ["$step1", {"arg1": "$step2"}]},
        },
        {
            "step1": {"1out": []},
            "step2": {
                "2inmaplist": {"in1": "$step1", "in2": {"subarg1": ["$step3.out2"]}}
            },
            "step3": {"2out": []},
        },
        {
            "step1": {"1out": []},
            "step2": {
                "task": "2in",
                "args": ["$step1.out"],
                "kwargs": {"in2": "$step3.out1"},
            },
            "step3": {"2out": []},
        },
    ],
)
def test_valid_step_references(graph) -> None:
    experiment_desc = {
        "types": {
            "str_to_num": {"mapping": ["string", "number"]},
            "str_to_list_num": {"mapping": ["string", {"list": "number"}]},
        },
        "tasks": {
            "1out": {"plugin": "org.example.task1out", "outputs": {"out": "number"}},
            "2out": {
                "plugin": "org.example.task2out",
                "outputs": [{"out1": "number"}, {"out2": "number"}],
            },
            "1in": {"plugin": "org.example.task1in", "inputs": [{"in": "number"}]},
            "2in": {
                "plugin": "org.example.task2in",
                "inputs": [{"in1": "number"}, {"in2": "number"}],
            },
            "2inmap": {
                "plugin": "org.example.task2inmap",
                "inputs": [{"in1": "number"}, {"in2": "str_to_num"}],
            },
            "2inmaplist": {
                "plugin": "org.example.task2inmaplist",
                "inputs": [{"in1": "number"}, {"in2": "str_to_list_num"}],
            },
        },
        "graph": graph,
    }

    assert is_valid(experiment_desc)


def test_output_named_name():
    # "name" has special meaning in an input (it's a long form input);
    # ensure it does not have that meaning in an output and I didn't mess
    # it up anywhere...
    experiment_desc = {
        "tasks": {
            "nameout": {"plugin": "org.example.nameout", "outputs": {"name": "string"}},
            "nameoutarr": {
                "plugin": "org.example.nameout",
                "outputs": [{"name": "string"}],
            },
            "1in": {
                "plugin": "org.example.1in",
                "inputs": [{"name": "in", "type": "string"}],
            },
        },
        "graph": {
            "singleout": {"nameout": []},
            "arrayout": {"nameoutarr": []},
            "in_1": {"1in": "$singleout"},
            "in_2": {"1in": "$arrayout"},
            "in_3": {"1in": "$singleout.name"},
            "in_4": {"1in": "$arrayout.name"},
        },
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {"1innum": "$param1"}},
        {"step1": {"1innestedthing": {"foo": [{"bar": ["$param2"]}]}}},
    ],
)
def test_valid_parameter_references(graph) -> None:
    experiment_desc = {
        "parameters": {
            "param1": 1.23,  # inferred type: number
            "param2": {"type": "string"},
        },
        "types": {"nestedthing": {"tuple": [{"mapping": {"bar": {"list": "string"}}}]}},
        "tasks": {
            "1innum": {"plugin": "org.example.task1", "inputs": [{"in": "number"}]},
            "1innestedthing": {
                "plugin": "org.example.task2",
                "inputs": [{"foo": "nestedthing"}],
            },
        },
        "graph": graph,
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {"task1": "$step2"}},
        {"step1": {"task1": 1}, "step2": {"task2": "$step1.foo"}},
        {"step1": {"task1": {"arg1": "$step3"}}, "step3": {"task3": []}},
        {"step1": {"task1": "$param3"}},
        {"step1": {"task1": "$param1.value"}},
        {"step1": {"task4": []}, "step2": {"task1": "$step1"}},
        {"step1": {"task4": []}, "step2": {"task1": "$step1.value1"}},
    ],
)
def test_invalid_references(graph) -> None:
    experiment_desc = {
        "parameters": {"param1": "number", "param2": "number"},
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [{"arg1": "number"}],
                "outputs": {"value": "number"},
            },
            "task2": {
                "plugin": "org.example.task2",
                "inputs": [{"in": "number"}],
                "outputs": {"value": "number"},
            },
            "task3": {
                "plugin": "org.example.task3",
                "outputs": [{"value1": "number"}, {"value2": "number"}],
            },
            "task4": {"plugin": "org.example.task4"},
        },
        "graph": graph,
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {"task1": "$step1"}},
        {
            "step1": {"task1": ["$step2"]},
            "step2": {"task2": {"foo": "$step1.value"}},
        },
        {
            "step1": {"task": "task1", "args": ["$step3.value2"]},
            "step2": {"task2": {"foo": "$step1"}},
            "step3": {"task3": {"bar": {"baz": ["$step2.value"]}}},
        },
        {"step1": {"task1": 1, "dependencies": ["step1"]}},
        {
            "step1": {"task1": 1, "dependencies": ["step3"]},
            "step2": {"task2": 2, "dependencies": ["step1"]},
            "step3": {"task3": [{"abc": [1]}], "dependencies": ["step2"]},
        },
    ],
)
def test_step_cycle(graph) -> None:
    experiment_desc = {
        "types": {"str_to_list_num": {"mapping": ["string", {"list": "number"}]}},
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [{"in": "number"}],
                "outputs": {"value": "number"},
            },
            "task2": {
                "plugin": "org.example.task2",
                "inputs": [{"foo": "number"}],
                "outputs": [{"value": "number"}],
            },
            "task3": {
                "plugin": "org.example.task3",
                "inputs": [{"bar": "str_to_list_num"}],
                "outputs": [{"value1": "number"}, {"value2": "number"}],
            },
        },
        "graph": graph,
    }

    assert not is_valid(experiment_desc)


def test_name_collision() -> None:
    # parameter name collides with a step name
    experiment_desc = {
        "parameters": {"foo": 1},
        "tasks": {"task1": {"plugin": "org.example.foo", "inputs": [{"in": "number"}]}},
        "graph": {"foo": {"task1": 1}},
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {"task1": [], "dependencies": ["step2"]}, "step2": {"task1": []}},
        {
            "step1": {"task1": [], "dependencies": ["step2", "step3"]},
            "step2": {"task1": [], "dependencies": ["step3"]},
            "step3": {"task1": []},
        },
        {"step1": {"task1": [], "dependencies": "step2"}, "step2": {"task1": []}},
    ],
)
def test_valid_dependencies(graph) -> None:
    experiment_desc = {
        "tasks": {"task1": {"plugin": "org.example.foo"}},
        "graph": graph,
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {"task1": [], "dependencies": ["step2"]}},
        {
            "step1": {"task1": [], "dependencies": ["step2", "step3"]},
            "step2": {"task1": []},
        },
        {"step1": {"task1": [], "dependencies": 1}},
    ],
)
def test_invalid_dependencies(graph) -> None:
    experiment_desc = {
        "tasks": {"task1": {"plugin": "org.example.foo"}},
        "graph": graph,
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {"allopt": {}}},
        {"step1": {"allopt": 1}},
        {"step1": {"allopt": {"in2": 2}}},
        {"step1": {"allopt": [1, 2]}},
        {"step1": {"allopt": {"in1": 1, "in2": 2}}},
        {"step1": {"1stopt": {"in2": 2}}},
        {"step1": {"task": "1stopt", "kwargs": {"in2": 2}}},
        {"step1": {"1stopt": [1, 2]}},
        {"step1": {"2ndopt": 1}},
        {"step1": {"2ndopt": [1]}},
        {"step1": {"2ndopt": {"in1": 1}}},
        {"step1": {"task": "2ndopt", "args": 1, "kwargs": {"in2": 2}}},
    ],
)
def test_optional_task_inputs_valid(graph) -> None:
    experiment_desc = {
        "tasks": {
            "allopt": {
                "plugin": "org.example.taskallopt",
                "inputs": [
                    {"name": "in1", "type": "number", "required": False},
                    {"name": "in2", "type": "number", "required": False},
                ],
            },
            "1stopt": {
                "plugin": "org.example.task1stopt",
                "inputs": [
                    {"name": "in1", "type": "number", "required": False},
                    {"name": "in2", "type": "number", "required": True},
                ],
            },
            "2ndopt": {
                "plugin": "org.example.task2ndopt",
                "inputs": [
                    {"name": "in1", "type": "number", "required": True},
                    {"name": "in2", "type": "number", "required": False},
                ],
            },
        },
        "graph": graph,
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "graph",
    [
        {"step1": {}},
        {"step1": {"1stopt": 1}},
        {"step1": {"1stopt": {"in1": 1}}},
        {"step1": {"task": "1stopt", "args": [1]}},
        {"step1": {"task": "1stopt", "kwargs": {"in1": 1}}},
        {"step1": {"2ndopt": {"in2": 1}}},
        {"step1": {"task": "2ndopt", "kwargs": {"in2": 1}}},
    ],
)
def test_optional_task_inputs_invalid(graph) -> None:
    experiment_desc = {
        "tasks": {
            "1stopt": {
                "plugin": "org.example.task1stopt",
                "inputs": [
                    {"name": "in1", "type": "number", "required": False},
                    {"name": "in2", "type": "number", "required": True},
                ],
            },
            "2ndopt": {
                "plugin": "org.example.task2ndopt",
                "inputs": [
                    {"name": "in1", "type": "number", "required": True},
                    {"name": "in2", "type": "number", "required": False},
                ],
            },
        },
        "graph": graph,
    }

    assert not is_valid(experiment_desc)


def test_invocation_too_many_positional_args() -> None:
    experiment_desc = {
        "tasks": {
            "atask": {"plugin": "org.example.task", "inputs": [{"in1": "number"}]}
        },
        "graph": {"step1": {"atask": [1, 2, 3]}},
    }

    assert not is_valid(experiment_desc)


def test_invocation_bad_kwarg() -> None:
    experiment_desc = {
        "tasks": {
            "atask": {"plugin": "org.example.task", "inputs": [{"in1": "number"}]}
        },
        "graph": {"step1": {"atask": {"badkwarg": 1}}},
    }

    assert not is_valid(experiment_desc)


@pytest.mark.parametrize(
    "types",
    [
        {"A": {"is_a": "A"}},
        {"A": {"list": "A"}},
        {"A": {"tuple": ["A"]}},
        {"A": {"mapping": ["string", "A"]}},
        {"A": {"union": ["A"]}},
        {"A": {"is_a": "B"}, "B": {"is_a": "A"}},
        {
            "A": {"list": "B"},
            "B": {"mapping": ["string", {"tuple": ["number", "C"]}]},
            "C": {"union": ["string", "boolean", "A"]},
        },
    ],
)
def test_type_reference_cycle(types) -> None:
    experiment_desc = {
        "types": types,
        "tasks": {"foo": {"plugin": "org.example.foo"}},
        "graph": {"step1": {"foo": []}},
    }

    assert not is_valid(experiment_desc)


def test_union_dupes():
    experiment_desc = {
        "types": {
            "A": None,
            "B": None,
            "C": None,
            "dupe_union": {"union": ["A", "B", "C", "C", "A"]},
        },
        "tasks": {"task1": {"plugin": "org.example.task1"}},
        "graph": {"step1": {"task1": []}},
    }

    issues = validate(experiment_desc)

    # Should only get a warning for the dupe_union type.
    assert len(issues) == 1 and issues[0].severity is IssueSeverity.WARNING

    # Since this is only a warning, ensure that is_valid() returns True, even
    # though there are issues.
    assert is_valid(experiment_desc)
