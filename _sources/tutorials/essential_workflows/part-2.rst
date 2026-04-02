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

.. _tutorial-adding-inputs-and-outputs:

Adding Inputs and Outputs
=========================

Overview
--------

In the :ref:`Hello World Tutorial <tutorial-hello-world-in-dioptra>`, you created a plugin with one task and ran it through an entrypoint and experiment. Now, you will extend that idea to include **task inputs**, **task outputs**, and **entrypoint parameters**.

This will let you parameterize **input parameters** for a plugin task when running a job. After running multiple jobs, 
you will compare outputs and observe how different **sample sizes** impact the observed sample mean's relationship to its underlying distribution.

Prerequisites
-------------
Before starting, ensure you have set up Dioptra and have :ref:`created a User and Queue <tutorial-setup-dioptra-in-the-gui>`.

* :ref:`explanation-install-dioptra` - Obtain the Dioptra containers and create a deployment
* :ref:`tutorial-setup-dioptra-in-the-gui` - Create a user and queue in the GUI (Hello World Tutorial)


Workflow
--------

.. rst-class:: header-on-a-card header-steps

Step 1: Create a New Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Plugin Task you will define will output a Numpy array. Before registering this output in your plugin task, you need to **define the Numpy array type** in Dioptra.

1. Navigate to the **Plugin Parameters** tab.
2. Click **Create**.
3. Enter the name: ``NumpyArray``. Add an optional short description. 
4. Click **Submit**.

.. figure:: ../../images/screenshots/plugin_param_types/create_plugin_parameter_numpy_array_dioptra_1_1.png
   :alt: Screenshot of creating a new type called NumpyArray.
   :width: 900px
   :figclass: border-image clickable-image

   Creating a new Parameter Type in the GUI.

.. admonition:: Learn More

   * :ref:`explanation-plugin-parameter-types` - Explainer on Plugin Parameter Types


.. rst-class:: header-on-a-card header-steps

Step 2: Create the Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will now create a new plugin with one task. This task accepts four parameters:

* ``random_seed``
* ``sample_size``
* ``mean``
* ``var``

The function samples a normal distribution, logs the mean, and then returns the array.

**Steps** 

1. Go to the **Plugins** tab and click the **Create** button in the Plugins table.
2. Name it ``sample_normal`` and add a short description. Click **Submit** to save the Plugin. 
3. In the plugin list, **click the row** corresponding to the ``sample_normal`` Plugin you just created to go to the Plugin Files table.
4. Click the **Create** button to add a new Python file. Name it ``sample_normal.py`` and add a description.
5. Paste the code below into the editor.

.. admonition:: sample_normal.py
    :class: code-panel python

    .. literalinclude:: ../../../../docs/source/documentation_code/plugins/essential_workflows_tutorial/sample_normal.py
       :language: python

.. rst-class:: header-on-a-card header-steps

.. _tutorial-1-part-2-register-the-task:

Step 3: Register the Task
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unlike in simple logging function task with no inputs/outputs from the :ref:`Hello World <tutorial-hello-world-in-dioptra>` tutorial, this task requires us to register the inputs and outputs along with their Parameter Types. Using Dioptra's autodetect functionality will help here.

1. Click **Import Function Tasks** (top right of the editor) to auto-detect functions from ``sample_normal.py``.

.. figure:: ../../images/screenshots/plugin_files/import_function_tasks_sample_normal_dioptra_1_1.png
   :alt: Screenshot of the "Import Function Tasks" button.
   :width: 900px
   :figclass: border-image clickable-image

   Using "Import Tasks" to automatically detect and register plugin tasks.

.. note::
   Input and output types are auto-detected from **Python type hints** and the **return annotation** (``->``).

2. You may see an error under **Plugin Tasks**: *Resolve missing type* for the ``np_ndarray`` output. This is because the custom type is called ``NumpyArray``, not ``np_ndarray``, which is the default name inferred from the return type.

.. figure:: ../../images/screenshots/plugin_files/resolve_missing_type_numpy_array_dioptra_1_1.png
   :alt: Screenshot of a missing type error in Plugin Task registration.
   :width: 900px
   :figclass: border-image clickable-image

   The output type was detected as np_ndarray, but the type you created is called NumpyArray.

**Fix the mismatched param type**:

* Click the ``output`` badge.
* Set **Name** to ``output`` and **Type** to ``NumpyArray``.

*Alternatively*, you could go back and edit the name of your Plugin Parameter Type to ``np_ndarray``.

Once you've corrected the errors, **save** the plugin file by clicking **Submit File**.

.. admonition:: Learn More

   * :ref:`reference-plugins` - Syntax reference for creating plugins


.. rst-class:: header-on-a-card header-steps

Step 4: Create Entrypoint Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will create an entrypoint that accepts a parameter, allowing you to change the sample size passed to this Function Task dynamically at Job runtime. 

1. Navigate to **Entrypoints** and click **Create Entrypoint**.
2. Name it ``sample_normal_ep`` and add a short description. 
3. Attach the ``tensorflow-cpu`` Queue to the Entrypoint.
4. In the **Entrypoint Parameters** window, click **Add Parameter**:

   - **Name:** ``sample_size``
   - **Type:** ``integer``
   - **Default value:** ``100``

.. figure:: ../../images/screenshots/entrypoints/create_entrypoint_parameter_sample_size_dioptra_1_1.png
   :alt: Screenshot of adding the sample_size parameter to Entrypoint 2.
   :width: 900px
   :figclass: border-image clickable-image

   Creating an entrypoint parameter allows the parameter to be changed during a job run.

.. rst-class:: header-on-a-card header-steps

Step 5: Define Task Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now add the task to the graph and bind the parameters.

1. In the **Task Plugins** window, select ``sample_normal``.
2. Click **Add to Task Graph**. This auto-populates the YAML with default structure.

.. figure:: ../../images/screenshots/entrypoints/add_to_task_graph_sample_normal_dioptra_1_1.png
   :alt: Screenshot of adding sample_normal to Entrypoint 2.
   :width: 900px
   :figclass: border-image clickable-image

   Using "Add To Task Graph" to automatically populate the YAML editor.

3. Edit the YAML to bind the parameters. Map ``sample_size`` to the entrypoint parameter (``$sample_size``) and hardcode the others to something reasonable (e.g. ``random_seed=0``, ``mean=10``, ``var=10``). Rename the **step-name** to ``draw_and_log``.


.. figure:: ../../images/screenshots/entrypoints/task_graph_editor_sample_normal_dioptra_1_1.png
   :alt: Screenshot of editing parameters in Entrypoint 2 task graph.
   :width: 900px
   :figclass: border-image clickable-image

   Binding the task parameters in the YAML editor.

4. Ensure the task graph is valid by clicking **Validate Inputs**. Assuming all Types are set appropriately for inputs / outputs, this should pass.
5. Click **Submit Entrypoint** to save.

.. admonition:: Learn More 

   See :ref:`reference-entrypoints-task-graph-syntax` for detailed reference documentation on Task Graph YAML syntax 

.. rst-class:: header-on-a-card header-steps

Step 6: Create an Experiment and Run Jobs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will create an Experiment and then run multiple Jobs within it using different parameters.

1. Navigate to the **Experiments** tab. Create a new Experiment called ``Sample Normal``.
2. In the **Entrypoints** list, add the ``sample_normal_ep`` Entrypoint.
3. Click **Submit Experiment**, then **click the row** corresponding to that Experiment.
4. Click **Create** in the Jobs table.
5. Select ``sample_normal_ep`` for the Entrypoint and ``tensorflow-cpu`` for the queue.

**Submit a high sample size job**:

6. Set the ``sample_size`` parameter to ``10000``. Add a Job description.
7. Click **Submit Job**.

.. figure:: ../../images/screenshots/jobs/submit_job_sample_normal_10000_sample_size_dioptra_1_1.png
   :alt: Screenshot of running Entrypoint 2 with sample_size=10000.
   :width: 900px
   :figclass: border-image clickable-image

   Setting the sample size parameter for a job to 10,000.

**Submit a low sample size job**:

8. Create a **second job** using ``sample_normal_ep``, but this time leave ``sample_size`` at the default ``100``.

.. figure:: ../../images/screenshots/jobs/jobs_table_sample_normal.png
   :alt: Screenshot showing multiple jobs created with different sample sizes.
   :width: 900px
   :figclass: border-image clickable-image

   Jobs queue, start, and finish.

.. rst-class:: header-on-a-card header-steps

Step 7: Inspect Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the jobs finish, inspect the logs for each.

**Job with Sample Size 100:**

.. admonition:: Log Output (Small Sample)
   :class: code-panel console

   .. code-block:: console

      [info     ] Plugin 2 - The mean value of the draws was 10.2565, which was 0.2565 different from the passed-in mean (2.56%). [Passed-in Parameters]Seed: 0; Mean: 10; Variance: 10; Sample Size: 100; [sample_normal.sample_normal]

**Job with Sample Size 10,000:**

.. admonition:: Log Output (Large Sample)
   :class: code-panel console

   .. code-block:: console

      [info     ] Plugin 2 - The mean value of the draws was 10.0200, which was 0.0200 different from the passed-in mean (0.20%). [Passed-in Parameters]Seed: 0; Mean: 10; Variance: 10; Sample Size: 10000; [sample_normal.sample_normal]

Notice that the sample mean was much closer to the distribution mean when the sample size was larger.

.. note::
   This experiment is a simple illustration of the **Law of Large Numbers**: as the sample size increases, the sample mean tends to get closer to the population mean.

Conclusion
----------

You now know how to:

- Define custom :ref:`Types <explanation-plugin-parameter-types>`
- Register :ref:`Plugin Tasks <explanation-plugins>` with inputs and outputs
- Run :ref:`Entrypoints <explanation-entrypoints>` and :ref:`Jobs <explanation-experiments-and-jobs>` with parameters

Next, :ref:`you'll chain multiple tasks together <tutorial-building-a-multi-step-workflow>` into a single workflow.