import pytest
import yaml

from dioptra.sdk.api.swappable_validation import get_json_schema
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

    assert schema_validate(graph, get_json_schema()) == []