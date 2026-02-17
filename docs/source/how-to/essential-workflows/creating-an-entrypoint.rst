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

This how-to explains how to build :ref:`Entrypoints <explanation-entrypoints>` in Dioptra. 


Prerequisites
-------------

.. tabs:: 

   .. group-tab:: GUI

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.
      * :ref:`tutorial-setup-dioptra-in-the-gui` - Access Dioptra services in the GUI, create a user, and login.
      * :ref:`how-to-create-plugins` - Plugins are needed to attach to the Entrypoint
      * :ref:`how-to-create-queues` - A queue is needed to attach to the Entrypoint

   .. group-tab:: Python Client

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.
      * :ref:`how-to-create-plugins` - Plugins are needed to attach to the Entrypoint
      * :ref:`how-to-create-queues` - A queue is needed to attach to the Entrypoint



Entrypoint Creation Workflow
------------------------

Follow these steps to create an Entrypoint. You can perform these actions via the Graphical User Interface (GUI) or programmatically using the Python Client.

.. rst-class:: header-on-a-card header-steps

Step 1: Locate Plugins, Queues, Groups, and Parameter Types to attach to the Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tabs::

   .. group-tab:: GUI

      Ensure you have created at least one :ref:`plugin <how-to-create-plugins>` and at least one :ref:`queue <how-to-create-queues>`.

      You will be able to automatically select these resources in the GUI using dropdown menus in the following steps.


   .. group-tab:: Python Client

      Retrieve IDs for the following resources:
      
      - **Plugins**
      - **Queues**
      - **Groups**
      - **Plugin Parameter Types**

      **Groups:**

      .. automethod:: dioptra.client.groups.GroupsCollectionClient.get

      **Plugins:**

      .. automethod:: dioptra.client.plugins.PluginsCollectionClient.get

      **Parameter Types:**

      .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.get

      **Queues:**

      .. automethod:: dioptra.client.queues.QueuesCollectionClient.get


.. rst-class:: header-on-a-card header-steps


Step 2: Create an Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Entrypoints** tab. Click **Create**. Enter metadata, including:
      
      - **name**
      - **group**
      - **queues**
      - **description** (optional)


   .. group-tab:: Python Client

      Create the Entrypoint using the Client. Use the Group ID, Plugin IDs, Queue IDs, and Parameter Type IDs from step 1. 
      Also pass in the following as parameters:

      - **Task Graph YAML**
      - **Artifact Graph YAML** (optional)
      - **Parameters** (optional)
      - **Artifact Input Parameters** (Optional)
      - **Description** (Optional)

      **Entrypoint client CREATE method:**

      .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.create

.. rst-class:: header-on-a-card header-steps


Step 3: Add Entrypoint Parameters (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Entrypoints are parameterizable. Any parameters or artifact input parameters you create can be specified when an Entrypoint is :ref:`run as a job <how-to-running-jobs>`. 

.. tabs::

   .. group-tab:: GUI

      On the Entrypoint creation page, go to the **Entrypoint Parameters** box and click **Create**. 

      For each parameter, enter the following:

      - **Name**
      - **Type**
      - **Default Value** (optional). 

   .. group-tab:: Python Client

      The parameter values were provided as a list of dictionaries during entrypoint creation in :ref:`Step 2 <step-2-create-an-entrypoint>`. 

.. rst-class:: header-on-a-card header-steps


Step 4: Add Artifact Input Parameters (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you would like this entrypoint to load an artifact from disk and make it available to the Task Graph, create an artifact input parameter. 

.. tabs::

   .. group-tab:: GUI

      On the Entrypoint creation page, go to the **Artifact Parameters** box and click **Create**. 

      For each artifact input parameter, provide the following: 

      - **Artifact Input Name** 
      - **Output Parameters** (one or more)

      An artifact task can produce multiple output parameters in the ``deserialize()`` method. Which artifact handler is used is selected at job run time. 

      For each artifact input's output parameter, provide the following:

      - **Output Parameter Name**
      - **Output Parameter Type**


   .. group-tab:: Python Client

      The artifact input parameters values were provided as a list of dictionaries during entrypoint creation in :ref:`Step 2 <step-2-create-an-entrypoint>`. 

.. rst-class:: header-on-a-card header-steps


Step 5. Create the Task Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an entrypoint is run as a job, the task graph will be executed by the worker in order. Define the Task Graph for the entrypoint. 

.. tabs::

   .. group-tab:: GUI

      On the Entrypoint creation page, scroll to the **Task Graph Info** box and select the **Task Plugins** dropdown - select any Plugins that you want to use for this Entrypoint.

      In the **Task Graph** code editor, add YAML code that defines your Task Graph. You can also add tasks to the code editor by clicking **add to task graph** from the **Function Tasks** table. 

   .. group-tab:: Python Client

      - The task graph YAML was provided as a string during entrypoint creation in :ref:`Step 2 <step-2-create-an-entrypoint>`. 
      - The Plugin IDs for task plugins were provided during entrypoint creation in :ref:`Step 2 <step-2-create-an-entrypoint>`. 

.. rst-class:: header-on-a-card header-steps


Step 6. Create the Artifact Task Graph (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to save any objects from your entrypoint to disk, you need to define that logic in the Artifact Task Graph section. 

.. tabs::

   .. group-tab:: GUI

      On the Entrypoint creation page, scroll to the **Artifact Info** box and select the **Artifact Task Plugins** dropdown - select any plugins that you wish to use the Artifact Tasks from.

      In the **Artifact Output Graph** code editor, add YAML code that defines your Artifact Output Graph. You can also add artifact tasks to the code editor by clicking **add to task graph** from the **Artifact Tasks** table. 

   .. group-tab:: Python Client

      - The artifact output graph YAML is provided as a string during entrypoint creation. 
      - The Plugin IDs for artifact plugins are provided during entrypoint creation. 


.. rst-class:: header-on-a-card header-seealso

See Also 
---------

* :ref:`Entrypoints explanation <explanation-entrypoints>` - Understand what entrypoints are conceptually.
* :ref:`Entrypoints: Syntax reference for YAML <reference-entrypoints>` - See syntax and other reference material for entrypoints 
* :ref:`Task Graphs explanation <explanation-task-graph>` - Learn more about the Task Graphs 
* :ref:`Artifacts: explanation <explanation-artifacts>` - Learn about artifacts.

