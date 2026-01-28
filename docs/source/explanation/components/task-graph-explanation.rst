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
workflow between plugin function tasks used by the entrypoint, as well as the parameter inputs to
each of those tasks. A directed acyclic graph (DAG) representing the dependencies between the 
various steps is constructed to ensure that the steps are executed in the correct order.


.. figure:: /images/task-graph-function.png
   :alt: Task graph purpose.
   :figclass: border-image clickable-image 

   The primary function of the task graph is to describe the relationship between variables and plugins within an entrypoint.
   It describes dependencies between the various steps, as well as how the outputs, global variables, and artifacts fit in as 
   input to the plugins invoked in each step.


Summary: What is a step?
------------------------

A **step** is one component of the task graph, which correlates, essentially, to a plugin task invocation
with a given set of parameters. A single step has several components:

* a **step name**, which functions as a variable storage for the output of the invoked task,
* a **task name**, which references the plugin task to invoke by name. At runtime, plugins associated with the entrypoint will be searched for a matching task.
* a **list of parameters**, which are passed to the referenced plugin task during invocation.


Below is an example task graph. In the first step, the step name is ``rng``, the task name is ``configure_rng`` and the list of parameters contains
a single member named ``seed`` which is being passed a value of ``1234``.


.. code:: yaml
   
   rng:
      configure_rng:
         seed: 1234

   trained_model:
      train:
         model: $model_artifact
         dataset: $training_ds
         epochs: $num_epochs
      dependencies: [rng]

   predictions:
      predict:
         model: $defended_model
         dataset: $testing_ds
         samples: $num_samples
      dependencies: [rng]

   defended_model:
      adversarial_training:
         model: $trained_model.model
         dataset: $adversarial_ds
         split: 0.5
      dependencies: [rng]

   metrics: 
      run_metrics:
         predictions: $predictions


Variables
~~~~~~~~~

You can reference the output of steps by referencing the step name. This is useful for passing the
output of one step as a parameter to another. For example: ``$trained_model`` will take the output stored in the
step with the name ``trained_model``. 

Alternatively, if the plugin task has named output (perhaps named ``model``, it can be accessed with 
``$trained_model.model``). The names of these outputs are defined at plugin task registration, and the number
of outputs of the registered task should match the number of outputs of the function it is associated with.


Global variables
~~~~~~~~~~~~~~~~

Entrypoints are parameterizable, and you can reference these parameters the same way variables are referenced. So, for example,
``$num_samples`` could reference an entrypoint parameter, and be used as an input to a task.

Artifact variables
~~~~~~~~~~~~~~~~~~

Entrypoints can also have artifact parameters, which are referenced in the same way. ``$training_ds`` could reference
the output of an artifact deserialization plugin task, and the entire artifact can then be used as input to a plugin
task. 

Explicit dependencies and DAG creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While a dependency on a variable will automatically be represented in the DAG, there are some cases where it may be
desirable to have a step always run after another step. For example, system configurations such as setting RNG seeds
or designating the worker as GPU enabled may not produce an output, but may still be required for multiple other steps
in the task graph.

Consider the following example task graph as a candidate for the DAG - explicit dependencies are declared for the ``defended_model``, 
``predictions`` and ``trained_model`` steps on the ``configure_rng`` step. Additionally, the ``defended_model`` step has an implicit
dependency on the ``trained_model`` step, and the ``predictions`` step has an implicit dependency on the ``defended_model`` step (by using
the output of those steps).


.. figure:: /images/DAG.png
   :alt: Generated directed acyclic graph based on dependencies within the task graph.
   :figclass: border-image clickable-image 

   The DAG generated from the above task graph. Dioptra creates dependencies in the DAG only based off the input/output
   chaining of plugin tasks. If a user wants to add additional explicit dependencies in the task graph, this can be done.
   See :ref:`<reference-task-graph>` for more details on this.

.. rst-class:: fancy-header header-seealso

See Also 
---------

* :ref:`reference-task-graph` - Reference for task graph construction.   
* :ref:`explanation-entrypoints` - Entrypoints explanation, of which task graphs are a component
* :ref:`how-to-create-plugins` - Step-by-step guide on building plugins
* :ref:`how-to-create-entrypoints` - Step-by-step guide on building entrypoints
