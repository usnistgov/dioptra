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
"""Reset a stopped development job using the Dioptra database and MLflow."""

from datetime import datetime, timezone
from uuid import UUID

import click
from mlflow import MlflowClient
from sqlalchemy import Uuid, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """Local mappings for the existing development database."""


class ResourceLock(Base):
    __tablename__ = "resource_locks"

    resource_id: Mapped[int] = mapped_column(primary_key=True)
    resource_lock_type: Mapped[str] = mapped_column(primary_key=True)


class ResourceSnapshot(Base):
    __tablename__ = "resource_snapshots"

    resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[int]
    resource_type: Mapped[str]
    user_id: Mapped[int]
    description: Mapped[str | None]
    created_on: Mapped[datetime]


class Job(Base):
    __tablename__ = "jobs"

    resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[int]
    timeout: Mapped[str]
    status: Mapped[str]


class JobMlflowRun(Base):
    __tablename__ = "job_mlflow_runs"

    job_resource_id: Mapped[int] = mapped_column(primary_key=True)
    mlflow_run_id: Mapped[UUID] = mapped_column(Uuid)


def reset_job(session: Session, client: MlflowClient, job_id: int) -> UUID:
    """Append a queued snapshot and replace the job's MLflow run in one commit.

    Args:
        session: Dedicated session with write access to the development database.
        client: Client for the same MLflow tracking server as the API and worker.
        job_id: Resource ID of a job whose execution has stopped.

    Returns:
        The newly assigned MLflow run ID.

    Raises:
        click.ClickException: The job is unavailable or the database commit
            could not be confirmed.
    """
    deleted = select(ResourceLock).where(
        ResourceLock.resource_id == job_id, ResourceLock.resource_lock_type == "delete"
    )
    current = session.execute(
        select(ResourceSnapshot, Job)
        .join(Job, Job.resource_snapshot_id == ResourceSnapshot.resource_snapshot_id)
        .where(Job.resource_id == job_id, ~deleted.exists())
        .order_by(ResourceSnapshot.created_on.desc())
        .limit(1)
    ).first()
    if current is None:
        raise click.ClickException(f"Job {job_id} does not exist or has been deleted.")

    previous, job = current
    run_id = UUID(client.create_run(experiment_id="0").info.run_id)
    try:
        queued = ResourceSnapshot(
            resource_id=job_id,
            resource_type="job",
            user_id=previous.user_id,
            description=previous.description,
            created_on=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(queued)
        session.flush()
        session.add(
            Job(
                resource_snapshot_id=queued.resource_snapshot_id,
                resource_id=job_id,
                timeout=job.timeout,
                status="queued",
            )
        )
        session.merge(JobMlflowRun(job_resource_id=job_id, mlflow_run_id=run_id))
        session.flush()
    except Exception:
        session.rollback()
        client.delete_run(run_id.hex)
        raise

    try:
        session.commit()
    except Exception as error:
        raise click.ClickException(
            f"Could not confirm the reset of job {job_id}. Check its status and run "
            f"ID before retrying. The replacement run is {run_id}."
        ) from error
    return run_id


@click.command()
@click.argument("job_id", type=int)
@click.option(
    "--database-uri",
    envvar="DIOPTRA_RESTAPI_DATABASE_URI",
    required=True,
    show_envvar=True,
    help="SQLAlchemy URI of the development database.",
)
@click.option(
    "--tracking-uri",
    envvar="MLFLOW_TRACKING_URI",
    required=True,
    show_envvar=True,
    help="MLflow tracking URI used by the API and worker.",
)
def main(job_id: int, database_uri: str, tracking_uri: str) -> None:
    """Reset JOB_ID for a manual rerun and print its replacement MLflow run ID.

    \f
    Args:
        job_id: Resource ID of a stopped development job.
        database_uri: Connection URI for the development database.
        tracking_uri: URI of the development MLflow tracking server.
    """
    engine = create_engine(database_uri)
    with Session(engine) as session:
        if engine.dialect.name == "sqlite":
            session.execute(text("PRAGMA foreign_keys = ON"))
        run_id = reset_job(session, MlflowClient(tracking_uri=tracking_uri), job_id)
    click.echo(str(run_id))


if __name__ == "__main__":
    main()
