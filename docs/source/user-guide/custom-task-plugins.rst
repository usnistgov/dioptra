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

.. _user-guide-custom-task-plugins:

Custom Task Plugins
===================

.. include:: /_glossary_note.rst

When designing a custom example, you may be required to create a new task plugin in order to effect specific behaviors not included in the core plugins.

Task Organization: Built-in Tasks
---------------------------------

Dioptra contains a number of built-in task plugins that can be executed across all available examples.
They are stored in the following directories:

.. code-block:: none

   task-plugins/
       └── dioptra_builtins
           ├── artifacts
           |   ├── exceptions.py
           |   ├── mlflow.py
           |   └── utils.py
           ├── attacks
           |   └── fgm.py
           ├── backend_configs
           |   └── tensorflow.py
           ├── data
           |   └── tensorflow.py
           ├── estimators
           |   ├── keras_classifiers.py
           |   └── tensorflow.py
           ├── metrics
           |   ├── distance.py
           |   ├── exceptions.py
           |   └── performance.py
           ├── random
           |   ├── rng.py
           |   └── sample.py
           ├── registry
           |   ├── art.py
           |   └── mlflow.py
           └──tracking
              └── mlflow.py

Please refer to :ref:`user-guide-task-plugins-collection` for more information regarding each built-in task.

Task Organization: Local Tasks
------------------------------

In general while built-in task plugins are located in the ``task-plugins/dioptra_builtins`` folder, local tasks can be stored in the same way as local python functions in each example's src code folder.

For instance, in our previous guide on creating custom entry points we had a localized task called ``task_B`` which was stored in the python file ``custom_local_task_plugins.py``.

.. code-block::

   example_dir/
   ├── src/
   │   ├── custom_entrypoint_script.py
   │   ├── <Other src code>
   │   └── custom_local_task_plugins.py
   ├── ...
   └── MLproject

To retrieve this plugin for our entry point we had to call the import statement ``from .custom_local_task_plugins import task_B``, similar to how we would import and use a python function.
For additional examples on how these plugins are constructed, you can refer to ``examples/tensorflow-mnist-classifier/src/tasks.py`` for local plugins.

The following sections will now involve creating built-in and localized task plugins.

Creating a Built-in Task
------------------------

To create a built-in task, first the user must identify which built-in subdirectory (artifacts, attacks, etc.) should contain the new task.
Once this is done, the task can be declared as follows:

.. code-block::

   from dioptra import pyplugs

   @pyplugs.register
   def add_values(x, y):
       return x + y

It is generally best practice to create small tasks, atomizing your workflow down to discrete units of work.
Those tasks may then be chained together.
Tasks can be as complex as needed with no ill effect.
For a slightly more complex task, consider the sample below, which will generate random samples according to the parameters you set.

.. code-block::

   @pyplugs.register
   def draw_random_integers(
       rng: RNGenerator,
       low: int = 0,
       high: int = 2 ** 31 - 1,
       size: Optional[Union[int, Tuple[int, ...]]] = None,
   ) -> np.ndarray:
       size = size or 1
       result: np.ndarray = rng.integers(low=low, high=high, size=size)

       return result

To access the built-in task from a given example, users will need to call the plugin-task using the following notation in their flow pipeline.
Note that we assumed these new tasks have been saved in a module named ``ops.py`` under the `data` task plugins directory:

.. code-block:: python

   from dioptra import pyplugs
   ...
   def custom_flow() -> Flow:
       ...
       // Call new builtin task.
       result = pyplugs.call_task(
           "dioptra_builtins.data",
           "ops",
           "add_values",
           x=input_x,
           y=input_y,
       )

For local tasks we will use a different notation for both creating and invoking tasks in the flow pipeline.

Creating a Local Task
---------------------

In general the major difference besides location of local task plugins is that the the `@task` decorator now replaces the `@pyplugs.register` decorator.
The task decorator is imported from the prefect library:

.. code-block:: python

   from prefect import task

   @task
   def add_values(x, y):
       return x + y

   @task
   def draw_random_integers(
       rng: RNGenerator,
       low: int = 0,
       high: int = 2 ** 31 - 1,
       size: Optional[Union[int, Tuple[int, ...]]] = None,
   ) -> np.ndarray:
       size = size or 1
       result: np.ndarray = rng.integers(low=low, high=high, size=size)

       return result

Furthermore as seen in the :ref:`previous guide on building new entry points <user-guide-custom-entry-points>` calling local tasks is also more similar to calling a local python function:

.. code-block:: python

   from .tasks import add_values
   ...
   def custom_flow() -> Flow:
       ...
       // Call new local task.
       result = add_values(
           x=input_x, y=input_y
       )
