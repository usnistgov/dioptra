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
=================


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-entrypoints-definition:

Entrypoint Definition
---------------------

An **Entrypoint** in Dioptra is a repeatable workflow that can be executed as a Job. Entrypoints execute the function tasks defined in the task graph upon job submission. 
Entrypoint parameters and Artifact Input Parameters can optionally be attached to entrypoints and then used in the Task Graph. The outputs from Function Tasks 
can be saved as Artifacts, and the logic for this is defined in the Artifact Task Graph. 

.. _reference-experiments-attributes:


Entrypoint Attributes
---------------------

This section describes the attributes that define an Entrypoint.

.. _reference-entrypoints-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

.. _reference-entrypoints-optional-attributes:

- **Name**: (string) The display name for the Entrypoint. 
- **Group**: (integer ID) The Group that owns this Experiment and controls access permissions.
- **Task Graph**: (YAML string) The task graph for entrypoint, which as a YAML-formatted string that defines the core workflow (technically, a Directed Acyclical Graph). Composed of function task invocations and their input arguments. (See: :ref:`syntax requirements <reference-entrypoints-task-graph-syntax>`)
- **Drafts**: ?

Optional Attributes
~~~~~~~~~~~~~~~~~~~

- **Description**: (string, optional) A text description of the Entrypoint's purpose or scope. Defaults to empty.
- **Plugins**: (list of Plugin IDs, optional) A list of Plugin containers to attach to the entrypoint - the associated Plugin Function Tasks are then made available to the Entrypoint Task Graph. Defaults to empty.
- **Artifact Plugins**:  (list of Plugin IDs, optional) A list of Plugin containers to attach to the entrypoint - the associated Plugin Artifact Tasks are then made available to the Artifact Output Task Graph. Defaults to empty.
- **Parameters**: (list of Dicts, optional) Global parameters that can be used in the Entrypoint Task Graph and Artifact Task Graph. Each Parameter has a type and can optionally have a default value. Parameter values are set at Job runtime. Defaults to empty.
    - **Name** (string) The Name of the Entrypoint Parameter, used to access the Parameter in the Task Graphs 
    - **Type** (Plugin Parameter Type ID) The type for the parameter, used for type validation 
    - **Default Value** (String, Optional) An optional default value for the parameter which can be overwritten during job execution. Gets type converted during job execution time. 
- **Artifact Parameters**: (list of Dicts, optional) Global objects, loaded from disk at Job execution, can be used in the Entrypoint Task Graph and Artifact Task Graph. User selects which specific artifact snapshot to load into the Artifact Parameter at Job Runtime. Defaults to empty.
    - **Name** (string) The Name of the Artifact Parameter, used to access the Object(s) in the Task Graphs 
    - **Output Parameters** (List of Outputs) List of outputs that the deserialize method of an artifact task is expected to produce
- **Artifact Task Graph**: (YAML string, optional) The artifact task graph for entrypoint, which as a YAML-formatted string that defines the artifact serialization logic. Artifact Tasks are called once the main Task Graph execution is completed. Defaults to empty. (See: :ref:`syntax requirements <reference-entrypoints-artifact-output-graph-syntax>`)
- **Queues**: (list of integer IDs, optional) A list of the queues that can pick up Job submissions of this entrypoint and carry out their execution. Job will not be runnable without at least one attached Queue. Defaults to empty.
- **Snapshot**: ? 

.. _reference-entrypoints-system-generated-attributes:

System-Generated Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **ID**: Unique identifier assigned upon creation.
- **Created On**: Timestamp indicating when the Entrypoint was created.
- **Last Modified On**: Timestamp indicating when the Entrypoint was last modified.
- **Jobs**: ?
- **Experiments**: ?

.. _reference-entrypoints-task-graph-syntax:

Task Graph Syntax
------------------

The task graph consists of a list of step descriptions. Each step corresponds to the execution of a function task.
The task graph is defined in YAML, and each function task can be invoked using one of three invocation styles:

- Positional
- Keyword  
- Mixed 


There are similarities across all three invocation styles:

    * **Step Names**: ``step1`` and ``step2`` refer to the names of steps, and also to the *location in which the output of that step is stored*. The variable ``$step1`` contains the output of the task that was run in that step.

    * **Task Names**: ``task1`` and ``task2`` refer to the registered names of plugin function tasks (and also the name of the corresponding Python functions). Each step in the graph represents an invocation of a function task.

    * **Arguments for Function Tasks**: ``arg1``, ``arg2``, ``arg3``, and ``arg4`` are arguments provided to the function tasks.

    * **Argument Names for Function Tasks**: ``keyword1``, ``keyword2``, ``keyword3``, and ``keyword4`` are the parameter names for that particular function. These names are defined at task registration time.


Invocation Styles
~~~~~~~~~~~~~~~~~~~~~~

**Positional Style Invocation**

All task arguments are passed in as positional arguments. These positional arguments are assumed to correspond to the ordering of plugin input parameters for the task. Upon task execution, 
these arguments are passed into the Python function without names in order. 

.. margin::

    .. note::
        
        The ``graph:`` keyword that starts the YAML code blocks below does not need to be included in the task graph definition in the Graphical User Interface (GUI). When defining an entire entrypoint via YAML, this word is used to designate the task graph section of the file (as distinct from the parameter definitions, the artifact task graph, etc.)


.. admonition:: Task Graph
    :class: code-panel yaml

    .. code-block:: yaml

        graph:
            step1:
                task1: [arg1, arg2]
            step2:
                task2: [arg3, arg4]

**Keyword Style Invocation**

The keywords correspond to the names of the Function Task parameters. Upon function execution, these values are passed in as named arguments to the Python function. 

.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        graph:
            step1:
                task1:
                    keyword1: arg1
                    keyword2: arg2
            step2:
                task2:
                    keyword3: arg3
                    keyword4: arg4

**Mixed Style Invocation**

Combines positional arguments with named arguments. The positional arguments are assumed to correspond to the ordering of plugin input parameters for the task, and the 
keyword arguments must match one of the names of the function task arguments that does not correspond to any of those claimed by the positional arguments. Upon task execution, 
the positional arguments are passed into the Python function without names in order, and then the keyword arguments are passed in with their corresponding names. 


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        graph:
            step1:
                task: task1
                args: [posarg1, posarg2]
                kwargs:
                    keyword1: arg1
                    keyword2: arg2
            step2:
                task: task2
                args: [posarg3, posarg4]
                kwargs:
                    keyword3: arg3
                    keyword4: arg4

Argument Structure
~~~~~~~~~~~~~~~~~~~~~~

Though the above examples provide strings (such as ``arg1`` or ``arg2``) as arguments, it is also fine to use YAML to provide
arguments with structure. For example, a list of strings (in this case ``["arg1", "arg11", "arg111"]``) could be provided
as an argument to the ``keyword1`` parameter as follows:


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        graph:
            step1:
                task1:
                    keyword1: 
                        - arg1
                        - arg11
                        - arg111
                    keyword2: arg2
            step2:
                task2:
                    keyword3: arg3
                    keyword4: arg4


Alternatively, a mapping (in this case ``{"k1":"arg1", "k2":"arg11", "k3":"arg111"}``) can also be provided 
as an argument to the ``keyword1`` parameter if needed:


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        graph:
            step1:
                task1:
                    keyword1: 
                        - k1: arg1
                        - k2: arg11
                        - k3: arg111
                    keyword2: [arg2, arg22]
            step2:
                task2:
                    - keyword3: arg3
                    - keyword4: arg4


References Within a Task Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned earlier, the output of each function task is stored in a variable designated by the step name. These variables
can be used in other steps.

Here is an example of using the output of a function task.


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        graph:
            step1:
                task1: [arg1, arg2]
            step2:
                task2: [$step1, arg4]

This passes the output of the step named ``step1`` as input to the first parameter of the function task named ``task2``.

It is possible for function tasks to have multiple outputs. See :ref:`explanation-plugins` for more details. Each output
is given a name when registered. In an example where ``task1`` is registered to have two separate outputs, ``output1`` and 
``output2``, these can be referenced as follows:


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        graph:
            step1:
                task1: [arg1, arg2]
            step2:
                task2: [$step1.output1, $step1.output2]

Task Graph Parameters
~~~~~~~~~~~~~~~~~~~~~~

Parameters to the task graph are simply variables assumed to be provided by the job at runtime. In the following example, 
``$myparam`` clearly does not reference a step name. As a result, this is a parameter which needs to be provided
at job runtime, either as a default or by the user running the job.

Note that this applies to *both* entrypoint parameters and artifact parameters. From the perspective of the task 
graph, the usage is equivalent, though the parameters are supplied separately at runtime.

See :ref:`explanation-entrypoints` and :ref:`explanation-artifacts` for more details.


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        graph:
            step1:
                task1: [arg1, arg2]
            step2:
                task2: [$myparam, $step1.output2]


Additional Dependencies
~~~~~~~~~~~~~~~~~~~~~~

Explicit dependencies between steps can be added via the ``dependencies`` keyword. Dependencies between steps are
automatically created when a step uses the output of another step as a parameter, but sometimes a dependency is 
needed without the presence of output. In this example, ``step2`` will always be executed after the completion of ``step1``.


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        graph:
            step1:
                task1: [arg1, arg2]
            step2:
                task2: [$param1, $param2]
                dependencies: [step1]



.. _reference-entrypoints-artifact-output-graph-syntax:

Artifact Output Graph Syntax
--------------------------------

Upon successful completion of the artifact task graph within a Job execution, the artifact output graph will then execute (if it is defined) to save any designated task outputs 
as artifacts. 

There are many similarities between invoking artifact tasks and function tasks:

    * **Step Names**: ``artifactStep1`` and ``artifactStep2`` refer to the names of steps in the artifact graph. ``taskGraphStep1`` and ``taskGraphStep2`` refer to step names from the task graph. 

    * **Artifact Task Names**: ``artifactHandler1`` and ``artifactHandler2`` refer to the registered names of artifact function tasks (and also the name of the corresponding Python classes). Each step in the graph represents an invocation of the ``serialize()`` method of an artifact handler. 

    * **Arguments for the Artifact Tasks**: ``arg1``, ``arg2`` are arguments provided to the artifact tasks.

    * **Argument Names for Artifact Tasks**: ``keyword1``, ``keyword2``  are the parameter names for that particular artifact task. These names are defined at artifact task registration time.



.. margin::

    .. note::
        
        The ``artifact_outputs:`` keyword that starts the YAML code blocks below does not need to be included in the artifact task graph definition in the Graphical User Interface (GUI). When defining an entire entrypoint via YAML, this word is used to designate the artifact output graph section of the file (as distinct from the parameter definitions, the task graph, etc.)

.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        artifact_outputs:
            artifactStep1:
                contents: taskGraphStep1$output # assumes the name of output from task graph step "taskGraphStep1" is "output"
                task:
                    name: artifactHandler1
            artifactStep2:
                contents: taskGraphStep2 # If a function task only has one output, then only the step name is required
                task:
                    name: artifactHandler2

Invocation Styles 
~~~~~~~~~~~~~~~~

Some artifact tasks define task inputs to customize the serialization logic (for example, specifying a file format). 
Similar to the task graph, the arguments for artifact tasks can be passed in in a variety of ways.
These arguments are used in the ``serialization`` method of the Artifact Handler, as well as the ``validate`` method (if it is defined).


**Positional Style Invocation**


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        artifact_outputs:
            artifactStep1:
                contents: taskGraphStep1$output
                task:
                    name: artifactHandler1
                    args: [arg1, arg2]


**Keyword Style Invocation**


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        artifact_outputs:
            artifactStep1:
                contents: taskGraphStep1$output
                task:
                    name: artifactHandler1
                    args:
                        - keyword1: arg1
                        - keyword 2: arg2 

**Mixed Style Invocation**


.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        artifact_outputs:
            artifactStep1:
                contents: taskGraphStep1$output
                task:
                    name: artifactHandler1
                    args: [arg1]
                    kwargs:
                        - keyword 2: arg2 


Artifact Output Graph Parameters
~~~~~~~~~~~~~~~~~~~~~~

Similar to the Task Graph, the Artifact Output Graph also has access to global entrypoint parameters. Entrypoint parameters can be referenced in the 
artifact task graph using the same syntax as the task graph. 

For example, if an entrypoint parameter had the named ``dataFrameFileFormat``, then it could be referenced in the following way:

.. admonition:: Task Graph
    :class: code-panel yaml
    
    .. code-block:: yaml

        artifact_outputs:
            saveDataFrame:
                contents: createDataFrame$output
                task:
                    name: dataFrameHandler
                    kwargs:
                        - format: $dataFrameFileFormat 


Again, this applies to *both* entrypoint parameters and artifact parameters.


.. _reference-entrypoints-registration-interfaces:

Registration Interfaces
-----------------------

.. _reference-entrypoints-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Create an Entrypoint**

    .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.create

.. _reference-entrypoints-rest-api:

Using REST API
~~~~~~~~~~~~~~

Entrypoints can be created directly via the HTTP API.

**Create Entrypoints**

See the :http:post:`POST /api/v1/entrypoints </api/v1/entrypoints/>` endpoint documentation for payload requirements.



.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Jobs <reference-jobs>`
* :ref:`Plugins <reference-plugins>`
