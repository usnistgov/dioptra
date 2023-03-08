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

.. _user-guide-task-plugins:

Task Plugins
============

.. include:: /_glossary_note.rst

.. tip::

   Instructions for how to create your own task plugins are available in the :doc:`Custom Task Plugins guide <custom-task-plugins>`.

What are Task Plugins?
----------------------

.. figure:: /images/entry-point-task-plugin-composition.svg

Task plugins are the main compositional unit of an entry point script.
They perform a variety of basic, low-level functions such as loading models, preparing data, and computing metrics, as well as implementing atomic portions of attacks and defenses such as generating adversarial examples or pre-processing images before inference.
:ref:`As discussed at the end of the previous section <entry-points-prefect-task-execution>`, the Prefect_ library sets up and manages the data flows between the task plugins and the task execution order.

Calling a Task Plugin
---------------------

Let's return to the :ref:`final example from the previous guide <entry-points-prefect-task-execution-code>` and expand the code to include the next task plugin call.

.. code-block::

   from prefect import Flow, Parameter
   from dioptra import pyplugs

   with Flow("Image Resizer") as flow:
       data_dir, image_size = Parameter("data_dir"), Parameter("image_size")
       resize_output = pyplugs.call_task(
           "dioptra_builtins.data",    # namespace.package import path
           "images",                      # module to import
           "resize",                      # function to call
           data_dir=training_dir,         # Named argument of resize()
           image_size=image_size,         # Named argument of resize()
       )
       rotated_image = pyplugs.call_task( # Task won't run until resize_output is available
           "dioptra_builtins.data",    # namespace.package import path
           "images",                      # module to import
           "rotate",                      # function to call
           data=resize_output,            # Named argument of rotate()
           image_size=image_size,         # Named argument of rotate()
       )
       ...

Some inline annotations have been added to the code to illustrate the anatomy of the :py:func:`.pyplugs.call_task` function calls.
The first two arguments provide the ``namespace.package.module`` import path that leads you towards your function of interest, and the third argument names that function.
This means that the full paths to our functions are ``dioptra_builtins.data.images.resize()`` and ``dioptra_builtins.data.images.rotate()``.
Any number of named arguments may follow after these first three, which is how you pass specific arguments to the functions we're using.
Here, the ``resize()`` function will get `data_dir` and `image_size` arguments and the ``rotate`` function will get ``data`` and ``image_size`` arguments.
Finally, we should note that, because we are passing the output of the first :py:func:`.pyplugs.call_task` function call into the second one with `data=resize_output`, we are declaring that there should be an explicit dependency between these task plugin calls, meaning the ``rotate()`` function will **never** be called before the ``resize()`` function call has finished running.

.. warning::

   The Prefect_ library's task execution engine makes no guarantee that the tasks will run in the order they're written in your script file, so the only thing that prevents tasks from running in the wrong order is the explicit dependency graph.
   If you need to call a function for its side effects and certain functions should wait, you can declare this implicit dependency using the special `upstream_tasks` argument.
   For example, if the ``rotate()`` task plugin didn't have a data argument and instead the ``resize`` function just saved its results to disk, you could add the following to ensure that ``rotate()`` never runs before ``resize()``,

   .. code-block::
   
      ...
      rotated_image = pyplugs.call_task(  # Task won't run until resize_output is available
          "dioptra_builtins.data",     # namespace.package import path
          "images",                       # module to import
          "rotate",                       # function to call
          image_size=image_size,          # Named argument of rotate()
          upstream_tasks=[resize_output], # Adds output of resize() as implicit dependency
      )
      ...

PyPlugs and the Task Plugin Registry
------------------------------------

.. note::

   The forked PyPlugs_ package in the ``dioptra`` package namespace is, in essence, a sophisticated wrapper for the :py:func:`importlib.import_module` function in the standard library.
   Most of the code in PyPlugs_ is dedicated to managing the plugin registry and catching errors.
   Please see the following article for an explanation of how this type of plugin registry works: https://realpython.com/python-import/#example-a-package-of-plugins.

Now that we've seen how :py:func:`.pyplugs.call_task` is used to call task plugins, the next question is, "how does :py:func:`.pyplugs.call_task` find the task plugins and build its internal registry?"
We address those questions with the following three sections.

Storage
~~~~~~~

The task plugins are stored in a specific bucket and directory on the Testbed's S3 storage.
When a Testbed Worker pulls a new experiment job from the queue, it is instructed to first synchronize its plugins with the latest copies on S3.
This means that new plugins are installed in the Testbed environment simply by copying them to the relevant S3 storage location.

Registration
~~~~~~~~~~~~

PyPlugs will only be aware of functions that have a ``@pyplugs.register`` decorator attached to them.
The example below illustrates how to apply this decorator to a Python function so that PyPlugs can discover it and include it in its internal registry.

.. code-block::

   from numpy.random._generator import Generator as RNGenerator

   from dioptra import pyplugs


   @pyplugs.register
   def draw_random_integer(rng: RNGenerator, low: int = 0, high: int = 2 ** 31 - 1) -> int:
       return int(rng.integers(low=low, high=high))

Discovery
~~~~~~~~~

The directory where the Testbed Worker syncs the latest copies of the plugins from S3 must be added to Python's system path so that PyPlugs can search for them.
However, modifying the Python system path must be done with care to ensure that you will still be able to import your other installed packages and avoid creating dependency conflicts.
For this reason, the Testbed :term:`SDK` provides the :py:func:`~dioptra.sdk.plugin_dirs` function, which modifies the Python system path within a temporary context, see the example below.

.. code-block::

   from dioptra.sdk.utilities.contexts import plugin_dirs

   with plugin_dirs():
       _ = entry_point_script()

:py:func:`~dioptra.sdk.plugin_dirs` determines the paths it needs to add to the Python system path by inspecting the ``DIOPTRA_PLUGIN_DIR`` environment variable, which is the same variable used by the Testbed Worker when it downloads the latest copies of the task plugins from S3.

.. Links

.. _Prefect: https://www.prefect.io
.. _PyPlugs: https://github.com/gahjelle/pyplugs
