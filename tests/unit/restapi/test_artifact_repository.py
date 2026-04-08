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
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.db.models.plugins import (
    ArtifactTask,
    PluginTask,
    PluginTaskOutputParameter,
    PluginTaskParameterType,
)


def make_artifact(
    creator,
    group,
    job,
    uri="s3://test-bucket/test-artifact",
    is_dir=False,
    file_size=None,
    description="",
):
    """Create a basic Artifact."""
    artifact_resource = models.Resource("artifact", group)
    artifact = models.Artifact(
        uri=uri,
        is_dir=is_dir,
        file_size=file_size,
        description=description,
        resource=artifact_resource,
        creator=creator,
    )
    job.children.append(artifact_resource)
    return artifact


def make_artifact_snapshot(source_artifact, hours_offset=1):
    """Create a new Artifact snapshot based on an existing artifact.

    Args:
        source_artifact: The source Artifact to create snapshot from
        hours_offset: Hours to add to source_artifact's created_on timestamp
    """
    artifact_resource = source_artifact.resource
    artifact = models.Artifact(
        uri=source_artifact.uri,
        is_dir=source_artifact.is_dir,
        file_size=source_artifact.file_size,
        description=source_artifact.description,
        resource=artifact_resource,
        creator=source_artifact.creator,
    )
    artifact.created_on = source_artifact.created_on + datetime.timedelta(
        hours=hours_offset
    )
    return artifact


def make_plugin_task_parameter_type(
    creator, group, name="test_param_type", description=None
):
    """Create a plugin task parameter type."""
    resource = models.Resource("plugin_task_parameter_type", group)
    return models.PluginTaskParameterType(
        name=name,
        description=description,
        structure=None,
        resource=resource,
        creator=creator,
    )


def make_artifact_with_task(
    creator,
    group,
    job,
    task,
    uri="s3://test-bucket/test-artifact",
    is_dir=False,
    file_size=None,
    description="",
):
    """Create an artifact linked to a plugin task."""
    artifact_resource = models.Resource("artifact", group)
    artifact = models.Artifact(
        uri=uri,
        is_dir=is_dir,
        file_size=file_size,
        description=description,
        resource=artifact_resource,
        creator=creator,
    )
    artifact.plugin_file_id = task.plugin_file_resource_snapshot_id
    artifact.task_name = task.plugin_task_name
    job.children.append(artifact_resource)
    return artifact


def make_artifact_task(plugin_file, task_name="test_task"):
    """Create a plugin task of type 'artifact'."""
    return models.ArtifactTask(
        plugin_task_name=task_name,
        file=plugin_file,
        output_parameters=[],
    )


def make_plugin_file(creator, group, name="test_plugin.py"):
    """Create a plugin file."""
    resource = models.Resource("plugin_file", group)
    return models.PluginFile(
        filename=name,
        contents="# test plugin",
        description=None,
        resource=resource,
        creator=creator,
    )


def make_output_parameter(task, param_type, parameter_number, value="test"):
    """Create a plugin task output parameter."""
    output_param = models.PluginTaskOutputParameter(
        name=f"param_{parameter_number}",
        parameter_number=parameter_number,
        parameter_type=param_type,
    )
    task.output_parameters.append(output_param)
    return output_param


@pytest.fixture
def job_with_dependencies(db_session, account, fake_data):
    """Create a job with all required dependencies."""
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

    entry_point = fake_data.entry_point(
        account.user, account.group, fake_plugin.plugin, queue
    )
    db_session.add(entry_point)
    db_session.commit()

    experiment.resource.children.append(entry_point.resource)
    db_session.commit()

    job_resource = models.Resource("job", account.group)
    job = models.Job(
        timeout="24h",
        status="queued",
        description="test job",
        resource=job_resource,
        creator=account.user,
    )
    job.entry_point_job = models.EntryPointJob(
        job_resource=job_resource,
        entry_point=entry_point,
        entry_point_parameter_values=[],
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
    db_session.add(job)
    db_session.commit()

    return job


class TestArtifactCreate:
    """Tests for ArtifactRepository.create()"""

    def test_artifact_create_success(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            description="test artifact",
        )

        artifact_repo.create(artifact)
        db_session.commit()

        result = artifact_repo.get_one(
            artifact.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == artifact

    def test_artifact_create_exists(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        artifact_repo.create(artifact)
        db_session.commit()

        with pytest.raises(errors.EntityExistsError):
            artifact_repo.create(artifact)

    def test_artifact_create_exists_deleted(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        artifact_repo.create(artifact)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, artifact.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            artifact_repo.create(artifact)

    def test_artifact_create_wrong_resource_type(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact_resource = models.Resource("artifact", account.group)
        artifact = models.Artifact(
            uri="s3://test-bucket/test-artifact",
            is_dir=False,
            file_size=None,
            description="",
            resource=artifact_resource,
            creator=account.user,
        )
        artifact.resource.resource_type = "queue"

        with pytest.raises(errors.MismatchedResourceTypeError):
            artifact_repo.create(artifact)


class TestArtifactCreateSnapshot:
    """Tests for ArtifactRepository.create_snapshot()"""

    def test_artifact_create_snapshot_success(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact1 = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        artifact_repo.create(artifact1)
        db_session.commit()

        artifact2 = make_artifact_snapshot(artifact1)

        artifact_repo.create_snapshot(artifact2)
        db_session.commit()

        check_resource = db_session.get(models.Resource, artifact2.resource_id)
        assert check_resource is not None
        assert len(check_resource.versions) == 2

    def test_artifact_create_snapshot_resource_not_exist(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )

        with pytest.raises(errors.EntityDoesNotExistError):
            artifact_repo.create_snapshot(artifact)

    def test_artifact_create_snapshot_resource_deleted(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        lock = models.ResourceLock(resource_lock_types.DELETE, artifact.resource)
        db_session.add_all((artifact, lock))
        db_session.commit()

        artifact2 = make_artifact_snapshot(artifact)

        with pytest.raises(errors.EntityDeletedError):
            artifact_repo.create_snapshot(artifact2)

    def test_artifact_create_snapshot_snapshot_exists(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        artifact_repo.create(artifact)
        db_session.commit()

        with pytest.raises(errors.EntityExistsError):
            artifact_repo.create_snapshot(artifact)


class TestArtifactGet:
    """Tests for ArtifactRepository.get()"""

    def test_artifact_get_single_exists(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            description="test artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result = artifact_repo.get(
            artifact.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == artifact

    def test_artifact_get_single_not_exists(self, db_session: DBSession, artifact_repo):
        result = artifact_repo.get(99999, utils.DeletionPolicy.NOT_DELETED)
        assert result is None

    def test_artifact_get_single_deleted(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            description="test artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, artifact.resource)
        db_session.add(lock)
        db_session.commit()

        result = artifact_repo.get(
            artifact.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result is None

    def test_artifact_get_multiple(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact1 = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            uri="s3://test-bucket/artifact1",
        )
        artifact_repo.create(artifact1)
        db_session.commit()

        result = artifact_repo.get(
            [artifact1.resource_id], utils.DeletionPolicy.NOT_DELETED
        )
        assert len(result) == 1
        assert artifact1 in result


class TestArtifactGetByJob:
    """Tests for ArtifactRepository.get_by_job()"""

    def test_artifact_get_by_job_exists(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result = artifact_repo.get_by_job(
            job_with_dependencies.resource_id,
            deletion_policy=utils.DeletionPolicy.NOT_DELETED,
        )
        assert len(result) == 1
        assert result[0] == artifact

    def test_artifact_get_by_job_not_exists(self, db_session: DBSession, artifact_repo):
        result = artifact_repo.get_by_job(
            99999,
            deletion_policy=utils.DeletionPolicy.NOT_DELETED,
        )
        assert len(result) == 0

    def test_artifact_get_by_job_multiple_artifacts(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            uri="s3://test-bucket/artifact1",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result = artifact_repo.get_by_job(
            job_with_dependencies.resource_id,
            deletion_policy=utils.DeletionPolicy.NOT_DELETED,
        )
        assert len(result) == 1


class TestArtifactGetOne:
    """Tests for ArtifactRepository.get_one()"""

    def test_artifact_get_one_exists(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            description="test artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result = artifact_repo.get_one(
            artifact.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == artifact

    def test_artifact_get_one_not_exists(self, db_session: DBSession, artifact_repo):
        with pytest.raises(errors.EntityDoesNotExistError):
            artifact_repo.get_one(99999, utils.DeletionPolicy.NOT_DELETED)

    def test_artifact_get_one_deleted(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            description="test artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, artifact.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            artifact_repo.get_one(
                artifact.resource_id, utils.DeletionPolicy.NOT_DELETED
            )


class TestArtifactGetOneSnapshot:
    """Tests for ArtifactRepository.get_one_snapshot()"""

    def test_artifact_get_one_snapshot_exists(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact1 = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        artifact_repo.create(artifact1)
        db_session.commit()

        artifact2 = make_artifact_snapshot(artifact1)
        artifact_repo.create_snapshot(artifact2)
        db_session.commit()

        result = artifact_repo.get_one_snapshot(
            artifact1.resource_id,
            artifact2.resource_snapshot_id,
            utils.DeletionPolicy.ANY,
        )
        assert result == artifact2

    def test_artifact_get_one_snapshot_not_exists(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        artifact_repo.create(artifact)
        db_session.commit()

        with pytest.raises(errors.EntityDoesNotExistError):
            artifact_repo.get_one_snapshot(
                artifact.resource_id, 99999, utils.DeletionPolicy.ANY
            )

    def test_artifact_get_one_snapshot_deleted(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
        )
        artifact_repo.create(artifact)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, artifact.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            artifact_repo.get_one_snapshot(
                artifact.resource_id,
                artifact.resource_snapshot_id,
                utils.DeletionPolicy.NOT_DELETED,
            )


class TestArtifactDelete:
    """Tests for ArtifactRepository.delete()"""

    def test_artifact_delete_exists(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            description="test artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        artifact_repo.delete(artifact)
        db_session.commit()

        assert artifact.resource.is_deleted is True

    def test_artifact_delete_not_exists(self, db_session: DBSession, artifact_repo):
        with pytest.raises(errors.EntityDoesNotExistError):
            artifact_repo.delete(99999)

    def test_artifact_delete_already_deleted(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            description="test artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, artifact.resource)
        db_session.add(lock)
        db_session.commit()

        artifact_repo.delete(artifact)


class TestArtifactGetByFiltersPaged:
    """Tests for ArtifactRepository.get_by_filters_paged()"""

    def test_artifact_get_by_filters_paged_empty(
        self, db_session: DBSession, artifact_repo
    ):
        result, count = artifact_repo.get_by_filters_paged(
            group=None,
            filters=[],
            output_params=None,
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 0
        assert len(result) == 0

    def test_artifact_get_by_filters_paged_with_results(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            uri="s3://test-bucket/artifact1",
            description="test artifact 1",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result, count = artifact_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            output_params=None,
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 1
        assert len(result) == 1

    def test_artifact_get_by_filters_paged_with_pagination(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        for i in range(5):
            artifact = make_artifact(
                account.user,
                account.group,
                job_with_dependencies,
                uri=f"s3://test-bucket/artifact{i}",
                description=f"description{i}",
            )
            artifact_repo.create(artifact)
        db_session.commit()

        result, count = artifact_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            output_params=None,
            page_start=0,
            page_length=2,
            sort_by="uri",
            descending=False,
        )
        assert count == 5
        assert len(result) == 2

    def test_artifact_get_by_filters_paged_with_invalid_sort(
        self, db_session: DBSession, artifact_repo
    ):
        with pytest.raises(errors.SortParameterValidationError):
            artifact_repo.get_by_filters_paged(
                group=None,
                filters=[],
                output_params=None,
                page_start=0,
                page_length=10,
                sort_by="invalid_field",
                descending=False,
            )

    def test_artifact_get_by_filters_paged_with_unlimited_length(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        for i in range(15):
            artifact = make_artifact(
                account.user,
                account.group,
                job_with_dependencies,
                uri=f"s3://test-bucket/artifact{i}",
                description=f"description{i}",
            )
            artifact_repo.create(artifact)
        db_session.commit()

        result, count = artifact_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            output_params=None,
            page_start=0,
            page_length=0,
            sort_by="uri",
            descending=False,
        )
        assert count == 15
        assert len(result) == 15


class TestArtifactGetByFiltersPagedOutputParams:
    """Tests for ArtifactRepository.get_by_filters_paged() with output_params filter.

    The output_params filter allows filtering artifacts based on their plugin task
    output parameter types. This verifies the _apply_ouput_params_filter method.
    """

    def test_output_params_single_type(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        """Filter artifacts by single output param type."""
        param_type = make_plugin_task_parameter_type(
            account.user, account.group, name="image"
        )
        db_session.add(param_type)
        db_session.commit()

        plugin_file = make_plugin_file(account.user, account.group)
        db_session.add(plugin_file)
        db_session.commit()

        task = make_artifact_task(plugin_file, task_name="generate_image")
        db_session.add(task)
        db_session.commit()

        output_param = make_output_parameter(task, param_type, parameter_number=0)
        db_session.add(output_param)
        db_session.commit()

        artifact = make_artifact_with_task(
            account.user,
            account.group,
            job_with_dependencies,
            task,
            uri="s3://test-bucket/image_artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result, count = artifact_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            output_params=[param_type.resource_id],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 1
        assert result[0].uri == "s3://test-bucket/image_artifact"

    def test_output_params_wrong_type(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        """Filter by param type that doesn't match should return empty."""
        param_type_a = make_plugin_task_parameter_type(
            account.user, account.group, name="image"
        )
        param_type_b = make_plugin_task_parameter_type(
            account.user, account.group, name="model"
        )
        db_session.add_all([param_type_a, param_type_b])
        db_session.commit()

        plugin_file = make_plugin_file(account.user, account.group)
        db_session.add(plugin_file)
        db_session.commit()

        task = make_artifact_task(plugin_file, task_name="generate_model")
        db_session.add(task)
        db_session.commit()

        output_param = make_output_parameter(task, param_type_a, parameter_number=0)
        db_session.add(output_param)
        db_session.commit()

        artifact = make_artifact_with_task(
            account.user,
            account.group,
            job_with_dependencies,
            task,
            uri="s3://test-bucket/model_artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result, count = artifact_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            output_params=[param_type_b.resource_id],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 0
        assert len(result) == 0

    def test_output_params_multiple_types(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        """Filter by multiple output param types."""
        param_type_a = make_plugin_task_parameter_type(
            account.user, account.group, name="image"
        )
        param_type_b = make_plugin_task_parameter_type(
            account.user, account.group, name="label"
        )
        db_session.add_all([param_type_a, param_type_b])
        db_session.commit()

        plugin_file = make_plugin_file(account.user, account.group)
        db_session.add(plugin_file)
        db_session.commit()

        task = make_artifact_task(plugin_file, task_name="process_data")
        db_session.add(task)
        db_session.commit()

        output_param_a = make_output_parameter(task, param_type_a, parameter_number=0)
        output_param_b = make_output_parameter(task, param_type_b, parameter_number=1)
        db_session.add_all([output_param_a, output_param_b])
        db_session.commit()

        artifact = make_artifact_with_task(
            account.user,
            account.group,
            job_with_dependencies,
            task,
            uri="s3://test-bucket/multi_output_artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result, count = artifact_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            output_params=[param_type_a.resource_id, param_type_b.resource_id],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 1
        assert result[0].uri == "s3://test-bucket/multi_output_artifact"

    def test_output_params_wrong_count(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        """Filter by single param type should not match artifact with 2 params."""
        param_type_a = make_plugin_task_parameter_type(
            account.user, account.group, name="image"
        )
        param_type_b = make_plugin_task_parameter_type(
            account.user, account.group, name="label"
        )
        db_session.add_all([param_type_a, param_type_b])
        db_session.commit()

        plugin_file = make_plugin_file(account.user, account.group)
        db_session.add(plugin_file)
        db_session.commit()

        task = make_artifact_task(plugin_file, task_name="dual_output_task")
        db_session.add(task)
        db_session.commit()

        output_param_a = make_output_parameter(task, param_type_a, parameter_number=0)
        output_param_b = make_output_parameter(task, param_type_b, parameter_number=1)
        db_session.add_all([output_param_a, output_param_b])
        db_session.commit()

        artifact = make_artifact_with_task(
            account.user,
            account.group,
            job_with_dependencies,
            task,
            uri="s3://test-bucket/dual_artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result, count = artifact_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            output_params=[param_type_a.resource_id],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 0
        assert len(result) == 0

    def test_output_params_empty_returns_all(
        self, db_session: DBSession, account, artifact_repo, job_with_dependencies
    ):
        """Filter by empty output_params should return all artifacts."""
        artifact = make_artifact(
            account.user,
            account.group,
            job_with_dependencies,
            uri="s3://test-bucket/no_task_artifact",
        )
        artifact_repo.create(artifact)
        db_session.commit()

        result, count = artifact_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            output_params=[],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 1
        assert result[0].uri == "s3://test-bucket/no_task_artifact"
