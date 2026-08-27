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
import datetime

import pytest
from sqlalchemy.orm.session import Session as DBSession

import dioptra.restapi.db.models as models
import dioptra.restapi.db.repository.utils as utils
import dioptra.restapi.errors as errors
from dioptra.restapi.db.models.constants import (
    group_lock_types,
    resource_lock_types,
    user_lock_types,
)
from dioptra.restapi.v1.jobs.schema import JobLogSeverity
from dioptra.restapi.v1.shared.search_parser import parse_search_text


def make_job(
    creator,
    group,
    experiment,
    entry_point,
    queue,
    timeout="24h",
    status="queued",
    description="",
):
    """Create a basic Job with required relationships."""
    job_resource = models.Resource("job", group)
    entry_point_parameter_values = [
        models.EntryPointParameterValue(
            value="test_value",
            job_resource=job_resource,
            parameter=entry_point.parameters[0] if entry_point.parameters else None,
        ),
    ]
    job = models.Job(
        timeout=timeout,
        status=status,
        description=description,
        resource=job_resource,
        creator=creator,
    )
    job.entry_point_job = models.EntryPointJob(
        job_resource=job_resource,
        entry_point=entry_point,
        entry_point_parameter_values=entry_point_parameter_values,
        entry_point_artifact_parameter_values=[],
    )
    job.experiment_job = models.ExperimentJob(
        job_resource=job_resource,
        experiment=experiment,
    )
    job.queue_job = models.QueueJob(
        job_resource=job_resource,
        queue=queue,
    )
    return job


def make_job_snapshot(source_job, hours_offset=1, new_status=None):
    """Create a new Job snapshot based on an existing job.

    Args:
        source_job: The source Job to create snapshot from
        hours_offset: Hours to add to source_job's created_on timestamp
        new_status: Optional new status for the snapshot. If None, uses source_job's status.
    """
    job_resource = source_job.resource
    status = new_status if new_status is not None else source_job.status
    job = models.Job(
        timeout=source_job.timeout,
        status=status,
        description=source_job.description,
        resource=job_resource,
        creator=source_job.creator,
    )
    job.created_on = source_job.created_on + datetime.timedelta(hours=hours_offset)
    return job


@pytest.fixture
def experiment_with_dependencies(db_session, account, fake_data):
    """Create an experiment with entrypoint and queue dependencies."""
    experiment = fake_data.experiment(account.user, account.group)
    db_session.add(experiment)
    db_session.commit()

    str_param_type = fake_data.plugin_task_parameter_type(
        account.user, account.group, name="string"
    )
    db_session.add(str_param_type)
    db_session.commit()

    fake_plugin = fake_data.plugin(account.user, account.group, str_param_type)
    db_session.add(fake_plugin.plugin)
    db_session.add(fake_plugin.plugin_file)
    db_session.add(fake_plugin.init_plugin_file)
    db_session.commit()

    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    entry_point = fake_data.entry_point(account.user, account.group, queue)
    db_session.add(entry_point)
    db_session.commit()

    experiment.resource.children.append(entry_point.resource)
    db_session.commit()

    return experiment, entry_point, queue


class TestJobCreate:
    """Tests for JobRepository.create()"""

    def test_job_create_success(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )

        job_repo.create(job)
        db_session.commit()

        result = job_repo.get_one(job.resource_id, utils.DeletionPolicy.NOT_DELETED)
        assert result == job

    def test_job_create_exists(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        with pytest.raises(errors.EntityExistsError):
            job_repo.create(job)

    def test_job_create_exists_deleted(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, job.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            job_repo.create(job)

    def test_job_create_user_not_exist(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job.creator = models.User("user2", "pass2", "user2@example.org")

        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.create(job)

    def test_job_create_user_deleted(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )

        lock = models.UserLock(user_lock_types.DELETE, account.user)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            job_repo.create(job)

    def test_job_create_group_not_exist(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )

        user2 = models.User("user2", "pass2", "user2@example.org")
        group2 = models.Group("group2", user2)
        job.resource.owner = group2

        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.create(job)

    def test_job_create_group_deleted(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )

        lock = models.GroupLock(group_lock_types.DELETE, account.group)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            job_repo.create(job)

    def test_job_create_user_not_member(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )

        user2 = models.User("user2", "pass2", "user2@example.org")
        group2 = models.Group("group2", user2)
        db_session.add(group2)
        db_session.commit()

        job.resource.owner = group2
        with pytest.raises(errors.UserNotInGroupError):
            job_repo.create(job)

    def test_job_create_with_experiment(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test_description",
        )
        job_repo.create(job1)
        db_session.commit()

        result = job_repo.get_by_filters_paged(
            group=account.group,
            experiment=experiment,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert result[1] == 1

    def test_job_create_name_reuse(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job1)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, job1.resource)
        db_session.add(lock)
        db_session.commit()

        job2 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job2)
        db_session.commit()

        check_job = db_session.get(models.Job, job2.resource_snapshot_id)
        assert check_job == job2

    def test_job_create_wrong_resource_type(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job.resource_type = "queue"

        with pytest.raises(errors.MismatchedResourceTypeError):
            job_repo.create(job)

        job.resource_type = "job"
        job.resource.resource_type = "queue"

        with pytest.raises(errors.MismatchedResourceTypeError):
            job_repo.create(job)


class TestJobStatusTransition:
    """Tests for job status transitions (which create new snapshots).

    Status transition validation (JOB_STATUS_TRANSITIONS) is enforced by the
    repository. These tests verify direct snapshot creation and the higher-level
    set_status helper.
    """

    def test_job_status_transition_queued_to_started(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        """Creating snapshot with new status should work."""
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="queued",
        )
        job_repo.create(job1)
        db_session.commit()

        job2 = make_job_snapshot(job1, new_status="started")

        job_repo.create_snapshot(job2)
        db_session.commit()

        check_resource = db_session.get(models.Resource, job2.resource_id)
        assert check_resource is not None
        assert len(check_resource.versions) == 2

    def test_job_status_transition_started_to_finished(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        """Creating snapshot with different status should work."""
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="started",
        )
        job_repo.create(job1)
        db_session.commit()

        job2 = make_job_snapshot(job1, new_status="finished")

        job_repo.create_snapshot(job2)
        db_session.commit()

        check_resource = db_session.get(models.Resource, job2.resource_id)
        assert len(check_resource.versions) == 2

    def test_job_status_transition_same_status(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        """Creating snapshot with same status is allowed (creates new version)."""
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="queued",
        )
        job_repo.create(job1)
        db_session.commit()

        job2 = make_job_snapshot(job1, new_status="queued")

        job_repo.create_snapshot(job2)
        db_session.commit()

        check_resource = db_session.get(models.Resource, job2.resource_id)
        assert len(check_resource.versions) == 2

    def test_job_status_transition_resource_deleted(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        """Cannot create snapshot for deleted job."""
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="started",
        )
        lock = models.ResourceLock(resource_lock_types.DELETE, job.resource)
        db_session.add_all((job, lock))
        db_session.commit()

        job_snapshot = make_job_snapshot(job, new_status="finished")

        with pytest.raises(errors.EntityDeletedError):
            job_repo.create_snapshot(job_snapshot)

    def test_job_status_transition_snapshot_not_exist(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        """Cannot create snapshot for non-existent job."""
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="started",
        )

        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.create_snapshot(job)

    def test_job_set_status_queued_to_started(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="queued",
        )
        job_repo.create(job)
        db_session.commit()

        new_job = job_repo.set_status(
            job.resource_id,
            "started",
            utils.DeletionPolicy.NOT_DELETED,
            experiment.resource_id,
        )
        db_session.commit()

        assert new_job.status == "started"
        assert new_job.resource_id == job.resource_id
        assert (
            job_repo.get_one(job.resource_id, utils.DeletionPolicy.NOT_DELETED)
            == new_job
        )
        assert len(job.resource.versions) == 2

    def test_job_set_status_invalid_transition(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="queued",
        )
        job_repo.create(job)
        db_session.commit()

        with pytest.raises(errors.JobInvalidStatusTransitionError):
            job_repo.set_status(
                job.resource_id,
                "finished",
                utils.DeletionPolicy.NOT_DELETED,
                experiment.resource_id,
            )

    def test_job_set_status_experiment_mismatch(
        self,
        db_session: DBSession,
        account,
        fake_data,
        job_repo,
        experiment_with_dependencies,
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        other_experiment = fake_data.experiment(account.user, account.group)
        db_session.add(other_experiment)
        db_session.commit()
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="queued",
        )
        job_repo.create(job)
        db_session.commit()

        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.set_status(
                job.resource_id,
                "started",
                utils.DeletionPolicy.NOT_DELETED,
                other_experiment.resource_id,
            )

    def test_job_set_status_reset_clears_mlflow_run(
        self,
        db_session: DBSession,
        account,
        fake_data,
        job_repo,
        experiment_with_dependencies,
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="started",
        )
        job_repo.create(job)
        db_session.commit()
        db_session.add(fake_data.job_mlflow_run(job))
        db_session.commit()

        new_job = job_repo.set_status(
            job.resource_id,
            "reset",
            utils.DeletionPolicy.NOT_DELETED,
            experiment.resource_id,
        )
        db_session.commit()

        assert new_job.status == "queued"
        assert len(job.resource.versions) == 2
        latest_job = job_repo.get_one(job.resource_id, utils.DeletionPolicy.NOT_DELETED)
        assert latest_job.status == "queued"
        assert latest_job.mlflow_run is None


class TestJobGet:
    """Tests for JobRepository.get()"""

    def test_job_get_single_exists(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )
        job_repo.create(job)
        db_session.commit()

        result = job_repo.get(job.resource_id, utils.DeletionPolicy.NOT_DELETED)
        assert result == job

    def test_job_get_single_not_exists(self, db_session: DBSession, job_repo):
        result = job_repo.get(99999, utils.DeletionPolicy.NOT_DELETED)
        assert result is None

    def test_job_get_single_deleted(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )
        job_repo.create(job)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, job.resource)
        db_session.add(lock)
        db_session.commit()

        result = job_repo.get(job.resource_id, utils.DeletionPolicy.NOT_DELETED)
        assert result is None

    def test_job_get_multiple(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job 1",
        )
        job2 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job 2",
        )
        job_repo.create(job1)
        job_repo.create(job2)
        db_session.commit()

        result = job_repo.get(
            [job1.resource_id, job2.resource_id], utils.DeletionPolicy.NOT_DELETED
        )
        assert len(result) == 2
        assert job1 in result
        assert job2 in result


class TestJobGetOne:
    """Tests for JobRepository.get_one()"""

    def test_job_get_one_exists(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )
        job_repo.create(job)
        db_session.commit()

        result = job_repo.get_one(job.resource_id, utils.DeletionPolicy.NOT_DELETED)
        assert result == job

    def test_job_get_one_not_exists(self, db_session: DBSession, job_repo):
        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.get_one(99999, utils.DeletionPolicy.NOT_DELETED)

    def test_job_get_one_deleted(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )
        job_repo.create(job)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, job.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            job_repo.get_one(job.resource_id, utils.DeletionPolicy.NOT_DELETED)

    def test_job_get_one_with_experiment_id(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )
        job_repo.create(job)
        db_session.commit()

        result = job_repo.get_one(
            job.resource_id,
            utils.DeletionPolicy.NOT_DELETED,
            experiment_id=experiment.resource_id,
        )
        assert result == job

    def test_job_get_one_with_wrong_experiment_id(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )
        job_repo.create(job)
        db_session.commit()

        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.get_one(
                job.resource_id,
                utils.DeletionPolicy.NOT_DELETED,
                experiment_id=99999,
            )


class TestJobDelete:
    """Tests for JobRepository.delete()"""

    def test_job_delete_exists(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )
        job_repo.create(job)
        db_session.commit()

        job_repo.delete(job)
        db_session.commit()

        assert job.resource.is_deleted is True

    def test_job_delete_not_exists(self, db_session: DBSession, job_repo):
        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.delete(99999)

    def test_job_delete_wrong_resource_type(
        self, db_session: DBSession, account, fake_data, job_repo
    ):
        queue = fake_data.queue(account.user, account.group)
        db_session.add(queue)
        db_session.commit()

        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.delete(queue.resource_id)

        assert queue.resource.is_deleted is False

    def test_job_delete_already_deleted(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job",
        )
        job_repo.create(job)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, job.resource)
        db_session.add(lock)
        db_session.commit()

        job_repo.delete(job)


class TestJobGetByFiltersPaged:
    """Tests for JobRepository.get_by_filters_paged()"""

    def test_job_get_by_filters_paged_empty(self, db_session: DBSession, job_repo):
        result, count = job_repo.get_by_filters_paged(
            group=None,
            experiment=None,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 0
        assert len(result) == 0

    def test_job_get_by_filters_paged_with_results(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job 1",
        )
        job2 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="test job 2",
        )
        job_repo.create(job1)
        job_repo.create(job2)
        db_session.commit()

        result, count = job_repo.get_by_filters_paged(
            group=account.group,
            experiment=None,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 2
        assert len(result) == 2

    def test_job_get_by_filters_paged_with_filters(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="queued",
        )
        job2 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            status="started",
        )
        job_repo.create(job1)
        job_repo.create(job2)
        db_session.commit()

        result, count = job_repo.get_by_filters_paged(
            group=account.group,
            experiment=experiment,
            filters=parse_search_text("status:started"),
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 1
        assert result == [job2]

    def test_job_get_by_filters_paged_with_sort(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job1 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="aaa_job",
        )
        job2 = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
            description="zzz_job",
        )
        job_repo.create(job1)
        job_repo.create(job2)
        db_session.commit()

        result, count = job_repo.get_by_filters_paged(
            group=account.group,
            experiment=None,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by="description",
            descending=True,
        )
        assert count == 2
        assert result[0] == job2
        assert result[1] == job1

    @pytest.mark.parametrize(
        ("sort_by", "expected_order"),
        [
            ("experiment", ["aaa_experiment", "zzz_experiment"]),
            ("entrypoint", ["aaa_entrypoint", "zzz_entrypoint"]),
            ("queue", ["aaa_queue", "zzz_queue"]),
        ],
    )
    def test_job_get_by_filters_paged_with_related_resource_sort(
        self,
        db_session: DBSession,
        account,
        job_repo,
        fake_data,
        sort_by,
        expected_order,
    ):
        str_param_type = fake_data.plugin_task_parameter_type(
            account.user, account.group, name="string"
        )
        db_session.add(str_param_type)
        db_session.commit()

        fake_plugin = fake_data.plugin(account.user, account.group, str_param_type)
        db_session.add(fake_plugin.plugin)
        db_session.add(fake_plugin.plugin_file)
        db_session.add(fake_plugin.init_plugin_file)
        db_session.commit()

        queue_a = fake_data.queue(account.user, account.group)
        queue_z = fake_data.queue(account.user, account.group)
        queue_a.name = "aaa_queue"
        queue_z.name = "zzz_queue"
        db_session.add(queue_a)
        db_session.add(queue_z)
        db_session.commit()

        entry_point_a = fake_data.entry_point(account.user, account.group, queue_a)
        entry_point_z = fake_data.entry_point(account.user, account.group, queue_z)
        entry_point_a.name = "aaa_entrypoint"
        entry_point_z.name = "zzz_entrypoint"
        db_session.add(entry_point_a)
        db_session.add(entry_point_z)
        db_session.commit()

        experiment_a = fake_data.experiment(account.user, account.group)
        experiment_z = fake_data.experiment(account.user, account.group)
        experiment_a.name = "aaa_experiment"
        experiment_z.name = "zzz_experiment"
        db_session.add(experiment_a)
        db_session.add(experiment_z)
        db_session.commit()

        experiment_a.resource.children.append(entry_point_a.resource)
        experiment_z.resource.children.append(entry_point_z.resource)
        db_session.commit()

        job_a = make_job(
            account.user,
            account.group,
            experiment_a,
            entry_point_a,
            queue_a,
        )
        job_z = make_job(
            account.user,
            account.group,
            experiment_z,
            entry_point_z,
            queue_z,
        )
        job_repo.create(job_z)
        job_repo.create(job_a)
        db_session.commit()

        result, count = job_repo.get_by_filters_paged(
            group=account.group,
            experiment=None,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by=sort_by,
            descending=False,
        )

        actual_order = [
            {
                "experiment": job.experiment_job.experiment.name,
                "entrypoint": job.entry_point_job.entry_point.name,
                "queue": job.queue_job.queue.name,
            }[sort_by]
            for job in result
        ]
        assert count == 2
        assert actual_order == expected_order

    def test_job_get_by_filters_paged_with_pagination(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        for i in range(5):
            job = make_job(
                account.user,
                account.group,
                experiment,
                entry_point,
                queue,
                description=f"description{i}",
            )
            job_repo.create(job)
        db_session.commit()

        result, count = job_repo.get_by_filters_paged(
            group=account.group,
            experiment=None,
            filters=[],
            page_start=0,
            page_length=2,
            sort_by="description",
            descending=False,
        )
        assert count == 5
        assert len(result) == 2

    def test_job_get_by_filters_paged_with_invalid_sort(
        self, db_session: DBSession, job_repo
    ):
        with pytest.raises(errors.SortParameterValidationError):
            job_repo.get_by_filters_paged(
                group=None,
                experiment=None,
                filters=[],
                page_start=0,
                page_length=10,
                sort_by="invalid_field",
                descending=False,
            )

    def test_job_get_by_filters_paged_with_unlimited_length(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        for i in range(15):
            job = make_job(
                account.user,
                account.group,
                experiment,
                entry_point,
                queue,
                description=f"description{i}",
            )
            job_repo.create(job)
        db_session.commit()

        result, count = job_repo.get_by_filters_paged(
            group=account.group,
            experiment=None,
            filters=[],
            page_start=0,
            page_length=0,
            sort_by="description",
            descending=False,
        )
        assert count == 15
        assert len(result) == 15


class TestJobAssertResourcesRegistered:
    """Tests for JobRepository.assert_resources_registered()"""

    def test_assert_resources_registered_success(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies

        job_repo.assert_resources_registered(
            entry_point.resource_id,
            experiment.resource_id,
            queue.resource_id,
        )

    def test_assert_resources_registered_entrypoint_not_registered(
        self,
        db_session: DBSession,
        account,
        job_repo,
        experiment_with_dependencies,
        fake_data,
    ):
        experiment, entry_point, queue = experiment_with_dependencies

        str_param_type = fake_data.plugin_task_parameter_type(
            account.user, account.group, name="string2"
        )
        db_session.add(str_param_type)
        db_session.commit()

        fake_plugin2 = fake_data.plugin(account.user, account.group, str_param_type)
        db_session.add(fake_plugin2.plugin)
        db_session.add(fake_plugin2.plugin_file)
        db_session.add(fake_plugin2.init_plugin_file)
        db_session.commit()

        queue2 = fake_data.queue(account.user, account.group)
        db_session.add(queue2)
        db_session.commit()

        entry_point2 = fake_data.entry_point(account.user, account.group, queue2)
        db_session.add(entry_point2)
        db_session.commit()

        with pytest.raises(errors.EntityNotRegisteredError):
            job_repo.assert_resources_registered(
                entry_point2.resource_id,
                experiment.resource_id,
                queue.resource_id,
            )

    def test_assert_resources_registered_queue_not_registered(
        self,
        db_session: DBSession,
        account,
        job_repo,
        experiment_with_dependencies,
        fake_data,
    ):
        experiment, entry_point, queue = experiment_with_dependencies

        queue2 = fake_data.queue(account.user, account.group)
        db_session.add(queue2)
        db_session.commit()

        with pytest.raises(errors.EntityNotRegisteredError):
            job_repo.assert_resources_registered(
                entry_point.resource_id,
                experiment.resource_id,
                queue2.resource_id,
            )

    def test_assert_resources_registered_queue_registered_to_other_entrypoint(
        self,
        db_session: DBSession,
        account,
        job_repo,
        experiment_with_dependencies,
        fake_data,
    ):
        experiment, entry_point, queue = experiment_with_dependencies

        queue2 = fake_data.queue(account.user, account.group)
        db_session.add(queue2)
        db_session.commit()

        entry_point2 = fake_data.entry_point(account.user, account.group, queue2)
        db_session.add(entry_point2)
        db_session.commit()

        experiment.resource.children.append(entry_point2.resource)
        db_session.commit()

        with pytest.raises(errors.EntityNotRegisteredError):
            job_repo.assert_resources_registered(
                entry_point.resource_id,
                experiment.resource_id,
                queue2.resource_id,
            )


class TestJobMetrics:
    """Tests for JobRepository metrics methods"""

    def test_add_metric(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        metric = models.JobMetric(
            name="accuracy",
            value=0.95,
            special_value=None,
            step=1,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            job_resource=job.resource,
        )
        job_repo.add_metric(metric)
        db_session.commit()

        result = job_repo.get_latest_metrics(job.resource_id)
        assert len(result) == 1
        assert result[0].name == "accuracy"

    def test_get_latest_metrics(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        metric1 = models.JobMetric(
            name="accuracy",
            value=0.95,
            special_value=None,
            step=1,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            job_resource=job.resource,
        )
        metric2 = models.JobMetric(
            name="accuracy",
            value=0.96,
            special_value=None,
            step=2,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            job_resource=job.resource,
        )
        db_session.add_all((metric1, metric2))
        db_session.commit()

        result = job_repo.get_latest_metrics(job.resource_id)
        assert len(result) == 1
        assert result[0].step == 2

    def test_get_metric_step(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        metric = models.JobMetric(
            name="accuracy",
            value=0.95,
            special_value=None,
            step=1,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            job_resource=job.resource,
        )
        db_session.add(metric)
        db_session.commit()

        result = job_repo.get_metric_step(job.resource_id, "accuracy", 1)
        assert result is not None
        assert result.value == 0.95

    def test_get_metric_step_not_found(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        result = job_repo.get_metric_step(job.resource_id, "accuracy", 999)
        assert result is None

    def test_get_metric_history(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        base_time = datetime.datetime.now(tz=datetime.timezone.utc)
        metric1 = models.JobMetric(
            name="accuracy",
            value=0.95,
            special_value=None,
            step=3,
            timestamp=base_time + datetime.timedelta(minutes=1),
            job_resource=job.resource,
        )
        metric2 = models.JobMetric(
            name="accuracy",
            value=0.96,
            special_value=None,
            step=2,
            timestamp=base_time,
            job_resource=job.resource,
        )
        metric3 = models.JobMetric(
            name="loss",
            value=0.1,
            special_value=None,
            step=1,
            timestamp=base_time,
            job_resource=job.resource,
        )
        metric4 = models.JobMetric(
            name="accuracy",
            value=0.94,
            special_value=None,
            step=1,
            timestamp=base_time,
            job_resource=job.resource,
        )
        db_session.add_all((metric1, metric2, metric3, metric4))
        db_session.commit()

        result = job_repo.get_metric_history(job.resource_id, "accuracy")
        assert result == [metric4, metric2, metric1]

    def test_metric_reads_reject_non_job_resource(
        self, db_session: DBSession, account, fake_data, job_repo
    ):
        queue = fake_data.queue(account.user, account.group)
        db_session.add(queue)
        db_session.commit()
        queue_id = queue.resource_id

        metric_reads = (
            lambda: job_repo.get_latest_metrics(queue_id),
            lambda: job_repo.get_metric_step(queue_id, "accuracy", 1),
            lambda: job_repo.get_metric_history(queue_id, "accuracy"),
            lambda: job_repo.get_metric_history_paged(queue_id, "accuracy", 0, 10),
        )

        for metric_read in metric_reads:
            with pytest.raises(errors.EntityDoesNotExistError):
                metric_read()


class TestJobLogs:
    """Tests for JobRepository log methods"""

    def test_add_logs(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        records = [
            {
                "severity": JobLogSeverity.INFO,
                "logger_name": "test_logger",
                "message": "Test message 1",
            },
            {
                "severity": JobLogSeverity.ERROR,
                "logger_name": "test_logger",
                "message": "Test message 2",
            },
        ]
        result = job_repo.add_logs(job.resource_id, records)
        db_session.commit()

        assert len(result) == 2

    def test_get_logs(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        records = [
            {
                "severity": JobLogSeverity.INFO,
                "logger_name": "test_logger",
                "message": "Test message 1",
            },
            {
                "severity": JobLogSeverity.ERROR,
                "logger_name": "test_logger",
                "message": "Test message 2",
            },
        ]
        job_repo.add_logs(job.resource_id, records)
        db_session.commit()

        result, count = job_repo.get_logs(
            job_id=job.resource_id,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 2
        assert len(result) == 2

    def test_get_logs_rejects_non_job_resource(
        self, db_session: DBSession, account, fake_data, job_repo
    ):
        queue = fake_data.queue(account.user, account.group)
        db_session.add(queue)
        db_session.commit()

        with pytest.raises(errors.EntityDoesNotExistError):
            job_repo.get_logs(
                job_id=queue.resource_id,
                filters=[],
                page_start=0,
                page_length=10,
                sort_by=None,
                descending=False,
            )

    def test_get_logs_with_severity_filter(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        records = [
            {
                "severity": JobLogSeverity.INFO,
                "logger_name": "test_logger",
                "message": "Test message 1",
            },
            {
                "severity": JobLogSeverity.ERROR,
                "logger_name": "test_logger",
                "message": "Test message 2",
            },
        ]
        job_repo.add_logs(job.resource_id, records)
        db_session.commit()

        result, count = job_repo.get_logs(
            job_id=job.resource_id,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
            severity=["INFO"],
        )
        assert count == 1
        assert result[0]["message"] == "Test message 1"

    def test_get_logs_with_search_filter(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        records = [
            {
                "severity": JobLogSeverity.INFO,
                "logger_name": "training_logger",
                "message": "Training started",
            },
            {
                "severity": JobLogSeverity.INFO,
                "logger_name": "evaluation_logger",
                "message": "Evaluation complete",
            },
        ]
        job_repo.add_logs(job.resource_id, records)
        db_session.commit()

        result, count = job_repo.get_logs(
            job_id=job.resource_id,
            filters=parse_search_text("message:*Training*"),
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 1
        assert result[0]["message"] == "Training started"

    def test_get_logs_with_pagination(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        records = [
            {
                "severity": JobLogSeverity.INFO,
                "logger_name": "test_logger",
                "message": f"Test message {i}",
            }
            for i in range(5)
        ]
        job_repo.add_logs(job.resource_id, records)
        db_session.commit()

        result, count = job_repo.get_logs(
            job_id=job.resource_id,
            filters=[],
            page_start=0,
            page_length=2,
            sort_by=None,
            descending=False,
        )
        assert count == 5
        assert len(result) == 2

    def test_get_logs_with_sort(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        records = [
            {
                "severity": JobLogSeverity.INFO,
                "logger_name": "aaa_logger",
                "message": "Test message 1",
            },
            {
                "severity": JobLogSeverity.ERROR,
                "logger_name": "zzz_logger",
                "message": "Test message 2",
            },
        ]
        job_repo.add_logs(job.resource_id, records)
        db_session.commit()

        result, count = job_repo.get_logs(
            job_id=job.resource_id,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by="logger_name",
            descending=False,
        )
        assert count == 2
        assert len(result) == 2
        assert [record["logger_name"] for record in result] == [
            "aaa_logger",
            "zzz_logger",
        ]

    def test_get_logs_invalid_sort(
        self, db_session: DBSession, account, job_repo, experiment_with_dependencies
    ):
        experiment, entry_point, queue = experiment_with_dependencies
        job = make_job(
            account.user,
            account.group,
            experiment,
            entry_point,
            queue,
        )
        job_repo.create(job)
        db_session.commit()

        with pytest.raises(errors.SortParameterValidationError):
            job_repo.get_logs(
                job_id=job.resource_id,
                filters=[],
                page_start=0,
                page_length=10,
                sort_by="invalid_field",
                descending=False,
            )
