Getting Started Tutorial
=================

In this tutorial, you will create reusable workflows in Dioptra of increasing complexity. 
Each step will iterate on the previous step, incorporating more features and functionality from Dioptra. 

.. toctree::
   :caption: Steps
   :maxdepth: 1

   part-0
   part-1
   part-2

**By the end of this tutorial, you will have:**

- Loaded in Python files and registered their functions as Dioptra Plugin Tasks
- Created workflows from those Plugin tasks to simulate data, modify that data, and visualize it
- Inspected the output of different entrypoint runs to see how different parameterization options lead to different results

.. note::
   Dioptra supports multiple workflows. In this tutorial, we use the **web UI** to register Plugins, Entrypoints, and other components.  
   The same actions can also be done via the **Python client API** or by defining them in a **TOML configuration file**.  
   See :doc:`../guides/python_client` and :doc:`../guides/configuration` for details on these alternatives.
