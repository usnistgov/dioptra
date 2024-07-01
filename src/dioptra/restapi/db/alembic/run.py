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
"""Command-line script for applying migrations to the Dioptra database.

The database connection details are set using environment variables, see
dioptra/restapi/config.py for more information.

Examples:
    To upgrade the database to the latest revision::

        dioptra-db autoupgrade

    To downgrade the database to a previous revision::

        # Assume previous revision has a hash of 6b432d0a5ac7
        dioptra-db downgrade --revision 6b432d0a5ac7

    To display the database schema history::

        dioptra-db history

    To generate a new migration script::

        # Execute from the root of the repository
        dioptra-db migrate --message "Add new table"
"""
from __future__ import annotations

import os
import subprocess
from importlib.util import find_spec
from pathlib import Path

import click

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def _flask_db_current(alembic_dir: Path) -> str | None:
    """Get the current revision of the database.

    Args:
        alembic_dir: Path to directory containing the Alembic migration scripts.

    Returns:
        The current revision of the database.
    """
    p = subprocess.run(
        ["flask", "db", "current", "-d", str(alembic_dir)],
        capture_output=True,
        text=True,
    )
    output = p.stdout.strip().split(" ")[0]

    return output or None


def _flask_db_heads(alembic_dir: Path) -> str | None:
    """Get the HEAD revision of the database.

    Args:
        alembic_dir: Path to directory containing the Alembic migration scripts.

    Returns:
        The head revision of the database.
    """
    p = subprocess.run(
        ["flask", "db", "heads", "-d", str(alembic_dir)],
        capture_output=True,
        text=True,
    )
    output = p.stdout.strip().split(" ")[0]

    return output or None


def _flask_db_downgrade(alembic_dir: Path, revision: str) -> None:
    """Downgrade the database to the specified revision.

    Args:
        alembic_dir: Path to directory containing the Alembic migration scripts.
        revision: The revision identifier.
    """
    args = ["flask", "db", "downgrade", "-d", str(alembic_dir), revision]

    subprocess.run(
        args=args,
        capture_output=False,
        text=True,
    )


def _flask_db_history(alembic_dir: Path, indicate_current: bool) -> None:
    """Display the database schema history.

    Args:
        alembic_dir: Path to directory containing the Alembic migration scripts.
        indicate_current: Indicate the current revision in the history.
    """
    args = ["flask", "db", "history", "-d", str(alembic_dir)]

    if indicate_current:
        args.append("--indicate-current")

    subprocess.run(
        args=args,
        capture_output=False,
        text=True,
    )


def _flask_db_upgrade(alembic_dir: Path, revision: str) -> None:
    """Upgrade the database to the specified revision.

    Args:
        alembic_dir: Path to directory containing the Alembic migration scripts.
        revision: The revision identifier.
    """
    args = ["flask", "db", "upgrade", "-d", str(alembic_dir), revision]
    subprocess.run(
        args=args,
        capture_output=False,
        text=True,
    )


def _flask_db_migrate(
    alembic_dir: Path,
    message: str | None,
    sql: bool,
    head: str | None,
    splice: bool,
    branch_label: str | None,
    version_path: str | None,
    rev_id: str | None,
    x_arg: list[str],
) -> None:
    """Autogenerate a new revision file.

    Args:
        alembic_dir: Path to directory containing the Alembic migration scripts.
        message: The revision message.
        sql: Don't emit SQL to database - dump to standard output instead.
        head: Specify head revision or <branchname>@head to base new revision on.
        splice: Allow a non-head revision as the "head" to splice onto.
        branch_label: Specify a branch label to apply to the new revision.
        version_path: Specify specific path from config for version file.
        rev_id: Specify a hardcoded revision id instead of generating one.
        x_arg: Additional arguments consumed by custom env.py scripts.
    """
    args = ["flask", "db", "migrate", "-d", str(alembic_dir)]

    if message is not None:
        args.extend(["--message", message])

    if sql:
        args.append("--sql")

    if head is not None:
        args.extend(["--head", head])

    if splice:
        args.append("--splice")

    if branch_label is not None:
        args.extend(["--branch-label", branch_label])

    if version_path is not None:
        args.extend(["--version-path", version_path])

    if rev_id is not None:
        args.extend(["--rev-id", rev_id])

    if x_arg:
        for arg in x_arg:
            args.extend(["--x-arg", arg])

    subprocess.run(
        args=args,
        capture_output=False,
        text=True,
    )


def _flask_db_revision(
    alembic_dir: Path,
    message: str | None,
    autogenerate: bool,
    sql: bool,
    head: str | None,
    splice: bool,
    branch_label: str | None,
    version_path: str | None,
    rev_id: str | None,
) -> None:
    """Autogenerate a new revision file.

    Args:
        alembic_dir: Path to directory containing the Alembic migration scripts.
        message: The revision message.
        autogenerate: Populate revision script with candidate migration operations,
            based on comparison of database to model.
        sql: Don't emit SQL to database - dump to standard output instead.
        head: Specify head revision or <branchname>@head to base new revision on.
        splice: Allow a non-head revision as the "head" to splice onto.
        branch_label: Specify a branch label to apply to the new revision.
        version_path: Specify specific path from config for version file.
        rev_id: Specify a hardcoded revision id instead of generating one.
    """
    args = ["flask", "db", "revision", "-d", str(alembic_dir)]

    if message is not None:
        args.extend(["--message", message])

    if autogenerate:
        args.append("--autogenerate")

    if sql:
        args.append("--sql")

    if head is not None:
        args.extend(["--head", head])

    if splice:
        args.append("--splice")

    if branch_label is not None:
        args.extend(["--branch-label", branch_label])

    if version_path is not None:
        args.extend(["--version-path", version_path])

    if rev_id is not None:
        args.extend(["--rev-id", rev_id])

    subprocess.run(
        args=args,
        capture_output=False,
        text=True,
    )


def autoupgrade_cmd(alembic_dir: Path) -> None:
    """Command for automatically upgrading the database schema to the latest version.

    Args:
        alembic_dir: Path to directory containing the Alembic migration scripts.
    """
    db_revision_id = _flask_db_current(alembic_dir=alembic_dir)
    head_revision_id = _flask_db_heads(alembic_dir=alembic_dir)

    if db_revision_id == head_revision_id:
        print("Database is up to date.")
        return None

    if db_revision_id is None:
        print("Initializing database.")
        _flask_db_upgrade(alembic_dir=alembic_dir, revision="head")
        return None

    print("Migrating database tables to latest revision.")
    _flask_db_upgrade(alembic_dir=alembic_dir, revision="head")


def find_alembic_dir() -> Path:
    """Find the directory containing the Alembic migration scripts.

    Returns:
        The path to the directory containing the Alembic migration scripts.
    """
    module_spec = find_spec("dioptra.restapi.db.alembic")

    if module_spec is None or module_spec.submodule_search_locations is None:
        raise ModuleNotFoundError(
            "Unable to find the spec for the dioptra.restapi.db.alembic submodule. "
            "The dioptra package does not appear to be installed correctly."
        )

    alembic_dir: Path = Path(module_spec.submodule_search_locations[0])
    return alembic_dir


def is_db_uri_set() -> bool:
    """Check if the database URI is set in the environment.

    Returns:
        True if the database URI is set in the environment, False otherwise.
    """
    app_env = os.getenv("DIOPTRA_RESTAPI_ENV", "dev")
    env_vars = {
        "dev": "DIOPTRA_RESTAPI_DEV_DATABASE_URI",
        "prod": "DIOPTRA_RESTAPI_DATABASE_URI",
    }

    if (env_var := env_vars.get(app_env)) is None:
        raise ValueError(
            f"Invalid value for DIOPTRA_RESTAPI_ENV: {app_env}. "
            f"Valid values are 'dev' and 'prod'."
        )

    result = os.getenv(env_var) is not None

    if not result:
        print(
            f"Environment variable {env_var} is not set. "
            "The database cannot be found. Please set the environment variable and "
            "try again."
        )

    return result


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """Command-line interface for managing the Dioptra database.

    The database connection details are set using the following environment
    variables.

    \b
    DIOPTRA_RESTAPI_ENV:
        The environment in which the Dioptra REST API is running. Valid values
        are 'dev' and 'prod'. Defaults to 'dev'.

    \b
    DIOPTRA_RESTAPI_DEV_DATABASE_URI:
        The connection URI for the development database. Used when
        DIOPTRA_RESTAPI_ENV is set to 'dev'.

    \b
    DIOPTRA_RESTAPI_DATABASE_URI:
        The connection URI for the production database. Used when
        DIOPTRA_RESTAPI_ENV is set to 'prod'.
    """
    pass


@cli.command()
def autoupgrade() -> None:
    """Automatically upgrade the Dioptra database schema to the latest version."""
    if not is_db_uri_set():
        return None

    autoupgrade_cmd(alembic_dir=find_alembic_dir())


@cli.command()
@click.option(
    "--revision",
    type=click.STRING,
    default="head",
    show_default=True,
    help="Revision identifier",
)
def upgrade(revision: str):
    """Upgrade the Dioptra database schema to the specified revision."""
    if not is_db_uri_set():
        return None

    _flask_db_upgrade(alembic_dir=find_alembic_dir(), revision=revision)


@cli.command()
@click.argument(
    "revision",
    nargs=1,
    type=click.STRING,
)
def downgrade(revision: str):
    """Downgrade the Dioptra database schema to an earlier version.

    REVISION: Revision identifier
    """
    if not is_db_uri_set():
        return None

    _flask_db_downgrade(alembic_dir=find_alembic_dir(), revision=revision)


@cli.command()
@click.option(
    "-i",
    "--indicate-current",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Indicate the current revision",
)
def history(indicate_current: bool):
    """Display the Dioptra database schema history."""
    if not is_db_uri_set():
        return None

    _flask_db_history(alembic_dir=find_alembic_dir(), indicate_current=indicate_current)


@cli.command()
@click.option(
    "-d",
    "--directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("src", "dioptra", "restapi", "db", "alembic"),
    help='Migration script directory (default is "src/dioptra/restapi/db/alembic")',
)
@click.option("-m", "--message", type=click.STRING, help="Revision message")
@click.option(
    "--sql",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output instead",
)
@click.option(
    "--head",
    type=click.STRING,
    help="Specify head revision or <branchname>@head to base new revision on",
)
@click.option(
    "--splice",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help='Allow a non-head revision as the "head" to splice onto',
)
@click.option(
    "--branch-label",
    type=click.STRING,
    help="Specify a branch label to apply to the new revision",
)
@click.option(
    "--version-path",
    type=click.STRING,
    help="Specify specific path from config for version file",
)
@click.option(
    "--rev-id",
    type=click.STRING,
    help="Specify a hardcoded revision id instead of generating one",
)
@click.option(
    "-x",
    "--x-arg",
    type=click.STRING,
    multiple=True,
    help="Additional arguments consumed by custom env.py scripts",
)
def migrate(
    directory: Path,
    message: str | None,
    sql: bool,
    head: str | None,
    splice: bool,
    branch_label: str | None,
    version_path: str | None,
    rev_id: str | None,
    x_arg: list[str],
):
    """Autogenerate a new revision file (Alias for 'flask db migrate')."""
    if not is_db_uri_set():
        return None

    _flask_db_migrate(
        alembic_dir=directory,
        message=message,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
        rev_id=rev_id,
        x_arg=x_arg,
    )


@cli.command()
@click.option(
    "-d",
    "--directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("src", "dioptra", "restapi", "db", "alembic"),
    help='Migration script directory (default is "src/dioptra/restapi/db/alembic")',
)
@click.option("-m", "--message", type=click.STRING, help="Revision message")
@click.option(
    "--autogenerate",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help=(
        "Populate revision script with candidate migration operations, based on "
        "comparison of database to model"
    ),
)
@click.option(
    "--sql",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output instead",
)
@click.option(
    "--head",
    type=click.STRING,
    help="Specify head revision or <branchname>@head to base new revision on",
)
@click.option(
    "--splice",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help='Allow a non-head revision as the "head" to splice onto',
)
@click.option(
    "--branch-label",
    type=click.STRING,
    help="Specify a branch label to apply to the new revision",
)
@click.option(
    "--version-path",
    type=click.STRING,
    help="Specify specific path from config for version file",
)
@click.option(
    "--rev-id",
    type=click.STRING,
    help="Specify a hardcoded revision id instead of generating one",
)
def revision(
    directory: Path,
    message: str | None,
    autogenerate: bool,
    sql: bool,
    head: str | None,
    splice: bool,
    branch_label: str | None,
    version_path: str | None,
    rev_id: str | None,
):
    """Create a new revision file (Alias for 'flask db revision')."""
    if not is_db_uri_set():
        return None

    _flask_db_revision(
        alembic_dir=directory,
        message=message,
        autogenerate=autogenerate,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
        rev_id=rev_id,
    )


if __name__ == "__main__":
    cli()
