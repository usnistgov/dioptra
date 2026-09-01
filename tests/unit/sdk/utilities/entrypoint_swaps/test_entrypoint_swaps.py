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
from pathlib import Path

import pytest
import yaml

from dioptra.sdk.utilities.entrypoint_swaps import (
    check_duplicate_swap_names,
    check_multiple_swaps_per_step,
    extract_swaps,
    render_swaps_graph,
    validate_swaps_graph,
)

FILES_LOCATION = "entrypoint_swaps_files"

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
