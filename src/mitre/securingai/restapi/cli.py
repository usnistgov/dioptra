import os

import click

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--data",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, resolve_path=True),
    help="Filepath to raw training data",
)
@click.option(
    "--model",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, resolve_path=True),
    help="Filepath to pickled model",
)
@click.option(
    "--scaler",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, resolve_path=True),
    help="Filepath to pickled scaler",
)
@click.option(
    "--env",
    type=click.Choice(["prod", "dev", "test"], case_sensitive=False),
    default="prod",
    help="Flask configuration environment",
)
@click.option("--debug", is_flag=True, help="Run Flask server in debug mode")
def start_endpoint(data, model, scaler, debug, env):
    """Start Flask server and deploy model to endpoint."""
    if model:
        os.environ["AI_MODEL_FILEPATH"] = str(model)

    if data:
        os.environ["AI_TRAINING_DATA_FILEPATH"] = str(data)

    if scaler:
        os.environ["AI_TRAINING_SCALER_FILEPATH"] = str(scaler)

    from .app import create_app

    app = create_app(env=env)
    app.run_forever(debug=debug)
