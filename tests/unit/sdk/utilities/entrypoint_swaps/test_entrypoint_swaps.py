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

import pytest
import yaml

from dioptra.sdk.utilities.entrypoint_swaps import (
    check_duplicate_swap_names,
    check_multiple_swaps_per_step,
    check_swaps_graph_dependencies,
    extract_swaps,
    render_swaps_graph,
    validate_swaps_graph,
)

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
