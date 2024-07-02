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
import textwrap
import uuid
from dataclasses import dataclass

from faker import Faker
from passlib.hash import pbkdf2_sha256

from dioptra.restapi.db import models


@dataclass
class FakeAccount(object):
    """Dataclass for storing a fake account's ORM objects.

    Attributes:
        user: An ORM object representing a fake user.
        group: An ORM object representing a fake group.
    """

    user: models.User
    group: models.Group


@dataclass
class FakePlugin(object):
    """Dataclass for storing a fake plugin's ORM objects.

    Attributes:
        plugin: An ORM object representing a fake plugin.
        plugin_task: An ORM object representing a fake plugin task.
        plugin_file: An ORM object representing a fake plugin file.
        init_plugin_file: An ORM object representing a fake init plugin file.
    """

    plugin: models.Plugin
    plugin_task: models.PluginTask
    plugin_file: models.PluginFile
    init_plugin_file: models.PluginFile


class FakeData(object):
    """A fake data generator for creating ORM objects for use in testing."""

    def __init__(self, faker: Faker) -> None:
        """Instantiate a new FakeData object.

        Args:
            faker: The Faker object to use for generating fake data.
        """
        self._faker = faker

    def account(self) -> FakeAccount:
        """Generate a fake account consisting of a user that belongs to a default group.

        Returns:
            A FakeAccount object containing user and group ORM objects.
        """
        username = self._faker.user_name()
        password = self._faker.password()
        hashed_password = pbkdf2_sha256.hash(password)
        email_address = self._faker.email()

        user = models.User(
            username=username, password=hashed_password, email_address=email_address
        )
        group = models.Group(name=username, creator=user)

        group.members.append(
            models.GroupMember(
                user=user,
                read=True,
                write=True,
                share_read=True,
                share_write=True,
            )
        )
        group.managers.append(models.GroupManager(user=user, owner=True, admin=True))

        return FakeAccount(user=user, group=group)

    def tag(self, creator: models.User, group: models.Group) -> models.Tag:
        """Generate a fake tag.

        Args:
            creator: The user that created the tag.
            group: The group that owns the tag.

        Returns:
            An ORM object representing a fake tag.
        """
        tag = models.Tag(name=self._faker.slug(), owner=group, creator=creator)
        return tag

    def queue(
        self,
        creator: models.User,
        group: models.Group,
        include_description: bool = False,
    ) -> models.Queue:
        """Generate a fake queue.

        Args:
            creator: The user that created the queue.
            group: The group that owns the queue.
            include_description: Whether to generate a fake description for the queue.

        Returns:
            An ORM object representing a fake queue.
        """
        queue_name = self._faker.sentence(nb_words=3, variable_nb_words=True)
        description = self._faker.sentence() if include_description else None

        resource = models.Resource(resource_type="queue", owner=group)
        queue = models.Queue(
            name=queue_name, description=description, resource=resource, creator=creator
        )

        return queue

    def experiment(
        self,
        creator: models.User,
        group: models.Group,
        include_description: bool = False,
    ) -> models.Experiment:
        """Generate a fake experiment.

        Args:
            creator: The user that created the experiment.
            group: The group that owns the experiment.
            include_description: Whether to generate a fake description for the
                experiment.

        Returns:
            An ORM object representing a fake experiment.
        """
        experiment_name = self._faker.word()
        description = self._faker.sentence() if include_description else None

        resource = models.Resource(resource_type="experiment", owner=group)
        experiment = models.Experiment(
            name=experiment_name,
            description=description,
            resource=resource,
            creator=creator,
        )

        return experiment

    def plugin_task_parameter_type(
        self,
        creator: models.User,
        group: models.Group,
        name: str | None = None,
        include_description: bool = False,
    ) -> models.Experiment:
        """Generate a fake plugin task parameter type.

        Args:
            creator: The user that created the plugin task parameter type.
            group: The group that owns the plugin task parameter type.
            name: The name of the plugin task parameter type. If not provided, a random
                name will be generated.
            include_description: Whether to generate a fake description for the plugin
                task parameter type.

        Returns:
            An ORM object representing a fake plugin task parameter type.
        """
        type_name = name or self._faker.word()
        structure = None
        description = self._faker.sentence() if include_description else None

        resource = models.Resource(
            resource_type="plugin_task_parameter_type", owner=group
        )
        plugin_task_parameter_type = models.PluginTaskParameterType(
            name=type_name,
            structure=structure,
            description=description,
            resource=resource,
            creator=creator,
        )

        return plugin_task_parameter_type

    def plugin(
        self,
        creator: models.User,
        group: models.Group,
        str_parameter_type: models.PluginTaskParameterType,
        include_description: bool = False,
    ) -> FakePlugin:
        """Generate a fake plugin.

        Args:
            creator: The user that created the plugin.
            group: The group that owns the plugin.
            str_parameter_type: The plugin task parameter type for string parameters.
            include_description: Whether to generate a fake description for the plugin.

        Returns:
            A FakePlugin object containing plugin, plugin task, plugin file, and init
            plugin file ORM objects.
        """
        plugin_name = self._faker.word()
        plugin_description = self._faker.sentence() if include_description else None
        plugin_init_file_name = "__init__.py"
        plugin_init_file_description = (
            self._faker.sentence() if include_description else None
        )
        plugin_file_stem = self._faker.word()
        plugin_file_name = f"{plugin_file_stem}.py"
        plugin_file_description = (
            self._faker.sentence() if include_description else None
        )
        plugin_file_contents = textwrap.dedent(
            """from dioptra import pyplugs

            @pyplugs.register
            def hello_world(name: str) -> str:
                return f"Hello, {name}!"
            """
        )
        input_parameter_name = "name"
        output_parameter_name = "hello_world_message"
        plugin_task_name = "hello_world"

        plugin_resource = models.Resource(resource_type="plugin", owner=group)
        init_plugin_file_resource = models.Resource(
            resource_type="plugin_file", owner=group
        )
        plugin_file_resource = models.Resource(resource_type="plugin_file", owner=group)

        plugin = models.Plugin(
            name=plugin_name,
            resource=plugin_resource,
            description=plugin_description,
            creator=creator,
        )
        init_plugin_file = models.PluginFile(
            filename=plugin_init_file_name,
            contents="",
            description=plugin_init_file_description,
            resource=init_plugin_file_resource,
            creator=creator,
        )
        plugin_file = models.PluginFile(
            filename=plugin_file_name,
            contents=plugin_file_contents,
            description=plugin_file_description,
            resource=plugin_file_resource,
            creator=creator,
        )
        input_parameter = models.PluginTaskInputParameter(
            name=input_parameter_name,
            parameter_number=1,
            parameter_type=str_parameter_type,
            required=True,
        )
        output_parameter = models.PluginTaskOutputParameter(
            name=output_parameter_name,
            parameter_number=1,
            parameter_type=str_parameter_type,
        )
        plugin_task = models.PluginTask(
            file=plugin_file,
            plugin_task_name=plugin_task_name,
            input_parameters=[input_parameter],
            output_parameters=[output_parameter],
        )

        init_plugin_file.parents.append(plugin.resource)
        plugin_file.parents.append(plugin.resource)

        return FakePlugin(
            plugin=plugin,
            plugin_task=plugin_task,
            plugin_file=plugin_file,
            init_plugin_file=init_plugin_file,
        )

    def entry_point(
        self,
        creator: models.User,
        group: models.Group,
        plugin: models.Plugin,
        plugin_files: list[models.PluginFile],
        queue: models.Queue,
        include_description: bool = False,
    ) -> models.EntryPoint:
        """Generate a fake entry point.

        Args:
            creator: The user that created the entry point.
            group: The group that owns the entry point.
            plugin: A plugin associated with the entry point.
            plugin_files: Plugin files associated with the entry point.
            queue: A queue associated with the entry point.
            include_description: Whether to generate a fake description for the entry
                point.

        Returns:
            An ORM object representing a fake entry point.
        """
        entry_point_name = self._faker.word()
        entry_point_parameters = [
            models.EntryPointParameter(
                parameter_number=1,
                parameter_type="string",
                name="name",
                default_value=self._faker.word(),
            ),
        ]
        task_graph = textwrap.dedent(
            """# hello world graph
            graph:
              message:
                hello_world: $name
            """
        )
        description = self._faker.sentence() if include_description else None
        entry_point_resource = models.Resource(resource_type="entry_point", owner=group)
        entry_point = models.EntryPoint(
            name=entry_point_name,
            task_graph=task_graph,
            parameters=entry_point_parameters,
            description=description,
            resource=entry_point_resource,
            creator=creator,
        )
        entry_point_plugin_files = [
            models.EntryPointPluginFile(
                entry_point=entry_point, plugin=plugin, plugin_file=plugin_file
            )
            for plugin_file in plugin_files
        ]
        entry_point.entry_point_plugin_files.extend(entry_point_plugin_files)
        entry_point.children.append(queue.resource)
        return entry_point

    def job(
        self,
        creator: models.User,
        group: models.Group,
        entry_point: models.EntryPoint,
        experiment: models.Experiment,
        queue: models.Queue,
        include_description: bool = False,
    ) -> models.Job:
        """Generate a fake job.

        Args:
            creator: The user that created the job.
            group: The group that owns the job.
            entry_point: The entry point used to instantiate the job.
            experiment: The experiment the job is for.
            queue: The queue where the job will be run.associated with the job.
            include_description: Whether to generate a fake description for the job.

        Returns:
            An ORM object representing a fake job.
        """
        timeout = "24h"
        status = "queued"
        description = self._faker.sentence() if include_description else None

        job_resource = models.Resource(resource_type="job", owner=group)
        entry_point_parameter_values = [
            models.EntryPointParameterValue(
                value=self._faker.word(),
                job_resource=job_resource,
                parameter=entry_point.parameters[0],
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

    def job_mlflow_run(self, job: models.Job) -> models.JobMlflowRun:
        """Generate a fake job MLflow run.

        Args:
            job: The job that registered a run on the MLflow Tracking server.

        Returns:
            An ORM object representing a fake job MLflow run.
        """
        job_mlflow_run = models.JobMlflowRun(
            job_resource_id=job.resource_id,
            mlflow_run_id=uuid.uuid4(),
        )

        return job_mlflow_run

    def artifact(
        self,
        creator: models.User,
        group: models.Group,
        job: models.Job,
        include_description: bool = False,
    ) -> models.Artifact:
        """Generate a fake artifact.

        Args:
            creator: The user that created the artifact.
            group: The group that owns the artifact.
            job: The job that produced the artifact.
            include_description: Whether to generate a fake description for the
                artifact.

        Returns:
            An ORM object representing a fake artifact.
        """
        description = self._faker.sentence() if include_description else None
        artifact_resource = models.Resource(resource_type="artifact", owner=group)
        new_artifact = models.Artifact(
            uri=self._faker.uri(schemes=["s3"]),
            description=description,
            resource=artifact_resource,
            creator=creator,
        )

        # This is how to link an artifact to a job resource
        job.children.append(new_artifact.resource)

        return new_artifact

    def ml_model(
        self,
        creator: models.User,
        group: models.Group,
        artifact: models.Artifact,
        include_description: bool = False,
    ) -> models.MlModel:
        """Generate a fake ML model.

        Args:
            creator: The user that created the ML model.
            group: The group that owns the ML model.
            artifact: The artifact to register as a ML model.
            include_description: Whether to generate a fake description for the ML
                model.

        Returns:
            An ORM object representing a fake ML model.
        """
        description = self._faker.sentence() if include_description else None
        ml_model_resource = models.Resource(resource_type="ml_model", owner=group)
        new_ml_model = models.MlModel(
            name=self._faker.word(),
            description=description,
            resource=ml_model_resource,
            creator=creator,
            artifact=artifact,
        )

        return new_ml_model
