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

.. _how-to-create-queues:

Create Queues
========================

This how-to explains how to build :ref:`Queues <queues-explanation>` in Dioptra. Queues logically represent a 
queue of jobs for workers to pull from. 

.. note::
   In order for a queue to be effective, :ref:`Workers <explanation-queues-and-workers>`
   which listen on that queue are necessary.

   If the worker is already created or running, check what queue name it is using and create if it doesn't exist.

   If the queue you created has no worker, then you will need to start one, as the jobs sent to that queue will not be
   processed without a worker.


Prerequisites
-------------

.. tabs:: 

   .. group-tab:: GUI

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.
      * :ref:`tutorial-setup-dioptra-in-the-gui` - Access Dioptra services in the GUI, create a user, and login.

   .. group-tab:: Python Client

      * :ref:`how-to-prepare-deployment` -  A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.

.. _how-to-create-queues-queue-creation-workflow:

Queue Creation Workflow
----------------------

Follow these steps to create and register a new queue. You can perform these actions via the Guided User Interface (GUI) or programmatically using the Python Client.

.. rst-class:: header-on-a-card header-steps


Step 1: Create the Queue
~~~~~~~~~~~~~~~~~~~~~~~

Register a queue for a specific group, with a name and a description.

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Queues** tab. Click **Create**. Enter a *name* and, optionally, a *description*, select a *group* for the queue, then click **Confirm**.
      
      .. note:: 
          Dioptra does not currently support the creation of additional groups. All resources are under the same default public group.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to create the queue.

      .. automethod:: dioptra.client.queues.QueuesCollectionClient.create


Step 2: Associate your Queue with Existing Entrypoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Entrypoints** tab. Click one
      of the existing entrypoints to add the newly created queue to.
      
      Under **Basic Info**, select the queue you just created for **Queues**.
      Click **Submit Entrypoint** when finished.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to update the entrypoint with the id of the queue.

      .. automethod:: dioptra.client.entrypoints.EntrypointQueuesSubCollectionClient.modify_by_id


.. rst-class:: fancy-header header-seealso

See Also 
--------

* :ref:`Queues and Workers <explanation-queues-and-workers>` - Understand what queues and workers are for.