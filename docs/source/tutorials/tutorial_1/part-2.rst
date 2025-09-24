:html_theme.sidebar_secondary.remove:

Adding Inputs and Outputs
=========================

Overview
--------

In the previous tutorial, you created a plugin with one task and ran it through an Entrypoint and Experiment.  
Now, you will extend that example to include **parameters and outputs**.  

This will let you:

- Define **input parameters** for a Plugin Task  
- Create a custom **Plugin Parameter type** (NumPy array)  
- Parameterize Entrypoints and Jobs to get different results  

The goal is to run our Entrypoint twice with different **sample sizes** and see how the observed mean compares to the true distribution mean.  


Create a New Type
-----------------

Before a task can output a NumPy array, we need to define the type in Dioptra.

.. admonition:: Steps

   1. Navigate to the **Plugin-Params** tab.  
   2. Click **Create**.  
   3. Enter the name: ``NumpyArray``.  
   4. Save.

.. figure:: _static/screenshots/make_numpy_array_type.png
   :alt: Screenshot of creating a new type called NumpyArray.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Creating a new type in the UI


Make Plugin 2
-------------

We will now create a new plugin with one task. This task:

- Accepts four parameters: ``random_seed``, ``sample_size``, ``mean``, and ``var``  
- Samples a NumPy array from a normal distribution  
- Returns the array as an output  

.. admonition:: Steps

   1. Go to the **Plugins** tab → **Create Plugin**.  
   2. Name it ``plugin_2`` and add a short description.  
   3. Add a new Python file ``plugin_2.py`` and paste in the following code:

**Plugin 2 Code**


.. admonition:: Plugin 2
    :class: code-panel python

    .. literalinclude:: ../../../../examples/tutorials/tutorial_1/plugin_2.py
       :language: python
       :linenos:


Register the Task
~~~~~~~~~~~~~~~~~~~

Unlike last time, we must specify input and output types for the Plugin Task.

Instead of manually specifying the input/output types, let's use Dioptra's autodetect functionality.

.. admonition:: Steps

   1. Click **Import Function Tasks** to auto-detect functions from ``plugin_2.py``.  

.. figure:: _static/screenshots/import_plugin_tasks.png
   :alt: Screenshot of the "Import Function Tasks" button.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Using "Import Tasks" to automatically detect and register Plugin Tasks in a Python file

.. note::

   Input and output types are auto-detected from **Python type hints** and the
   **return annotation** (``->``); see `PEP 484 <https://peps.python.org/pep-0484/>`_ for more.


You may see an error under **Plugin Tasks**: *Resolve missing Type* for the ``np_ndarray`` output.

.. figure:: _static/screenshots/resolve_missing_type.png
   :alt: Screenshot of a missing type error in Plugin Task registration.
   :width: 900px
   :figclass: big-image border-image clickable-image

   The output type was detected as np_ndarray, but our type is called NumpyArray. Click the output to fix this.

This is because we called our custom type ``NumpyArray``, not ``np_ndarray``.  

Let's correct the output type. Delete the auto-detected output and then add a new one with the following specs:

- Name: ``draws`` (more descriptive than 'output')  
- Type: ``NumpyArray``  

Save the Plugin file. 

Create Entrypoint 2
-------------------

Entrypoint setup is very similar to before, but we now add an **Entrypoint parameter** and use it in our task graph.

.. admonition:: Steps

   1. Create a new Entrypoint (``entrypoint_2``).  
   2. Define an **Entrypoint Parameter**:
      
      In the **Entrypoint Parameters** window, create a parameter with the following specs:
      - Name: ``sample_size``  
      - Type: ``int``  
      - Default value: e.g., ``100``  


.. figure:: _static/screenshots/sample_size_entrypoint_param.png
   :alt: Screenshot of adding the sample_size parameter to Entrypoint 2.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Creating an entrypoint parameter allows the parameter to be changed during a job run.


Create the Entrypoint Task Graph 
~~~~~~~~~~~~~~~~~~~

Next, add the plugin task to the graph:

.. admonition:: Steps (continued)

   1. Go to **Task Graph Info** window in the UI.  
   2. Select **plugin_2** from the Plugins list.  
   3. Click **Add to Task Graph** to automatically populate the Task Graph.  


.. figure:: _static/screenshots/entrypoint_2_add_to_task_graph.png
   :alt: Screenshot of adding plugin_2 to Entrypoint 2.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Using "Add To Task Graph" to automatically add Plugin Tasks into an entrypoint. Step Name and Parameterization need to be defined by hand.

By default, the **step** of the graph has no name and no parameter bindings. We must configure inputs.
Use the following values:

- ``mean`` = ``10``  
- ``var`` = ``10``  
- ``random_seed`` = ``0``  
- ``sample_size`` = ``$sample_size`` (a reference to the Entrypoint parameter)  


.. admonition:: Steps (finalized)
   1. Edit the Task Graph YAML code to overwrite the default values 

.. figure:: _static/screenshots/entrypoint_2_edit_task_graph.png
   :alt: Screenshot of editing parameters in Entrypoint 2 task graph.
   :width: 900px
   :figclass: big-image border-image clickable-image


Add Entrypoint 2 to Experiment 1
--------------------------------

We don’t need a new Experiment. We can add Entrypoint 2 to the one we already made.

.. admonition:: Steps

   1. Open **Experiment 1**.  
   2. Add **Entrypoint 2** to the experiment.  

.. figure:: _static/screenshots/add_entrypoint_2_to_experiment_1.png
   :alt: Screenshot of adding Entrypoint 2 to an existing experiment.
   :width: 900px
   :figclass: big-image border-image clickable-image

   You can edit experiments and add new entrypoints to them.

Run Two Jobs
------------

Now we’ll test different parameter values.

.. admonition:: Steps

   1. Click on the **Jobs** tab and create a new job
   2. Select experiment 1 and entrypoint 2
   3. Set ``sample_size`` to a large value (e.g., 10,000).  
   4. Submit the Job.  

.. figure:: _static/screenshots/entrypoint_2_job_10000.png
   :alt: Screenshot of running Entrypoint 2 with sample_size=10000.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Setting the sample size parameter for a job to 10,000.

Repeat the process:

.. admonition:: Steps (continued)

   1. Create another Job with ``sample_size`` = 100.  

.. figure:: _static/screenshots/entrypoint_2_showing_all_jobs.png
   :alt: Screenshot showing multiple jobs created with different sample sizes.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Jobs change from "queued" to "started", and then either "fail" or "finish".

Wait for both jobs to finish.


Inspect Results
---------------

When jobs complete, check:

- Logs confirm the parameter values used  
- The returned ``NumpyArray`` outputs differ in how close their sample mean is to the true mean  

.. note::
   This experiment shows a basic illustration of the Law of Large Numbers: 
   as the sample size increases, the sample mean tends to get closer to the population mean.


Conclusion
----------

You now know how to:

- Define custom types  
- Register Plugin Tasks with inputs and outputs  
- Run Entrypoints and Jobs with parameters  

Next, we’ll chain multiple tasks together into a single workflow.
