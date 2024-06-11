from __future__ import with_statement

import logging
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from dioptra.restapi.db.custom_types import GUID, TZDateTime

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from flask import current_app

config.set_main_option(
    "sqlalchemy.url",
    str(current_app.extensions["migrate"].db.engine.url).replace("%", "%%"),
)
target_metadata = current_app.extensions["migrate"].db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    app_env = os.getenv("DIOPTRA_RESTAPI_ENV", "dev")
    env_urls = {
        "dev": os.getenv("DIOPTRA_RESTAPI_DEV_DATABASE_URI"),
        "prod": os.getenv("DIOPTRA_RESTAPI_DATABASE_URI"),
    }

    return env_urls[app_env]


def render_item(type_, obj, autogen_context):
    """Apply custom rendering for selected items."""

    if type_ == "type" and isinstance(obj, GUID):
        # add import for this type
        autogen_context.imports.add("from dioptra.restapi.db.custom_types import GUID")
        return "%r" % obj

    if type_ == "type" and isinstance(obj, TZDateTime):
        # add import for this type
        autogen_context.imports.add(
            "from dioptra.restapi.db.custom_types import TZDateTime"
        )
        return "%r" % obj

    # default rendering for other objects
    return False


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    connectable = create_engine(get_url())

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            render_item=render_item,
            **current_app.extensions["migrate"].configure_args,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
