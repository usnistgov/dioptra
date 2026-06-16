import json
import pathlib

import dioptra.task_engine.validation

SWAP_SCHEMA_FILENAME = "swappable_experiment_schema.json"
GRAPH_SCHEMA_FILENAME = "swap_graph.json"


def get_json_schema(default: bool = False, filename: str | None = None) -> dict:
    """
    Read and parse the declarative experiment description JSON-Schema file. Will first
    look in a ".dioptra" folder to see if an altered version is available, otherwise
    the default

    Args:
        default: if true returns the default schema regardless of the existence of any
            available altered version

    Returns:
        The schema, as parsed JSON
    """
    # attempt to get the override first
    filename = filename or SWAP_SCHEMA_FILENAME

    schema_path = pathlib.Path(".dioptra") / filename
    if default or not schema_path.exists():
        # Currently assumes the schema json file and this source file are in the
        # same directory.
        schema_path = pathlib.Path(__file__).with_name(filename)

    schema: dict
    with schema_path.open("r", encoding="utf-8") as fp:
        schema = json.load(fp)

    return schema


def get_swap_graph_schema() -> dict:
    """Retrieve a schema which defines just a swap graph."""
    return get_json_schema(filename=GRAPH_SCHEMA_FILENAME)


def get_swappable_json_schema_resources() -> list[tuple[str, dict]]:
    """Retrieve the resources needed for swappable JSON schemas."""
    return [
        ("swap_graph.json", get_json_schema(filename=GRAPH_SCHEMA_FILENAME)),
        ("experiment_schema.json", dioptra.task_engine.validation.get_json_schema()),
    ]


def get_swappable_experiment_schema() -> dict:
    """Retrieve an experiment schema which takes swaps into account in the graph portion."""
    return get_json_schema()
