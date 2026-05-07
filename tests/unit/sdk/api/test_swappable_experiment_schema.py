import pytest
import yaml

from dioptra.sdk.api.swappable_validation import get_swap_graph_schema, get_swappable_json_schema_resources
from dioptra.task_engine.util import schema_validate
from pathlib import Path


FILES_LOCATION = 'swappable'

@pytest.mark.parametrize(
    "yaml_file",
    [
        'no_swap_test.yml',
        'swap_test.yml',
        'swappable_dataset_transformer.yml',
        'unswappable_dataset_transformer.yml',
    ],
)
def test_swappable_experiment_schema(yaml_file):
    with (Path(__file__).absolute().parent / FILES_LOCATION / yaml_file).open('r') as f:
        data = f.read()
    graph = yaml.safe_load(data)

    errors = schema_validate(graph, get_swap_graph_schema(), resources=get_swappable_json_schema_resources())

    assert errors == []

@pytest.mark.parametrize(
    "yaml_file",
    [
        'question_mark_task.yml',
        'question_mark_task_in_swap.yml',
    ],
)

def test_question_mark_not_swap_fails(yaml_file):
    """A YAML file that contains a task name starting with a question mark should
    not be valid. The swap graph schema expects a proper swap structure for keys 
    that begin with ?. This test ensures that such a file produces validation errors.
    """
    yaml_path = Path(__file__).absolute().parent / FILES_LOCATION / yaml_file
    with yaml_path.open("r") as f:
        data = f.read()
    graph = yaml.safe_load(data)

    errors = schema_validate(
        graph, get_swap_graph_schema(), resources=get_swappable_json_schema_resources()
    )
    assert errors != []