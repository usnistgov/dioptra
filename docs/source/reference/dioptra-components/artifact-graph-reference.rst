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

The artifact graph allows you to capture outputs from the task graph as :ref:`Artifacts <explanation-artifacts>`.

For example, if we have a task graph that loads a dataset, uses it to train a model, and runs inference on a test set:

.. code:: yaml

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

Then, we may want to capture the model and the predictions as artifacts with the following artifact graph:

.. code:: yaml

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

* The top level field names define the artifact names (``saved_predictions`` and ``saved_model``). Note that the name provided here is passed as the name parameter to the ``serialize()`` function of the artifact task. See the :ref:`artifact reference <reference-artifacts>` for more details. 
* The value of the ``contents`` field corresponds to a step name in the task graph (``predictions`` and ``trained_model``) and denotes which outputs should be saved in the artifact.
* The value of the ``task`` field specifies the :ref:`Artifact Task <explanation-artifacts-artifact-tasks>` which defines how the artifact is serialized and deserialized.
  
    - The ``name`` field is the artifact task name (``DataFrameArtifactTask`` and ``ModelArtifactTask``)
    - The ``args`` field allows addtional keyword arguments to be passed to the function. In this example, the ``format`` argument is used to specify the output format of the dataframe.

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`Artifacts Reference <reference-artifacts>`
* :ref:`Task Graph Explanation <explanation-task-graph>`
* :ref:`What are Artifacts? <explanation-artifacts>`
* :ref:`What are Plugins? <explanation-plugins>`
* :ref:`How to create a plugin <how-to-create-plugins>`
