:html_theme.sidebar_secondary.remove:
:html_theme.content_width: 100%

Using Saved Artifacts
=====================

Overview
--------

In the last section, you learned how to save task outputs as artifacts.  
Now, we will take the next step: **using a saved artifact as input in a new workflow**.  

This is done through **artifact parameters**. They behave like Entrypoint parameters, but instead of being set at job creation, they are **loaded from disk**. You can then reference them throughout the task graph.  

In this example, we will build a new workflow that:

- Loads a saved NumPy array artifact from Entrypoint 4  
- Applies multiple rescaling methods  
- Visualizes the results with Matplotlib  
- Saves the resulting figure as a new artifact  



Create a Rescaling Plugin
----------------------------------

First, we need a new plugin containing several rescaling methods.  
This is similar to first few steps in this tutorial.

.. admonition:: Steps

   1. Go to the **Plugins** tab → **Create Plugin**.  
   2. Name it ``rescaling_plugin`` and add a short description.  
   3. Copy and paste the code below.  
   4. Import the functions via **Import Function Tasks**.  

**Rescaling Plugin Code**

.. literalinclude:: ../../../../examples/tutorials/tutorial_1/plugin_4.py
   :language: python
   :linenos:

This plugin defines two new tasks - ``scale_array`` to rescale the array three different ways and ``visualize_rescaling_multi`` to visualize all the rescaled arrays. 



Add Matplotlib Figure Artifact
---------------------------------------

Next, let’s update the artifact plugin so that we can save a Matplotlib figure (the output of our second task).

.. admonition:: Steps

   1. Open your ``artifact_plugin`` from Part 4.  
   2. Add the code below to define ``MatplotlibArtifactTask``.  
   3. Register it the same way as the ``NumpyArrayArtifactTask``.  

**Matplotlib Artifact Code**

.. literalinclude:: ../../../../examples/tutorials/tutorial_1/matplotlib_fig_artifact_plugin.py
   :language: python
   :linenos:



Create Entrypoint 5
-------------------------

Now let’s define a new Entrypoint that uses an artifact as input.  

.. admonition:: Steps

   1. Go to the **Entrypoints** tab → **Create Entrypoint**.  
   2. Name it ``entrypoint_5``.  
   3. Copy the following code into the Task Graph 

**Entrypoint 5 Task Graph** 

.. literalinclude:: ../../../../examples/tutorials/tutorial_1/entrypoint_5_task_graph.yaml
   :language: yaml
   :linenos:

.. note::
    Note that we are referencing ``$artifact_input_array``. We need to define this as a artifact input param. 

.. admonition:: Steps (continued)
    In addition to the task graph, also define the artifact output graph to save the Matplotlib figure

**Entrypoint 5 Artifact Output Task Graph**

.. literalinclude:: ../../../../examples/tutorials/tutorial_1/entrypoint_5_artifact_output_task_graph.yaml
   :language: yaml
   :linenos:

.. figure:: _static/screenshots/entrypoint_5_task_graph_and_artifact_output_graph.png
   :alt: Screenshot showing artifact parameter input in Entrypoint 5.
   :width: 100%
   :figclass: big-image border-image clickable-image



.. admonition:: Steps (finalized)

   1. Add an **artifact parameter** pointing to the saved NumPy array artifact from Part 4.  
   2. Add standard parameters if desired (e.g., plot title).  

.. figure:: _static/screenshots/entrypoint_5_params_and_artifact_params.png
   :alt: Screenshot showing artifact parameter input in Entrypoint 5.
   :width: 100%
   :figclass: big-image border-image clickable-image



Create Experiment and Job
----------------------------------

Finally, let’s test it out.

.. admonition:: Steps

   1. Create a new Experiment (``experiment_3``).  
   2. Add **Entrypoint 5**.  
   3. Create a new Job.  
   4. When configuring the job, select the artifact snapshot created in Part 4.  

.. figure:: _static/screenshots/job_select_artifact.png
   :alt: Screenshot of job configuration showing artifact snapshot selection.
   :width: 100%
   :figclass: big-image border-image clickable-image



Inspect Results
---------------

After running the job, open the logs and artifact view. Comparing the original array to rescaling methods


The original NumPy array from Entrypoint 4 ranged from 0–516.  
Here’s how the three scaling methods reshape it:

- **Min–Max Scaling**: Linearly maps values into $[0,1]$, preserving relative spacing.  
- **Z-Score Scaling**: Centers data at 0 with unit variance; shows distance from the mean.  
- **Log1p Scaling**: Nonlinear compression; reduces the impact of large values and outliers.  

The saved Matplotlib figure should display these transformations side-by-side.  


**Artifact Output from Entrypoint 5**

.. figure:: _static/screenshots/entrypoint_5_artifact_visualization.png
   :alt: The Matplotlib Figure created from Entrypoint 5 showing three scatter plots of rescaled data
   :width: 100%
   :figclass: big-image border-image clickable-image




Conclusion
----------

You now know how to:

- Define new plugins for additional data transformations  
- Extend the artifact plugin to handle new object types (e.g., Matplotlib figures)  
- Create Entrypoints that use **artifact parameters** as inputs  
- Chain workflows together across Experiments using artifacts  

**Tutorial complete!** 
You’re now ready to design your own workflows in Dioptra, combining multiple plugins, artifacts, and experiments.
