import json
import pathlib

import dioptra.task_engine.validation

SCHEMA_FILENAME = "swappable_experiment_schema.json"


def get_json_schema(default: bool = False) -> dict:
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
    schema_path = pathlib.Path(".dioptra") / SCHEMA_FILENAME
    if default or not schema_path.exists():
        # Currently assumes the schema json file and this source file are in the
        # same directory.
        schema_path = pathlib.Path(__file__).with_name(SCHEMA_FILENAME)

    schema: dict
    with schema_path.open("r", encoding="utf-8") as fp:
        schema = json.load(fp)

    return schema


def get_swappable_experiment_schema():
    base_schema = dioptra.task_engine.validation.get_json_schema()
    swappable_schema = get_json_schema()

    if "$defs" in base_schema and "$defs" in swappable_schema:
        # since the definitions have the same keys, we can just replace the definitions
        # in the original schema with the ones from the swappable schema.
        base_schema["$defs"].update(swappable_schema["$defs"])

    return base_schema
