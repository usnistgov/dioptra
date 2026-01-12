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

.. _how-to-create-plugins:

Create Plugins
========================

This how-to explains how to build :ref:`Plugins <explanation-plugins>` in Dioptra. You will learn how to create a plugin container, add code to it, and register tasks.

Prerequisites
-------------

.. tabs:: 

   .. group-tab:: GUI

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.
      * :ref:`tutorial-setup-dioptra-in-the-gui` - Access Dioptra services in the GUI, create a user, and login.

   .. group-tab:: Python Client

      * :ref:`how-to-prepare-deployment` -  A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.

.. _how-to-create-plugins-plugin-creation-workflow:

Plugin Creation Workflow
------------------------

Follow these steps to create and register a new plugin. You can perform these actions via the Guided User Interface (GUI) or programmatically using the Python Client.

.. rst-class:: header-on-a-card header-steps

Step 1: Prepare your Python Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write your Python functions or Artifact classes in a local file. Ensure you have applied the necessary decorators or class inheritance.

* For standard functions, see :ref:`Function Tasks Reference <reference-plugins-plugin-function-tasks>`.
* For artifact handlers, see :ref:`Artifact Tasks Reference <reference-plugins-plugin-artifact-tasks>`.

.. rst-class:: header-on-a-card header-steps

Step 2: Create the Plugin Container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


First, define the container that will hold your files.

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Plugins tab**. Click **CREATE**. Enter a *name* and *description*, then click **SUBMIT**.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to create the plugin container.

      .. automethod:: dioptra.client.plugins.PluginsCollectionClient.create


.. rst-class:: header-on-a-card header-steps

Step 3: Create a Plugin File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, add your Python code to the container.

.. tabs::

   .. group-tab:: GUI

      Click into your newly created Plugin. Within the Plugin container, click the **"Create"** button in the Plugin Files window. 

      In the Plugin file editor, provide a filename, a description, and paste or upload your Python code (from Step 1) into the code editor.

   .. group-tab:: Python Client
      
      **Client Method:**

      Use the ``client.plugins.files.create()`` method to upload code and register tasks simultaneously.

      .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.create


.. rst-class:: header-on-a-card header-steps

Step 4: Register Tasks (GUI only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, register the tasks so they are visible to Dioptra.

.. tabs::

   .. group-tab:: GUI

      Use the **Task Form** on the right side of the file editor:

      * **For Functions:** Click **"Import Function Tasks"** to auto-detect and register decorated functions (requires type annotations in Python code). Alternatively, register tasks manually:
         
         * **Task Name:** Must match the Python *Function Name* exactly.
         * **Input Params:** Add parameters matching your function arguments exactly.
         * **Output Params:** Define names for the returned values.

      * **For Artifacts:** You must **manually register** the task. 
         
         * **Task Name:** Must match the Python *Class Name* exactly.
         * **Output Params:** Select the **Parameter Type** that corresponds to the object produced by the ``deserialize`` method.

      All inputs and outputs require a **Parameter Type** for validation. See :ref:`Plugin Parameter Types <explanation-plugin-parameter-types>` for more.

   .. group-tab:: Python Client

      This is done as part of ``create()`` method in step 3


.. rst-class:: header-on-a-card header-steps

Step 5: Save and Confirm (GUI only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Once the tasks appear in the list (GUI) or the API call returns successfully (Python Client), your plugin is ready for use in experiments.



.. rst-class:: header-on-a-card header-seealso

See Also 
---------

* :ref:`Overview of Experiments <explanation-workflow-architecture>` - Understand how plugins fit into experiments.
* :ref:`Artifacts: explanation <explanation-artifacts>` - Learn about artifacts.
* :ref:`Learning the Essentials Tutorial: Saving Artifacts <tutorial-saving-artifacts>` - See artifacts used in a data science workflow.
* :ref:`Plugins: reference <reference-plugins>` - More information on syntax requirements for Plugins

