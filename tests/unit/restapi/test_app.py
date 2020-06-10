from flask import Flask, Response


def test_create_app(app: Flask):
    assert isinstance(app, Flask)


def test_app_healthy(app: Flask):
    with app.test_client() as client:
        resp: Response = client.get("/health")
        assert resp.status_code == 200
        assert resp.is_json
        assert resp.json == "healthy"
