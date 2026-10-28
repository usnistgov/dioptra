"""Exercise API command policy and native server option delegation."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from flask import Flask

from dioptra.restapi import config
from dioptra.restapi.cli import api
from dioptra.restapi.key_file import initialize_key

POSIX = pytest.mark.skipif(os.name == "nt", reason="Gunicorn needs a POSIX host.")


@pytest.fixture(autouse=True)
def launcher_environment(monkeypatch, tmp_path):
    """Keep launcher tests independent of deployment variables and logging state."""
    for name in [
        *config._ENVIRONMENT_SETTINGS.values(),
        "DIOPTRA_RESTAPI_ENV",
        "DIOPTRA_RESTAPI_DATABASE_URI",
        "DIOPTRA_RESTAPI_DEV_DATABASE_URI",
        "DIOPTRA_RESTAPI_SECRET_KEY_FILE",
        "DIOPTRA_DEPLOY_SECRET_KEY",
        "FLASK_DEBUG",
        "FLASK_APP",
        "GUNICORN_CMD_ARGS",
    ]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tmp_path.resolve().as_uri())
    monkeypatch.setattr(api, "configure_logging", lambda settings: None)


@pytest.fixture
def key(tmp_path):
    path = tmp_path.resolve() / "api-data" / "key"
    initialize_key(path, development=True)
    return path


def test_initializer_ignores_api_settings(tmp_path, monkeypatch):
    """Initialize without selecting mode, constructing Flask or resolving services.

    Deliberately invalid unrelated deployment settings must not prevent explicit
    provisioning, and both creation and preservation return zero without secrets.
    """
    path = tmp_path.resolve() / "data" / "key"
    monkeypatch.setenv("DIOPTRA_RESTAPI_ENV", "bad")
    monkeypatch.setenv("DIOPTRA_RESTAPI_DEV_DATABASE_URI", "bad")
    monkeypatch.setenv("DIOPTRA_DEPLOY_SECRET_KEY", "must not be exposed")
    monkeypatch.setenv("RQ_REDIS_URI", "bad")

    def forbidden(*args, **kwargs):
        pytest.fail("initializer attempted API settings, construction or validation")

    monkeypatch.setattr(api, "create_app", forbidden)
    monkeypatch.setattr(api, "load_config", forbidden)
    monkeypatch.setattr(api, "run_pre_server_validation", forbidden)
    args = ["init-key", "--development", "--key-file", str(path)]
    first = CliRunner().invoke(api.main, args)
    second = CliRunner().invoke(api.main, args)
    assert first.exit_code == second.exit_code == 0
    assert "Created" in first.output and "Preserved" in second.output
    assert str(path) in first.output
    assert path.read_text().strip() not in first.output + second.output
    assert "must not be exposed" not in first.output + second.output


@pytest.mark.parametrize("source", ["argument", "environment", "default"])
def test_initializer_path_precedence(tmp_path, monkeypatch, source):
    """Use the shared argument, environment and per-user default precedence.

    The installed initializer and launchers must select one normalized path
    rather than trying alternatives when an explicitly selected path fails.
    """
    root = tmp_path.resolve()
    monkeypatch.chdir(root)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: root))
    args = ["init-key", "--development"]
    if source in {"argument", "environment"}:
        monkeypatch.setenv("DIOPTRA_RESTAPI_SECRET_KEY_FILE", "env-data/key")
        selected = root / "env-data/key"
    else:
        selected = root / ".local/share/dioptra/restapi/secret-key"
    if source == "argument":
        args += ["--key-file", "cli-data/key"]
        selected = root / "cli-data/key"
    result = CliRunner().invoke(api.main, args)
    assert result.exit_code == 0, result.output
    assert selected.exists()
    assert str(selected) in result.output


@pytest.mark.parametrize(
    "command", ["init-key", "dev", pytest.param("prod", marks=POSIX)]
)
def test_selected_missing_or_invalid_key_is_not_replaced(
    command, tmp_path, monkeypatch
):
    """Fail commands at the selected path without startup generation or fallback.

    Initialization preserves invalid bytes; launch requires a preexisting valid
    key. A valid environment alternative must never hide the selected failure.
    Production requires POSIX because native Windows rejects its mode before
    key access.
    """
    root = tmp_path.resolve()
    valid = root / "valid/key"
    initialize_key(valid, development=True)
    monkeypatch.setenv("DIOPTRA_RESTAPI_SECRET_KEY_FILE", str(valid))
    invalid = root / "invalid/key"
    if command == "init-key":
        invalid.parent.mkdir(mode=0o700)
        invalid.write_bytes(b"bad")
        invalid.chmod(0o600)
    result = CliRunner().invoke(
        api.main,
        [
            command,
            "--key-file",
            str(invalid),
            *(["--development"] if command == "init-key" else []),
        ],
    )
    assert result.exit_code != 0
    assert str(invalid) in result.output
    if command == "init-key":
        assert invalid.read_bytes() == b"bad"
    else:
        assert not invalid.exists()


@pytest.mark.parametrize(
    "flag,environment,expected",
    [
        ([], None, True),
        ([], "0", False),
        ([], "1", True),
        (["--debug"], "0", True),
        (["--no-debug"], "1", False),
        (["--debug"], "bad", True),
        (["--no-debug"], "bad", False),
        ([], " FaLsE ", False),
    ],
)
def test_dev_debug_and_native_options(key, flag, environment, expected, monkeypatch):
    """Keep debug precedence consistent with app policy and native Flask controls.

    Explicit flags precede FLASK_DEBUG and the development default. Native host,
    port, reload and debugger options retain independent effects on the server.
    """
    import flask.cli

    observed = {}
    if environment is not None:
        monkeypatch.setenv("FLASK_DEBUG", environment)
    monkeypatch.setenv("DIOPTRA_RESTAPI_ENV", "prod")
    monkeypatch.setenv("FLASK_APP", "replacement:app")

    def create(*, settings):
        observed["settings"] = settings
        app = Flask(__name__)
        app.config.from_object(settings)
        return app

    def serve(host, port, app, **options):
        observed.update(host=host, port=port, app=app, options=options)

    monkeypatch.setattr(api, "create_app", create)
    monkeypatch.setattr(flask.cli, "run_simple", serve)
    result = CliRunner().invoke(
        api.main,
        [
            "dev",
            "--key-file",
            str(key),
            *flag,
            "--host",
            "127.0.0.2",
            "--port",
            "54321",
            "--no-reload",
            "--no-debugger",
            "--without-threads",
        ],
    )
    assert result.exit_code == 0, result.output
    assert observed["settings"].CONFIG_NAME == "dev"
    assert observed["settings"].DEBUG is observed["app"].debug is expected
    assert observed["host"] == "127.0.0.2" and observed["port"] == 54321
    assert observed["options"]["use_reloader"] is False
    assert observed["options"]["use_debugger"] is False
    assert observed["options"]["threaded"] is False


@pytest.mark.parametrize("command", ["dev", pytest.param("prod", marks=POSIX)])
def test_preserver_failure_prevents_dispatch(command, key, monkeypatch):
    """Propagate direct pre-server validation failures before any serving starts.

    The test replaces the validation function with one that raises an error,
    ensuring that a failure prevents server dispatch. Production requires POSIX
    because native Windows rejects its mode before pre-server validation.
    """
    observed = []

    def reject(settings):
        assert settings.CONFIG_NAME == command
        assert settings.SECRET_KEY_FILE == key
        observed.append("validation")
        raise ValueError("injected database validation failure")

    def forbidden(*args, **kwargs):
        pytest.fail("server dispatched after failed pre-server validation")

    monkeypatch.setattr(api, "run_pre_server_validation", reject)
    monkeypatch.setattr(api, "create_app", forbidden)
    result = CliRunner().invoke(api.main, [command, "--key-file", str(key)])
    assert result.exit_code != 0
    assert "injected database validation failure" in result.output
    assert observed == ["validation"]


@pytest.mark.parametrize(
    "arguments", [["replacement:app"], ["--app", "replacement:app"]]
)
def test_dev_rejects_app_replacement(key, arguments):
    """Reject application replacement through the development command.

    The native run parser must reject a positional app or --app option so callers
    cannot bypass the resolved Dioptra factory and explicit operating policy.
    """
    result = CliRunner().invoke(api.main, ["dev", "--key-file", str(key), *arguments])
    assert result.exit_code != 0
    assert "Error" in result.output


@POSIX
def test_prod_native_configuration_and_fixed_factory(key, tmp_path, monkeypatch):
    """Retain Gunicorn option/config parsing with a fixed resolved Dioptra app.

    A working-directory change must not reinterpret the selected relative key or
    local database default, and TLS, worker and timeout options must reach Gunicorn.
    """
    from dioptra.restapi.cli.production import DioptraApplication

    root = tmp_path.resolve()
    target = root / "server"
    target.mkdir()
    config_path = root / "gunicorn.conf.py"
    config_path.write_text("workers = 2\ntimeout = 47\n")
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.setenv("DIOPTRA_RESTAPI_ENV", "dev")
    observed = {}

    def run(application):
        observed["application"] = application

    monkeypatch.setattr(DioptraApplication, "run", run)
    result = CliRunner().invoke(
        api.main,
        [
            "prod",
            "--key-file",
            str(key.relative_to(root)),
            "-c",
            "gunicorn.conf.py",
            "--chdir",
            str(target),
            "--bind",
            "127.0.0.1:54321",
            "--workers",
            "3",
            "--certfile",
            "server.crt",
            "--keyfile",
            "server.key",
        ],
    )
    assert result.exit_code == 0, result.output
    app = observed["application"]
    assert app.settings.CONFIG_NAME == "prod" and app.settings.DEBUG is False
    assert app.settings.SECRET_KEY_FILE == key
    assert app.settings.SQLALCHEMY_DATABASE_URI == f"sqlite:///{root / 'dioptra.db'}"
    assert app.cfg.workers == 3 and app.cfg.timeout == 47
    assert app.cfg.bind == ["127.0.0.1:54321"]
    assert app.cfg.certfile == "server.crt" and app.cfg.keyfile == "server.key"
    assert app.cfg.chdir == str(target)


@POSIX
@pytest.mark.parametrize(
    "source",
    [
        "positional",
        "paste-option",
        "wsgi-option",
        "paste-config",
        "wsgi-config",
        "paste-env",
        "wsgi-env",
        "positional-env",
    ],
)
def test_prod_rejects_alternative_dispatch(key, source, tmp_path, monkeypatch):
    """Reject replacement WSGI and Paste applications from native inputs.

    Gunicorn's arguments, config files and GUNICORN_CMD_ARGS all require checking,
    because any of them could otherwise bypass fixed application construction.
    """
    from dioptra.restapi.cli.production import DioptraApplication

    monkeypatch.setattr(
        DioptraApplication, "run", lambda app: pytest.fail("replacement dispatched")
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    args = ["prod", "--key-file", str(key)]
    if source == "positional":
        args += ["replacement:app"]
    elif source.endswith("-option"):
        args += [
            "--paste" if source.startswith("paste") else "--wsgi-app",
            "replacement",
        ]
    elif source.endswith("-config"):
        selected = tmp_path / "gunicorn.py"
        selected.write_text(
            ("paste" if source.startswith("paste") else "wsgi_app")
            + " = 'replacement'\n"
        )
        args += ["-c", str(selected)]
    else:
        option = {
            "paste-env": "--paste replacement",
            "wsgi-env": "--wsgi-app replacement",
            "positional-env": "replacement:app",
        }[source]
        monkeypatch.setenv("GUNICORN_CMD_ARGS", option)
    result = CliRunner().invoke(api.main, args)
    assert result.exit_code != 0
    assert "application" in result.output or "unrecognized arguments" in result.output


@POSIX
def test_pre_exec_retains_configured_hook_and_invocation_directory(
    key, tmp_path, monkeypatch
):
    """Keep native pre-exec customization while restoring invocation path semantics.

    Gunicorn records its cwd after --chdir. The launcher must reset only restart
    context and preserve the operator's hook; actual re-exec is qualified separately.
    """
    from dioptra.restapi.cli.production import DioptraApplication

    root = tmp_path.resolve()
    target = root / "server"
    target.mkdir()
    configuration = root / "gunicorn.conf.py"
    configuration.write_text(
        "def pre_exec(server):\n    server.operator_hook_ran = True\n"
    )
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    args = ["dioptra-api", "prod", "--key-file", "api-data/key"]
    monkeypatch.setattr(sys, "argv", args)
    settings = config.load_config("prod", overrides={"SECRET_KEY_FILE": key})
    app = DioptraApplication(
        settings, ["-c", str(configuration), "--chdir", str(target)]
    )
    assert sys.argv == args
    server = SimpleNamespace(START_CTX={"cwd": str(target)})
    app.cfg.pre_exec(server)
    assert server.operator_hook_ran
    assert server.START_CTX["cwd"] == str(root)
    assert Path.cwd() == target


@pytest.mark.parametrize("command", ["init-key", "dev", "prod"])
def test_explicit_empty_key_path_fails_without_side_effects(
    command, monkeypatch, tmp_path
):
    """Reject an explicit empty key option before filesystem or server actions.

    Click must preserve the invalid empty string until shared path validation;
    coercing it into the current directory could authorize a permission repair.
    """

    def forbidden(*args, **kwargs):
        pytest.fail("empty key selection reached initialization or server validation")

    monkeypatch.chdir(tmp_path)
    before = tmp_path.stat().st_mode
    original_paths = set(tmp_path.iterdir())
    monkeypatch.setattr(api, "initialize_key", forbidden)
    monkeypatch.setattr(api, "run_pre_server_validation", forbidden)
    result = CliRunner().invoke(api.main, [command, "--key-file", ""])
    assert result.exit_code != 0
    assert "SECRET_KEY_FILE" in result.output
    assert tmp_path.stat().st_mode == before
    assert set(tmp_path.iterdir()) == original_paths


@pytest.mark.parametrize("value", ["", "yes", "2", "enabled"])
def test_invalid_debug_environment_is_not_coerced(key, monkeypatch, value):
    """Reject unsupported FLASK_DEBUG text before server dispatch.

    Native Flask accepts broader truthy strings. The API uses its approved strict
    vocabulary so unexpected input cannot silently enable the debugger.
    """
    monkeypatch.setenv("FLASK_DEBUG", value)
    result = CliRunner().invoke(api.main, ["dev", "--key-file", str(key)])
    assert result.exit_code != 0
    assert "FLASK_DEBUG" in result.output


def test_direct_wsgi_uses_common_resolved_configuration(key, monkeypatch):
    """Keep direct WSGI construction on the common settings and logging path.

    An explicitly selected mode and key produce the fixed application. Packaged
    launcher validation remains separate from this direct factory consumer.
    """
    import runpy

    monkeypatch.setenv("DIOPTRA_RESTAPI_ENV", "dev")
    monkeypatch.setenv("DIOPTRA_RESTAPI_SECRET_KEY_FILE", str(key))
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:1")
    observed = {}

    def logging(settings):
        observed["settings"] = settings

    def forbidden(settings):
        pytest.fail("direct WSGI construction invoked launcher-only validation")

    monkeypatch.setattr(api, "configure_logging", logging)
    monkeypatch.setattr(api, "run_pre_server_validation", forbidden)
    module = runpy.run_path(str(Path(__file__).resolve().parents[3] / "wsgi.py"))
    app = module["app"]
    assert app.extensions["dioptra_settings"] is observed["settings"]
    assert observed["settings"].SECRET_KEY_FILE == key
    assert observed["settings"].CONFIG_NAME == "dev"
    assert app.test_client().get("/health").status_code == 200
