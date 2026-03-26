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
"""Generate openapi.yml from Flask-RESTX"""

import subprocess
import json

from dioptra.restapi.app import create_app

OUTPUT_FILE = "docs/source/reference/api-restapi/openapi.yml"
V2_FILE = "swagger.json"


def main():
    app = create_app(env="test")

    with app.app_context():
        with app.test_client() as client:
            response = client.get("/swagger.json")

            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch swagger.json: {response.status_code}"
                )
            print(f"response: {response}")

        schema_v2 = response.get_json()  # v2 = swagger

        with open(V2_FILE, "w") as f:
            json.dump(schema_v2, f, sort_keys=False)

        subprocess.run(
            ["swagger2openapi", "--patch", V2_FILE, "-o", OUTPUT_FILE], check=True
        )

        with open(OUTPUT_FILE, "r") as f:
            print(f"openapi.yml contents: {f.read()}")


if __name__ == "__main__":
    main()
