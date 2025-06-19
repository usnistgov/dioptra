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

from .base import (
    CollectionClient,
    DioptraClientError,
    DioptraSession,
    SubCollectionClient,
)
from .drafts import (
    ModifyResourceDraftsSubCollectionClient,
    NewResourceDraftsSubCollectionClient,
    make_draft_fields_validator,
)
from .snapshots import SnapshotsSubCollectionClient
from .tags import TagsSubCollectionClient

ARTIFACTS: Final[str] = "artifacts"
METRICS: Final[str] = "metrics"
MLFLOW_RUN: Final[str] = "mlflowRun"
STATUS: Final[str] = "status"

DRAFT_FIELDS: Final[set[str]] = {"name", "description", "entrypoints"}

T = TypeVar("T")


class ExperimentEntrypointsSubCollectionClient(SubCollectionClient[T]):
    """The client for managing Dioptra's /experiments/{id}/entrypoints sub-collection.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str] = "entrypoints"

    def __init__(
        self,
        session: DioptraSession[T],
        root_collection: CollectionClient[T],
        parent_sub_collections: list["SubCollectionClient[T]"] | None = None,
    ) -> None:
        """Initialize the ExperimentEntrypointsSubCollectionClient instance.

        Args:
            session: The Dioptra API session object.
            root_collection: The client for the root collection that owns this
                sub-collection.
            parent_sub_collections: Unused in this client, must be None.
        """
        if parent_sub_collections is not None:
            raise DioptraClientError(
                "The parent_sub_collections argument must be None for this client."
            )

        super().__init__(
            session=session,
            root_collection=root_collection,
            parent_sub_collections=parent_sub_collections,
        )

    def get(self, experiment_id: int | str) -> T:
        """Get a list of entrypoints added to the experiment.

        Args:
            experiment_id: The experiment id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.build_sub_collection_url(experiment_id))

    def create(
        self,
        experiment_id: str | int,
        entrypoint_ids: list[int],
    ) -> T:
        """Adds one or more entrypoints to the experiment.

        If an entrypoint id matches an entrypoint that is already attached to the
        experiment, then the experiment will update the entrypoint to the latest
        version.

        Args:
            experiment_id: The experiment id, an integer.
            entrypoint_ids: A list of entrypoint ids that will be registered to the
                experiment.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"ids": entrypoint_ids}
        return self._session.post(
            self.build_sub_collection_url(experiment_id), json_=json_
        )

    def delete(self, experiment_id: str | int) -> T:
        """Remove all entrypoints from the experiment.

        Args:
            experiment_id: The experiment id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.build_sub_collection_url(experiment_id))

    def modify_by_id(
        self,
        experiment_id: str | int,
        entrypoint_ids: list[int],
    ) -> T:
        """Replaces the experiment's full list of entrypoints.

        If an entrypoint id matches an entrypoint that is already attached to the
        experiment, then the experiment will update the entrypoint to the latest
        version. If an empty list is provided, then all entrypoints will be removed from
        the experiment.

        Args:
            experiment_id: The experiment id, an integer.
            entrypoint_ids: A list of entrypoint ids that will replace the current list
                of experiment entrypoints.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"ids": entrypoint_ids}
        return self._session.put(
            self.build_sub_collection_url(experiment_id), json_=json_
        )

    def delete_by_id(self, experiment_id: str | int, entrypoint_id: str | int) -> T:
        """Remove an entrypoint from the experiment.

        Args:
            experiment_id: The experiment id, an integer.
            entrypoint_id: The id for the entrypoint that will be removed.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(
            self.build_sub_collection_url(experiment_id), str(entrypoint_id)
        )


class ExperimentJobsSubCollectionClient(SubCollectionClient[T]):
    """The client for managing Dioptra's /experiments/{id}/jobs sub-collection.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str] = "jobs"

    def __init__(
        self,
        session: DioptraSession[T],
        root_collection: CollectionClient[T],
        parent_sub_collections: list["SubCollectionClient[T]"] | None = None,
    ) -> None:
        """Initialize the ExperimentJobsSubCollectionClient instance.

        Args:
            session: The Dioptra API session object.
            root_collection: The client for the root collection that owns this
                sub-collection.
            parent_sub_collections: Unused in this client, must be None.
        """
        if parent_sub_collections is not None:
            raise DioptraClientError(
                "The parent_sub_collections argument must be None for this client."
            )

        super().__init__(
            session=session,
            root_collection=root_collection,
            parent_sub_collections=parent_sub_collections,
        )

    def get(
        self,
        experiment_id: str | int,
        index: int = 0,
        page_length: int = 10,
        sort_by: str | None = None,
        descending: bool | None = None,
        search: str | None = None,
    ) -> T:
        """Get an experiment's jobs.

        Args:
            experiment_id: The experiment id, an integer.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of jobs to return in the paged
                response. Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for models using the Dioptra API's query language. Optional,
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

        return self._session.get(
            self.build_sub_collection_url(experiment_id), params=params
        )

    def get_by_id(self, experiment_id: str | int, job_id: str | int) -> T:
        """Get a specific job from an experiment.

        Args:
            experiment_id: The experiment id, an integer.
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(
            self.build_sub_collection_url(experiment_id),
            str(job_id),
        )

    def create(
        self,
        experiment_id: str | int,
        entrypoint_id: int,
        queue_id: int,
        entrypoint_snapshot_id: int | None = None,
        values: dict[str, Any] | None = None,
        timeout: str | None = None,
        description: str | None = None,
    ) -> T:
        """Creates a job for an experiment.

        Args:
            experiment_id: The experiment id, an integer.
            entrypoint_id: The id for the entrypoint that the job will run.
            queue_id: The id for the queue that will execute the job.
            entrypoint_snapshot_id: The id for a snapshot associated with the
                entrypoint. If specified, the snapshotted version of the entrypoint will
                be used to run the job. If not specified, the job will use the latest
                version of the entrypoint. Defaults to None.
            values: A dictionary of keyword arguments to pass to the entrypoint that
                parameterize the job.
            timeout: The maximum alloted time for a job before it times out and is
                stopped. If omitted, the job timeout will use the default set in the
                API.
            description: The description for the job. Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {"entrypoint": entrypoint_id, "queue": queue_id}

        if entrypoint_snapshot_id is not None:
            json_["entrypointSnapshot"] = entrypoint_snapshot_id

        if values is not None:
            json_["values"] = values

        if timeout is not None:
            json_["timeout"] = timeout

        if description is not None:
            json_["description"] = description

        return self._session.post(
            self.build_sub_collection_url(experiment_id), json_=json_
        )

    def delete_by_id(self, experiment_id: str | int, job_id: str | int) -> T:
        """Delete a job from the experiment.

        Args:
            experiment_id: The experiment id, an integer.
            job_id: The id for the job that will be deleted.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(
            self.build_sub_collection_url(experiment_id), str(job_id)
        )

    def create_artifact(
        self,
        experiment_id: str | int,
        job_id: str | int,
        uri: str,
        description: str | None = None,
    ) -> T:
        """Creates a job artifact for an experiment.

        Args:
            experiment_id: The experiment id, an integer.
            job_id: The id of the job that produced this artifact.
            uri: The URI pointing to the location of the artifact.
            description: The description of the new artifact. Optional, defaults to
                None.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"uri": uri}

        if description is not None:
            json_["description"] = description

        return self._session.post(
            self.build_sub_collection_url(experiment_id),
            str(job_id),
            ARTIFACTS,
            json_=json_,
        )

    def get_mlflow_run_id(self, experiment_id: str | int, job_id: str | int) -> T:
        """Gets the MLflow run id for an experiment's job.

        Args:
            experiment_id: The experiment id, an integer.
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(
            self.build_sub_collection_url(experiment_id), str(job_id), MLFLOW_RUN
        )

    def set_mlflow_run_id(
        self, experiment_id: str | int, job_id: str | int, mlflow_run_id: str
    ) -> T:
        """Sets the MLflow run id for an experiment's job.

        Args:
            experiment_id: The experiment id, an integer.
            job_id: The job id, an integer.
            mlflow_run_id: The UUid as a string for the associated MLflow run.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {
            "mlflowRunId": mlflow_run_id,
        }
        return self._session.post(
            self.build_sub_collection_url(experiment_id),
            str(job_id),
            MLFLOW_RUN,
            json_=json_,
        )

    def get_status(self, experiment_id: str | int, job_id: str | int) -> T:
        """Gets the status for an experiment's job.

        Args:
            experiment_id: The experiment id, an integer.
            job_id: The job id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(
            self.build_sub_collection_url(experiment_id), str(job_id), STATUS
        )

    def set_status(self, experiment_id: str | int, job_id: str | int, status: str) -> T:
        """Sets the status for an experiment's job.

        Args:
            experiment_id: The experiment id, an integer.
            job_id: The job id, an integer.
            status: The new status for the job. The allowed values are: queued, started,
                deferred, finished, failed.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"status": status}
        return self._session.put(
            self.build_sub_collection_url(experiment_id),
            str(job_id),
            STATUS,
            json_=json_,
        )


class ExperimentsCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /experiments collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "experiments"

    def __init__(self, session: DioptraSession[T]) -> None:
        """Initialize the ExperimentsCollectionClient instance.

        Args:
            session: The Dioptra API session object.
        """
        super().__init__(session)
        self._entrypoints = ExperimentEntrypointsSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._jobs = ExperimentJobsSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._new_resource_drafts = NewResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
        )
        self._modify_resource_drafts = ModifyResourceDraftsSubCollectionClient[T](
            session=session,
            validate_fields_fn=make_draft_fields_validator(
                draft_fields=DRAFT_FIELDS,
                resource_name=self.name,
            ),
            root_collection=self,
        )
        self._snapshots = SnapshotsSubCollectionClient[T](
            session=session, root_collection=self
        )
        self._tags = TagsSubCollectionClient[T](session=session, root_collection=self)

    @property
    def entrypoints(self) -> ExperimentEntrypointsSubCollectionClient[T]:
        """The client for managing the entrypoints sub-collection."""
        return self._entrypoints

    @property
    def jobs(self) -> ExperimentJobsSubCollectionClient[T]:
        """The client for managing the jobs sub-collection."""
        return self._jobs

    @property
    def new_resource_drafts(self) -> NewResourceDraftsSubCollectionClient[T]:
        """The client for managing the new experiment drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the new experiment drafts sub-collection. Below are examples of how
        HTTP requests to this sub-collection translate into method calls for an active
        Python Dioptra Python client called ``client``::

            # GET /api/v1/experiments/drafts
            client.experiments.new_resource_drafts.get()

            # GET /api/v1/experiments/drafts/1
            client.experiments.new_resource_drafts.get_by_id(draft_id=1)

            # PUT /api/v1/experiments/drafts/1
            client.experiments.new_resource_drafts.modify(
                draft_id=1, name="new-name", description="new-description"
            )

            # POST /api/v1/experiments/drafts
            client.experiments.new_resource_drafts.create(
                group_id=1, name="name", description="description"
            )

            # DELETE /api/v1/experiments/drafts/1
            client.experiments.new_resource_drafts.delete(draft_id=1)
        """
        return self._new_resource_drafts

    @property
    def modify_resource_drafts(self) -> ModifyResourceDraftsSubCollectionClient[T]:
        """The client for managing the experiment modification drafts sub-collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the experiment modification drafts sub-collection. Below are examples
        of how HTTP requests to this sub-collection translate into method calls for an
        active Python Dioptra Python client called ``client``::

            # GET /api/v1/experiments/1/draft
            client.experiments.modify_resource_drafts.get_by_id(1)

            # PUT /api/v1/experiments/1/draft
            client.experiments.modify_resource_drafts.modify(
                1,
                resource_snapshot_id=1,
                name="new-name",
                description="new-description"
            )

            # POST /api/v1/experiments/1/draft
            client.experiments.modify_resource_drafts.create(
                1, name="name", description="description"
            )

            # DELETE /api/v1/experiments/1/draft
            client.experiments.modify_resource_drafts.delete(1)
        """
        return self._modify_resource_drafts

    @property
    def snapshots(self) -> SnapshotsSubCollectionClient[T]:
        """The client for retrieving experiment resource snapshots.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the experiment snapshots sub-collection. Below are examples of how HTTP
        requests to this sub-collection translate into method calls for an active Python
        Dioptra Python client called ``client``::

            # GET /api/v1/experiments/1/snapshots
            client.experiments.snapshots.get(1)

            # GET /api/v1/experiments/1/snapshots/2
            client.experiments.snapshots.get_by_id(1, snapshot_id=2)
        """
        return self._snapshots

    @property
    def tags(self) -> TagsSubCollectionClient[T]:
        """
        The client for managing the tags sub-collection owned by the /experiments
        collection.

        Each client method in the sub-collection accepts an arbitrary number of
        positional arguments called ``*resource_ids``. These are the parent resource ids
        that own the tags sub-collection. Below are examples of how HTTP requests to
        this sub-collection translate into method calls for an active Python Dioptra
        Python client called ``client``::

            # GET /api/v1/experiments/1/tags
            client.experiments.tags.get(1)

            # PUT /api/v1/experiments/1/tags
            client.experiments.tags.modify(1, ids=[2, 3])

            # POST /api/v1/experiments/1/tags
            client.experiments.tags.append(1, ids=[2, 3])

            # DELETE /api/v1/experiments/1/tags/3
            client.experiments.tags.remove(1, tag_id=3)

            # DELETE /api/v1/experiments/1/tags
            client.experiments.tags.remove(1)
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
        """Get a list of experiments.

        Args:
            group_id: The group id the experiments belong to. If None, return
                experiments from all groups that the user has access to. Optional,
                defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of experiments to return in the paged
                response. Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for experiments using the Dioptra API's query language.
                Optional, defaults to None.

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

    def get_by_id(self, experiment_id: str | int) -> T:
        """Get the experiment matching the provided id.

        Args:
            experiment_id: The experiment id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(experiment_id))

    def create(
        self,
        group_id: int,
        name: str,
        description: str | None = None,
        entrypoints: list[int] | None = None,
    ) -> T:
        """Creates an experiment.

        Args:
            group_id: The id of the group that will own the experiment.
            name: The name of the new experiment.
            description: The description of the new experiment. Optional, defaults to
                None.
            entrypoints: A list of entrypoint ids to associate with the new experiment.
                Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {
            "group": group_id,
            "name": name,
        }

        if description is not None:
            json_["description"] = description

        if entrypoints is not None:
            json_["entrypoints"] = entrypoints

        return self._session.post(self.url, json_=json_)

    def modify_by_id(
        self,
        experiment_id: str | int,
        name: str,
        description: str | None,
        entrypoints: list[int] | None,
    ) -> T:
        """Modify the experiment matching the provided id.

        Args:
            experiment_id: The experiment id, an integer.
            name: The new name of the experiment.
            description: The new description of the experiment. To remove the
                description, pass None.
            entrypoints: A new list of entrypoint ids to associate with the experiment.
                To remove all associated entrypoints, pass an empty list or None.

        Returns:
            The response from the Dioptra API.
        """
        json_: dict[str, Any] = {"name": name}

        if description is not None:
            json_["description"] = description

        if entrypoints is not None:
            json_["entrypoints"] = entrypoints

        return self._session.put(self.url, str(experiment_id), json_=json_)

    def delete_by_id(self, experiment_id: str | int) -> T:
        """Delete the experiment matching the provided id.

        Args:
            experiment_id: The experiment id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, str(experiment_id))

    def get_metrics_by_id(
        self,
        experiment_id: str | int,
        index: int = 0,
        page_length: int = 10,
        sort_by: str | None = None,
        descending: bool | None = None,
        search: str | None = None,
    ) -> T:
        """Get the metrics for the jobs in this experiment.

        Args:
            experiment_id: The experiment id, an integer.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of experiments to return in the paged
                response. Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for jobs using the Dioptra API's query language.
                Optional, defaults to None.

        Returns:
            The response from the Dioptra API.
        """

        params: dict[str, Any] = {
            "experiment_id": experiment_id,
            "index": index,
            "pageLength": page_length,
        }

        if sort_by is not None:
            params["sortBy"] = sort_by

        if descending is not None:
            params["descending"] = descending

        if search is not None:
            params["search"] = search

        return self._session.get(self.url, str(experiment_id), METRICS, params=params)
