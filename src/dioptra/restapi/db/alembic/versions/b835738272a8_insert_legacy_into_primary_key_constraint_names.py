"""Insert legacy into primary key constraint names.

Revision ID: b835738272a8
Revises: 8ffe4640e009
Create Date: 2024-04-07 17:12:23.966704

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b835738272a8"
down_revision = "8ffe4640e009"
branch_labels = None
depends_on = None

POSTGRES_DIALECT = "postgresql"


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    dialect_name = op.get_context().dialect.name

    with op.batch_alter_table("legacy_experiments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_experiments_name"))

    with op.batch_alter_table("legacy_jobs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_jobs_status"))
        batch_op.drop_index(batch_op.f("ix_legacy_jobs_queue_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_jobs_mlflow_run_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_jobs_experiment_id"))
        batch_op.drop_constraint(
            batch_op.f("fk_legacy_jobs_status_legacy_job_statuses")
        )
        batch_op.drop_constraint(batch_op.f("fk_legacy_jobs_queue_id_legacy_queues"))
        batch_op.drop_constraint(
            batch_op.f("fk_legacy_jobs_experiment_id_legacy_experiments")
        )

    with op.batch_alter_table("legacy_queues", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_queues_name"))

    with op.batch_alter_table("legacy_queue_locks", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_legacy_queue_locks_queue_id_legacy_queues")
        )

    with op.batch_alter_table("legacy_experiments", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_experiments"))

        if dialect_name == POSTGRES_DIALECT:
            batch_op.execute(
                'ALTER SEQUENCE IF EXISTS "experiments_experiment_id_seq" '
                'RENAME TO "legacy_experiments_experiment_id_seq"'
            )

        batch_op.create_primary_key("pk_legacy_experiments", ["experiment_id"])

    with op.batch_alter_table("legacy_job_statuses", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_job_statuses"))
        batch_op.create_primary_key("pk_legacy_job_statuses", ["status"])

    with op.batch_alter_table("legacy_jobs", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_jobs"))
        batch_op.create_primary_key("pk_legacy_jobs", ["job_id"])

    with op.batch_alter_table("legacy_queue_locks", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_queue_locks"))
        batch_op.create_primary_key("pk_legacy_queue_locks", ["queue_id"])

    with op.batch_alter_table("legacy_queues", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_queues"))

        if dialect_name == POSTGRES_DIALECT:
            batch_op.execute(
                'ALTER SEQUENCE IF EXISTS "queues_queue_id_seq" '
                'RENAME TO "legacy_queues_queue_id_seq"'
            )

        batch_op.create_primary_key("pk_legacy_queues", ["queue_id"])

    with op.batch_alter_table("legacy_users", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_users"))

        if dialect_name == POSTGRES_DIALECT:
            batch_op.execute(
                'ALTER SEQUENCE IF EXISTS "users_user_id_seq" '
                'RENAME TO "legacy_users_user_id_seq"'
            )

        batch_op.create_primary_key("pk_legacy_users", ["user_id"])

    with op.batch_alter_table("legacy_experiments", schema=None) as batch_op:
        batch_op.create_index("ix_legacy_experiments_name", ["name"], unique=1)

    with op.batch_alter_table("legacy_jobs", schema=None) as batch_op:
        batch_op.create_index("ix_legacy_jobs_status", ["status"], unique=False)
        batch_op.create_index("ix_legacy_jobs_queue_id", ["queue_id"], unique=False)
        batch_op.create_index(
            "ix_legacy_jobs_mlflow_run_id", ["mlflow_run_id"], unique=False
        )
        batch_op.create_index(
            "ix_legacy_jobs_experiment_id", ["experiment_id"], unique=False
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_legacy_jobs_status_legacy_job_statuses"),
            "legacy_job_statuses",
            ["status"],
            ["status"],
        )
        batch_op.create_foreign_key(
            "fk_legacy_jobs_queue_id_legacy_queues",
            "legacy_queues",
            ["queue_id"],
            ["queue_id"],
        )
        batch_op.create_foreign_key(
            "fk_legacy_jobs_experiment_id_legacy_experiments",
            "legacy_experiments",
            ["experiment_id"],
            ["experiment_id"],
        )

    with op.batch_alter_table("legacy_queues", schema=None) as batch_op:
        batch_op.create_index("ix_legacy_queues_name", ["name"], unique=1)

    with op.batch_alter_table("legacy_queue_locks", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_legacy_queue_locks_queue_id_legacy_queues",
            "legacy_queues",
            ["queue_id"],
            ["queue_id"],
        )

    # Repeating this from Revision 32d5c0055e1b since it was retroactively added. Will
    # do nothing if types have already been dropped.
    if dialect_name == POSTGRES_DIALECT:
        op.execute("DROP TYPE IF EXISTS jobqueue; DROP TYPE IF EXISTS jobstatus;")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    dialect_name = op.get_context().dialect.name

    with op.batch_alter_table("legacy_experiments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_experiments_name"))

    with op.batch_alter_table("legacy_jobs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_jobs_status"))
        batch_op.drop_index(batch_op.f("ix_legacy_jobs_queue_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_jobs_mlflow_run_id"))
        batch_op.drop_index(batch_op.f("ix_legacy_jobs_experiment_id"))
        batch_op.drop_constraint(
            batch_op.f("fk_legacy_jobs_status_legacy_job_statuses")
        )
        batch_op.drop_constraint(batch_op.f("fk_legacy_jobs_queue_id_legacy_queues"))
        batch_op.drop_constraint(
            batch_op.f("fk_legacy_jobs_experiment_id_legacy_experiments")
        )

    with op.batch_alter_table("legacy_queues", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legacy_queues_name"))

    with op.batch_alter_table("legacy_queue_locks", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_legacy_queue_locks_queue_id_legacy_queues")
        )

    with op.batch_alter_table("legacy_experiments", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_legacy_experiments"))

        if dialect_name == POSTGRES_DIALECT:
            batch_op.execute(
                'ALTER SEQUENCE IF EXISTS "legacy_experiments_experiment_id_seq" '
                'RENAME TO "experiments_experiment_id_seq"'
            )

        batch_op.create_primary_key("pk_experiments", ["experiment_id"])

    with op.batch_alter_table("legacy_job_statuses", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_legacy_job_statuses"))
        batch_op.create_primary_key("pk_job_statuses", ["status"])

    with op.batch_alter_table("legacy_jobs", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_legacy_jobs"))
        batch_op.create_primary_key("pk_jobs", ["job_id"])

    with op.batch_alter_table("legacy_queue_locks", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_legacy_queue_locks"))
        batch_op.create_primary_key("pk_queue_locks", ["queue_id"])

    with op.batch_alter_table("legacy_queues", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_legacy_queues"))

        if dialect_name == POSTGRES_DIALECT:
            batch_op.execute(
                'ALTER SEQUENCE IF EXISTS "legacy_queues_queue_id_seq" '
                'RENAME TO "queues_queue_id_seq"'
            )

        batch_op.create_primary_key("pk_queues", ["queue_id"])

    with op.batch_alter_table("legacy_users", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("pk_legacy_users"))

        if dialect_name == POSTGRES_DIALECT:
            batch_op.execute(
                'ALTER SEQUENCE IF EXISTS "legacy_users_user_id_seq" '
                'RENAME TO "users_user_id_seq"'
            )

        batch_op.create_primary_key("pk_users", ["user_id"])

    with op.batch_alter_table("legacy_experiments", schema=None) as batch_op:
        batch_op.create_index("ix_legacy_experiments_name", ["name"], unique=1)

    with op.batch_alter_table("legacy_jobs", schema=None) as batch_op:
        batch_op.create_index("ix_legacy_jobs_status", ["status"], unique=False)
        batch_op.create_index("ix_legacy_jobs_queue_id", ["queue_id"], unique=False)
        batch_op.create_index(
            "ix_legacy_jobs_mlflow_run_id", ["mlflow_run_id"], unique=False
        )
        batch_op.create_index(
            "ix_legacy_jobs_experiment_id", ["experiment_id"], unique=False
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_legacy_jobs_status_legacy_job_statuses"),
            "legacy_job_statuses",
            ["status"],
            ["status"],
        )
        batch_op.create_foreign_key(
            "fk_legacy_jobs_queue_id_legacy_queues",
            "legacy_queues",
            ["queue_id"],
            ["queue_id"],
        )
        batch_op.create_foreign_key(
            "fk_legacy_jobs_experiment_id_legacy_experiments",
            "legacy_experiments",
            ["experiment_id"],
            ["experiment_id"],
        )

    with op.batch_alter_table("legacy_queues", schema=None) as batch_op:
        batch_op.create_index("ix_legacy_queues_name", ["name"], unique=1)

    with op.batch_alter_table("legacy_queue_locks", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_legacy_queue_locks_queue_id_legacy_queues",
            "legacy_queues",
            ["queue_id"],
            ["queue_id"],
        )
    # ### end Alembic commands ###
