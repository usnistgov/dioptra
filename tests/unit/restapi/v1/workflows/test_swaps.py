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
from dioptra.restapi.v1.shared.swaps import validate, render
import yaml
import itertools
import pytest

FILES_LOCATION = "swaps_files"

available_swaps = {
    "output/output_load_defend.yml": {
        "load": "load_artifacts_for_job",
        "transform_data": "augment_data"
    },
    "output/output_load_fgm.yml": {
        "load": "load_artifacts_for_job",
        "transform_data": "attack_fgm"
    },
    "output/output_load_patch_apply.yml": {
        "load": "load_artifacts_for_job",
        "transform_data": "augment_patch"
    },
    "output/output_load_patch_gen.yml": {
        "load": "load_artifacts_for_job",
        "transform_data": "attack_patch"
    },
    "output/output_passthrough_defend.yml": {
        "load": "passthrough",
        "transform_data": "augment_data"
    },
    "output/output_passthrough_fgm.yml": {
        "load": "passthrough",
        "transform_data": "attack_fgm"
    },
    "output/output_passthrough_passthrough.yml": {
        "load": "passthrough",
        "transform_data": "passthrough_dataset"
    },
    "output/output_passthrough_patch_apply.yml": {
        "load": "passthrough",
        "transform_data": "augment_patch"
    },
    "output/output_passthrough_patch_gen.yml": {
        "load": "passthrough",
        "transform_data": "attack_patch"
    }
}

def verify_correct_yaml(graph, all_swaps):
    issues = []
    for output_file in all_swaps.keys():
        with (Path(__file__).absolute().parent / FILES_LOCATION / output_file).open('r') as f:
            data = f.read()
        expected_graph = yaml.safe_load(data)

        swaps = all_swaps[output_file]
        
        rendered_graph = render(graph, swaps)

        #if (expected_graph != rendered_graph):
        #    print("expected:", expected_graph)
        #    print("rendered:", rendered_graph)

        assert expected_graph == rendered_graph
        issues.append(validate(rendered_graph))
    if len(issues) > 0:
        print(issues, flush=True)

    return issues

@pytest.mark.parametrize(
    "yaml_file",
    [
        'dataset_transformer.yml',
        'dataset_transformer_with_anchors.yml'
    ],
)
def test_swap_render(yaml_file: str):
    with (Path(__file__).absolute().parent / FILES_LOCATION / yaml_file).open('r') as f:
        data = f.read()
    graph = yaml.safe_load(data)

    issues = verify_correct_yaml(graph, available_swaps)
    assert all([issue == [] for issue in issues])
