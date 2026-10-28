"""Configuration resolution and policy tests with caller-owned temporary keys."""

import logging
import os
import subprocess
import sys
from pathlib import Path

import mlflow
import pytest
from injector import Injector

from dioptra.restapi import app as app_module
from dioptra.restapi import config
from dioptra.restapi.app import create_app
from dioptra.restapi.bootstrap import bind_dependencies
from dioptra.restapi.config import load_config, resolve_database_uri, resolve_mode


@pytest.fixture(autouse=True)
def configuration_environment(monkeypatch):
    for name in [
        *config._ENVIRONMENT_SETTINGS.values(),
        "DIOPTRA_RESTAPI_ENV",
        "DIOPTRA_RESTAPI_DATABASE_URI",
        "DIOPTRA_RESTAPI_DEV_DATABASE_URI",
        "DIOPTRA_DEPLOY_SECRET_KEY",
        "DIOPTRA_RESTAPI_SECRET_KEY_FILE",
    ]:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def overrides(signing_key_file, tmp_path):
    return {
        "SECRET_KEY_FILE": signing_key_file,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "MLFLOW_TRACKING_URI": tmp_path.resolve().as_uri(),
        "RQ_REDIS_URI": "redis://localhost:6399/2",
    }


@pytest.mark.parametrize("mode", [None, "", "test", "test_no_login", "production"])
def test_mode_is_explicit(mode, monkeypatch):
    """Reject missing and unsupported modes without inferring policy.

    Neither debug nor testing flags select an operating mode. Historical packaged
    testing modes are also rejected so tests use real development or production.
    """
    monkeypatch.setenv("FLASK_DEBUG", "1")
    with pytest.raises(ValueError, match="dev.*prod"):
        load_config(mode, overrides={"TESTING": True, "DEBUG": True})


def test_argument_mode_precedes_environment(monkeypatch):
    """Select an explicit mode before an inherited environment value.

    A stale or invalid process mode must not change the policy selected by a
    caller. The standalone resolver and application loader share that rule.
    """
    monkeypatch.setenv("DIOPTRA_RESTAPI_ENV", "invalid")
    assert resolve_mode("dev") == "dev"
    monkeypatch.setenv("DIOPTRA_RESTAPI_ENV", "dev")
    assert resolve_mode() == "dev"


@pytest.mark.parametrize(
    "setting,variable",
    [
        ("LOGIN_DISABLED", "DIOPTRA_LOGIN_DISABLED"),
        ("REMEMBER_COOKIE_SECURE", "DIOPTRA_REMEMBER_COOKIE_SECURE"),
        ("DIOPTRA_RESTAPI_LOG_AS_JSON", "DIOPTRA_RESTAPI_LOG_AS_JSON"),
    ],
)
@pytest.mark.parametrize(
    "value,expected", [(" FaLsE ", False), ("0", False), ("true", True), (" 1 ", True)]
)
def test_environment_boolean_vocabulary(
    setting, variable, value, expected, overrides, monkeypatch
):
    """Parse false and true environment values deliberately.

    Presence alone must not enable login bypasses, secure cookies, or JSON logs.
    The supported case-insensitive vocabulary also tolerates surrounding spaces.
    """
    monkeypatch.setenv(variable, value)
    assert getattr(load_config("dev", overrides=overrides), setting) is expected


@pytest.mark.parametrize("value", ["", "yes", "off", "2"])
def test_invalid_environment_boolean(value, overrides, monkeypatch):
    """Fail for unsupported boolean text instead of selecting a default.

    An explicitly supplied environment value must either be understood or stop
    startup, since silent coercion can change authentication behavior.
    """
    monkeypatch.setenv("DIOPTRA_LOGIN_DISABLED", value)
    with pytest.raises(ValueError, match="LOGIN_DISABLED"):
        load_config("dev", overrides=overrides)


@pytest.mark.parametrize(
    "name,value",
    [
        ("DEBUG", "false"),
        ("TESTING", 1),
        ("LOGIN_DISABLED", "0"),
        ("REMEMBER_COOKIE_SECURE", 0),
        ("DIOPTRA_MAX_PAGE_SIZE", True),
        ("DIOPTRA_MAX_PAGE_SIZE", "100"),
        ("REMEMBER_COOKIE_DURATION", False),
        ("SQLALCHEMY_TRACK_MODIFICATIONS", "False"),
        ("USE_MOCK_EQUIVALENCY", 1),
        ("DIOPTRA_CORS_ORIGIN", ""),
        ("DIOPTRA_MAX_PAGE_SIZE", 9),
        ("SQLALCHEMY_DATABASE_URI", "credential-value"),
        ("RQ_REDIS_URI", "http://credential-value"),
        ("MLFLOW_TRACKING_URI", ""),
        ("MLFLOW_TRACKING_URI", None),
        ("DIOPTRA_RESTAPI_LOG_LEVEL", "unrecognized-value"),
        ("DIOPTRA_BASE_URL", ""),
        ("DIOPTRA_SWAGGER_PATH", True),
        ("SESSION_PROTECTION", "unrecognized-value"),
        ("RQ_REDIS_URI", b"redis://localhost"),
        ("MLFLOW_TRACKING_URI", b"http://localhost"),
        ("REMEMBER_COOKIE_NAME", b"cookie-name"),
        ("SECRET_KEY_FILE", None),
    ],
)
def test_invalid_typed_overrides(name, value, overrides):
    """Validate caller types and constraints without exposing submitted values.

    Typed overrides must not gain the coercions intended only for environment
    strings. Invalid URIs and empty optional inputs also fail explicitly.
    """
    overrides[name] = value
    with pytest.raises(ValueError, match=name) as caught:
        load_config("dev", overrides=overrides)
    assert "credential-value" not in str(caught.value)
    assert "unrecognized-value" not in str(caught.value)


@pytest.mark.parametrize(
    "name", ["SECRET_KEY", "CONFIG_NAME", "MLFLOW_S3_ENDPOINT_URL", "UNKNOWN"]
)
def test_unsupported_overrides(name, overrides):
    """Reject unsupported settings instead of pretending to apply them.

    Secrets come from files, mode has its own input, and MLflow owns the S3
    endpoint process environment independently of per-application settings.
    """
    overrides[name] = "private-submitted-value"
    with pytest.raises(ValueError, match=name) as caught:
        load_config("dev", overrides=overrides)
    assert "private-submitted-value" not in str(caught.value)


def test_resolution_precedence_and_snapshot(overrides, monkeypatch):
    """Use one environment snapshot and let typed overrides take precedence.

    A scoped replacement changes the process after the snapshot is taken.
    This load keeps the original inputs, while the next load sees the change.
    """
    monkeypatch.setenv("DIOPTRA_MAX_PAGE_SIZE", "25")
    monkeypatch.setenv("RQ_REDIS_URI", "redis://localhost:6398/1")
    original = config._resolve_mode

    def change_environment(env, environment):
        monkeypatch.setenv("DIOPTRA_MAX_PAGE_SIZE", "75")
        return original(env, environment)

    with monkeypatch.context() as scoped:
        scoped.setattr(config, "_resolve_mode", change_environment)
        first = load_config("dev", overrides=overrides)
    second = load_config("dev", overrides=overrides)
    assert first.DIOPTRA_MAX_PAGE_SIZE == 25
    assert second.DIOPTRA_MAX_PAGE_SIZE == 75
    assert first is not second
    assert first.RQ_REDIS_URI == overrides["RQ_REDIS_URI"]
    assert first.SECRET_KEY == second.SECRET_KEY


def test_setting_normalization_and_flask_values(overrides, monkeypatch):
    """Preserve Flask semantics while normalizing supported settings.

    Session protection 'none' becomes None rather than a truthy string, integer
    durations stay seconds, and explicit False disables Swagger documentation.
    """
    monkeypatch.setenv("DIOPTRA_SESSION_PROTECTION", "NoNe")
    monkeypatch.setenv("DIOPTRA_REMEMBER_COOKIE_DURATION", "60")
    monkeypatch.setenv("DIOPTRA_RESTAPI_LOG_LEVEL", "warning")
    settings = load_config(
        "dev", overrides={**overrides, "DIOPTRA_SWAGGER_PATH": False}
    )
    assert settings.SESSION_PROTECTION is None
    assert settings.REMEMBER_COOKIE_DURATION == 60
    assert settings.DIOPTRA_RESTAPI_LOG_LEVEL == "WARNING"
    assert settings.DIOPTRA_SWAGGER_PATH is False


def test_mlflow_default_resolved_once(overrides, monkeypatch):
    """Ask MLflow for its current public default only when needed.

    Dioptra must pass a concrete URI to clients without replacing MLflow's
    supported local default selection with a historical hard-coded location.
    """
    calls = []

    def default_uri():
        calls.append(True)
        return "sqlite:///isolated-tracking.db"

    monkeypatch.setattr(mlflow, "get_tracking_uri", default_uri)
    del overrides["MLFLOW_TRACKING_URI"]
    settings = load_config("dev", overrides=overrides)
    settings.validate()
    assert settings.MLFLOW_TRACKING_URI == "sqlite:///isolated-tracking.db"
    assert len(calls) == 1
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "databricks://profile")
    assert (
        load_config("dev", overrides=overrides).MLFLOW_TRACKING_URI
        == "databricks://profile"
    )
    assert len(calls) == 1


def test_import_has_no_configuration_side_effects(monkeypatch):
    """Import class defaults without consuming deployment settings or files.

    Deliberately invalid ambient inputs must not prevent
    importing configuration; only an explicit resolution attempt may reject them.
    """
    monkeypatch.setenv("DIOPTRA_MAX_PAGE_SIZE", "invalid")
    monkeypatch.setenv("DIOPTRA_DEPLOY_SECRET_KEY", "private-value")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from dioptra.restapi.config import BaseConfig, DevelopmentConfig; "
            "assert DevelopmentConfig.DEBUG is True; "
            "assert BaseConfig.SECRET_KEY is None; "
            "assert BaseConfig.DIOPTRA_MAX_PAGE_SIZE == 1000",
        ],
        env=dict(os.environ),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("replacement_present", [False, True])
def test_retired_database_variable_rejected(monkeypatch, replacement_present):
    """Reject the retired database variable even beside its replacement.

    Silently ignoring an old development URI could select an unintended database.
    Migration guidance names both variables and never prints their credentials.
    """
    monkeypatch.setenv("DIOPTRA_RESTAPI_DEV_DATABASE_URI", "sqlite:///private-value")
    if replacement_present:
        monkeypatch.setenv(
            "DIOPTRA_RESTAPI_DATABASE_URI", "sqlite:///other-private-value"
        )
    with pytest.raises(ValueError) as caught:
        resolve_database_uri()
    message = str(caught.value)
    assert "DIOPTRA_RESTAPI_DEV_DATABASE_URI" in message
    assert "DIOPTRA_RESTAPI_DATABASE_URI" in message
    assert "private-value" not in message


def test_database_uri_is_mode_independent(overrides, tmp_path, monkeypatch):
    """Resolve the same absolute default for API and database tooling.

    The default database is dioptra.db in the invocation directory. A later
    directory change cannot change the target already held by an application.
    """
    monkeypatch.chdir(tmp_path)
    uri = resolve_database_uri()
    del overrides["SQLALCHEMY_DATABASE_URI"]
    dev = load_config("dev", overrides=overrides)
    assert uri == f"sqlite:///{tmp_path / 'dioptra.db'}"
    assert dev.SQLALCHEMY_DATABASE_URI == uri
    if not config._is_windows():
        assert load_config("prod", overrides=overrides).SQLALCHEMY_DATABASE_URI == uri
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert dev.SQLALCHEMY_DATABASE_URI == uri
    assert resolve_database_uri() != uri


def test_retired_secret_variable_rejected(overrides, monkeypatch):
    """Require file-based keys even when a valid file is also supplied.

    The old direct-value environment variable must fail with setup guidance so
    callers cannot unknowingly keep supplying a retired shared-secret mechanism.
    """
    monkeypatch.setenv("DIOPTRA_DEPLOY_SECRET_KEY", "private-value")
    with pytest.raises(ValueError, match="DIOPTRA_RESTAPI_SECRET_KEY_FILE") as caught:
        load_config("dev", overrides=overrides)
    assert "private-value" not in str(caught.value)


@pytest.mark.skipif(
    config._is_windows(), reason="Production startup requires a POSIX host."
)
@pytest.mark.parametrize("name", ["DEBUG", "LOGIN_DISABLED"])
def test_production_rejects_bypasses_even_when_testing(name, overrides):
    """Keep production operating policy active under TESTING.

    Testing changes error handling, not authentication or debug policy. Both
    loading and later supplied-instance validation must reject a policy bypass.
    """
    with pytest.raises(ValueError, match="Production"):
        load_config("prod", overrides={**overrides, "TESTING": True, name: True})
    settings = load_config("prod", overrides={**overrides, "TESTING": True})
    setattr(settings, name, True)
    with pytest.raises(ValueError, match=name):
        create_app(settings=settings, injector=Injector())


@pytest.mark.parametrize("testing", [False, True])
def test_windows_production_rejected_before_key_access(testing, overrides, monkeypatch):
    """Reject native-Windows production without a testing exception.

    A scoped platform replacement exercises the policy on every host. The key
    reader is deliberately unavailable to prove rejection precedes key access.
    """

    def unexpected_read(*args, **kwargs):
        pytest.fail("Rejected production settings must not read a key")

    monkeypatch.setattr(config, "_is_windows", lambda: True)
    monkeypatch.setattr(config, "read_key", unexpected_read)
    with pytest.raises(ValueError, match="native Windows"):
        load_config("prod", overrides={**overrides, "TESTING": testing})


@pytest.mark.parametrize("inputs", [{"env": "dev"}, {"overrides": {}}])
def test_supplied_settings_reject_mixed_inputs(inputs, overrides):
    """Reject both forms of factory input being supplied together.

    Even an explicit empty overrides mapping is ambiguous. A resolved instance
    must be the sole settings input so no ambient values supplement it.
    """
    settings = load_config("dev", overrides=overrides)
    with pytest.raises(ValueError, match="settings alone"):
        create_app(settings=settings, injector=Injector(), **inputs)


@pytest.mark.parametrize("mode_value", [None, "dev", "prod", "", "invalid"])
def test_supplied_settings_ignore_ambient_values_with_warning(
    mode_value, overrides, monkeypatch
):
    """Use a supplied configuration unchanged and warn about an ambient mode.

    Invalid ambient database, key and ordinary settings do not participate in
    resolution. Every present mode value is reported once, including empty text.
    """
    settings = load_config("dev", overrides=overrides)
    warnings = []

    class Logger:
        def warning(self, event, **values):
            warnings.append((event, values))

    monkeypatch.setattr(app_module, "LOGGER", Logger())
    monkeypatch.setenv("DIOPTRA_RESTAPI_DEV_DATABASE_URI", "invalid")
    monkeypatch.setenv("DIOPTRA_MAX_PAGE_SIZE", "invalid")
    monkeypatch.setenv("DIOPTRA_DEPLOY_SECRET_KEY", "private-value")
    if mode_value is not None:
        monkeypatch.setenv("DIOPTRA_RESTAPI_ENV", mode_value)
    app = create_app(settings=settings, injector=Injector())
    assert app.extensions["dioptra_settings"] is settings
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    assert len(warnings) == (mode_value is not None)
    if warnings:
        event, values = warnings[0]
        assert "ignored" in event
        assert values["DIOPTRA_RESTAPI_ENV"] == mode_value
        assert values["effective_mode"] == "dev"


@pytest.mark.parametrize(
    "failure",
    ["mode", "missing-key", "malformed-key", "setting", "redis-uri", "instance"],
)
def test_rejected_settings_precede_extensions_and_clients(
    failure, overrides, monkeypatch, tmp_path
):
    """Reject invalid application inputs before initialization has side effects.

    Extension and provider initialization are replaced with deliberate failures.
    Invalid mode, key, ordinary values, and supplied instances must fail earlier.
    """

    def unexpected_initialization(*args, **kwargs):
        pytest.fail("Invalid settings reached extension or client construction")

    monkeypatch.setattr(app_module, "Flask", unexpected_initialization)
    monkeypatch.setattr(app_module.db, "init_app", unexpected_initialization)
    monkeypatch.setattr(
        "dioptra.restapi.bootstrap.bind_dependencies", unexpected_initialization
    )
    mode = "dev"
    if failure == "mode":
        mode = None
    elif failure == "missing-key":
        overrides["SECRET_KEY_FILE"] = tmp_path.resolve() / "absent"
    elif failure == "malformed-key":
        parent = tmp_path.resolve() / "key-data"
        parent.mkdir(mode=0o700)
        key = parent / "key"
        key.write_bytes(b"deploy123")
        key.chmod(0o600)
        overrides["SECRET_KEY_FILE"] = key
    elif failure == "setting":
        overrides["DEBUG"] = "invalid"
    elif failure == "redis-uri":
        overrides["RQ_REDIS_URI"] = (
            "redis://user:private-password@localhost:invalid-port"
        )
    if failure == "instance":
        with pytest.raises(ValueError, match="load_config"):
            create_app(settings=config.DevelopmentConfig())
    else:
        with pytest.raises(ValueError):
            create_app(mode, overrides=overrides)


def test_two_applications_keep_their_settings(overrides, monkeypatch):
    """Keep existing applications stable when later construction sees new inputs.

    Fresh resolution observes environment changes, while the Flask dictionaries
    and resolved instances already held by another application remain unchanged.
    """
    monkeypatch.setenv("DIOPTRA_MAX_PAGE_SIZE", "25")
    first = create_app("dev", Injector(), overrides=overrides)
    monkeypatch.setenv("DIOPTRA_MAX_PAGE_SIZE", "50")
    second = create_app("dev", Injector(), overrides=overrides)
    assert first.config["DIOPTRA_MAX_PAGE_SIZE"] == 25
    assert second.config["DIOPTRA_MAX_PAGE_SIZE"] == 50


def test_dependency_bindings_consume_resolved_values(overrides, monkeypatch):
    """Construct default clients with the application's resolved connection URIs.

    Local client replacements observe inputs without opening services. Their
    constructors must receive overrides despite later conflicting environment
    values, and binding must not construct a direct S3 session or client.
    """
    from dioptra.restapi import bootstrap

    settings = load_config("dev", overrides=overrides)
    observed = {}

    class RedisClient:
        @staticmethod
        def from_url(uri):
            observed["redis"] = uri
            return object()

    class TrackingClient:
        def __init__(self, tracking_uri):
            observed["mlflow"] = tracking_uri

    monkeypatch.setattr(bootstrap, "Redis", RedisClient)
    monkeypatch.setattr(bootstrap, "MlflowClient", TrackingClient)
    monkeypatch.setenv("RQ_REDIS_URI", "invalid")
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "invalid")
    monkeypatch.setenv("MLFLOW_S3_ENDPOINT_URL", "invalid-library-owned-value")
    injector = Injector()
    bind_dependencies(injector.binder, settings)
    assert observed == {
        "redis": overrides["RQ_REDIS_URI"],
        "mlflow": overrides["MLFLOW_TRACKING_URI"],
    }
    assert "MLFLOW_S3_ENDPOINT_URL" not in vars(settings)
    assert logging.getLevelName(settings.DIOPTRA_RESTAPI_LOG_LEVEL) == logging.INFO


def test_default_factory_does_not_construct_unused_s3_clients(overrides, monkeypatch):
    """Construct the ordinary API with real default bindings and no S3 client.

    An intentionally unusable library-owned S3 endpoint must not affect API
    construction. Redis and HTTP tracking clients are real but have no running
    backing services; this checks construction rather than storage operations.
    """
    monkeypatch.setenv("MLFLOW_S3_ENDPOINT_URL", "invalid-endpoint")
    app = create_app(
        "dev",
        overrides={
            **overrides,
            "MLFLOW_TRACKING_URI": "http://127.0.0.1:1",
            "RQ_REDIS_URI": "redis://127.0.0.1:1",
        },
    )
    assert app.config["MLFLOW_TRACKING_URI"] == "http://127.0.0.1:1"
    assert app.config["RQ_REDIS_URI"] == "redis://127.0.0.1:1"


@pytest.mark.parametrize(
    "name,value",
    [
        ("SECRET_KEY", None),
        ("SECRET_KEY", "a" * 64 + "\n"),
        ("SECRET_KEY_FILE", Path("relative-key")),
        ("CONFIG_NAME", "prod"),
        ("DIOPTRA_MAX_PAGE_SIZE", 9),
        ("RQ_REDIS_URI", b"redis://localhost"),
        ("MLFLOW_TRACKING_URI", b"http://localhost"),
        ("REMEMBER_COOKIE_NAME", b"cookie-name"),
    ],
)
def test_supplied_instance_requires_complete_valid_values(name, value, overrides):
    """Revalidate required fields on supplied configuration instances.

    A previously resolved object can be changed by a caller. Construction must
    still reject incomplete values, noncanonical key text and a changed mode
    instead of allowing mutation to bypass normal validation.
    """
    settings = load_config("dev", overrides=overrides)
    setattr(settings, name, value)
    # Windows rejects production before comparing the configuration class.
    match = None if name == "CONFIG_NAME" else name
    with pytest.raises(ValueError, match=match):
        create_app(settings=settings, injector=Injector())


@pytest.mark.parametrize(
    "uri",
    [
        "redis://user:private-password@localhost:invalid-port",
        "redis://user:private-password@localhost?db=invalid-database",
        "rediss://user:private-password@localhost?socket_timeout=invalid-timeout",
    ],
)
def test_redis_uri_parser_rejects_invalid_components(uri, overrides):
    """Reject malformed Redis components before constructing clients.

    Redis's pure parser owns port and query conversion. Its failures must be
    reported as configuration errors without exposing credentials or submitted
    query values, and without contacting a Redis server.
    """
    with pytest.raises(ValueError, match="RQ_REDIS_URI") as caught:
        load_config("dev", overrides={**overrides, "RQ_REDIS_URI": uri})
    message = str(caught.value)
    assert "private-password" not in message
    assert "invalid-port" not in message
    assert "invalid-database" not in message
    assert "invalid-timeout" not in message


@pytest.mark.parametrize(
    "uri", ["redis://", "rediss://localhost:6380?db=2", "unix:///tmp/redis.sock?db=1"]
)
def test_redis_uri_parser_preserves_supported_forms(uri, overrides):
    """Keep the supported Redis schemes and the packaged default usable.

    Adding pure parsing must preserve ordinary Redis, TLS and Unix-socket URLs
    instead of replacing them with an HTTP-only or host-required constraint.
    """
    assert (
        load_config("dev", overrides={**overrides, "RQ_REDIS_URI": uri}).RQ_REDIS_URI
        == uri
    )
