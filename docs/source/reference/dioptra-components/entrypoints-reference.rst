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

.. _reference-entrypoints:

Entrypoints
===========


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-entrypoints-definition:

Entrypoint Definition
---------------------

An **Entrypoint** in Dioptra is a repeatable workflow that can be executed as a Job. Entrypoints execute the function tasks defined in the Task Graph upon job submission. 
Entrypoint parameters and Artifact Input Parameters can optionally be attached to entrypoints and then used in the Task Graphs. The outputs from Function Tasks 
can be saved as Artifacts, and the logic for this is defined in the Artifact Output Graph. 

.. _reference-entrypoints-attributes:


Entrypoint Attributes
---------------------

This section describes the attributes that define an Entrypoint.

.. _reference-entrypoints-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

- **Name**: (string) The display name for the Entrypoint. 
- **Group**: (integer ID) The Group that owns this Experiment and controls access permissions.
- **Task Graph**: (YAML string) The Task Graph for the entrypoint, which is a YAML-formatted string that defines the core workflow (technically, a Directed Acyclic Graph, or DAG). Composed of function task invocations and their input arguments. (See: :ref:`Task Graph Syntax Requirements <reference-entrypoints-task-graph-syntax>`)

.. _reference-entrypoints-optional-attributes:

Optional Attributes
~~~~~~~~~~~~~~~~~~~

- **Description**: (string, optional) A text description of the Entrypoint's purpose or scope. Defaults to empty.
- **Plugins**: (list of Plugin IDs, optional) A list of Plugin containers to attach to the entrypoint - the associated Plugin Function Tasks are then made available to the Entrypoint Task Graph. Defaults to empty. (See: :ref:`Plugins Reference <reference-plugins>`)
- **Artifact Plugins**:  (list of Plugin IDs, optional) A list of Plugin containers to attach to the entrypoint - the associated Plugin Artifact Tasks are then made available to the Artifact Output Graph. Defaults to empty. (See: :ref:`Plugins Reference <reference-plugins>`)
- **Parameters**: (list of Dicts, optional) Global parameters that can be used in the Entrypoint Task Graph and Artifact Output Graph. Each Parameter has a type and can optionally have a default value. Parameter values are set at Job runtime. Defaults to empty.
    - **Name** (string) The Name of the Entrypoint Parameter, used to access the Parameter in the Task Graphs 
    - **Type** (Plugin Parameter Type ID) The type for the parameter, used for type validation. (See: :ref:`Plugin Parameter Types <reference-parameter-types>`) 
    - **Default Value** (String, Optional) An optional default value for the parameter which can be overwritten during job execution. Gets type converted during job execution time. 
- **Artifact Parameters**: (list of Dicts, optional) Global objects, loaded from disk at Job execution, can be used in the Entrypoint Task Graph and Artifact Output Graph. User selects which specific artifact snapshot to load into the Artifact Parameter at Job Runtime. Defaults to empty.
    - **Name** (string) The Name of the Artifact Parameter, used to access the Object(s) in the Task Graphs 
    - **Output Parameters** (List of Outputs) List of outputs that the deserialize method of an artifact task is expected to produce
- **Artifact Output Graph**: (YAML string, optional) A YAML-formatted string that defines the artifact serialization logic. Artifact Tasks referenced in the Artifact Output Graph are called once the main Task Graph execution is completed. Defaults to empty. (See: :ref:`Artifact Output Graph Syntax Requirements <reference-entrypoints-artifact-output-graph-syntax>`)
- **Queues**: (list of integer IDs, optional) A list of the queues that can pick up Job submissions of this entrypoint and carry out their execution. Job will not be runnable without at least one attached Queue. Defaults to empty. (See: :ref:`Queues Reference <reference-queues>`)
- **Tags**: (list of Tag Objects, optional) A list of tags for organizational purposes. 

.. _reference-entrypoints-system-generated-attributes:

System-Managed State
~~~~~~~~~~~~~~~~~~~~

- **ID**: (integer) Unique identifier assigned upon creation.
- **Last Modified On**: (timestamp) The time when the Entrypoint was last modified. If any entrypoint has not yet been modified, then this equals the timestamp when the entrypoint was originally created. Upon modification, the old configuration is saved as a Snapshot and added to the Version History. 
- **Version History**: (list of Snapshot Objects, optional) An ordered list of past Entrypoint Snapshots, automatically created by Dioptra each time the Entrypoint is modified. View prior snapshots by clicking the **Show History** toggle. Contains the following attributes:
    - **Created On**: (timestamp) When the Entrypoint state was saved as a snapshot . 
    - *Every other required and optional attribute listed above*



.. _reference-entrypoints-task-graph-syntax:

Task Graph Syntax
------------------

The Task Graph consists of a list of step descriptions. Each step corresponds to the execution of a function task.
The Task Graph is defined in YAML, and each function task can be invoked using one of three invocation styles:

- :ref:`Positional Invocation Style <reference-entrypoints-task-graph-syntax-positional-style-invocation>`
- :ref:`Keyword Invocation Style  <reference-entrypoints-task-graph-syntax-keyword-style-invocation>`
- :ref:`Mixed Invocation Style  <reference-entrypoints-task-graph-syntax-mixed-style-invocation>`


There are similarities across all three invocation styles:

    * **Step Names**: ``taskGraphStep1`` and ``taskGraphStep2`` refer to the names of steps, and also to the *location in which the output of that step is stored*. The variable ``$taskGraphStep1`` contains the output of the task that was run in that step.

    * **Task Names**: ``task1`` and ``task2`` refer to the registered names of plugin function tasks (and also the name of the corresponding Python functions). Each step in the graph represents an invocation of a function task.

    * **Arguments for Function Tasks**: ``arg1``, ``arg2``, ``arg3``, and ``arg4`` are arguments provided to the function tasks.

    * **Argument Names for Function Tasks**: ``keyword1``, ``keyword2``, ``keyword3``, and ``keyword4`` are the parameter names for that particular function. These names are defined at task registration time.


.. _reference-entrypoints-example-task-graph-model-training:

Example Task Graph: Model Training
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following hypothetical task graph loads a dataset from disk, trains a model on that dataset, and then makes predictions on a test dataset:

.. tabs::

   .. tab:: Positional Invocation Style

        .. admonition:: Model Training - Positional Style Invocation
            :class: code-panel yaml

            .. code-block:: yaml

                dataset:
                    load_from_disk: [$location] # Referencing an entrypoint parameter

                trained_model:
                    train: [le_net, $dataset.training] # Using the output from the first step

                predictions:
                    predict: [$train, $dataset.testing]

   .. tab:: Keyword Invocation Style

        .. admonition:: Model Training - Keyword Invocation Style
            :class: code-panel yaml

            .. code-block:: yaml

                dataset:
                    load_from_disk:
                        location: $location # Referencing an entrypoint parameter

                trained_model:
                    train:
                        architecture: le_net
                        dataset: $dataset.training # Using the output from the first step

                predictions:
                    predict:
                        model: $train
                        dataset: $dataset.testing

   .. tab:: Mixed Invocation Style

        .. admonition:: Model Training - Mixed Invocation Style
            :class: code-panel yaml

            .. code-block:: yaml

                dataset:
                    task: load_from_disk 
                    args: [$location] # Referencing an entrypoint parameter

                trained_model:
                    task: train
                    args: [le_net] 
                    kwargs:
                        dataset: $dataset.training # Using the output from the first step

                predictions:
                    task: predict
                    kwargs:
                        model: $train
                        dataset: $dataset.testing

Continue reading below to understand all the details in this example. 

Invocation Styles
~~~~~~~~~~~~~~~~~

.. _reference-entrypoints-task-graph-syntax-positional-style-invocation:

**Positional Style Invocation**

All task arguments are passed in as positional arguments. These positional arguments are assumed to correspond to the ordering of plugin input parameters for the task. Upon task execution, 
these arguments are passed into the Python function without names in order. 

.. margin::

    .. note::
        
        The ``graph:`` keyword that starts the YAML code blocks below does not need to be included in the Task Graph definition in the Graphical User Interface (GUI). When defining an entire entrypoint via YAML, this word is used to designate the Task Graph section of the file (as distinct from the parameter definitions, the Artifact Output Graph, etc.)

.. margin::
        
    .. important:: 

        If your Plugin Task does not have any input parameters, then you should use :ref:`the mixed style invocation syntax<reference-entrypoints-task-graph-syntax-mixed-style-invocation>`, deleting both of the lines for args and kwargs. 

.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Positional Style Invocation
            :class: code-panel yaml

            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task1: [arg1, arg2]
                    taskGraphStep2:
                        task2: [arg3, arg4]

   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Task Graph - Positional Style Invocation
            :class: code-panel yaml

            .. code-block:: yaml

                taskGraphStep1:
                    task1: [arg1, arg2]
                taskGraphStep2:
                    task2: [arg3, arg4]

.. _reference-entrypoints-task-graph-syntax-keyword-style-invocation:

**Keyword Style Invocation**

The keywords correspond to the names of the Function Task parameters. Upon function execution, these values are passed in as named arguments to the Python function. 


.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Keyword Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task1:
                            keyword1: arg1
                            keyword2: arg2
                    taskGraphStep2:
                        task2:
                            keyword3: arg3
                            keyword4: arg4

   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Task Graph - Keyword Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task1:
                        keyword1: arg1
                        keyword2: arg2
                taskGraphStep2:
                    task2:
                        keyword3: arg3
                        keyword4: arg4

.. _reference-entrypoints-task-graph-syntax-mixed-style-invocation:

**Mixed Style Invocation**

Combines positional arguments with named arguments. The positional arguments are assumed to correspond to the ordering of plugin input parameters for the task, and the 
keyword arguments must match one of the names of the function task arguments that does not correspond to any of those claimed by the positional arguments. Upon task execution, 
the positional arguments are passed into the Python function without names in order, and then the keyword arguments are passed in with their corresponding names. 

.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Mixed Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task: task1
                        args: [posarg1, posarg2]
                        kwargs:
                            keyword1: arg1
                            keyword2: arg2
                    taskGraphStep2:
                        task: task2
                        args: [posarg3, posarg4]
                        kwargs:
                            keyword3: arg3
                            keyword4: arg4

   .. group-tab:: Entrypoint defined in the GUI / Standalone component


        .. admonition:: Task Graph - Mixed Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task: task1
                    args: [posarg1, posarg2]
                    kwargs:
                        keyword1: arg1
                        keyword2: arg2
                taskGraphStep2:
                    task: task2
                    args: [posarg3, posarg4]
                    kwargs:
                        keyword3: arg3
                        keyword4: arg4

The mixed style invocation method can be used to call a **function task that has no inputs**:

.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Mixed Style Invocation With No Inputs
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task: task1 # Assuming task1 has no inputs

   .. group-tab:: Entrypoint defined in the GUI / Standalone component


        .. admonition::  Task Graph - Mixed Style Invocation With No Inputs
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task: task1 # Assuming task1 has no inputs
    
Argument Structure
~~~~~~~~~~~~~~~~~~

Though the above examples provide strings (such as ``arg1`` or ``arg2``) as arguments, it is also fine to use YAML to provide
arguments with structure. For example, a list of strings (in this case ``["arg1", "arg11", "arg111"]``) could be provided
as an argument to the ``keyword1`` parameter as follows:

.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Lists of Arguments
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task1:
                            keyword1: 
                                - arg1
                                - arg11
                                - arg111
                            keyword2: arg2
                    taskGraphStep2:
                        task2:
                            keyword3: arg3
                            keyword4: arg4

   .. group-tab:: Entrypoint defined in the GUI / Standalone component


        .. admonition:: Task Graph - Lists of Arguments
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task1:
                        keyword1: 
                            - arg1
                            - arg11
                            - arg111
                        keyword2: arg2
                taskGraphStep2:
                    task2:
                        keyword3: arg3
                        keyword4: arg4




Alternatively, a mapping (in this case ``{"k1":"arg1", "k2":"arg11", "k3":"arg111"}``) can also be provided 
as an argument to the ``keyword1`` parameter if needed:


.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Mapping Arguments
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task1:
                            keyword1: 
                                - k1: arg1
                                - k2: arg11
                                - k3: arg111
                            keyword2: [arg2, arg22]
                    taskGraphStep2:
                        task2:
                            - keyword3: arg3
                            - keyword4: arg4

   .. group-tab:: Entrypoint defined in the GUI / Standalone component


        .. admonition:: Task Graph - Mapping Arguments
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task1:
                        keyword1: 
                            - k1: arg1
                            - k2: arg11
                            - k3: arg111
                        keyword2: [arg2, arg22]
                taskGraphStep2:
                    task2:
                        - keyword3: arg3
                        - keyword4: arg4




References Within a Task Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned earlier, the output of each function task is stored in a variable designated by the step name. These variables
can be used in other steps.

Here is an example of using the output of a function task.

.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Referencing Task Outputs
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task1: [arg1, arg2]
                    taskGraphStep2:
                        task2: [$taskGraphStep1, arg4]


   .. group-tab:: Entrypoint defined in the GUI / Standalone component


        .. admonition:: Task Graph - Referencing Task Outputs
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task1: [arg1, arg2]
                taskGraphStep2:
                    task2: [$taskGraphStep1, arg4]




This passes the output of the step named ``taskGraphStep1`` as input to the first parameter of the function task named ``task2``.

It is possible for function tasks to have multiple outputs. See :ref:`explanation-plugins` for more details. Each output
is given a name when registered. In an example where ``task1`` is registered to have two separate outputs, ``output1`` and 
``output2``, these can be referenced as follows:

.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Referencing Outputs from Task with Multiple Outputs
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task1: [arg1, arg2]
                    taskGraphStep2:
                        task2: [$taskGraphStep1.output1, $taskGraphStep1.output2]


   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Task Graph - Referencing Outputs from Task with Multiple Outputs
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task1: [arg1, arg2]
                taskGraphStep2:
                    task2: [$taskGraphStep1.output1, $taskGraphStep1.output2]

Task Graph Parameters
~~~~~~~~~~~~~~~~~~~~~

Parameters to the Task Graph are simply variables assumed to be provided by the job at runtime. In the following example, 
``$myparam`` clearly does not reference a step name. As a result, this is a parameter which needs to be provided
at job runtime, either as a default or by the user running the job.

Note that this applies to *both* entrypoint parameters and artifact parameters. From the perspective of the task 
graph, the usage is equivalent, though the parameters are supplied separately at runtime.

See :ref:`explanation-entrypoints` and :ref:`explanation-artifacts` for more details.

.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph - Referencing Entrypoint Parameters
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task1: [arg1, arg2]
                    taskGraphStep2:
                        task2: [$myparam, $taskGraphStep1.output2]


   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Task Graph - Referencing Entrypoint Parameters
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task1: [arg1, arg2]
                taskGraphStep2:
                    task2: [$myparam, $taskGraphStep1.output2]


.. _reference-entrypoints-task-graph-dependencies:

Additional Dependencies - Managing Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Explicit dependencies between steps can be added via the ``dependencies`` keyword. Dependencies between steps are
automatically created when a step uses the output of another step as a parameter, but sometimes a dependency is 
needed without the presence of output. In this example, ``taskGraphStep2`` will always be executed after the completion of ``taskGraphStep1``.

.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Task Graph
            :class: code-panel yaml
            
            .. code-block:: yaml

                graph:
                    taskGraphStep1:
                        task1: [arg1, arg2]
                    taskGraphStep2:
                        task2: [$param1, $param2]
                        dependencies: [taskGraphStep1]


   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Task Graph
            :class: code-panel yaml
            
            .. code-block:: yaml

                taskGraphStep1:
                    task1: [arg1, arg2]
                taskGraphStep2:
                    task2: [$param1, $param2]
                    dependencies: [taskGraphStep1]



.. _reference-entrypoints-artifact-output-graph-syntax:

Artifact Output Graph Syntax
----------------------------

Upon successful completion of the Task Graph within a Job execution, the Artifact Output Graph will then execute (if it is defined) to save any designated Function Task outputs 
as Artifacts. 

There are many similarities between invoking artifact tasks and function tasks:

    * **Step Names**: ``artifactStep1`` and ``artifactStep2`` refer to the names of steps in the artifact graph, similar to how ``taskGraphStep1`` and ``taskGraphStep2`` referred to step names in the Task Graph. 
        * **Note**: The name provided here is passed as the name parameter to the ``serialize()`` function of the artifact task. See the :ref:`artifact reference <reference-artifacts>` for more details. 

    * **Artifact Task Names**: ``artifactHandler1`` and ``artifactHandler2`` refer to the registered names of artifact function tasks (and also the name of the corresponding Python classes). Each step in the graph represents an invocation of the ``serialize()`` method of an artifact handler. 

    * **Arguments for the Artifact Tasks**: ``arg1``, ``arg2`` are arguments provided to the artifact tasks (specifically, the ``serialize`` method)

    * **Argument Names for Artifact Tasks**: ``keyword1``, ``keyword2``  are the parameter names for that particular artifact task. These names are defined at artifact task registration time.



.. _reference-entrypoints-example-artifact-task-graph-saving-a-model-and-a-dataset:

Example Artifact Task Graph: Saving a Model and a Dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Building off the example :ref:`Task Graph <reference-entrypoints-example-task-graph-model-training>` in the previous section, the following hypothetical Artifact Task Graph saves the generated prediction dataframe and trained model to disk using two different Artifact Handlers. 

.. tabs::

   .. tab:: Positional Invocation Style

        .. admonition:: Saving a Model and a Dataset - Positional Style Invocation
            :class: code-panel yaml

            .. code-block:: yaml

                saved_predictions:
                    contents: $predictions # Referencing a step name in the Task Graph
                    task:
                        name: DataframeArtifactTask # The name of the Artifact Handler
                        args: [ csv, false ] # Positional args to be passed to the serialize method
                saved_model:
                    contents: $trained_model
                    task:
                        name: ModelArtifactTask

   .. tab:: Keyword Invocation Style

        .. admonition:: Saving a Model and a Dataset - Keyword Invocation Style
            :class: code-panel yaml

            .. code-block:: yaml

                saved_predictions:
                    contents: $predictions # Referencing a step name in the Task Graph
                    task:
                        name: DataframeArtifactTask # The name of the Artifact Handler
                        kwargs:
                            format: csv       # A keyword arg to be passed to the serialize method
                            save_index: false # A keyword arg to be passed to the serialize method
                saved_model:
                    contents: $trained_model
                    task:
                        name: ModelArtifactTask

   .. tab:: Mixed Invocation Style


        .. admonition:: Saving a Model and a Dataset - Mixed Invocation Style
            :class: code-panel yaml

            .. code-block:: yaml

                saved_predictions:
                    contents: $predictions # Referencing a step name in the Task Graph
                    task:
                        name: DataframeArtifactTask # The name of the Artifact Handler
                        args: [csv] # A positional arg
                        kwargs: 
                            save_index: false # A keyword arg
                saved_model:
                    contents: $trained_model
                    task:
                        name: ModelArtifactTask

Generalized Syntax 
~~~~~~~~~~~~~~~~~~

The syntax below is a generalized version of the Artifact Output Graph syntax in above example: 


.. margin::

    .. note::
        
        The ``artifact_outputs:`` keyword that starts the YAML code blocks below does not need to be included in the Artifact Output Graph definition in the Graphical User Interface (GUI). When defining an entire entrypoint via YAML, this word is used to designate the Artifact Output Graph section of the file (as distinct from the parameter definitions, the Task Graph, etc.)



.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file


        .. admonition:: Artifact Output Graph
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifact_outputs:
                    artifactStep1:
                        contents: $taskGraphStep1.output # assumes name of output from "taskGraphStep1" is "output"
                        task:
                            name: artifactHandler1
                    artifactStep2:
                        contents: $taskGraphStep2 # If function task only has one output, then only step name is required
                        task:
                            name: artifactHandler2


   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Artifact Output Graph
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifactStep1:
                    contents: $taskGraphStep1.output # assumes name of output from "taskGraphStep1" is "output"
                    task:
                        name: artifactHandler1
                artifactStep2:
                    contents: $taskGraphStep2 # If function task only has one output, then only step name is required
                    task:
                        name: artifactHandler2

Invocation Styles 
~~~~~~~~~~~~~~~~~

Some artifact tasks define task inputs to customize the serialization logic (for example, specifying a file format). 
Similar to the Task Graph, the arguments for artifact tasks can be passed in in a variety of ways.
These arguments are used in the ``serialization`` method of the Artifact Handler.


**Positional Style Invocation**


.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file


        .. admonition:: Artifact Output Graph - Positional Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifact_outputs:
                    artifactStep1:
                        contents: $taskGraphStep1.output
                        task:
                            name: artifactHandler1
                            args: [arg1, arg2]

   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Artifact Output Graph - Positional Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifactStep1:
                    contents: $taskGraphStep1.output
                    task:
                        name: artifactHandler1
                        args: [arg1, arg2]




**Keyword Style Invocation**


.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file

        .. admonition:: Artifact Output Graph - Keyword Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifact_outputs:
                    artifactStep1:
                        contents: $taskGraphStep1.output
                        task:
                            name: artifactHandler1
                            args:
                                keyword1: arg1
                                keyword2: arg2 

   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Artifact Output Graph - Keyword Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifactStep1:
                    contents: $taskGraphStep1.output
                    task:
                        name: artifactHandler1
                        args:
                            keyword1: arg1
                            keyword2: arg2 



**Mixed Style Invocation**


.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file


        .. admonition:: Artifact Output Graph - Mixed Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifact_outputs:
                    artifactStep1:
                        contents: $taskGraphStep1.output
                        task:
                            name: artifactHandler1
                            args: [arg1]
                            kwargs:
                                keyword2: arg2 


   .. group-tab:: Entrypoint defined in the GUI / Standalone component


        .. admonition:: Artifact Output Graph - Mixed Style Invocation
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifactStep1:
                    contents: $taskGraphStep1.output
                    task:
                        name: artifactHandler1
                        args: [arg1]
                        kwargs:
                            keyword2: arg2 





Artifact Output Graph Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar to the Task Graph, the Artifact Output Graph also has access to global entrypoint parameters. Entrypoint parameters can be referenced in the 
Artifact Output Graph using the same syntax as the Task Graph. 

For example, if an entrypoint parameter was named ``dataFrameFileFormat``, then it could be referenced in the following way:


.. tabs::

   .. group-tab:: Entrypoint defined in a TOML file


        .. admonition:: Artifact Output Graph - Using Entrypoint Parameters
            :class: code-panel yaml
            
            .. code-block:: yaml

                artifact_outputs:
                    saveDataFrame:
                        contents: createDataFrame$output
                        task:
                            name: dataFrameHandler
                            kwargs:
                                format: $dataFrameFileFormat 


   .. group-tab:: Entrypoint defined in the GUI / Standalone component

        .. admonition:: Artifact Output Graph - Using Entrypoint Parameters
            :class: code-panel yaml
            
            .. code-block:: yaml

                saveDataFrame:
                    contents: createDataFrame$output
                    task:
                        name: dataFrameHandler
                        kwargs:
                            format: $dataFrameFileFormat 




Again, this applies to *both* entrypoint parameters and artifact parameters.


.. _reference-entrypoints-registration-interfaces:

Registration Interfaces
-----------------------

.. _reference-entrypoints-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~


      
    .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.create
        :noindex:


.. _reference-entrypoints-rest-api:

Using REST API
~~~~~~~~~~~~~~

Entrypoints can be created directly via the HTTP API.


**Create Entrypoints**
 
See the :http:post:`POST /api/v1/entrypoints </api/v1/entrypoints/>` endpoint documentation for payload requirements.



.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Jobs Reference <reference-jobs>`
* :ref:`Plugins Reference <reference-plugins>`
