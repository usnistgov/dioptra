"""Add public groups and personal groups for existing users

Revision ID: 9e2b1d0f4c3a
Revises: ad4f89b2288d
Create Date: 2026-05-12 12:00:00.000000

"""

import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9e2b1d0f4c3a"
down_revision = "ad4f89b2288d"
branch_labels = None
depends_on = None

BUILTIN_PARAMETER_TYPES = ("any", "number", "integer", "string", "boolean", "null")


def _ensure_lock(
    connection: sa.Connection,
    resource_locks: sa.Table,
    resource_id: int,
    lock_type: str,
    timestamp: datetime.datetime,
) -> None:
    lock_exists = connection.scalar(
        sa.select(sa.literal(True)).where(
            sa.exists().where(
                resource_locks.c.resource_id == resource_id,
                resource_locks.c.resource_lock_type == lock_type,
            )
        )
    )
    if not lock_exists:
        connection.execute(
            resource_locks.insert().values(
                resource_id=resource_id,
                resource_lock_type=lock_type,
                created_on=timestamp,
            )
        )


def _ensure_builtin_parameter_types(
    connection: sa.Connection,
    tables: dict[str, sa.Table],
    group_id: int,
    user_id: int,
    timestamp: datetime.datetime,
) -> None:
    resources = tables["resources"]
    resource_snapshots = tables["resource_snapshots"]
    resource_locks = tables["resource_locks"]
    parameter_types = tables["plugin_task_parameter_types"]

    for name in BUILTIN_PARAMETER_TYPES:
        resource_id = connection.scalar(
            sa.select(parameter_types.c.resource_id)
            .join(
                resources,
                resources.c.resource_id == parameter_types.c.resource_id,
            )
            .where(resources.c.group_id == group_id, parameter_types.c.name == name)
            .limit(1)
        )
        if resource_id is not None:
            connection.execute(
                resource_locks.delete().where(
                    resource_locks.c.resource_id == resource_id,
                    resource_locks.c.resource_lock_type == "delete",
                )
            )
            _ensure_lock(connection, resource_locks, resource_id, "readonly", timestamp)
            continue

        resource_result = connection.execute(
            resources.insert().values(
                group_id=group_id,
                resource_type="plugin_task_parameter_type",
                created_on=timestamp,
            )
        )
        resource_id = resource_result.inserted_primary_key[0]
        snapshot_result = connection.execute(
            resource_snapshots.insert().values(
                resource_id=resource_id,
                resource_type="plugin_task_parameter_type",
                user_id=user_id,
                description=None,
                created_on=timestamp,
            )
        )
        snapshot_id = snapshot_result.inserted_primary_key[0]
        connection.execute(
            parameter_types.insert().values(
                resource_snapshot_id=snapshot_id,
                resource_id=resource_id,
                name=name,
                structure=None,
            )
        )
        _ensure_lock(connection, resource_locks, resource_id, "readonly", timestamp)


def _backfill_personal_groups() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData()
    table_names = (
        "users",
        "user_locks",
        "groups",
        "group_locks",
        "group_members",
        "group_managers",
        "resources",
        "resource_snapshots",
        "resource_locks",
        "plugin_task_parameter_types",
    )
    metadata.reflect(bind=connection, only=table_names)
    tables = {name: metadata.tables[name] for name in table_names}

    users = tables["users"]
    user_locks = tables["user_locks"]
    groups = tables["groups"]
    group_locks = tables["group_locks"]
    group_members = tables["group_members"]
    group_managers = tables["group_managers"]

    active_users = (
        connection.execute(
            sa.select(users.c.user_id, users.c.username).where(
                ~sa.exists().where(
                    user_locks.c.user_id == users.c.user_id,
                    user_locks.c.user_lock_type == "delete",
                )
            )
        )
        .mappings()
        .all()
    )

    for user in active_users:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        user_id = user["user_id"]
        username = user["username"]
        group_id = connection.scalar(
            sa.select(groups.c.group_id).where(
                groups.c.user_id == user_id,
                groups.c.name == username,
            )
        )

        if group_id is None:
            group_result = connection.execute(
                groups.insert().values(
                    name=username,
                    user_id=user_id,
                    public=True,
                    created_on=timestamp,
                    last_modified_on=timestamp,
                )
            )
            group_id = group_result.inserted_primary_key[0]
        else:
            connection.execute(
                groups.update().where(groups.c.group_id == group_id).values(public=True)
            )
            connection.execute(
                group_locks.delete().where(
                    group_locks.c.group_id == group_id,
                    group_locks.c.group_lock_type == "delete",
                )
            )

        member = connection.scalar(
            sa.select(group_members.c.user_id).where(
                group_members.c.user_id == user_id,
                group_members.c.group_id == group_id,
            )
        )
        member_values = {
            "read": True,
            "write": True,
            "share_read": True,
            "share_write": True,
        }
        if member is None:
            connection.execute(
                group_members.insert().values(
                    user_id=user_id,
                    group_id=group_id,
                    **member_values,
                )
            )
        else:
            connection.execute(
                group_members.update()
                .where(
                    group_members.c.user_id == user_id,
                    group_members.c.group_id == group_id,
                )
                .values(**member_values)
            )

        manager = connection.scalar(
            sa.select(group_managers.c.user_id).where(
                group_managers.c.user_id == user_id,
                group_managers.c.group_id == group_id,
            )
        )
        manager_values = {"owner": True, "admin": True}
        if manager is None:
            connection.execute(
                group_managers.insert().values(
                    user_id=user_id,
                    group_id=group_id,
                    **manager_values,
                )
            )
        else:
            connection.execute(
                group_managers.update()
                .where(
                    group_managers.c.user_id == user_id,
                    group_managers.c.group_id == group_id,
                )
                .values(**manager_values)
            )

        _ensure_builtin_parameter_types(
            connection, tables, group_id, user_id, timestamp
        )


def upgrade() -> None:
    op.add_column(
        "groups",
        sa.Column("public", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        op.f("ix_groups_user_id_name"),
        "groups",
        ["user_id", "name"],
        unique=True,
    )

    groups_table = sa.table(
        "groups",
        sa.column("group_id", sa.BigInteger()),
        sa.column("public", sa.Boolean()),
    )
    op.execute(groups_table.update().values(public=True))
    _backfill_personal_groups()


def downgrade() -> None:
    op.drop_index(op.f("ix_groups_user_id_name"), table_name="groups")
    op.drop_column("groups", "public")
