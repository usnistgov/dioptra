#!/usr/bin/env python
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
"""Generate the OpenAPI specification with caller-owned isolated API settings."""

import argparse
import json
import secrets
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from injector import Injector

from dioptra.restapi.app import create_app

OUTPUT_FILE = "docs/source/reference/api-restapi/openapi.yml"


def main(output_file: str | Path = OUTPUT_FILE) -> None:
    """Write a converted OpenAPI schema using isolated temporary API settings.

    Create a temporary key and application without default service clients, request
    the Swagger schema, and invoke ``swagger2openapi`` to write the output. The
    temporary directory is removed on exit.

    Args:
        output_file: Destination for the converted schema. Defaults to the
            repository's REST API reference output path.

    Raises:
        RuntimeError: If the application's Swagger endpoint does not return 200.
        subprocess.CalledProcessError: If conversion fails.
    """
    output = Path(output_file).absolute()
    with TemporaryDirectory(prefix="dioptra-openapi-") as temporary:
        directory = Path(temporary).resolve()
        directory.chmod(0o700)
        key_file = directory / "secret-key"
        key_file.touch(mode=0o600)
        key_file.chmod(0o600)
        key_file.write_bytes((secrets.token_hex(32) + "\n").encode("ascii"))
        app = create_app(
            env="dev",
            injector=Injector(),
            overrides={
                "SECRET_KEY_FILE": key_file,
                "TESTING": True,
                "DEBUG": False,
                "LOGIN_DISABLED": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "MLFLOW_TRACKING_URI": directory.as_uri(),
                "RQ_REDIS_URI": "redis://",
                "DIOPTRA_SWAGGER_PATH": "/",
                "DIOPTRA_BASE_URL": None,
            },
        )
        with app.test_client() as client:
            response = client.get("/swagger.json")
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch swagger.json: {response.status_code}"
                )
            schema_v2 = response.get_json()
        swagger = directory / "swagger.json"
        swagger.write_text(json.dumps(schema_v2), encoding="utf-8")
        subprocess.run(
            ["swagger2openapi", "--patch", str(swagger), "-o", str(output)], check=True
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=OUTPUT_FILE)
    main(parser.parse_args().output)
