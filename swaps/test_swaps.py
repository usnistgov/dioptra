from swap_proto import validate, render
import yaml
import itertools

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
    for output_file in all_swaps.keys():
        with open(output_file) as f:
            data = f.read()
        expected_graph = yaml.safe_load(data)

        swaps = all_swaps[output_file]
        
        rendered_graph = render(graph, swaps)

        if (expected_graph != rendered_graph):
            print("expected:", expected_graph)
            print("rendered:", rendered_graph)
        assert expected_graph == rendered_graph
        issues = validate(rendered_graph)
        print(issues)


def test_no_anchors():
    with open('dataset_transformer.yml') as f:
        data = f.read()
    graph = yaml.safe_load(data)

    verify_correct_yaml(graph, available_swaps)

def test_anchors():
    with open('dataset_transformer_with_anchors.yml') as f:
        data = f.read()
    graph = yaml.safe_load(data)

    verify_correct_yaml(graph, available_swaps)

test_no_anchors()
test_anchors()