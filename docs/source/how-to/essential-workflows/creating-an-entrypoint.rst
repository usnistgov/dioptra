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

.. _how-to-create-entrypoints:

Create Entrypoints
========================

This how-to explains how to build :ref:`Entrypoints <explanation-entrypoints>` in Dioptra. You will learn how to create an entrypoint, define a task graph, and optionally define an artifacts graph to add capture artifacts.

Prerequisites
-------------

.. tabs:: 

   .. group-tab:: GUI

      * :ref:`getting-started-running-dioptra` - A deployment of Dioptra is required.
      * :ref:`tutorial-setup-dioptra-in-the-gui` - Access Dioptra services in the GUI, create a user, and login.
      * :ref:`how-to-create-plugins` - One or more Plugins are needed
      * :ref:`how-to-create-queues` - One or more Queues are needed

   .. group-tab:: Python Client

      * :ref:`getting-started-running-dioptra` -  A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.
      * :ref:`how-to-create-plugins` - One or more Plugins are needed
      * :ref:`how-to-create-queues` - One or more Queues are needed

.. _how-to-create-entrypoints-entrypoint-creation-workflow:

Entrypoint Creation Workflow
------------------------

Follow these steps to create and register a new entrypoint. You can perform these actions via the Guided User Interface (GUI) or programmatically using the Python Client.

.. rst-class:: header-on-a-card header-steps

Step 1: Basic Entrypoint Info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Entrypoints tab**. Click **Create**. Enter a *name* and *description*, then confirm.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to create the entrypoint. The following steps will help you identify the required information.

      .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.create



.. rst-class:: header-on-a-card header-steps

Step 2: Define Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

Next, define the Entrypoint and Artifact parameters, which are the inputs that will be used in this Entrypoint.

See :ref:`the explanation for entrypoint parameters <explanation-entrypoints>`.
.. Note: might be able to link to a specific subsection of the entrypoint explainer.
.. Note: might need separate explainer link for artifact parameters.

.. tabs::

   .. group-tab:: GUI

      Click the **"Create""** button in the Entrypoint Parameters table. Provide a name, select a type from the dropdown, and provide a default value, and click **"Confirm"** to add the new Entrypoint Parameter. It will appear in the table. Repeat until all desired Entrypoint Parameters are defined.

      Click the **"Create""** button in the Artifact Parameters table. Provide a name, then define all output parameters by providing a name, selecting a type, and clicking the **"+"** icon. Then click **"Confirm"** to add the new Artifact Parameter. It will appear in the table. Repeat until all desired Entrypoint Parameters are defined.

   .. group-tab:: Python Client

      **Client Method:**

      Use the ``client.plugin_parameter_types.get()`` method to fetch parameter types which are needed to define Artifact Parameters.

      .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.get


.. rst-class:: header-on-a-card header-steps

Step 3: Write the Task Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :ref:`Overview of Experiments <explanation-task-graph>`

.. tabs::

   .. group-tab:: GUI

      Select 
      Click into your newly created Plugin. Within the Plugin container, click the **"Create"** button in the Plugin Files window. 

      In the Plugin file editor, provide a filename, a description, and paste or upload your Python code (from Step 1) into the code editor.

   .. group-tab:: Python Client
      
      **Client Method:**

      Use the ``client.plugins.get()`` method to fetch plugins, whose tasks you wish to use in this Entrypoint.

      .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.get

      Add plugins.
      .. automethod:: dioptra.client.entrypoints.EntrypointPluginsSubCollectionClient.create

  

.. rst-class:: header-on-a-card header-steps

Step 4: Write the Artifact Graph (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The artifact graph is only needed if you want to save outputs of the task graph as registered Artifacts in Dioptra.

See :ref:`Artifacts <explanation-artifacts>`

.. tabs::

   .. group-tab:: GUI

   .. group-tab:: Python Client

      Use the ``client.plugins.get()`` method to fetch plugins, whose artifact tasks you wish to use in this Entrypoint.

      .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.get

      Add artifact plugins.
      .. automethod:: dioptra.client.entrypoints.EntrypointArtifactPluginsSubCollectionClient.create


.. rst-class:: header-on-a-card header-steps

Step 5: Save and Confirm (GUI only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Once the tasks appear in the list (GUI) or the API call returns successfully (Python Client), your entrypoint is ready for use in experiments.



.. rst-class:: header-on-a-card header-seealso

See Also 
---------

* :ref:`Overview of Experiments <explanation-experiment-overview>` - Understand how entrypoints fit into experiments.
* :ref:`Artifacts: explanation <explanation-artifacts>` - Learn about artifacts.
* :ref:`Learning the Essentials Tutorial: Saving Artifacts <tutorial-saving-artifacts>` - See artifacts used in a data science workflow.
* :ref:`Entrypoints: reference <reference-entrypoints>` - More information on syntax requirements for Entrypoints

