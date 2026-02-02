.. This Software (Dioptra) is being made available as a public service by theExpand commentComment on line R1Resolved
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

.. _reference-artifact-graph:

Artifact Graph
==============

Artifact outputs allow you to designate the contents of a variable as an :ref:`artifact <explanation-artifacts>`.

The ``artifacts`` section contains a list of artifact names. In the graph below, two artifact outputs are defined - ``saved_model`` and 
``saved_predictions``. 

.. note:: 
    
    When using the UI, the ``artifacts`` section will be separate from the ``graph`` section, and there is no 
    need to use either keyword. However, when using the python client, a single file is assumed and both of
    these keywords are necessary.


.. code:: yaml

    artifacts:
        saved_predictions:
            contents: $predictions
            task:
                name: DataframeArtifactTask
                args:
                    format: csv
        saved_model:
            contents: $trained_model
            task:
                name: ModelArtifactTask

    graph:
        dataset:
            load_from_disk:
                location: $location

        trained_model:
            train:
                architecture: le_net
                dataset: $dataset.training

        predictions:
            predict:
                model: $train
                dataset: $dataset.testing


The ``task`` section of each artifact references the artifact task which should be used to serialize and deserialize the artifact.

Below is an example artifact task which serializes dataframes. 

* The input to the ``name`` parameter in ``serialize()`` for the above YAML will be ``saved_predictions``. 
* The input to the ``contents`` parameter will be the value stored in ``$predictions`` (the output of the ``predict`` task plugin).
* Any additional arguments provided under the ``args`` keyword will be passed to the function. In this example, the ``format`` argument is used to specify the output format of the dataframe.

When used in another entrypoint, the deserialize function is called with the location of the artifact to turn the file back into a Python object of the specified type.

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


.. rst-class:: fancy-header header-seealso

See Also 
---------
   
* :ref:`Task Graph Explanation <explanation-task-graph>`
* :ref:`What are Artifacts? <explanation-artifacts>`
* :ref:`What are Plugins? <explanation-plugins>` 
* :ref:`How to create a plugin <how-to-create-plugins>`