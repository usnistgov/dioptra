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


class DioptraClient(object):
    """Connects to the Dioptra REST api, and provides access to endpoints.

    Args:
        address: Address of the Dioptra REST api or if no address is given the
            DIOPTRA_RESTAPI_URI environment variable is used.
        api_version: The version of the Dioptra REST API to use. Defaults to "v0".

    Notes:
        See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for
        more information on Dioptra's REST api.
    """

    def __init__(self, address: str | None = None, api_version: str = "v0") -> None:
        address = (
            f"{address}/api/{api_version}"
            if address
            else f"{os.environ['DIOPTRA_RESTAPI_URI']}/api/{api_version}"
        )
        self._scheme, self._netloc, self._path, _, _, _ = urlparse(address)

    @property
    def experiment_endpoint(self) -> str:
        """Experiment endpoint url"""
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, "experiment/"), "", "", "")
        )

    @property
    def job_endpoint(self) -> str:
        """Job endpoint url"""
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, "job/"), "", "", "")
        )

    @property
    def task_plugin_endpoint(self) -> str:
        """Task plugins endpoint url"""
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, "taskPlugin/"), "", "", "")
        )

    @property
    def task_plugin_builtins_endpoint(self) -> str:
        """Builtin task plugins endpoint url"""
        return urlunparse(
            (
                self._scheme,
                self._netloc,
                urljoin(self._path, "taskPlugin/dioptra_builtins"),
                "",
                "",
                "",
            )
        )

    @property
    def task_plugin_custom_endpoint(self) -> str:
        """Custom task plugins endpoint url"""
        return urlunparse(
            (
                self._scheme,
                self._netloc,
                urljoin(self._path, "taskPlugin/dioptra_custom"),
                "",
                "",
                "",
            )
        )

    @property
    def queue_endpoint(self) -> str:
        """Queue endpoint url"""
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, "queue/"), "", "", "")
        )

    def delete_custom_task_plugin(self, name: str) -> dict[str, Any]:
        """Deletes a custom task plugin by its unique name.

        Args:
            name: A unique string identifying a task plugin package within
                dioptra_custom collection.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'collection': 'dioptra_custom',
                    'status': 'Success',
                    'taskPluginName': ['evaluation']
                }

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        plugin_name_query: str = urljoin(self.task_plugin_custom_endpoint, name)
        result = cast(dict[str, Any], requests.delete(plugin_name_query).json())
        return result

    def get_experiment_by_id(self, id: int) -> dict[str, Any]:
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
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        experiment_id_query: str = urljoin(self.experiment_endpoint, str(id))
        return cast(dict[str, Any], requests.get(experiment_id_query).json())

    def get_experiment_by_name(self, name: str) -> dict[str, Any]:
        """Gets an experiment by its unique name.

        Args:
            name: The name of the experiment.

        Returns:
            The Dioptra REST api's response containing the experiment id, name, and
            metadata.

            Example::

                {
                    'experimentId': 1,
                    'name': 'mnist',
                    'createdOn': '2023-06-22T13:42:35.379462',
                    'lastModified': '2023-06-22T13:42:35.379462'
                }

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        experiment_name_query: str = urljoin(self.experiment_endpoint, "name", name)
        return cast(dict[str, Any], requests.get(experiment_name_query).json())

    def get_job_by_id(self, id: str) -> dict[str, Any]:
        """Gets a job by its unique identifier.

        Args:
            id: A string specifying a job's UUID.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'mlflowRunId': None,
                    'lastModified': '2023-06-26T15:26:43.100093',
                    'experimentId': 10,
                    'queueId': 2,
                    'workflowUri': 's3://workflow/268a7620/workflows.tar.gz',
                    'entryPoint': 'train',
                    'dependsOn': None,
                    'status': 'queued',
                    'timeout': '24h',
                    'jobId': '4eb2305e-57c3-4867-a59f-1a1ecd2033d4',
                    'entryPointKwargs': '-P model_architecture=shallow_net -P epochs=3',
                    'createdOn': '2023-06-26T15:26:43.100093'
                }

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        job_id_query: str = urljoin(self.job_endpoint, id)
        return cast(dict[str, Any], requests.get(job_id_query).json())

    def get_queue_by_id(self, id: int) -> dict[str, Any]:
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
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        queue_id_query: str = urljoin(self.queue_endpoint, str(id))
        return cast(dict[str, Any], requests.get(queue_id_query).json())

    def get_queue_by_name(self, name: str) -> dict[str, Any]:
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
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        queue_name_query: str = urljoin(self.queue_endpoint, "name", name)
        return cast(dict[str, Any], requests.get(queue_name_query).json())

    def get_builtin_task_plugin(self, name: str) -> dict[str, Any]:
        """Gets a custom builtin plugin by its unique name.

        Args:
            name: A unique string identifying a task plugin package within
                dioptra_builtins collection.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'taskPluginName': 'attacks',
                    'collection': 'dioptra_builtins',
                    'modules': ['__init__.py', 'fgm.py']
                }

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        task_plugin_name_query: str = urljoin(self.task_plugin_builtins_endpoint, name)
        return cast(dict[str, Any], requests.get(task_plugin_name_query).json())

    def get_custom_task_plugin(self, name: str) -> dict[str, Any]:
        """Gets a custom task plugin by its unique name.

        Args:
            name: A unique string identifying a task plugin package within
                dioptra_builtins collection.

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'taskPluginName': 'custom_poisoning_plugins',
                    'collection': 'dioptra_custom',
                    'modules': [
                        '__init__.py',
                        'attacks_poison.py',
                        'data_tensorflow.py',
                        'datasetup.py',
                        'defenses_image_preprocessing.py',
                        'defenses_training.py',
                        'estimators_keras_classifiers.py',
                        'registry_art.py',
                        'tensorflow.py'
                    ]
                }

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        task_plugin_name_query: str = urljoin(self.task_plugin_custom_endpoint, name)
        return cast(dict[str, Any], requests.get(task_plugin_name_query).json())

    def list_experiments(self) -> list[dict[str, Any]]:
        """Gets a list of all registered experiments.

        Returns:
            A list of responses detailing all experiments.

            Example::

                [
                    {
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
                    }
                ]

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        return cast(list[dict[str, Any]], requests.get(self.experiment_endpoint).json())

    def list_jobs(self) -> list[dict[str, Any]]:
        """Gets a list of all submitted jobs.

        Returns:
            A list of responses detailing all jobs.

            Example::

                [
                    {
                        'mlflowRunId': None,
                        'lastModified': '2023-04-24T20:54:30.722304',
                        'experimentId': 2,
                        'queueId': 2,
                        'workflowUri': 's3://workflow/268a7620/workflows.tar.gz',
                        'entryPoint': 'train',
                        'dependsOn': None,
                        'status': 'queued',
                        'timeout': '1h',
                        'jobId': 'a4c574dd-cbd1-43c9-9afe-17d69cd1c73d',
                        'entryPointKwargs': '-P data_dir=/nfs/data/Mnist',
                        'createdOn': '2023-04-24T20:54:30.722304'
                    },
                    ...
                ]

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        return cast(list[dict[str, Any]], requests.get(self.job_endpoint).json())

    def list_queues(self) -> list[dict[str, Any]]:
        """Gets a list of all registered queues.

        Returns:
            A list of responses detailing all registered queues.

            Example::

                [
                    {
                        'lastModified': '2023-04-24T20:53:09.801442',
                        'name': 'tensorflow_cpu',
                        'queueId': 1,
                        'createdOn': '2023-04-24T20:53:09.801442'
                    },
                    {
                        'lastModified': '2023-04-24T20:53:09.824101',
                        'name': 'tensorflow_gpu',
                        'queueId': 2,
                        'createdOn': '2023-04-24T20:53:09.824101'
                    },
                    {
                        'lastModified': '2023-04-24T20:53:09.867917',
                        'name': 'pytorch_cpu',
                        'queueId': 3,
                        'createdOn': '2023-04-24T20:53:09.867917'
                    },
                    {
                        'lastModified': '2023-04-24T20:53:09.893451',
                        'name': 'pytorch_gpu',
                        'queueId': 4,
                        'createdOn': '2023-04-24T20:53:09.893451'
                    }
                ]

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        return cast(list[dict[str, Any]], requests.get(self.queue_endpoint).json())

    def list_all_task_plugins(self) -> list[dict[str, Any]]:
        """Gets a list of all registered builtin task plugins.

        Returns:
            A list of responses detailing all plugins.

            Example::

                [
                    {
                        'taskPluginName': 'artifacts',
                        'collection': 'dioptra_builtins',
                        'modules': ['__init__.py', 'mlflow.py', 'utils.py']
                    },
                    ...
                    {
                        'taskPluginName': 'pixel_threshold',
                        'collection': 'dioptra_custom',
                        'modules': ['__init__.py', 'pixelthreshold.py']
                    }
                ]

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """

        return cast(
            list[dict[str, Any]], requests.get(self.task_plugin_endpoint).json()
        )

    def list_builtin_task_plugins(self) -> list[dict[str, Any]]:
        """Gets a list of all registered builtin task plugins.

        Returns:
            A list of responses detailing all builtin plugins.

            Example::

                [
                    {
                        'taskPluginName': 'artifacts',
                        'collection': 'dioptra_builtins',
                        'modules': ['__init__.py', 'mlflow.py', 'utils.py']
                    },
                    ...
                    {
                        'taskPluginName': 'backend_configs',
                        'collection': 'dioptra_builtins',
                        'modules': ['__init__.py', 'tensorflow.py']
                    }
                ]

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html for
            more information on Dioptra's REST api.
        """
        return cast(
            list[dict[str, Any]],
            requests.get(self.task_plugin_builtins_endpoint).json(),
        )

    def list_custom_task_plugins(self) -> list[dict[str, Any]]:
        """Gets a list of all registered custom task plugins.

        Returns:
            A list of responses detailing all custom plugins.

            Example::

                [
                    {
                        'taskPluginName': 'model_inversion',
                        'collection': 'dioptra_custom',
                        'modules': ['__init__.py', 'modelinversion.py']
                    },
                    ...
                    {
                        'taskPluginName': 'pixel_threshold',
                        'collection': 'dioptra_custom',
                        'modules': ['__init__.py', 'pixelthreshold.py']
                    }
                ]

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        return cast(
            list[dict[str, Any]], requests.get(self.task_plugin_custom_endpoint).json()
        )

    def lock_queue(self, name: str) -> dict[str, Any]:
        """Locks the queue (name reference) if it is unlocked.

        Args:
            name: The name of the queue.

        Returns:
            The Dioptra REST api's response.

            Example::

                {'name': ['tensorflow_cpu'], 'status': 'Success'}

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        queue_name_query: str = urljoin(self.queue_endpoint, "name", name, "lock")
        return cast(dict[str, Any], requests.put(queue_name_query).json())

    def unlock_queue(self, name: str) -> dict[str, Any]:
        """Removes the lock from the queue (name reference) if it exists.

        Args:
            name: The name of the queue.

        Returns:
            The Dioptra REST api's response.

            Example::

                {'name': ['tensorflow_cpu'], 'status': 'Success'}

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        queue_name_query: str = urljoin(self.queue_endpoint, "name", name, "lock")
        return cast(dict[str, Any], requests.delete(queue_name_query).json())

    def register_experiment(self, name: str) -> dict[str, Any]:
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
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        experiment_registration_form = {"name": name}

        response = requests.post(
            self.experiment_endpoint,
            json=experiment_registration_form,
        )

        return cast(dict[str, Any], response.json())

    def register_queue(self, name: str = "tensorflow_cpu") -> dict[str, Any]:
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
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        queue_registration_form = {"name": name}

        response = requests.post(
            self.queue_endpoint,
            json=queue_registration_form,
        )

        return cast(dict[str, Any], response.json())

    def submit_job(
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
            workflows_file: A tarball archive or zip file containing, at a minimum,
                a MLproject file and its associated entry point scripts.
            experiment_name:The name of a registered experiment.
            entry_point: Entrypoint name.
            entry_point_kwargs: A string listing parameter values to pass to the
                entry point for the job. The list of parameters is specified using the
                following format: “-P param1=value1 -P param2=value2”. Defaults to None.
            depends_on: A UUID for a previously submitted job to set as a dependency
                for the current job. Defaults to None.
            queue: Name of the queue the job is submitted to. Defaults to
                "tensorflow_cpu".
            timeout: The maximum alloted time for a job before it times out and is
                stopped. Defaults to "24h".

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'createdOn': '2023-06-26T15:26:43.100093',
                    'dependsOn': None,
                    'entryPoint': 'train',
                    'entryPointKwargs': '-P data_dir=/dioptra/data/Mnist',
                    'experimentId': 10,
                    'jobId': '4eb2305e-57c3-4867-a59f-1a1ecd2033d4',
                    'lastModified': '2023-06-26T15:26:43.100093',
                    'mlflowRunId': None,
                    'queueId': 2,
                    'status': 'queued',
                    'timeout': '24h',
                    'workflowUri': 's3://workflow/07d2c0a9/workflows.tar.gz'
                }

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        job_form: dict[str, Any] = {
            "experimentName": experiment_name,
            "queue": queue,
            "timeout": timeout,
            "entryPoint": entry_point,
        }

        if entry_point_kwargs is not None:
            job_form["entryPointKwargs"] = entry_point_kwargs

        if depends_on is not None:
            job_form["dependsOn"] = depends_on

        workflows_file = Path(workflows_file)

        with workflows_file.open("rb") as f:
            job_files = {"workflow": (workflows_file.name, f)}
            response = requests.post(
                self.job_endpoint,
                data=job_form,
                files=job_files,
            )

        return cast(dict[str, Any], response.json())

    def upload_custom_plugin_package(
        self,
        custom_plugin_name: str,
        custom_plugin_file: str | Path,
        collection: str = "dioptra_custom",
    ) -> dict[str, Any]:
        """Registers a new task plugin uploaded via the task plugin upload form.

        Args:
            custom_plugin_name: Plugin name for for the upload form.
            custom_plugin_file: Path to custom plugin.
            collection: Collection to upload the plugin to. Defaults to
                "dioptra_custom".

        Returns:
            The Dioptra REST api's response.

            Example::

                {
                    'taskPluginName': 'evaluation',
                    'collection': 'dioptra_custom',
                    'modules': [
                        'tensorflow.py',
                        'import_keras.py',
                        '__init__.py'
                    ]
                }

        Notes:
            See https://pages.nist.gov/dioptra/user-guide/api-reference-restapi.html
            for more information on Dioptra's REST api.
        """
        plugin_upload_form = {
            "taskPluginName": custom_plugin_name,
            "collection": collection,
        }

        custom_plugin_file = Path(custom_plugin_file)

        with custom_plugin_file.open("rb") as f:
            custom_plugin_file_dict = {"taskPluginFile": (custom_plugin_file.name, f)}
            response = requests.post(
                self.task_plugin_endpoint,
                data=plugin_upload_form,
                files=custom_plugin_file_dict,
            )

        return cast(dict[str, Any], response.json())
