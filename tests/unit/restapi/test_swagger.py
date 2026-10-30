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
"""Regression tests for enum fields in generated Swagger documentation."""

import enum
from http import HTTPStatus
from typing import Any

import pytest
from flask import Flask
from flask_accepts.utils import for_swagger
from flask_restx import Api, Namespace
from marshmallow import Schema, ValidationError, fields

from dioptra.restapi.patches import register_enum_swagger_mapping
from dioptra.restapi.routes import register_routes
from dioptra.restapi.v1.jobs.schema import JobLogRecordsSchema, JobLogSeverity


def test_job_log_swagger_documents_severity() -> None:
    """The actual JSON POST and GET models include severity and its choices."""
    app = Flask(__name__)
    api = Api(app)
    register_routes(api)

    response = app.test_client().get("/swagger.json")
    assert response.status_code == HTTPStatus.OK
    swagger = response.get_json()
    definitions = swagger["definitions"]

    def resolve(reference: dict[str, Any]) -> dict[str, Any]:
        return definitions[reference["$ref"].rsplit("/", 1)[1]]

    endpoint = swagger["paths"]["/api/v1/jobs/{id}/log"]
    body = next(p for p in endpoint["post"]["parameters"] if p["in"] == "body")
    request_model = resolve(body["schema"])
    post_record = resolve(request_model["properties"]["data"]["items"])
    get_page = resolve(endpoint["get"]["responses"]["200"]["schema"])
    get_record = resolve(get_page["properties"]["data"]["items"])

    for record in (post_record, get_record):
        severity = record["properties"]["severity"]
        assert "severity" in record["required"]
        assert severity["type"] == "string"
        assert severity["enum"] == ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert severity["example"] in severity["enum"]
        assert "Log severity level" in severity["description"]
    assert "createdOn" not in post_record["properties"]
    assert "createdOn" in get_record["properties"]


@pytest.mark.parametrize("by_value", [False, True])
def test_enum_swagger_serializes_defaults(by_value: bool) -> None:
    """Enums using names or string values retain JSON-compatible defaults."""

    class Status(enum.Enum):
        READY = "ready"
        DONE = "done"

    class StatusSchema(Schema):
        status = fields.Enum(
            Status,
            by_value=by_value,
            load_default=Status.READY,
            dump_default=Status.DONE,
        )

    register_enum_swagger_mapping()
    model = for_swagger(StatusSchema, Namespace("test"), operation="load")
    properties = model.__schema__["properties"]["status"]
    assert properties["enum"] == (["ready", "done"] if by_value else ["READY", "DONE"])
    assert properties["default"] == ("ready" if by_value else "READY")
    assert properties["example"] == ("done" if by_value else "DONE")


@pytest.mark.parametrize("severity", list(JobLogSeverity))
def test_log_severity_still_loads_as_enum(severity: JobLogSeverity) -> None:
    """The documentation mapping leaves the service's enum input unchanged."""
    register_enum_swagger_mapping()
    payload = {
        "data": [{"severity": severity.name, "loggerName": "test", "message": "ok"}]
    }
    schema = JobLogRecordsSchema()
    loaded = schema.load(payload)
    assert loaded["data"][0]["severity"] is severity
    assert schema.dump(loaded) == payload


@pytest.mark.parametrize("severity", [None, "INVALID"])
def test_log_severity_remains_required_and_validated(severity: str | None) -> None:
    """Missing and unknown severities continue to fail validation."""
    register_enum_swagger_mapping()
    record = {"loggerName": "test", "message": "ok"}
    if severity is not None:
        record["severity"] = severity
    with pytest.raises(ValidationError) as error:
        JobLogRecordsSchema().load({"data": [record]})
    assert "severity" in error.value.messages["data"][0]
