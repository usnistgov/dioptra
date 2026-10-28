"""Database-only construction and installed migration command behavior."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from dioptra.restapi.config import resolve_database_uri
from dioptra.restapi.db import db
from dioptra.restapi.db.alembic import run
from dioptra.restapi.db.alembic.app import create_migration_app


def test_migration_factory_has_only_database_dependencies(tmp_path, monkeypatch):
    """Build complete migration metadata without an API mode, key or clients.

    Invalid unrelated API and service settings must not stop database tooling.
    The factory retains the same model metadata and migration options as the API.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DIOPTRA_RESTAPI_DEV_DATABASE_URI", raising=False)
    monkeypatch.setenv("DIOPTRA_RESTAPI_ENV", "invalid")
    monkeypatch.setenv("DIOPTRA_DEPLOY_SECRET_KEY", "retired-value")
    monkeypatch.setenv("RQ_REDIS_URI", "invalid")
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "invalid")
    monkeypatch.setenv("DIOPTRA_MAX_PAGE_SIZE", "invalid")
    app = create_migration_app(overrides={"SQLALCHEMY_DATABASE_URI": "sqlite://"})
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    assert "dioptra_settings" not in app.extensions
    assert not hasattr(app, "login_manager")
    assert app.extensions["migrate"].db is db
    assert app.extensions["migrate"].configure_args["render_as_batch"] is True
    assert {"users", "resources", "jobs", "artifacts", "entry_points"} <= set(
        db.metadata.tables
    )
    assert {rule.rule for rule in app.url_map.iter_rules()} == {
        "/static/<path:filename>"
    }


@pytest.mark.parametrize("replacement", [False, True])
def test_database_cli_rejects_retired_variable_with_failure(replacement, monkeypatch):
    """Return nonzero when database configuration is rejected.

    Both obsolete-variable combinations must fail before any subprocess starts,
    with replacement guidance and no credential-bearing URI in the diagnostic.
    """

    def unexpected_subprocess(*args, **kwargs):
        pytest.fail("Invalid database configuration started a subprocess")

    monkeypatch.setattr(run.subprocess, "run", unexpected_subprocess)
    monkeypatch.setenv("DIOPTRA_RESTAPI_DEV_DATABASE_URI", "postgresql://private-value")
    if replacement:
        monkeypatch.setenv(
            "DIOPTRA_RESTAPI_DATABASE_URI", "postgresql://other-private-value"
        )
    result = CliRunner().invoke(run.cli, ["autoupgrade"])
    assert result.exit_code != 0
    assert "DIOPTRA_RESTAPI_DATABASE_URI" in result.output
    assert "DIOPTRA_RESTAPI_DEV_DATABASE_URI" in result.output
    assert "private-value" not in result.output


def test_database_cli_keeps_child_failure(monkeypatch):
    """Propagate a failed native migration command to the caller.

    The subprocess deliberately returns failure. Dioptra must not report an
    empty current revision as success or continue to initialize a database.
    """

    def failed_subprocess(args, **kwargs):
        return subprocess.CompletedProcess(
            args, 7, stdout="", stderr="injected failure"
        )

    monkeypatch.delenv("DIOPTRA_RESTAPI_DEV_DATABASE_URI", raising=False)
    monkeypatch.setenv("DIOPTRA_RESTAPI_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(run.subprocess, "run", failed_subprocess)
    result = CliRunner().invoke(run.cli, ["autoupgrade"])
    assert result.exit_code == 7
    assert "injected failure" in result.output
    assert "Initializing database" not in result.output


def test_installed_database_command_without_api_configuration(tmp_path, monkeypatch):
    """Run installed migrations without a mode, signing key or backing services.

    An isolated SQLite database is initialized through the real console entry
    point. A rerun preserves its head revision, and SQLite metadata remains
    complete without registering API routes or starting unrelated clients.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DIOPTRA_RESTAPI_DEV_DATABASE_URI", raising=False)
    monkeypatch.delenv("DIOPTRA_RESTAPI_DATABASE_URI", raising=False)
    environment = {
        name: value
        for name, value in os.environ.items()
        if name not in {"DIOPTRA_RESTAPI_ENV", "DIOPTRA_RESTAPI_SECRET_KEY_FILE"}
    }
    environment.update(
        {
            "DIOPTRA_MAX_PAGE_SIZE": "invalid-unrelated-setting",
            "RQ_REDIS_URI": "invalid-unrelated-setting",
            "MLFLOW_TRACKING_URI": "invalid-unrelated-setting",
            "FLASK_APP": "invalid-unrelated-app",
        }
    )
    command = Path(sys.executable).parent / (
        "dioptra-db.exe" if os.name == "nt" else "dioptra-db"
    )
    first = subprocess.run(
        [str(command), "autoupgrade"], env=environment, capture_output=True, text=True
    )
    assert first.returncode == 0, first.stderr
    assert "Initializing database" in first.stdout
    assert (tmp_path / "dioptra.db").is_file()
    second = subprocess.run(
        [str(command), "autoupgrade"], env=environment, capture_output=True, text=True
    )
    assert second.returncode == 0, second.stderr
    assert "up to date" in second.stdout
    app = create_migration_app()
    assert app.config["SQLALCHEMY_DATABASE_URI"] == resolve_database_uri()
    with app.app_context():
        from sqlalchemy import inspect

        assert set(db.metadata.tables) <= set(inspect(db.engine).get_table_names())
        db.session.remove()
        db.engine.dispose()
