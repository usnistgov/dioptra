"""empty message

Revision ID: 32d5c0055e1b
Revises: a278f46a1c9d
Create Date: 2020-11-18 17:45:26.337542

"""

import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import sessionmaker

try:
    from sqlalchemy.orm import declarative_base

except ImportError:
    from sqlalchemy.ext.declarative import declarative_base


# revision identifiers, used by Alembic.
revision = "32d5c0055e1b"
down_revision = "a278f46a1c9d"
branch_labels = None
depends_on = None

POSTGRES_DIALECT = "postgresql"

# Migration data models
Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    job_id = sa.Column(sa.String(36), primary_key=True)
    queue_id = sa.Column(sa.BigInteger(), sa.ForeignKey("queues.queue_id"), index=True)
    queue = sa.Column(sa.Text(), index=True)


class Queue(Base):
    __tablename__ = "queues"

    queue_id = sa.Column(
        sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True
    )
    created_on = sa.Column(sa.DateTime())
    last_modified = sa.Column(sa.DateTime())
    name = sa.Column(sa.Text(), index=True, nullable=False, unique=True)
    is_deleted = sa.Column(sa.Boolean(), default=False)


def next_queue_id(session):
    """Generate the next id in the sequence."""
    stmt = sa.select(Queue).order_by(Queue.queue_id.desc())
    queue = session.scalars(stmt).first()

    if queue is None:
        return 1

    return int(queue.queue_id) + 1


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    dialect_name = op.get_context().dialect.name

    job_statuses = op.create_table(
        "job_statuses",
        sa.Column("status", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("status", name=op.f("pk_job_statuses")),
    )

    op.bulk_insert(
        job_statuses,
        [
            {"status": "queued"},
            {"status": "started"},
            {"status": "deferred"},
            {"status": "finished"},
            {"status": "failed"},
        ],
    )

    op.create_table(
        "queues",
        sa.Column(
            "queue_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            nullable=False,
        ),
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.Column("last_modified", sa.DateTime(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("queue_id", name=op.f("pk_queues")),
    )

    with op.batch_alter_table("queues", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_queues_name"), ["name"], unique=True)

    op.create_table(
        "queue_locks",
        sa.Column(
            "queue_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            nullable=False,
        ),
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["queue_id"],
            ["queues.queue_id"],
            name=op.f("fk_queue_locks_queue_id_queues"),
        ),
        sa.PrimaryKeyConstraint("queue_id", name=op.f("pk_queue_locks")),
    )

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("queue_id", sa.BigInteger(), nullable=True))
        batch_op.alter_column(
            "status",
            type_=sa.String(length=255),
            existing_type_=sa.Enum(
                "queued",
                "started",
                "deferred",
                "finished",
                "failed",
                name="jobstatus",
            ),
        )
        batch_op.create_index(
            batch_op.f("ix_jobs_queue_id"), ["queue_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_jobs_status"), ["status"], unique=False)
        batch_op.create_foreign_key(
            batch_op.f("fk_jobs_status_job_statuses"),
            "job_statuses",
            ["status"],
            ["status"],
        )
        batch_op.drop_index("ix_jobs_queue")
        batch_op.alter_column(
            "queue",
            type_=sa.String(length=255),
            existing_type_=sa.Enum(
                "tensorflow_cpu",
                "tensorflow_gpu",
                name="jobstatus",
            ),
        )

    with Session() as session:
        queue_name_id_dict = {}
        stmt = sa.select(Job)

        for job in session.scalars(stmt):
            if job.queue is not None and job.queue not in queue_name_id_dict:
                new_queue_id = next_queue_id(session)
                timestamp = datetime.datetime.now()

                new_queue = Queue(
                    queue_id=new_queue_id,
                    name=job.queue,
                    created_on=timestamp,
                    last_modified=timestamp,
                )
                session.add(new_queue)

                queue_name_id_dict[job.queue] = new_queue_id

            job.queue_id = queue_name_id_dict.get(job.queue)

        session.commit()

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.create_foreign_key(
            batch_op.f("fk_jobs_queue_id_queues"), "queues", ["queue_id"], ["queue_id"]
        )
        batch_op.drop_column("queue")

    if dialect_name == POSTGRES_DIALECT:
        op.execute("DROP TYPE IF EXISTS jobqueue; DROP TYPE IF EXISTS jobstatus;")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    dialect_name = op.get_context().dialect.name

    # Repeating this from the upgrade function since it was retroactively added. Will do
    # nothing if types have already been dropped.
    if dialect_name == POSTGRES_DIALECT:
        op.execute("DROP TYPE IF EXISTS jobqueue; DROP TYPE IF EXISTS jobstatus;")

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        if dialect_name == POSTGRES_DIALECT:
            op.execute(
                "CREATE TYPE jobqueue AS ENUM('tensorflow_cpu', 'tensorflow_gpu');"
            )

        batch_op.add_column(
            sa.Column(
                "queue",
                sa.Enum("tensorflow_cpu", "tensorflow_gpu", name="jobqueue"),
                nullable=True,
            ),
        )
        batch_op.drop_constraint(
            batch_op.f("fk_jobs_queue_id_queues"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_jobs_status_job_statuses"), type_="foreignkey"
        )

    with Session() as session:
        downgraded_queue_names_set = {"tensorflow_cpu", "tensorflow_gpu"}
        stmt = sa.select(Queue.name, Job).join(Queue, Job.queue_id == Queue.queue_id)

        for queue_name, job in session.execute(stmt):
            job.queue = queue_name if queue_name in downgraded_queue_names_set else None

        session.commit()

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.create_index("ix_jobs_queue", ["queue"], unique=False)
        batch_op.drop_index(batch_op.f("ix_jobs_status"))
        batch_op.drop_index(batch_op.f("ix_jobs_queue_id"))

        if dialect_name == POSTGRES_DIALECT:
            op.execute(
                "CREATE TYPE jobstatus AS "
                "ENUM('queued', 'started', 'deferred', 'finished', 'failed'); "
                "ALTER TABLE jobs "
                "ALTER COLUMN status TYPE jobstatus "
                "USING status::text::jobstatus;"
            )

        else:
            batch_op.alter_column(
                "status",
                type_=sa.Enum(
                    "queued",
                    "started",
                    "deferred",
                    "finished",
                    "failed",
                    name="jobstatus",
                ),
                existing_type=sa.String(length=255),
            )

        batch_op.drop_column("queue_id")

    op.drop_table("queue_locks")
    with op.batch_alter_table("queues", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_queues_name"))

    op.drop_table("queues")
    op.drop_table("job_statuses")
    # ### end Alembic commands ###
