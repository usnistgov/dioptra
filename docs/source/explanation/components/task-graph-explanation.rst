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

.. _explanation-task-graph:

Task Graph
==========

Summary: What is a Task Graph?
------------------------------
The **task graph** is the component of an entrypoint description which describes the steps of the 
workflow between plugin function tasks used by the entrypoint, as well as which the parameter inputs to
each of those tasks. A dependency graph between the various steps is constructed to ensure that the
steps are executed in the correct order (for example, if the output of one step is used as input
to another step).

The task graph consists of a list of step descriptions. These descriptions can be written using various
invocation styles: positional, keyword, and mixed.

In each of these invocation styles, you'll notice some commonalities:
    * ``step1`` and ``step2`` refer to the names of steps, and also to the *location in which the output of that step is stored*. 
    The variable ``$step1`` contains the output of the task that was run in that step.
    * ``task1`` and ``task2`` refer to the names of plugin function tasks. Each step in the graph represents an invocation of 
    a function task.
    * ``arg1``, ``arg2``, ``arg3``, and ``arg4`` are arguments provided to the function tasks.
    * ``keyword1``, ``keyword2``, ``keyword3``, and ``keyword4`` are the parameter names for that particular function.
    * The ``graph:`` keyword designates this section of the full entrypoint YAML dictionary as the task graph. If creating entrypoints
    through the UI, this keyword is unnecessary and is provided to the RESTAPI automatically.


Positional Style Invocation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    graph:
        step1:
            task1: [arg1, arg2]
        step2:
            task2: [arg3, arg4]

Keyword Style Invocation
~~~~~~~~~~~~~~~~~~~~~~~~

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

Mixed Style Invocation
~~~~~~~~~~~~~~~~~~~~~~

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
------------------

Though the above examples provide strings (such as ``arg1`` or ``arg2``) as arguments, it is also fine to use YAML to provide
arguments with structure. For example, a list of strings (in this case ``["arg1", "arg11", "arg111"]``) could be provided
as an argument to the ``keyword1`` parameter as follows:

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

.. code-block:: yaml

    graph:
        step1:
            task1:
                keyword1: 
                    - k1: arg1
                      k2: arg11
                      k3: arg111
                keyword2: [arg2, arg22]
        step2:
            task2:
                keyword3: arg3
                keyword4: arg4


References Within a Task Graph
------------------------------

As mentioned earlier, the output of each function task is stored in a variable designated by the step name. These variables
can be used in other steps.

Here is an example of using the output of a function task.

.. code-block:: yaml

    graph:
        step1:
            task1: [arg1, arg2]
        step2:
            task2: [$step1, arg4]

This passes the output of the step named ``step1`` as input to the first parameter of the function task named ``task2``.

It is possible for function tasks to have multiple outputs. See :ref:`<_explanation-plugins>` for more details. Each output
is given a name when registered. In an example where ``task1`` is registered to have two separate outputs, ``output1`` and 
``output2``, these can be referenced as follows:

.. code-block:: yaml

    graph:
        step1:
            task1: [arg1, arg2]
        step2:
            task2: [$step1.output1, $step1.output2]

Task Graph Parameters
---------------------

Parameters to the task graph are simply variables assumed to be provided by the job at runtime. In the following example, 
``$myparam`` clearly does not reference a step name. As a result, this is a parameter which needs to be provided
at job runtime, either as a default or by the user running the job.

Note that this applies to *both* entrypoint parameters and artifact parameters. From the perspective of the task 
graph, the usage is equivalent, though the parameters are supplied separately at runtime.

See :ref:`<explanation-entrypoints>` and :ref:`<explanation-artifacts>` for more details.

.. code-block:: yaml

    graph:
        step1:
            task1: [arg1, arg2]
        step2:
            task2: [$myparam, $step1.output2]

