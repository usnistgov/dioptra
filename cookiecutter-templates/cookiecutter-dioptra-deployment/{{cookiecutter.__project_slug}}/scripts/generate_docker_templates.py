#!/usr/bin/env python
"""Render the Jinja templates containing the Docker Compose configuration."""
from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

DATASETS_DIRECTORY = "{{ cookiecutter.datasets_directory }}"
BASE_DIRECTORY = Path.cwd()
DOCKER_FILE = Path("scripts", "templates", "docker-compose.yml.j2")
JINJA_ENV = Environment(loader=FileSystemLoader([str(BASE_DIRECTORY)]))


logger = logging.getLogger("generate_docker_templates.py")


def validate_datasets_directory(datasets_directory: str) -> Path | None:
    """Validates the datasets directory"""

    if datasets_directory == "":
        logger.info("A datasets directory was not set.")
        return None

    datasets_directory = Path(datasets_directory)

    if not datasets_directory.exists():
        message = f"The provided datasets directory ({datasets_directory}) does not exist."
        logger.info(message)
        raise FileNotFoundError(message)

    if not datasets_directory.is_dir:
        message = f"The provided datasets directory ({datasets_directory}) is not a directory."
        logger.info(message)
        raise NotADirectoryError(message)

    logger.info(f"Using the provided datasets directory ({datasets_directory}) as a mount in all worker containers.")

    return datasets_directory


def render_template_files(
    env: Environment,
    template_files: list[tuple[Path, Path]],
    datasets_directory: Path,
) -> None:
    """Render the Jinja template files.

    Args:
        env: A Jinja2 environment object.
        template_files: A list of tuples containing the template name and output
            filepath.
    """
    variables = dict(datasets_directory=str(datasets_directory))

    logger.info(f"Generating docker-compose.yml")
    content = _render_template(
        env=env,
        # Jinja2 requires forward slashes in the template name.
        template_name=str(DOCKER_FILE.as_posix()),
        variables=variables,
    )

    with (BASE_DIRECTORY / "docker-compose.yml").open("wt") as f:
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
    datasets_directory = validate_datasets_directory(DATASETS_DIRECTORY)
    render_template_files(JINJA_ENV, DOCKER_FILE, datasets_directory)
