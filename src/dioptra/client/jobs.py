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
from typing import Any, ClassVar, Final, TypeVar

from .base import CollectionClient, DioptraSession
from .snapshots import SnapshotsSubCollectionClient
from .tags import TagsSubCollectionClient

METRICS: Final[str] = "metrics"
MLFLOW_RUN: Final[str] = "mlflowRun"
SNAPSHOTS: Final[str] = "snapshots"
STATUS: Final[str] = "status"
PARAMETERS: Final[str] = "parameters"
ARTIFACT_PARAMETERS: Final[str] = "artifactParameters"

T = TypeVar("T")


class JobsCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /jobs collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "jobs"

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the JobsCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)
        self._snapshots = SnapshotsSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._tags = TagsSubCollectionClient[T](session=session, root_collection=self)

    @property
    def snapshots(self) -> SnapshotsSubCollectionClient[T]:
        """The client for retrieving job resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the job snapshots sub-collection. Below are examples of how HTTP
        requests to this sub-collection translate into method calls for an active Python
        Dioptra Python client called ``client``::

            # GET /api/v1/jobs/1/snapshots
            client.jobs.snapshots.get(1)

            # GET /api/v1/jobs/1/snapshots/2
            client.jobs.snapshots.get_by_id(1, snapshot_id=2)
        """
        return self._snapshots

    @property
    def tags(self) -> TagsSubCollectionClient[T]:
        """
        The client for managing the tags sub-collection owned by the /jobs
        collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the tags sub-collection. Below are examples of how HTTP requests to
        this sub-collection translate into method calls for an active Python Dioptra
        Python client called ``client``::

            # GET /api/v1/jobs/1/tags
            client.jobs.tags.get(1)

            # PUT /api/v1/jobs/1/tags
            client.jobs.tags.modify(1, ids=[2, 3])

            # POST /api/v1/jobs/1/tags
            client.jobs.tags.append(1, ids=[2, 3])

            # DELETE /api/v1/jobs/1/tags/3
            client.jobs.tags.remove(1, tag_id=3)

            # DELETE /api/v1/jobs/1/tags
            client.jobs.tags.remove(1)
        """
        return self._tags

    def get(
        self,
        group_id: int | None = None,
        index: int = 0,
        page_length: int = 10,
        sort_by: str | None = None,
        descending: bool | None = None,
        search: str | None = None,
    ) -> T:
        """Get a list of jobs.

        Args:
            group_id: The group id the jobs belong to. If None, return
                jobs from all groups that the user has access to. Optional,
                defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of jobs to return in the paged
                response. Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for jobs using the Dioptra API's query language. Optional,
                defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        params: dict[str, Any] = {
            "index": index,
            "pageLength": page_length,
        }

        if sort_by is not None:
            params["sortBy"] = sort_by

        if descending is not None:
            params["descending"] = descending

        if search is not None:
            params["search"] = search

        if group_id is not None:
            params["groupId"] = group_id

        return self._session.get(
            self.url,
            params=params,
        )

    def get_by_id(self, job_id: str | int) -> T:
        """Get the job matching the provided id.

        Args:
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(job_id))

    def delete_by_id(self, job_id: str | int) -> T:
        """Delete the job matching the provided id.

        Args:
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, str(job_id))

    def get_mlflow_run_id(self, job_id: str | int) -> T:
        """Gets the MLflow run id for a job.

        Args:
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(job_id), MLFLOW_RUN)

    def set_mlflow_run_id(self, job_id: str | int, mlflow_run_id: str) -> T:
        """Sets the MLflow run id for a job.

        Args:
            job_id: The job id, an integer.
            mlflow_run_id: The UUID as a string for the associated MLflow run.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {
            "mlflowRunId": mlflow_run_id,
        }

        return self._session.post(self.url, str(job_id), MLFLOW_RUN, json_=json_)

    def get_parameters(self, job_id: str | int) -> T:
        """Gets the parameters for a job.

        Args:
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(job_id), PARAMETERS)

    def get_artifact_parameters(self, job_id: str | int) -> T:
        """Gets the artifact parameters for a job.

        Args:
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(job_id), ARTIFACT_PARAMETERS)

    def get_status(self, job_id: str | int) -> T:
        """Gets the status for a job.

        Args:
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(job_id), STATUS)

    def get_metrics_by_id(self, job_id: str | int) -> T:
        """Gets all the latest metrics for a job.

        Args:
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(job_id), METRICS)

    def append_metric_by_id(
        self,
        job_id: str | int,
        metric_name: str,
        metric_value: float,
        metric_step: int | None = None,
    ) -> T:
        """Posts a new metric to a job.

        Args:
            job_id: The job id, an integer.
            metric_name: The name of the metric.
            metric_value: The value of the metric.
            metric_step: The step number of the metric, optional.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {
            "name": metric_name,
            "value": metric_value,
        }

        if metric_step is not None:
            json_["step"] = metric_step

        return self._session.post(self.url, str(job_id), METRICS, json_=json_)

    def get_metrics_snapshots_by_id(
        self,
        job_id: str | int,
        metric_name: str | int,
        index: int = 0,
        page_length: int = 10,
    ) -> T:
        """Gets the metric history for a job with a specific metric name.

        Args:
            job_id: The job id, an integer.
            metric_name: The name of the metric.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of metrics to return in the paged
                response. Optional, defaults to 10.
        Returns:
            The response from the Dioptra API.
        """
        params: dict[str, Any] = {
            "index": index,
            "pageLength": page_length,
        }
        return self._session.get(
            self.url, str(job_id), METRICS, metric_name, SNAPSHOTS, params=params
        )
