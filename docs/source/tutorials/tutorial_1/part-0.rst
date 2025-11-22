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

.. _tutorial-1-part-0:

Setup
=====================

Before running your first plugin task, we need to prepare the environment.

Start the Dioptra Services
--------------------------

.. note:: 
   If you have not already built the Dioptra Docker containers, you need to do that first.
   See :ref:`getting-started-building-the-containers`

Make sure the Dioptra Docker containers are running:

.. code-block:: bash

   docker compose up

You should now be able to access the Dioptra web UI in your browser (default: http://127.0.0.1).

Login or Sign Up
----------------

Open the web UI and either **log in** with an existing account or **sign up** for a new one.

.. figure:: _static/screenshots/login_dioptra.png
   :alt: Screenshot of the Dioptra login page with sign-in and sign-up options.
   :width: 900px
   :figclass: border-image clickable-image

.. note::
   More info is available at :ref:`how_to_create_a_user` (forthcoming)

Groups
------

Navigate to the **Groups** tab.  
You should see only the default **Public** group — this is where we will run our first experiments.

.. figure:: _static/screenshots/groups_dioptra.png
   :alt: Screenshot of the Groups tab showing the Public group.
   :figclass: border-image clickable-image

Queues
------

Navigate to the **Queues** tab and create a new queue:

- **Name:** `tensorflow_cpu`  
- **Visibility:** Public  


We call it `tensorflow_cpu` because this tutorial assumes only CPU resources are available.  
By making it **public**, all users in the Public group can submit jobs to it.

.. note::
   For more info, see our how-to on Queue creation: :ref:`how_to_create_a_queue`

.. figure:: _static/screenshots/queues_dioptra.png
   :alt: Screenshot of the queue creation form with "tensorflow_cpu" entered as the name.
   :figclass: border-image clickable-image

.. note::
   To learn more about the purpose of groups and queues, refer to these explanation materials:

   - :ref:`explanation-groups` (forthcoming)
   - :ref:`explanation-queues` (forthcoming)

Next Steps
----------

Now that Dioptra is set up, let's begin: :ref:`tutorial-1-part-1`