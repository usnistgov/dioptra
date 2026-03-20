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

.. _tutorial-using-saved-artifacts:

Using Saved Artifacts
=====================

Overview
--------

In the last section, you learned how to save task outputs as artifacts. Now, you will take the next step: **using a saved artifact as input in a new workflow**.

This is done through **artifact parameters**. They behave like Entrypoint parameters, but instead of being set at job creation, they are **loaded from disk**. You can then reference them throughout the task graph.


Using Saved Artifacts in an Entrypoint Task Graph 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, you will build a new workflow that:

- **Loads** a NumPy array **artifact** that was saved from :ref:`the last tutorial step <tutorial-saving-artifacts>`
- Applies **multiple rescaling methods**
- **Visualizes** the results with Matplotlib
- **Saves** the resulting **PNG file as a new artifact**

To accomplish this, you'll need to perform the following:

- **Create a new Artifact Handler** that is capable of serializing Matplotlib figures to PNG files
- **Define a new Plugin** that reads in a Numpy array as an input and produces a Matplotlib figure as an artifact 
- **Define a new Entrypoint** to use the new plugin and new artifact handler

Once all that is done, we can run a job for this Entrypoint and **select the previously saved NumPy Array** as the **Artifact Input Parameter**. 


Workflow
--------

.. rst-class:: header-on-a-card header-steps

Step 1: Add two New Plugin Parameter Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You'll use the python ``dict`` type and the ``bytes`` type in your next Function Task and Artifact Task, so go ahead and add them now:

1. Go to the **Plugin Parameters** tab.
2. Create two new types:

   1. Type one: Called ``dict`` (for a Python dictionary type object)
   2. Type two: Called ``bytes`` (for a raw PNG image)

3. For each type, add the name an a short description, then click **Submit**.

.. rst-class:: header-on-a-card header-steps

Step 2: Create the "rescale_and_graph_array" Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You want to create a plugin that utilizes a saved numpy array as an *input*.

1. Go to the **Plugins** tab and click **Create**.
2. Name it ``rescale_and_graph_array`` and add a short description.
3. **Open** the Plugin. **Create** a new file named ``rescale_and_graph_array.py``.
4. Copy and paste the code below.
5. Import the functions via **Import Function Tasks**. Fix any types as needed.

.. admonition:: rescale_and_graph_array.py
    :class: code-panel python

    .. literalinclude:: ../../../../docs/source/documentation_code/plugins/essential_workflows_tutorial/rescale_and_graph_array.py
       :language: python

6. Click **Submit File** 

.. note::
   This plugin defines two new tasks:

   - ``scale_array``: to rescale the input array three different ways.
   - ``visualize_rescaling_multi``: to visualize all the rescaled arrays.

.. rst-class:: header-on-a-card header-steps

Step 3: Add Another Artifact Task
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your second plugin task outputs a Matplotlib figure as a PNG image. To view this output, you need to save it as an artifact. You will **add a new artifact plugin task** that serializes a Matplotlib object as a PNG.

1. In the **Plugins** tab, open your ``artifacts`` Plugin from the previous :ref:`tutorial step <tutorial-saving-artifacts-step-1-create-an-artifact-plugin>`.
2. Open the ``artifacts.py`` file. **Add the new artifact plugin class code** to the bottom of the file to define ``PngBytesArtifactTask``.
3. **Register** this new Artifact Task in your plugin the same way as the ``NumpyArrayArtifactTask`` (see :ref:`tutorial-saving-artifacts-step-2-register-artifact-task`).

   * **Name**: ``PngBytesArtifactTask``
   * **Output Parameters - Name**: ``output``
   * **Output Parameters - Type**: ``bytes``

**Code to paste to the bottom of the artifacts.py file:**

.. admonition:: artifacts.py (add to bottom)
    :class: code-panel python

    .. literalinclude:: ../../../../docs/source/documentation_code/plugins/essential_workflows_tutorial/artifacts.py
       :language: python
       :start-after: # [pngbytes-plugin-definition]
       :end-before: # [end-pngbytes-plugin-definition]


6. Click **Submit File** to save your changes to ``artifacts.py``

.. rst-class:: header-on-a-card header-steps

Step 4: Create "rescale_and_graph_array" Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now define a **new Entrypoint** that loads the array, transforms it, and saves the plot.

1. Go to the **Entrypoints** tab and view the Entrypoints table.

.. note:: 
   **Note**: Dioptra saves **Snapshots** of Resources each time Resources are modified. Notice that the artifacts Plugin, which we just updated, is now out of sync for the ``sample_and_transform`` Entrypoint. If an Entrypoint is referencing an old Plugin snapshot, Dioptra will warn you. 
   
   Feel free to sync this Plugin now or to ignore this warning - it is irrelevant for this portion of the tutorial. 

   .. figure:: ../../images/screenshots/entrypoints/entrypoints_plugin_out_of_date_dioptra_1_1.png
      :alt: Screenshot showing Plugin attached to entrypoint as being outdated
      :width: 100%
      :figclass:  border-image clickable-image



2. Click **Create** in the Entrypoints table.
3. Name the new Entrypoint ``rescale_and_graph_array_ep``. Attach ``tensorflow-cpu`` as a **Queue** and provide a **description**. 

**Add Parameters:**

4. In the **Entrypoint Parameters** box, add:

   - **Name:** ``figure_title``
   - **Type:** ``string``
   - **Default:** ``"Comparing rescaling methods plot"``

5. In the **Artifact Parameters** box, add the input parameter:

   - **Artifact parameter name:** ``artifact_input_array``
   - **Output parameter name:** ``output``
   - **Output parameter type:** ``NumpyArray``

.. figure:: ../../images/screenshots/entrypoints/ep_w_artifact_and_regular_parameters_dioptra_1_1.png
   :alt: Screenshot showing artifact parameter input in Entrypoint rescale_and_graph_array_ep.
   :width: 100%
   :figclass:  border-image clickable-image

   Create one Entrypoint parameter and one artifact parameter.

.. note::
   The specific artifact instantiated for a given artifact Entrypoint parameter is decided at job runtime.

**Define Task Graph:**

6. In the **Task Plugins** window, select the relevant plugin:

   * **Task Plugins**: ``rescale_and_graph_array``

7. Copy the **Task Graph** YAML below into the **Task Graph editor**. 


.. admonition:: rescale_and_graph_array_ep: Task Graph YAML
    :class: code-panel yaml

    .. literalinclude:: ../../../../docs/source/documentation_code/task_graphs/essential_workflows_tutorial/rescale_and_graph_array.yaml
       :language: yaml

.. note::
   Note the reference to ``$artifact_input_array`` in the task graph. This is referencing the loaded artifact.

**Define Artifact Output Graph:**
  
8. In the **Artifact Task Plugins** window, select the relevant plugin:

   * **Artifact Task Plugins**: ``artifacts``

9. Then, copy the **Artifact Output Graph** YAML below and paste it into the code editor for the **Artifact Output Graph**. It saves the generated matplotlib figure from step 2.

.. admonition:: rescale_and_graph_array: Artifact Output Task Graph YAML
    :class: code-panel yaml

    .. literalinclude:: ../../../../docs/source/documentation_code/artifact_task_graphs/essential_workflows_tutorial/save_graph_artifacts.yaml
       :language: yaml

.. figure:: ../../images/screenshots/entrypoints/artifact_output_and_task_graph_dioptra_1_1.png
   :alt: Screenshot showing the task graph editors.
   :width: 100%
   :figclass:  border-image clickable-image

   Showing how the Artifact Input Parameter is used in the task graph to produce a new output (a Matplotlib figure) which is then saved in the Artifact Output Graph

10. Click **Validate Inputs** - it should pass.
11. Click **Submit Entrypoint**.

.. rst-class:: header-on-a-card header-steps

Step 5: Create Experiment and Run a Job
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, test it out.

1. Create a new Experiment named ``Rescale and Graph Array Exp``. Add a description. 
2. Add the ``rescale_and_graph_array_ep`` entrypoint. Click **Submit Experiment**.
3. Under this new experiment, **create a new job**.
4. Select the correct Entrypoint (``rescale_and_graph_array_ep``) and add a description for the Job run. 
5. Under the **Artifact Parameters** box, select the Artifact generated from :ref:`the previous step <tutorial-saving-artifacts>`.
6. Click **Submit Job**.


.. figure:: ../../images/screenshots/jobs/utilizing_artifact_input_param_dioptra_1_1.png
   :alt: Screenshot of job configuration showing artifact input parameter selection.
   :width: 100%
   :figclass:  border-image clickable-image

   Selecting the input artifact at runtime.

.. rst-class:: header-on-a-card header-steps

Step 6: Inspect Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After running the job, open the Job and **download** the **Output Artifact** - it should be a PNG file that was saved from your Entrypoint. 


**Artifact Output** from ``rescale_and_graph_array_ep``:

.. figure:: _static/screenshots/entrypoint_5_artifact_visualization.png
   :alt: The Matplotlib figure created from rescale_and_graph_array_ep showing three scatter plots of rescaled data.
   :width: 100%
   :figclass:  border-image clickable-image

   The artifact that was generated from this Entrypoint - a Matplotlib figure showing the various rescaling methods.

The original NumPy array artifact from the :ref:`the previous workflow <tutorial-saving-artifacts>` ranged from roughly 0 to 500+. Here's how the three scaling methods reshape it:

- **Min-Max Scaling**: Linearly maps values into [0,1], preserving relative spacing.
- **Z-Score Scaling**: Centers data at 0 with unit variance; shows distance from the mean.
- **Log1p Scaling**: Nonlinear compression; reduces the impact of large values and outliers.

Conclusion
----------

You now know how to:

- Create Entrypoints that use **artifact parameters** as inputs
- **Chain workflows together** across experiments using artifacts

**Tutorial complete!**
You're now ready to design your own workflows in Dioptra by combining multiple plugins, artifacts, and experiments.

.. rst-class:: header-on-a-card header-seealso

Keep Learning 
-------------
This tutorial demonstrated the core functionalities of Dioptra. To see more interesting and complicated uses of
these capabilities, view the :ref:`advanced tutorials <tutorial-advanced-tutorials>` which utilize the Python Client for more complex workflows. 