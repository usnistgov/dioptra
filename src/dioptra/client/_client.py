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
from __future__ import annotations

import os
from pathlib import Path
from posixpath import join as urljoin
from typing import Any, cast
from urllib.parse import urlparse, urlunparse

import requests


def get_dioptra_client(address: str | None = None) -> DioptraClient:
    address = (
        f"{address}/api" if address else f"{os.environ['DIOPTRA_RESTAPI_URI']}/api"
    )
    scheme, netloc, path, _, _, _ = urlparse(address)

    # maybe we should make this into a wrapper class to deal with unexpectedly
    # closed connections, retries, error handling etc.?
    session = requests.Session()
    # More needed with the address most likely

    experiment_client = ExperimentClient(session, address)
    job_client = JobClient(session, address)
    queue_client = QueueClient(session, address)
    task_plugin_client = TaskPluginClient(session, address)
    builtin_task_plugin_client = BuiltinTaskPluginClient(session, address)
    custom_task_plugin_client = CustomTaskPluginClient(session, address)

    return DioptraClient(
        experiment=experiment_client,
        job=job_client,
        queue=queue_client,
        tasks_plugins=task_plugin_client,
        builtin_task_plugins=builtin_task_plugin_client,
        custom_task_plugins=custom_task_plugin_client,
        session=session,
    )


class DioptraClient(object):
    """Connects to the Dioptra REST api, and provides access to endpoints.

    Args:
        address: Address of the Dioptra REST api or if no address is given the DIOPTRA_RESTAPI_URI environment variable is used.

    Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
    """  # noqa B950

    def __init__(
        self,
        session,
        experiment,
        job,
        queue,
        tasks_plugins,
        custom_task_plugins,
        builtin_task_plugins,
    ) -> None:
        self._session = session
        self._experiment = experiment
        self._job = job
        self._queue = queue
        self._tasks_plugins = tasks_plugins
        self._custom_task_plugins = custom_task_plugins
        self._builtin_task_plugins = builtin_task_plugins

    @property
    def session(self):
        return self._session

    @property
    def experiment(self):
        self._experiment.set_session(self.session)
        return self._experiment

    @property
    def job(self):
        self._job.set_session(self.session)
        return self._job

    @property
    def queue(self):
        self._queue.set_session(self.session)
        return self._queue

    @property
    def tasks_plugins(self):
        self._tasks_plugins.set_session(self.session)
        return self._tasks_plugins

    @property
    def custom_task_plugins(self):
        self._custom_task_plugins.set_session(self.session)
        return self._custom_task_plugins

    @property
    def builtin_task_plugins(self):
        self._builtin_task_plugins.set_session(self.session)
        return self._builtin_task_plugins

    def set_session(self, session: requests.Session):
        self._session = session

    def refresh_session(self):
        self.set_session(requests.Session())
        self._experiment.set_session(self.session)
        self._job.set_session(self.session)
        self._queue.set_session(self.session)
        self._tasks_plugins.set_session(self.session)
        self._custom_task_plugins.set_session(self.session)
        self._builtin_task_plugins.set_session(self.session)


class ExperimentClient(object):
    def __init__(self, session: requests.Session, address: str | None = None):
        parsed = urlparse(address)
        self._scheme, self._netloc, self._path = (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
        )
        self._session = session

    @property
    def session(self):
        return self._session

    @property
    def experiment_endpoint(self) -> str:
        """Experiment endpoint url"""
        return urlunparse(
            (
                str(self._scheme),
                str(self._netloc),
                urljoin(str(self._path), "experiment/"),
                "",
                "",
                "",
            )
        )

    def set_session(self, session: requests.Session):
        self._session = session

    def get_by_id(self, id: int) -> dict[str, Any]:
        """Gets an experiment by its unique identifier.

        Args:
            id: An integer identifying a registered experiment.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'lastModified': '2023-06-22T13:42:35.379462',
                    'experimentId': 10,
                    'name': 'mnist_feature_squeezing',
                    'createdOn': '2023-06-22T13:42:35.379462'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        experiment_id_query: str = urljoin(self.experiment_endpoint, str(id))
        try:
            ret = cast(dict[str, Any], self.session.get(experiment_id_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def get_by_name(self, name: str) -> dict[str, Any]:
        """Gets an experiment by its unique name.

        Args:
            name: The name of the experiment.

        Returns:
            The Dioptra REST api's response containing the experiment id, name, and metadata.

            Example::

                {
                    'experimentId': 1,
                    'name': 'mnist',
                    'createdOn': '2023-06-22T13:42:35.379462',
                    'lastModified': '2023-06-22T13:42:35.379462'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        experiment_name_query: str = urljoin(self.experiment_endpoint, "name", name)
        try:
            ret = cast(dict[str, Any], self.session.get(experiment_name_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def get_all(self) -> list[dict[str, Any]]:
        """Gets a list of all registered experiments.

        Returns:
            A list of responses detailing all experiments.

            Example::

                [{
                    'lastModified': '2023-04-24T20:20:27.315687',
                    'experimentId': 1,
                    'name': 'mnist',
                    'createdOn': '2023-04-24T20:20:27.315687'
                },
                ...
                {
                    'lastModified': '2023-06-22T13:42:35.379462',
                    'experimentId': 10,
                    'name': 'mnist_feature_squeezing',
                    'createdOn': '2023-06-22T13:42:35.379462'
                }]

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            ret = cast(
                list[dict[str, Any]], self.session.get(self.experiment_endpoint).json()
            )
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def register(self, name: str) -> dict[str, Any]:
        """Creates a new experiment via an experiment registration form.

        Args:
            name: The name to register as a new experiment.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'lastModified': '2023-06-26T15:45:09.232878',
                    'experimentId': 11,
                    'name': 'experiment1234',
                    'createdOn': '2023-06-26T15:45:09.232878'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        experiment_registration_form = {"name": name}

        try:
            response = self.session.post(
                self.experiment_endpoint,
                data=experiment_registration_form,
            )
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")

        return cast(dict[str, Any], response.json())

    def delete_by_id(self, id: int) -> dict[str, Any]:
        """Deletes an experiment by its unique identifier.

        Args:
            name: The name to register as a new experiment.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'status': 'Success',
                    'id': 11,
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950

        experiment_id_query: str = urljoin(self.experiment_endpoint, str(id))
        try:
            response = self.session.delete(experiment_id_query)
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")

        return cast(dict[str, Any], response.json())

    def delete_by_name(self, name: str) -> dict[str, Any]:
        """Deletes an experiment by its unique name.

        Args:
            name: The name to register as a new experiment.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'status': 'Success',
                    'id': 11,
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950

        experiment_name_query: str = urljoin(self.experiment_endpoint, "name", name)
        try:
            response = self.session.delete(experiment_name_query)
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")

        return cast(dict[str, Any], response.json())

    def update_by_id(self, id: int, new_name: str) -> dict[str, Any]:
        """Updates an experiment via an experiment update by its unique identifier.

        Args:
            id: The id of the experiment to update.
            new_name: The new name for the experiment.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'lastModified': '2023-06-26T15:45:09.232878',
                    'experimentId': 11,
                    'name': 'experiment1234',
                    'createdOn': '2023-06-26T15:45:09.232878'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        experiment_id_query: str = urljoin(self.experiment_endpoint, str(id))
        experiment_update = {"name": new_name}

        try:
            response = self.session.put(
                experiment_id_query,
                data=experiment_update,
            )
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")

        return cast(dict[str, Any], response.json())

    def update_by_name(self, name: str, new_name: str) -> dict[str, Any]:
        """Updates an experiment via an experiment update by its unique name.

        Args:
            name: The name of the experiment to update.
            new_name: The new name for the experiment.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'lastModified': '2023-06-26T15:45:09.232878',
                    'experimentId': 11,
                    'name': 'experiment1234',
                    'createdOn': '2023-06-26T15:45:09.232878'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        experiment_name_query: str = urljoin(self.experiment_endpoint, "name", name)
        experiment_update = {"name": new_name}

        try:
            response = self.session.put(
                experiment_name_query,
                data=experiment_update,
            )
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")

        return cast(dict[str, Any], response.json())


class JobClient(object):
    def __init__(self, session: requests.Session, address: str | None = None):
        parsed = urlparse(address)
        self._scheme, self._netloc, self._path = (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
        )
        self._session = session

    @property
    def session(self):
        return self._session

    @property
    def job_endpoint(self) -> str:
        """Job endpoint url"""
        return urlunparse(
            (
                str(self._scheme),
                str(self._netloc),
                urljoin(str(self._path), "job/"),
                "",
                "",
                "",
            )
        )

    def set_session(self, session: requests.Session):
        self._session = session

    def get(self, id: str) -> dict[str, Any]:
        """Gets a job by its unique identifier.

        Args:
            id: A string specifying a job’s UUID.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'mlflowRunId': None,
                    'lastModified': '2023-06-26T15:26:43.100093',
                    'experimentId': 10,
                    'queueId': 2,
                    'workflowUri': 's3://workflow/07d2c0a91aaf4901acd7afe1580aea47/workflows.tar.gz',
                    'entryPoint': 'train',
                    'dependsOn': None,
                    'status': 'queued',
                    'timeout': '24h',
                    'jobId': '4eb2305e-57c3-4867-a59f-1a1ecd2033d4',
                    'entryPointKwargs': '-P model_architecture=shallow_net -P epochs=30 -P register_model_name=feature_squeezing_mnist_shallow_net -P data_dir=/dioptra/data/Mnist',
                    'createdOn': '2023-06-26T15:26:43.100093'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        job_id_query: str = urljoin(self.job_endpoint, id)
        try:
            ret = cast(dict[str, Any], self.session.get(job_id_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def get_all(self) -> list[dict[str, Any]]:
        """Gets a list of all submitted jobs.

        Returns:
            A list of responses detailing all jobs.

            Example::

                [{
                    'mlflowRunId': None,
                    'lastModified': '2023-04-24T20:54:30.722304',
                    'experimentId': 2,
                    'queueId': 2,
                    'workflowUri': 's3://workflow/268a7620de8247e3a00fbe466f023429/workflows.tar.gz',
                    'entryPoint': 'train',
                    'dependsOn': None,
                    'status': 'queued',
                    'timeout': '1h',
                    'jobId': 'a4c574dd-cbd1-43c9-9afe-17d69cd1c73d',
                    'entryPointKwargs': '-P dcd ata_dir=/nfs/data/Mnist',
                    'createdOn': '2023-04-24T20:54:30.722304'
                },
                ...]


        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            ret = cast(list[dict[str, Any]], self.session.get(self.job_endpoint).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def submit(
        self,
        workflows_file: str | Path,
        experiment_name: str,
        entry_point: str,
        entry_point_kwargs: str | None = None,
        depends_on: str | None = None,
        queue: str = "tensorflow_cpu",
        timeout: str = "24h",
    ) -> dict[str, Any]:
        """Creates a new job via a job submission form with an attached file.

        Args:
            workflows_file: A tarball archive or zip file containing, at a minimum, a MLproject file and its associated entry point scripts.
            experiment_name:The name of a registered experiment.
            entry_point: Entrypoint name.
            entry_point_kwargs: A string listing parameter values to pass to the entry point for the job. The list of parameters is specified using the following format: “-P param1=value1 -P param2=value2”. Defaults to None.
            depends_on: A UUID for a previously submitted job to set as a dependency for the current job. Defaults to None.
            queue: Name of the queue the job is submitted to. Defaults to "tensorflow_cpu".
            timeout: The maximum alloted time for a job before it times out and is stopped. Defaults to "24h".

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'createdOn': '2023-06-26T15:26:43.100093',
                    'dependsOn': None,
                    'entryPoint': 'train',
                    'entryPointKwargs': '-P model_architecture=shallow_net -P epochs=30 -P '
                    'register_model_name=feature_squeezing_mnist_shallow_net '
                    '-P data_dir=/dioptra/data/Mnist',
                    'experimentId': 10,
                    'jobId': '4eb2305e-57c3-4867-a59f-1a1ecd2033d4',
                    'lastModified': '2023-06-26T15:26:43.100093',
                    'mlflowRunId': None,
                    'queueId': 2,
                    'status': 'queued',
                    'timeout': '24h',
                    'workflowUri': 's3://workflow/07d2c0a91aaf4901acd7afe1580aea47/workflows.tar.gz'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        job_form = {
            "experiment_name": experiment_name,
            "queue": queue,
            "timeout": timeout,
            "entry_point": entry_point,
        }

        if entry_point_kwargs is not None:
            job_form["entry_point_kwargs"] = entry_point_kwargs

        if depends_on is not None:
            job_form["depends_on"] = depends_on

        workflows_file = Path(workflows_file)

        with workflows_file.open("rb") as f:
            job_files = {"workflow": (workflows_file.name, f)}
            try:
                response = self.session.post(
                    self.job_endpoint,
                    data=job_form,
                    files=job_files,
                )
            except requests.ConnectionError as e:
                print(e)
                print("Is the API endpoint running and available?")

        return cast(dict[str, Any], response.json())


class TaskPluginClient(object):
    """Connects to the Dioptra REST api, and provides access to task plugin endpoint.

    Args:
        session: Session object used to connect to the REST api.
        address: Address of the Dioptra REST api or if no address is given the DIOPTRA_RESTAPI_URI environment variable is used.

    Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
    """  # noqa B950

    def __init__(self, session: requests.Session, address: str | None = None):
        parsed = urlparse(address)
        self._scheme, self._netloc, self._path = (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
        )
        self._session = session

    @property
    def session(self):
        """Session object for client's connection to the API."""
        return self._session

    @property
    def task_plugin_endpoint(self) -> str:
        """Task plugins endpoint url"""
        return urlunparse(
            (
                str(self._scheme),
                str(self._netloc),
                urljoin(str(self._path), "taskPlugin/"),
                "",
                "",
                "",
            )
        )

    def set_session(self, session: requests.Session):
        self._session = session

    def get_all(self) -> list[dict[str, Any]]:
        """Gets a list of all registered builtin task plugins.


        Returns:
            A list of responses detailing all plugins.

            Example::

                [{
                    'taskPluginName': 'artifacts',
                    'collection': 'dioptra_builtins',
                    'modules': ['__init__.py', 'exceptions.py', 'mlflow.py', 'utils.py']},
                    ...
                    {'taskPluginName': 'pixel_threshold',
                    'collection': 'dioptra_custom',
                    'modules': ['__init__.py', 'pixelthreshold.py']
                }]


        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950

        try:
            ret = cast(
                list[dict[str, Any]], self.session.get(self.task_plugin_endpoint).json()
            )
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret


class BuiltinTaskPluginClient(object):
    """Connects to the Dioptra REST api, and provides access to builtin task plugin endpoint.

    Args:
        session: Session object used to connect to the REST api.
        address: Address of the Dioptra REST api or if no address is given the DIOPTRA_RESTAPI_URI environment variable is used.

    Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
    """  # noqa B950

    def __init__(self, session: requests.Session, address: str | None = None):
        parsed = urlparse(address)
        self._scheme, self._netloc, self._path = (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
        )
        self._session = session

    @property
    def session(self):
        """Session object for client's connection to the API."""
        return self._session

    @property
    def task_plugin_builtins_endpoint(self) -> str:
        """Builtin task plugins endpoint url"""
        return urlunparse(
            (
                str(self._scheme),
                str(self._netloc),
                urljoin(str(self._path), "taskPlugin/dioptra_builtins"),
                "",
                "",
                "",
            )
        )

    def set_session(self, session: requests.Session):
        self._session = session

    def get(self, name: str) -> dict[str, Any]:
        """Gets a custom builtin plugin by its unique name.

        Args:
            name: A unique string identifying a task plugin package within dioptra_builtins collection.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'taskPluginName': 'attacks',
                    'collection': 'dioptra_builtins',
                    'modules': ['__init__.py', 'fgm.py']
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        task_plugin_name_query: str = urljoin(self.task_plugin_builtins_endpoint, name)
        try:
            ret = cast(dict[str, Any], self.session.get(task_plugin_name_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def get_all(self) -> list[dict[str, Any]]:
        """Gets a list of all registered builtin task plugins.

        Returns:
            A list of responses detailing all builtin plugins.

            Example::

                [{
                    'taskPluginName': 'artifacts',
                    'collection': 'dioptra_builtins',
                    'modules': ['__init__.py', 'exceptions.py', 'mlflow.py', 'utils.py']},
                    ...
                    {'taskPluginName': 'backend_configs',
                    'collection': 'dioptra_builtins',
                    'modules': ['__init__.py', 'tensorflow.py']
                }]

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            ret = cast(
                list[dict[str, Any]],
                self.session.get(self.task_plugin_builtins_endpoint).json(),
            )
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret


class CustomTaskPluginClient(object):
    """Connects to the Dioptra REST api, and provides access to custom task plugin endpoint.

    Args:
        session: Session object used to connect to the REST api.
        address: Address of the Dioptra REST api or if no address is given the DIOPTRA_RESTAPI_URI environment variable is used.

    Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
    """  # noqa B950

    def __init__(self, session: requests.Session, address: str | None = None):
        parsed = urlparse(address)
        self._scheme, self._netloc, self._path = (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
        )
        self._session = session

    @property
    def session(self):
        return self._session

    @property
    def task_plugin_custom_endpoint(self) -> str:
        """Custom task plugins endpoint url"""
        return urlunparse(
            (
                str(self._scheme),
                str(self._netloc),
                urljoin(str(self._path), "taskPlugin/dioptra_custom"),
                "",
                "",
                "",
            )
        )

    @property
    def task_plugin_endpoint(self) -> str:
        """Task plugins endpoint url"""
        return urlunparse(
            (
                str(self._scheme),
                str(self._netloc),
                urljoin(str(self._path), "taskPlugin/"),
                "",
                "",
                "",
            )
        )

    def set_session(self, session: requests.Session):
        self._session = session

    def delete(self, name: str) -> dict[str, Any]:
        """Deletes a custom task plugin by its unique name.

        Args:
            name: A unique string identifying a task plugin package within dioptra_custom collection.

        Returns:
            The Dioptra REST api's response.

            Example::

                {'collection': 'dioptra_custom',
                'status': 'Success',
                'taskPluginName': ['evaluation']}

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        plugin_name_query: str = urljoin(self.task_plugin_custom_endpoint, name)
        try:
            ret = cast(dict[str, Any], self.session.delete(plugin_name_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def get(self, name: str) -> dict[str, Any]:
        """Gets a custom task plugin by its unique name.

        Args:
            name: A unique string identifying a task plugin package within dioptra_builtins collection.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'taskPluginName': 'custom_poisoning_plugins',
                    'collection': 'dioptra_custom',
                    'modules': ['__init__.py',
                    'attacks_poison.py',
                    'data_tensorflow.py',
                    'datasetup.py',
                    'defenses_image_preprocessing.py',
                    'defenses_training.py',
                    'estimators_keras_classifiers.py',
                    'registry_art.py',
                    'tensorflow.py']
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        task_plugin_name_query: str = urljoin(self.task_plugin_custom_endpoint, name)
        try:
            ret = cast(dict[str, Any], self.session.get(task_plugin_name_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def get_all(self) -> list[dict[str, Any]]:
        """Gets a list of all registered custom task plugins.

        Returns:
            A list of responses detailing all custom plugins.

            Example::

                [{
                    'taskPluginName': 'model_inversion',
                    'collection': 'dioptra_custom',
                    'modules': ['__init__.py', 'modelinversion.py']},
                    ...
                    {'taskPluginName': 'pixel_threshold',
                    'collection': 'dioptra_custom',
                    'modules': ['__init__.py', 'pixelthreshold.py']
                }]

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            ret = cast(
                list[dict[str, Any]],
                self.session.get(self.task_plugin_custom_endpoint).json(),
            )
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def upload(
        self,
        custom_plugin_name: str,
        custom_plugin_file: str | Path,
        collection: str = "dioptra_custom",
    ) -> dict[str, Any]:
        """Registers a new task plugin uploaded via the task plugin upload form.

        Args:
            custom_plugin_name: Plugin name for for the upload form.
            custom_plugin_file: Path to custom plugin.
            collection: Collection to upload the plugin to. Defaults to "dioptra_custom".

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'taskPluginName': 'evaluation',
                    'collection': 'dioptra_custom',
                    'modules': ['tensorflow.py',
                    'import_keras.py',
                    '__init__.py']
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        plugin_upload_form = {
            "task_plugin_name": custom_plugin_name,
            "collection": collection,
        }

        custom_plugin_file = Path(custom_plugin_file)
        try:
            with custom_plugin_file.open("rb") as f:
                custom_plugin_file_dict = {
                    "task_plugin_file": (custom_plugin_file.name, f)
                }
                response = self.session.post(
                    self.task_plugin_endpoint,  # shouldn't this be a different endpoint
                    data=plugin_upload_form,
                    files=custom_plugin_file_dict,
                )

            ret = cast(dict[str, Any], response.json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret


class QueueClient(object):
    """Connects to the Dioptra REST api, and provides access to Queue endpoint.

    Args:
        session: Session object used to connect to the REST api.
        address: Address of the Dioptra REST api or if no address is given the DIOPTRA_RESTAPI_URI environment variable is used.

    Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
    """  # noqa B950

    def __init__(
        self,
        session: requests.Session,
        address: str | None = None,
    ) -> None:
        parsed = urlparse(address)
        self._scheme, self._netloc, self._path = (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
        )
        self._session = session

    @property
    def session(self):
        """Session object for client's connection to the API."""
        return self._session

    @property
    def queue_endpoint(self) -> str:
        """Queue endpoint url"""
        return urlunparse(
            (
                str(self._scheme),
                str(self._netloc),
                urljoin(str(self._path), "queue/"),
                "",
                "",
                "",
            )
        )

    def set_session(self, session: requests.Session):
        self._session = session

    def get_by_id(self, id: int) -> dict[str, Any]:
        """Gets a queue by its unique identifier.

        Args:
            id: An integer identifying a registered queue.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'lastModified': '2023-04-24T20:53:09.801442',
                    'name': 'tensorflow_cpu',
                    'queueId': 1,
                    'createdOn': '2023-04-24T20:53:09.801442'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            queue_id_query: str = urljoin(self.queue_endpoint, str(id))
            ret = cast(dict[str, Any], self.session.get(queue_id_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def get_by_name(self, name: str) -> dict[str, Any]:
        """Gets a queue by its unique name.

        Args:
            name: The name of the queue.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'lastModified': '2023-04-24T20:53:09.801442',
                    'name': 'tensorflow_cpu',
                    'queueId': 1,
                    'createdOn': '2023-04-24T20:53:09.801442'
                }

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            queue_name_query: str = urljoin(self.queue_endpoint, "name", name)
            ret = cast(dict[str, Any], self.session.get(queue_name_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def get_all(self) -> list[dict[str, Any]]:
        """Gets a list of all registered queues.


        Returns:
            A list of responses detailing all registered queues.

            Example::

                [{
                    'lastModified': '2023-04-24T20:53:09.801442',
                    'name': 'tensorflow_cpu',
                    'queueId': 1,
                    'createdOn': '2023-04-24T20:53:09.801442'},
                    {'lastModified': '2023-04-24T20:53:09.824101',
                    'name': 'tensorflow_gpu',
                    'queueId': 2,
                    'createdOn': '2023-04-24T20:53:09.824101'},
                    {'lastModified': '2023-04-24T20:53:09.867917',
                    'name': 'pytorch_cpu',
                    'queueId': 3,
                    'createdOn': '2023-04-24T20:53:09.867917'},
                    {'lastModified': '2023-04-24T20:53:09.893451',
                    'name': 'pytorch_gpu',
                    'queueId': 4,
                    'createdOn': '2023-04-24T20:53:09.893451'
                }]

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            ret = cast(
                list[dict[str, Any]], self.session.get(self.queue_endpoint).json()
            )
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def lock(self, name: str) -> dict[str, Any]:
        """Locks the queue (name reference) if it is unlocked.

        Args:
            name: The name of the queue.

        Returns:
            The Dioptra REST api's response.

            Example::

                {'name': ['tensorflow_cpu'], 'status': 'Success'}


        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            queue_name_query: str = urljoin(self.queue_endpoint, "name", name, "lock")
            ret = cast(dict[str, Any], self.session.put(queue_name_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def unlock(self, name: str) -> dict[str, Any]:
        """Removes the lock from the queue (name reference) if it exists.

        Args:
            name: The name of the queue.

        Returns:
            The Dioptra REST api's response.

            Example::

                {'name': ['tensorflow_cpu'], 'status': 'Success'}

        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        try:
            queue_name_query: str = urljoin(self.queue_endpoint, "name", name, "lock")

            ret = cast(dict[str, Any], self.session.delete(queue_name_query).json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret

    def register(self, name: str = "tensorflow_cpu") -> dict[str, Any]:  # no
        """Creates a new queue via a queue registration form.
        Args:
            name: The name to register as a new queue. Defaults to "tensorflow_cpu".
        Returns:
            The Dioptra REST api's response.
            Example::
                {
                    'lastModified': '2023-06-26T15:48:47.662293',
                    'name': 'queue',
                    'queueId': 7,
                    'createdOn': '2023-06-26T15:48:47.662293'
                }
        Notes:
           See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for more
           information on Dioptra's REST api.
        """  # noqa B950
        queue_registration_form = {"name": name}
        try:
            response = requests.post(
                self.queue_endpoint,
                data=queue_registration_form,
            )

            ret = cast(dict[str, Any], response.json())
        except requests.ConnectionError as e:
            print(e)
            print("Is the API endpoint running and available?")
        return ret
