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


.. _tutorial-running-hello-world:


Running Hello World
==============================

This tutorial explains how to run a simple "Hello World" workflow in Dioptra using the Guided User Interface (GUI). You will learn the essential lifecycle of a Dioptra task: writing code, creating a plugin, defining an entrypoint, and running a job.

Prerequisites
-------------
Before starting, ensure you have :ref:`installed Dioptra <explanation-install-dioptra>` and completed the :ref:`setup step <tutorial-setup-dioptra-in-the-gui>` of this tutorial.


Hello World Workflow
--------------------

Our goal is to run a Python function that prints a message to the Dioptra logs.

.. _tutorial-running-hello-world-step-1-prepare-python-code:

.. rst-class:: header-on-a-card header-steps

Step 1: Prepare Python Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, we need the Python code that defines our task. We will use the ``structlog`` library to ensure our message appears in the Dioptra job dashboard.


.. admonition:: hello_world.py
    :class: code-panel python

    .. literalinclude:: ../../../../docs/source/documentation_code/plugins/hello_world_tutorial/hello_world.py
       :language: python

Copy the code above (you will paste it into the GUI in the next step).

   Note: The code uses the ``@pyplugs.register`` decorator to turn a standard function into a **Plugin Function Task**. :ref:`Learn More <reference-plugins>`.


.. _tutorial-running-hello-world-step-2-create-the-plugin:

.. rst-class:: header-on-a-card header-steps

Step 2: Create the Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We must create a container for our code and register the task in the system.

1. In the GUI, navigate to the **Plugins** tab.
2. Click the **Create** button in the Plugins table.
3. Enter the name ``hello_world_plugin`` and add a short description. Click **Submit**.

.. figure:: ../../images/screenshots/plugins/create_hello_world_plugin_dioptra_1_1.png
   :alt: Screenshot of the plugin creation / registration modal
   :width: 900px
   :figclass:  border-image clickable-image

   Creating the Hello World Plugin Container

4. In the plugin list, **click the row** corresponding to the Hello World Plugin you just created to go to the **Plugin Files table**.

.. figure:: ../../images/screenshots/plugins/hello_world_plugin_files_table_dioptra_1_1.png
   :alt: Screenshot of the plugin creation / registration modal
   :width: 900px
   :figclass:  border-image clickable-image

   The created Hello World Plugin container

5. In the Plugin Files table, click **Create** to add a new file.
6. Name the file ``plugin_1.py``, add a description, and **paste the code** from :ref:`step 1 <tutorial-running-hello-world-step-1-prepare-python-code>` into the editor.

**Register the Task**

7. In the **Task Form** (on the right side of the editor), register the function. Click the **Create** button under the Plugin Function Tasks table. Enter the following:
   
   - **Task Name:** ``hello_world`` (Must match the Python function name exactly).
   - **Input/Output Parameters:** *Leave blank* - Our function has no inputs and returns no outputs.

Click the **Confirm** button to finish task registration. 

.. figure:: ../../images/screenshots/plugin_files/register_hello_world_function_task_Dioptra_1_1.png
   :alt: Screenshot of the task registration
   :width: 900px
   :figclass:  border-image clickable-image

   Registering the Python function as a Plugin Task

8. Click **Submit File**.

.. figure:: ../../images/screenshots/plugin_files/hello_world_plugin_file_creation_dioptra_1_1.png
   :alt: Screenshot of the finalized hello world plugin file with task registered
   :width: 900px
   :figclass:  border-image clickable-image

   The Plugin file with our registered hello world task



.. rst-class:: header-on-a-card header-steps

Step 3: Create an Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Entrypoints define the workflow (Task Graph) that sequences our tasks. 
Our workflow is one with a single task only.

1. Navigate to the **Entrypoints** tab.
2. Click the **Create** button in the Entrypoints table.
3. Name it ``hello_world_entrypoint`` and add a brief description.
4. In the Queues section, attach the ``tensorflow-cpu`` Queue we created in the :ref:`setup step <tutorial-setup-dioptra-in-the-gui>` of this tutorial.

.. figure:: ../../images/screenshots/entrypoints/create_hello_world_ep_metadata_dioptra_1_1.png
   :alt: Screenshot of entrypoint creation metadata 
   :width: 900px
   :figclass:  border-image clickable-image


5. Scroll down. In the **Task Plugins** window, select the ``hello_world_plugin`` we created :ref:`earlier <tutorial-running-hello-world-step-2-create-the-plugin>`.
6. In the **Task Graph YAML** editor, paste the following YAML:

.. admonition:: Entrypoint Task Graph
   :class: code-panel yaml

   .. code-block:: yaml

      hello_world_step: # Task name
         task: hello_world # One of our registered tasks

7. Click **Validate Inputs** (it should pass as there are no parameters).

.. figure:: ../../images/screenshots/entrypoints/hello_world_task_graph_inputs_valid_dioptra_1_1.png
   :alt: Screenshot of the Entrypoint creation screen showing the YAML editor.
   :width: 900px
   :figclass:  border-image clickable-image

   Defining the workflow structure in the Entrypoint editor.


8. Click **Submit Entrypoint**.


.. rst-class:: header-on-a-card header-steps

Step 4: Create Experiment & Job
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To execute the entrypoint, we must place it inside an Experiment and run it as a Job.

1. Navigate to the **Experiments** tab and click the **Create** button in the Experiments table.
2. Name it ``hello_world_experiment``.
3. In the Entrypoint dropdown, select ``hello_world_entrypoint``.

.. figure:: ../../images/screenshots/experiments/create_hello_world_experiment_dioptra_1_1.png
   :alt: Screenshot of the Experiment creation process
   :width: 900px
   :figclass:  border-image clickable-image

   Creating the hello world experiment


4. Click **Submit Experiment**.
5. Once the experiment is created, **click on the experiment** - the Experiment's Job page should appear. 
6. In the jobs table, click **Create**.
7. Select the ``hello_world_entrypoint``.
8. Select the ``tensorflow-cpu`` queue (which we created in :ref:`the previous tutorial step <tutorial-setup-dioptra-in-the-gui>`) - attach it now if you forgot to attach it previously.
9. Add a short description, and then click **Submit Job**.

.. figure:: ../../images/screenshots/jobs/running_hello_world_job_dioptra_1_1.png
   :alt: Screenshot of the Job submission modal.
   :width: 900px
   :figclass:  border-image clickable-image

   Submitting the job to the queue.

.. rst-class:: header-on-a-card header-steps

Step 5: Inspect Logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The job will transition from **Queued** to **Finished**. We can verify the code ran by checking the logs.

1. In the **Jobs** tab, click the job you just ran.
2. Navigate to the **Logs** tab within the job details.

.. figure:: ../../images/screenshots/jobs/hello_world_job_log_outputs_dioptra_1_1.png
   :alt: Screenshot of the Job Logs tab showing the Hello World message.
   :width: 900px
   :figclass:  border-image clickable-image

   Viewing the execution logs.

You should see the following message generated by ``hello_world_plugin.plugin_1``:

.. admonition:: Job Log Output
   :class: code-panel console

   .. code-block:: console

      [info     ] Hello, World! Welcome to Dioptra. [hello_world_plugin.plugin_1]

.. note::

   If the Job never transitions out of the "Queued" state, there may be an issue with your Queue / Worker configuration. The ``tensorflow-cpu`` Queue is meant to 
   directly communicate with the ``tensorflow-cpu`` worker, one of the default workers available as a :ref:`pre-built container <how-to-download-container-images>`. The name of the 
   queue must exactly match the Worker configuration file (:ref:`Learn More <explanation-queues-and-workers>`).

Conclusion
----------

You have successfully run your first Dioptra job! You wrote a Python function, wrapped it in a Plugin, sequenced it in an Entrypoint, and executed it using the GUI.

.. rst-class:: fancy-header header-seealso

See Also 
---------
To understand in greater depth all the components utilized in this experiment, reference :ref:`Dioptra Components Explanation <explanation-dioptra-components>`.
You can also find syntax and file requirements in :ref:`Dioptra Components Reference <reference-dioptra-components>`.


Next Steps
----------

Now that you have the basics down, let's learn about more advanced functionality of Dioptra.

* :ref:`tutorial-learning-the-essentials` - Tutorial to learn about entrypoint parameters, artifacts, and multi-task workflows.
