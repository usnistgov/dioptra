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
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from dioptra.sdk.api.swappable_validation import (
    get_swap_graph_schema,
    get_swappable_json_schema_resources,
)
from dioptra.sdk.utilities.entrypoint_swaps import (
    check_duplicate_swap_names,
    check_multiple_swaps_per_step,
    check_swaps_graph_dependencies,
    compile_swaps_config,
    extract_swaps,
    render_swaps_config,
    render_swaps_graph,
    validate_swaps_graph,
)
from dioptra.task_engine.task_engine import EngineContext, _run_steps
from dioptra.task_engine.util import step_get_plugin_short_name
from dioptra.task_engine.validation import schema_validate

FILES_LOCATION = "entrypoint_swaps_files"


@pytest.mark.parametrize(
    "graph, cyclic",
    [
        # Both cross choices together make left depend on right and right on left;
        # either cross choice paired with the other default is acyclic.
        pytest.param(
            {
                "left": {
                    "?left-choice": {
                        "default": {"task": "constant"},
                        "cross": {"passthrough": {"value": "$right.value"}},
                    }
                },
                "right": {
                    "?right-choice": {
                        "default": {"task": "constant"},
                        "cross": {"passthrough": {"value": "$left.value"}},
                    }
                },
            },
            True,
            id="two-nondefault-choices",
        ),
        # The alias named task makes left depend on right. The ordinary step's
        # nested reference makes right depend on left, closing the cycle.
        pytest.param(
            {
                "left": {"?choice": {"task": {"consume": "$right.value"}}},
                "right": {"prepare": {"nested": ["$left.value"]}},
            },
            True,
            id="ordinary-step-and-alias-named-task",
        ),
        # The swap's keyword argument depends on right, while right's positional
        # argument depends on left: a cycle across mixed invocation forms.
        pytest.param(
            {
                "left": {
                    "?choice": {
                        "cross": {"task": "consume", "kwargs": {"value": "$right"}}
                    }
                },
                "right": {"task": "prepare", "args": ["$left.value"]},
            },
            True,
            id="mixed-invocations",
        ),
        # String-form and list-form explicit dependencies create opposing edges:
        # left depends on right, and right depends on left.
        pytest.param(
            {
                "left": {
                    "dependencies": "right",
                    "?choice": {"default": {"constant": None}},
                },
                "right": {"dependencies": ["left"], "constant": None},
            },
            True,
            id="explicit-string-and-list",
        ),
        # Selecting self makes left depend on its own output, creating a self-cycle.
        pytest.param(
            {
                "left": {
                    "?choice": {
                        "default": {"constant": None},
                        "self": {"consume": "$left.value"},
                    }
                },
            },
            True,
            id="self-reference",
        ),
        # Only right depends on left. Global/artifact references and the escaped
        # $$right.value string add no reverse step dependency, so there is no cycle.
        pytest.param(
            {
                "left": {
                    "?choice": {
                        "global": {
                            "task": "consume",
                            "args": ["$global", "$$right.value"],
                        },
                        "artifact": {"consume": {"value": "$artifact.value"}},
                    }
                },
                "right": {"dependencies": "left", "consume": "$left.value"},
            },
            False,
            id="globals-artifacts-and-escaped-references",
        ),
        # The cross choice makes left depend on right, but neither right-hand
        # choice depends on left. The union remains acyclic for every selection.
        pytest.param(
            {
                "left": {
                    "?choice": {
                        "default": {"constant": None},
                        "cross": {"consume": "$right.value"},
                    }
                },
                "right": {"?other": {"one": {"constant": 1}, "two": {"constant": 2}}},
            },
            False,
            id="acyclic-union",
        ),
    ],
)
def test_check_swaps_graph_dependencies(graph, cyclic):
    original = deepcopy(graph)
    issues = check_swaps_graph_dependencies(graph)
    assert graph == original
    if cyclic:
        assert len(issues) == 1
        assert "Step cycle detected" in issues[0].message
    else:
        assert issues == []


def test_check_swaps_graph_missing_explicit_dependency():
    issues = check_swaps_graph_dependencies(
        {"step": {"dependencies": "missing", "task": "constant"}}
    )
    assert len(issues) == 1
    assert "missing" in issues[0].message


available_swaps = {
    "output/output_load_defend.yml": {
        "load": "load_artifact",
        "transform_data": "augment",
    },
    "output/output_load_fgm.yml": {"load": "load_artifact", "transform_data": "attack"},
    "output/output_load_patch_apply.yml": {
        "load": "load_artifact",
        "transform_data": "attach",
    },
    "output/output_load_patch_gen.yml": {
        "load": "load_artifact",
        "transform_data": "patch",
    },
    "output/output_passthrough_defend.yml": {
        "load": "ignore",
        "transform_data": "augment",
    },
    "output/output_passthrough_fgm.yml": {"load": "ignore", "transform_data": "attack"},
    "output/output_passthrough_passthrough.yml": {
        "load": "ignore",
        "transform_data": "ignore",
    },
    "output/output_passthrough_patch_apply.yml": {
        "load": "ignore",
        "transform_data": "attach",
    },
    "output/output_passthrough_patch_gen.yml": {
        "load": "ignore",
        "transform_data": "patch",
    },
}


def verify_correct_yaml(graph, all_swaps):
    issues = []
    for output_file in all_swaps.keys():
        with (Path(__file__).absolute().parent / FILES_LOCATION / output_file).open(
            "r"
        ) as f:
            data = f.read()
        expected_graph = yaml.safe_load(data)

        swaps = all_swaps[output_file]

        rendered_graph = render_swaps_graph(graph, swaps)

        assert expected_graph == rendered_graph
        issues.append(validate_swaps_graph(rendered_graph))

    return issues


@pytest.mark.parametrize(
    "yaml_file",
    [
        "dataset_transformer.yml",
    ],
)
def test_swap_render(yaml_file: str):
    with (Path(__file__).absolute().parent / FILES_LOCATION / yaml_file).open("r") as f:
        data = f.read()
    graph = yaml.safe_load(data)

    issues = verify_correct_yaml(graph, available_swaps)
    assert all(issue == [] for issue in issues)


@pytest.mark.parametrize("yaml_file", ["no_swaps_test.yml"])
def test_without_swaps(yaml_file: str):
    with (Path(__file__).absolute().parent / FILES_LOCATION / yaml_file).open("r") as f:
        data = f.read()
    graph = yaml.safe_load(data)

    rendered_graph = render_swaps_graph(graph, {})
    assert rendered_graph == graph

    extra = {"load", "transform_data", "extra"}
    with pytest.raises(Exception, match=f"Swaps {extra} were provided but not used."):
        rendered_graph = render_swaps_graph(
            graph,
            {"load": "ignore", "transform_data": "patch", "extra": "function_name"},
        )


@pytest.mark.parametrize(
    "yaml_file",
    [
        "dataset_transformer.yml",
    ],
)
def test_swap_errors(yaml_file: str):
    with (Path(__file__).absolute().parent / FILES_LOCATION / yaml_file).open("r") as f:
        data = f.read()
    graph = yaml.safe_load(data)

    missing = {"load", "transform_data"}
    with pytest.raises(
        Exception, match=f"Swaps {missing} needed by graph but not provided."
    ):
        render_swaps_graph(graph, {})

    extra = {"extra"}
    with pytest.raises(Exception, match=f"Swaps {extra} were provided but not used."):
        render_swaps_graph(
            graph,
            {"load": "ignore", "transform_data": "patch", "extra": "function_name"},
        )

    nonexistant = {"nonexistant"}
    with pytest.raises(
        Exception, match=f"Tasks {nonexistant} requested for swaps but were not found."
    ):
        render_swaps_graph(
            graph,
            {
                "load": "ignore",
                "transform_data": "nonexistant",
            },
        )


def test_extract_swaps() -> None:
    graph = {
        "step": {"?transform": {"clean": {}, "augment": {}}},
        "other": {"task": {}},
    }

    assert extract_swaps(graph) == {"transform": ["clean", "augment"]}


def test_check_duplicate_swap_names() -> None:
    graph = {
        "first": {"?transform": {"clean": {}}},
        "second": {"?transform": {"augment": {}}},
    }

    issues = check_duplicate_swap_names(graph)

    assert len(issues) == 1
    assert "Duplicate swap name 'transform'" in issues[0].message


def test_check_multiple_swaps_per_step() -> None:
    graph = {
        "step": {
            "?load": {"disk": {}},
            "?transform": {"clean": {}},
        }
    }

    issues = check_multiple_swaps_per_step(graph)

    assert len(issues) == 1
    assert "Step 'step' contains multiple swaps" in issues[0].message


# -- Output interfaces, compilation, and execution ------------------------------------


@pytest.fixture
def config():
    """Provide compatible producers with different output names and two consumers."""
    return {
        "tasks": {
            "emit_x": {"plugin": "example.tasks.emit_x", "outputs": {"x": "number"}},
            "emit_y": {"plugin": "example.tasks.emit_y", "outputs": {"y": "number"}},
            "constant": {"plugin": "example.tasks.constant"},
            "consume": {
                "plugin": "example.tasks.consume",
                "inputs": [{"value": "number"}],
            },
        },
        "graph": {
            "producer": {
                "?producer-choice": {
                    "?outputs": ["value"],
                    "x-output": {"emit_x": []},
                    "y-output": {"emit_y": []},
                }
            },
            "consumer": {
                "?consumer-choice": {
                    "?outputs": [],
                    "independent": {"constant": []},
                    "use-value": {"consume": {"value": "$producer.value"}},
                }
            },
        },
    }


@pytest.mark.parametrize("producer", ["x-output", "y-output"])
@pytest.mark.parametrize("consumer", ["independent", "use-value"])
def test_all_combinations_validate_and_execute(config, producer, consumer):
    """Validate and execute every choice pair using canonical output references.

    Public rendering must retain registered task definitions, and neither
    rendering nor compilation may mutate the source configuration.
    """
    original = deepcopy(config)
    rendered = render_swaps_config(
        config, {"producer-choice": producer, "consumer-choice": consumer}
    )
    assert rendered["tasks"] == original["tasks"]
    assert rendered["graph"]["producer"]["?producer-choice"] == {
        "?outputs": ["value"],
        producer: original["graph"]["producer"]["?producer-choice"][producer],
    }
    compiled = compile_swaps_config(rendered)
    assert compiled.validate() == []
    context = EngineContext(compiled.config, {}, {}, {})
    with patch("dioptra.pyplugs.call", return_value=42) as call:
        _run_steps(context)
    assert context.step_outputs["producer"] == {"value": 42}
    if consumer == "use-value":
        assert call.call_args.kwargs["value"] == 42
    assert config == original


@pytest.mark.parametrize("producer, output", [("x-output", "x"), ("y-output", "y")])
def test_registered_output_names_are_private(config, producer, output):
    """Reject the selected producer's own registered name outside the swap interface."""
    config["graph"]["consumer"]["?consumer-choice"]["use-value"]["consume"]["value"] = (
        f"$producer.{output}"
    )
    rendered = render_swaps_config(
        config, {"producer-choice": producer, "consumer-choice": "use-value"}
    )
    assert any(
        f"unrecognized output: {output}" in issue.message
        for issue in compile_swaps_config(rendered).validate()
    )


def test_partial_render_can_be_completed(config):
    """Preserve unresolved choices and compile only after all swaps are selected.

    Resolving choices in stages must produce the same public configuration as
    selecting both swaps in a single render.
    """
    partial = render_swaps_config(config, {"producer-choice": "y-output"}, False)
    assert partial["graph"]["consumer"] == config["graph"]["consumer"]
    assert extract_swaps(partial["graph"]) == {
        "producer-choice": ["y-output"],
        "consumer-choice": ["independent", "use-value"],
    }
    assert check_swaps_graph_dependencies(config["graph"]) == []
    with pytest.raises(ValueError, match="consumer-choice.*exactly one"):
        compile_swaps_config(partial)
    completed = render_swaps_config(partial, {"consumer-choice": "use-value"}, False)
    assert completed == render_swaps_config(
        config, {"producer-choice": "y-output", "consumer-choice": "use-value"}
    )
    assert partial["tasks"] == config["tasks"]
    assert compile_swaps_config(completed).validate() == []


@pytest.mark.parametrize(
    "invocation",
    [
        {"score": "accuracy"},
        {"score": {"metric": "accuracy"}},
        {"task": "score", "args": ["accuracy"], "kwargs": {}},
    ],
)
def test_remap_multi_outputs_preserves_inputs_and_isolates_reuse(invocation):
    """Remap outputs per step for positional, keyword, and mixed invocations.

    Reused tasks must retain their inputs and independent output interfaces,
    preserve dependencies, and avoid collisions with registered task names.
    """
    task = {
        "plugin": "example.scoring.score",
        "inputs": [{"name": "metric", "type": "string", "required": True}],
        "outputs": [{"score": "number"}, {"class_name": "string"}],
    }
    config = {
        "tasks": {"score": task, "inference_score": {"plugin": "example.other.task"}},
        "graph": {
            "inference": {
                "?strategy": {"?outputs": ["prediction", "label"], "one": invocation}
            },
            "other": {
                "?other": {"?outputs": ["probability", "class"], "one": invocation}
            },
            "ordinary": invocation,
        },
    }
    config["graph"]["other"]["dependencies"] = ["inference"]
    original = deepcopy(config)
    rendered = render_swaps_config(config, {"strategy": "one", "other": "one"})
    assert rendered == original
    compiled = compile_swaps_config(rendered)
    assert compiled.validate() == []
    rendered = compiled.config
    inference_name = step_get_plugin_short_name(rendered["graph"]["inference"])
    other_name = step_get_plugin_short_name(rendered["graph"]["other"])
    assert inference_name not in config["tasks"]
    assert inference_name == "inference_score_"
    assert other_name == "other_score"
    assert inference_name != other_name
    assert rendered["tasks"][inference_name] == {
        **task,
        "outputs": [{"prediction": "number"}, {"label": "string"}],
    }
    assert rendered["tasks"][other_name]["outputs"] == [
        {"probability": "number"},
        {"class": "string"},
    ]
    assert rendered["graph"]["ordinary"] == invocation
    assert rendered["graph"]["other"]["dependencies"] == ["inference"]
    assert config == original


@pytest.mark.parametrize("interface", [None, "value", [""], ["value", "value"], [1]])
def test_interface_schema_rejects_invalid_names(config, interface):
    """Reject missing, non-list, empty-name, duplicate-name, and non-string interfaces."""
    declaration = config["graph"]["producer"]["?producer-choice"]
    if interface is None:
        del declaration["?outputs"]
    else:
        declaration["?outputs"] = interface
    assert schema_validate(
        config["graph"],
        get_swap_graph_schema(),
        resources=get_swappable_json_schema_resources(),
    )


def test_interface_requires_a_choice():
    """Reject a swap that declares an output interface without any task choices."""
    assert schema_validate(
        {"step": {"?choice": {"?outputs": []}}},
        get_swap_graph_schema(),
        resources=get_swappable_json_schema_resources(),
    )


def test_interface_metadata_cannot_be_selected(config):
    """Reject attempts to select the reserved ?outputs field as a task alias."""
    with pytest.raises(Exception, match="were not found"):
        render_swaps_config(config, {"producer-choice": "?outputs"}, False)


def test_compiler_rejects_output_count_mismatch(config):
    """Reject a selected task whose output count differs from its swap interface."""
    config["graph"]["producer"]["?producer-choice"]["?outputs"] = []
    rendered = render_swaps_config(
        config, {"producer-choice": "x-output", "consumer-choice": "independent"}
    )
    with pytest.raises(ValueError, match="interface requires 0"):
        compile_swaps_config(rendered)
