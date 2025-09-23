Running your first plugin task
==============================

Overview
--------

Our goal is to run some Python code in Dioptra.  
The essential steps are:

1. Write Python code to define Plugin Tasks  
2. Create a Plugin and register its tasks  
3. Create an Entrypoint workflow that calls those tasks  
4. Run the Entrypoint as a job within an Experiment  

.. figure:: _static/screenshots/dioptra_workflow.png
   :alt: Diagram showing steps needed to run Python functions in Dioptra.
   :width: 900px
   :figclass: big-image border-image clickable-image

   **Dioptra Workflow Overview**  
   The four essential steps needed to run Python functions in Dioptra.

The power of Dioptra is that it lets users reuse tasks and workflows across experiments.  
For this first tutorial, we’ll keep it simple: a single Plugin Task inside one Entrypoint.



Make Your First Plugin
----------------------

We will create a plugin with one task. This task will:

- Simulate data from a normal distribution  
- Print the mean using logging  



Create the Plugin in the UI
~~~~~~~~~~~~~~~~~~~

.. note::
   Plugins, tasks, entrypoints, and types can be created through the UI, API, or TOML files.  
   In this tutorial, we’ll use the UI.

.. admonition:: Steps

   1. Navigate to the **Plugins** tab.  
   2. Click **Create Plugin**.  
   3. Enter a name and description, then submit.



Add a Python File
~~~~~~~~~~~~~~~~~~~

We now attach code to the plugin.

.. admonition:: Steps (continued)

   1. In the plugin list, click the **file icon** for the plugin you just created.  
   2. Click **Create** to add a new Python file.  
   3. In the **Basic Info** tab, provide a filename (e.g., `plugin_1.py`).  
   4. Paste the following code into the editor:

.. literalinclude:: ../../../../examples/tutorials/tutorial_1/plugin_1.py
   :language: python
   :linenos:

.. figure:: _static/screenshots/plugin_1_add_file.png
   :alt: Screenshot of the plugin creation process in Dioptra.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Adding a Python file during Plugin creation

.. note::
   The ``@pyplugs.register`` decorator registers this Python function as a **Plugin Task**.



Register the Plugin Task
~~~~~~~~~~~~~~~~~~~

Functions must be registered as tasks before they can be used in Entrypoints.

.. admonition:: Steps (finalizing)

   1. In the task form window, register the function with the name ``sample_normal_distribution_print_mean``.  
   2. Leave input/output parameters blank.
   3. Click Save File



Create an Entrypoint
--------------------

Entrypoints define workflows made of tasks. Ours will be a single-task workflow.

.. admonition:: Steps

   1. Go to the **Entrypoints** tab.  
   2. Click **Create Entrypoint**.  
   3. Fill in the name and description.  
   4. In the **Task Graph** tab, paste the following YAML:

.. literalinclude:: ../../../../examples/tutorials/tutorial_1/entrypoint_1_task_graph.yaml
   :language: yaml
   :linenos:

.. figure:: _static/screenshots/entrypoint_1_task_graph.png
   :alt: Screenshot of the Entrypoint task graph editor with YAML pasted in.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Defining the Entrypoint task graph in the UI

.. admonition:: Steps (finalizing)

   5. Click **Validate Inputs** (it will always pass—this task has no parameters).  
   6. Click **Submit Entrypoint**.



Make an Experiment
------------------

Experiments hold entrypoints.

.. admonition:: Steps

   1. Navigate to the **Experiments** tab.  
   2. Click **Create Experiment** - fill in a name and description.  
   3. In the Entrypoint dropdown, select the Entrypoint you just created.  
   4. Click **Submit Experiment**.



Run a Job
---------

Jobs execute entrypoints within experiments.

.. admonition:: Steps

   1. Open the Experiment you just created.  
   2. Click **Create Job**.  
   3. Select the Entrypoint, add a name and description.  
   4. Click **Submit Job**.

.. figure:: _static/screenshots/create_job.png
   :alt: Screenshot of creating a job from the experiment page.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Submitting a job from the Experiment page

The job will first appear as **Queued**, then change to **Finished** after a short time.

.. figure:: _static/screenshots/job_1_finished.png
   :alt: Screenshot showing a finished job in Dioptra.
   :width: 900px
   :figclass: big-image border-image clickable-image

   Job status changes from Queued to Finished



Inspect Logs
~~~~~~~~~~~~~~~~~~~

(Placeholder) Open the job details to view logs. Confirm that the print statement output appears — this shows your Plugin Task executed successfully.



Conclusion
----------

You have now run your first Plugin Task in Dioptra.  
Next, we’ll add **inputs and outputs** so you can customize behavior and experiment with different Entrypoints.



Next Steps
----------

Continue to :doc:`part-2` to add inputs and outputs to your plugin task.
