# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from flask import Flask, Response


def test_create_app(app: Flask):
    assert isinstance(app, Flask)


def test_app_healthy(app: Flask):
    with app.test_client() as client:
        resp: Response = client.get("/health")
        assert resp.status_code == 200
        assert resp.is_json
        assert resp.json == "healthy"
