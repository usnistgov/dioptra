#!/usr/bin/env python
"""Render the Jinja templates containing the Docker Compose configuration."""
from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

CONFIG_FILE = Path("./config/docker/docker.json")
BASE_DIRECTORY = Path.cwd()
DOCKER_FILES: list[tuple[Path, Path]] = [
    (
        Path("scripts", "templates", "docker-compose.yml.j2"),
        Path("docker-compose.yml"),
    ),
    (
        Path("scripts", "templates", "docker-compose.override.yml.template.j2"),
        Path("docker-compose.override.yml.template"),
    ),
]
JINJA_ENV = Environment(loader=FileSystemLoader([str(BASE_DIRECTORY)]))


logger = logging.getLogger("generate_docker_templates.py")


def load_docker_configuration(config_file: Path) -> Dict[str, Any]:
    """Loads and validates the docker configuration file.

    Args:
        config_file: The path to the config file.
    """
    with open(config_file, "rb") as f:
        config = json.load(f)

    # handle the datasets_directory setting
    # if the path is not set, does not exist, or is not a directory,
    # then the setting is set to None, which will ensure the volumes
    # block is not added to the worker containers in docker-compose.yml
    if "datasets_directory" in config and config["datasets_directory"] != "":
        datasets_directory = Path(config["datasets_directory"])
        if datasets_directory.exists():
            if datasets_directory.is_dir:
                logger.info(f"Using '{datasets_directory}' .")
            else:
                logger.warn(f"The {datasets_directory} is not a directory.")
                config["datasets_directory"] = None
        else:
            logger.warn(f"The {datasets_directory} does not exist.")
            config["datasets_directory"] = None
    else:
        logger.warn("The datasets_directory setting was not found.")
        config["datasets_directory"] = None

    return config


def render_template_files(
    env: Environment,
    template_files: list[tuple[Path, Path]],
    docker_config: dict[str, Any],
) -> None:
    """Render the Jinja template files.

    Args:
        env: A Jinja2 environment object.
        template_files: A list of tuples containing the template name and output
            filepath.
    """
    variables = docker_config | dict(working_directory=str(BASE_DIRECTORY))
    logger.info(variables)
    for template_name, output_filepath in template_files:
        # if (BASE_DIRECTORY / output_filepath).exists():
            # logger.info(f"The file {str(output_filepath)} already exists, skipping")
            # continue

        logger.info(f"Generating {output_filepath}")
        content = _render_template(
            env=env,
            # Jinja2 requires forward slashes in the template name.
            template_name=str(template_name.as_posix()),
            variables=variables,
        )

        with (BASE_DIRECTORY / output_filepath).open("wt") as f:
            f.write(content)


def _render_template(
    env: Environment, template_name: str, variables: dict[str, Any]
) -> str:
    """Render a Jinja template.

    Args:
        env: A Jinja2 environment object.
        template_name: Name of the template file.
        variables: A dictionary of template variable to password mappings.
    """
    template = env.get_template(template_name)
    return template.render(**variables)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Current working directory: %s", str(BASE_DIRECTORY))
    docker_config = load_docker_configuration(CONFIG_FILE)
    render_template_files(JINJA_ENV, DOCKER_FILES, docker_config)
