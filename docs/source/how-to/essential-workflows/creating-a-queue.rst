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

This how-to explains how to create :ref:`Queues <explanation-queues-and-workers>` in Dioptra. A Queue is a group-owned API
resource whose name determines the Redis queue used to dispatch jobs to workers.

.. note::
   In order for a queue to process jobs, a :ref:`Worker <explanation-queues-and-workers>` must poll the same queue name.

   If the worker is already running, check which queue name it polls and create an API Queue with the same name if one does
   not exist in the intended group.

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
-----------------------

Follow these steps to create and register a new queue. You can perform these actions through the GUI or programmatically
using the Python client.

.. rst-class:: header-on-a-card header-steps


Step 1: Create the Queue
~~~~~~~~~~~~~~~~~~~~~~~~

Register a queue for a specific group, with a name and a description.

.. tabs::

   .. group-tab:: GUI

      Before creating the queue, use the header group switcher or the Groups page to select the intended active group. In
      the Dioptra GUI, navigate to the **Queues** tab and select **Create**. The read-only **Group** field shows the active
      group that will own the queue. Enter a *name* and, optionally, a *description*, and then select **Submit**.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to create the queue, passing the owning group explicitly as ``group_id``.

      .. automethod:: dioptra.client.queues.QueuesCollectionClient.create
         :noindex:

.. rst-class:: header-on-a-card header-steps

Step 2: Associate your Queue with Existing Entrypoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Entrypoints** tab. Select an existing entrypoint in the same group as the queue.
      
      Under **Basic Info**, select the queue you just created for **Queues**.
      Click **Submit Entrypoint** when finished.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to update the entrypoint with the id of the queue.

      .. automethod:: dioptra.client.entrypoints.EntrypointQueuesSubCollectionClient.modify_by_id
         :noindex:


.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`Queues and Workers Explanation <explanation-queues-and-workers>` - Understand what queues and workers are for.
* :ref:`Queues Reference <reference-queues>` - Queues reference page.
