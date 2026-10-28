"""Verify email nullability changes preserve users and foreign key references."""

from importlib import import_module
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import IntegrityError


def test_email_nullable_migration(tmp_path: Path) -> None:
    migration = import_module(
        "dioptra.restapi.db.alembic.versions.e64f9b2a7130_make_user_email_nullable"
    )
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    metadata = sa.MetaData()
    users = sa.Table(
        "users",
        metadata,
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("email_address", sa.Text(), nullable=False),
    )
    sa.Index("ix_users_username", users.c.username, unique=True)
    groups = sa.Table(
        "groups",
        metadata,
        sa.Column("group_id", sa.Integer(), primary_key=True),
        sa.Column("creator_id", sa.ForeignKey("users.user_id"), nullable=False),
    )
    with engine.connect() as connection:
        metadata.create_all(connection)
        connection.execute(
            users.insert().values(
                user_id=1, username="existing", email_address="old@example.org"
            )
        )
        connection.execute(groups.insert().values(group_id=1, creator_id=1))
        connection.commit()
        context = MigrationContext.configure(connection)

        with (
            Operations.context(context),
            context.begin_transaction(_per_migration=True),
        ):
            migration.upgrade()

        columns = {
            column["name"]: column
            for column in sa.inspect(connection).get_columns("users")
        }
        assert columns["email_address"]["nullable"]
        assert connection.scalar(sa.select(users.c.email_address)) == "old@example.org"
        assert connection.scalar(sa.select(groups.c.creator_id)) == 1
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert not connection.exec_driver_sql("PRAGMA foreign_key_check").all()
        connection.execute(
            users.insert().values(user_id=2, username="new", email_address=None)
        )
        connection.commit()

        with pytest.raises(RuntimeError, match="NULL values exist"):
            with (
                Operations.context(context),
                context.begin_transaction(_per_migration=True),
            ):
                migration.downgrade()

        connection.execute(
            users.update()
            .where(users.c.user_id == 2)
            .values(email_address="new@example.org")
        )
        connection.commit()
        with (
            Operations.context(context),
            context.begin_transaction(_per_migration=True),
        ):
            migration.downgrade()

        columns = {
            column["name"]: column
            for column in sa.inspect(connection).get_columns("users")
        }
        assert not columns["email_address"]["nullable"]
        assert connection.scalar(sa.select(groups.c.creator_id)) == 1
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        with pytest.raises(IntegrityError):
            connection.execute(
                users.insert().values(
                    user_id=3, username="existing", email_address="other@example.org"
                )
            )
        connection.rollback()
    engine.dispose()
