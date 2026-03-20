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

.. _how-to-create-experiments:

Create Experiments
==================

This how-to explains how to build :ref:`Experiments <explanation-experiments-and-jobs>` in Dioptra.

Prerequisites
-------------

.. tabs::

   .. group-tab:: GUI

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.
      * :ref:`tutorial-setup-dioptra-in-the-gui` - Access Dioptra services in the GUI, create a user, and login.
      * :ref:`how-to-create-entrypoints` - Entrypoints are needed to attach to the Experiment

   .. group-tab:: Python Client

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.
      * :ref:`how-to-create-entrypoints` - Entrypoints are needed to attach to the Experiment

Experiment Creation Workflow
----------------------------

Follow these steps to create an Experiment. You can perform these actions via the Graphical User Interface (GUI) or programmatically using the Python Client.

.. rst-class:: header-on-a-card header-steps

Step 1: Locate Entrypoints to attach to the Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. tabs::

   .. group-tab:: GUI

      Ensure you have created at least one :ref:`entrypoint <how-to-create-entrypoints>`.

      You will be able to automatically select these resources in the GUI using dropdown menus in the following steps.


   .. group-tab:: Python Client

      Retrieve IDs for the following resources:

      - **Groups**
      - **Entrypoints**

      **Groups:**

      .. automethod:: dioptra.client.groups.GroupsCollectionClient.get
         :noindex:

      **Queues:**

      .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.get
         :noindex:

.. rst-class:: header-on-a-card header-steps

Step 2: Locate Entrypoints to attach to the Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Experiments** tab. Click **Create**. Enter metadata, including:

      - **name**
      - **group**
      - **entrypoints**
      - **description** (optional)

      Click **Submit Experiment** when finished.

   .. group-tab:: Python Client

      Create the Experiment using the Client. Use the Group ID, and Entrypoint IDs from step 1.
      Also pass in the following as parameters:

      - **Name**
      - **Description** (Optional)

      **Experiment client CREATE method:**

      .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.create
         :noindex:



.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`Experiments Explanation <explanation-experiments-and-jobs>` - Understand what experiments are conceptually.
* :ref:`Experiments Reference <reference-experiments>` - Reference page for experiments.
