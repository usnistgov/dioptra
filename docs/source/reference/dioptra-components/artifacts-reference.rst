.. This Software (Dioptra) is being made available as a public service by the
.. National Institute of Standards and Technology (NIST), an Agency of the United
.. States Department of Commerce. This software was developed in part by employees of
.. NIST and in part by NIST contractors. Copyright in portions of this software that
.. were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
.. to Title 17 United States Code Section 105, works of NIST employees are not
.. subject to copyright protection in the United States. However, NIST may hold
.. international copyright in software created by its employees and domestic
.. copyright (or licensing rights) in portions of software that were assigned or
.. licensed to NIST. To the extent that NIST holds copyright in this software, it is
.. being made available under the Creative Commons Attribution 4.0 International
.. license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
.. of the software developed or licensed by NIST.
..
.. ACCESS THE FULL CC BY 4.0 LICENSE HERE:
.. https://creativecommons.org/licenses/by/4.0/legalcode

.. _reference-artifacts:

Artifacts
=================

.. contents:: Contents
   :local:
   :depth: 2

.. _reference-artifacts-definition:

Artifact Definition
---------------------

An **artifact** in Dioptra is a resource which represents a stored output of a job. 

Artifact Tasks
~~~~~~~~~~~~~~

An artifact must have an artifact task associated with it, which implements the ``ArtifactTaskInterface``. 

Below is an example of an artifact task. 

.. code:: python

    class DataframeArtifactTask(ArtifactTaskInterface):
        @staticmethod
        def serialize(
            working_dir: Path,
            name: str,
            contents: pd.DataFrame,
            format: str = "json",
            **kwargs,
        ) -> Path:
            ...

        @staticmethod
        def deserialize(working_dir: Path, path: str, **kwargs) -> pd.DataFrame:
            ...

        @staticmethod
        def validation() -> dict[str, Any]:
            ...

* The ``serialize()`` function is used to store the output of function tasks within an entrypoint. 
* Similarly the ``deserialize()`` function is used to load artifacts when they are provided as an artifact parameter to an entrypoint. 
* The ``validation()`` function should provide a schema for validating any additional keyword arguments to the ``serialize()`` function. The validation function provides a specification of this usage:

   .. automethod:: dioptra.sdk.api.artifact.ArtifactTaskInterface.validation

.. _reference-artifacts-attributes:

Artifact Attributes
---------------------

- **Task**: (integer ID) The Artifact Task associated with the Artifact. The associated task will be used for serialization and deserialization.
- **Group**: (integer ID) The Group that owns this Artifact and controls access permissions.
- **Plugin Snapshot**: (integer ID) The Plugin Snapshot which contains the artifact task. The artifact is associated with a snapshot, and so even if the plugin changes, the artifact will still be loadable using the snapshot.
- **Artifact URI**: (string) The URI representing the artifact's location.
- **Job**: (integer ID) The job the artifact should be associated with.

Optional Attributes
~~~~~~~~~~~~~~~~~~~

- **Description**: (string, optional) A text description of the Artifact's purpose or contents. Defaults to empty.

.. _reference-artifacts-system-generated-attributes:

System-Generated Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **ID**: Unique identifier assigned upon creation.
- **Created On**: Timestamp indicating when the Artifact was created.
- **Last Modified On**: Timestamp indicating when the Artifact was last modified.
- **File Size**: The size of the artifact.
- **Is Directory**: Whether the artifact is a directory.
- **File URL**: A link for downloading the artifact.

.. _reference-artifacts-retrieval-interfaces:

Retrieval Interfaces
--------------------

Artifacts can be retrieved via the Python Client or the RESTAPI. Alternatively, the :ref:`Job Dashboard <how-to-logging-metrics>` 
page of the UI has an Output Artifacts page where artifacts associated with a specific job can be viewed or downloaded.

.. _reference-artifacts-retrieval-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Retrieve a list of artifact resources**

   .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.get

**Retrieve an artifact using its ID**

   .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.get_by_id

**Retrieve the file listing associated with an artifact using its ID**

   .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.get_files

**Retrieve the contents of an artifact using its ID**

   .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.get_contents

.. _reference-artifacts-retrieval-rest-api:

Using REST API
~~~~~~~~~~~~~~


**Get a list of Artifacts**

See the :http:get:`GET /api/v1/artifacts </api/v1/artifacts/>` endpoint documentation for payload requirements.

**Download the contents of an Artifact**

See the :http:get:`GET /api/v1/artifacts/{int:id}/contents </api/v1/artifacts/{int:id}/contents>` endpoint documentation for payload requirements.

**Get a list of all files associated with an Artifact**

See the :http:get:`GET /api/v1/artifacts/{int:id}/files </api/v1/artifacts/{int:id}/files>` endpoint documentation for payload requirements.


Registration Interfaces
-----------------------

Artifacts are typically created automatically as an output of a job, through the use of the :ref:`Artifact Graph <reference-artifact-graph>` section of an entrypoint.
They can also be created via the Python Client or the RESTAPI.

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Create an Artifact**

   .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.create


Using REST API
~~~~~~~~~~~~~~

Artifacts can be created directly via the HTTP API.

**Create an Artifact**

See the :http:post:`POST /api/v1/artifacts </api/v1/artifacts/>` endpoint documentation for payload requirements.


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Artifact Graph <reference-artifact-graph>`
* :ref:`Entrypoints <reference-entrypoints>`
* :ref:`Plugins <reference-plugins>`
