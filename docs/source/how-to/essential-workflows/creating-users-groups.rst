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

.. _how-to-create-users-and-groups:

Create Users and Groups
========================

Currently, groups cannot be created in Dioptra - the users all share a single group.

This how-to explains how to create :ref:`Users <users-groups-explanation>` in Dioptra. 

Prerequisites
-------------

.. tabs:: 

   .. group-tab:: GUI

      * :ref:`getting-started-running-dioptra` - A deployment of Dioptra is required.

   .. group-tab:: Python Client

      * :ref:`getting-started-running-dioptra` -  A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.

.. _how-to-create-plugins-plugin-creation-workflow:

User Creation Workflow
----------------------

Follow these steps to create and register a new user. You can perform these actions via the Guided User Interface (GUI) or programmatically using the Python Client.

.. rst-class:: header-on-a-card header-steps


Step 1: Create the User
~~~~~~~~~~~~~~~~~~~~~~~

Register a user with a username, email address, and password to be able to create and access resources.

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, if you are not logged in, the front page will display a login screen. If you are logged in,
      click your username in the top right corner of the interface, and then click **LOG OUT** to log out.
      
      Click **Signup** and 
      enter the username, email address, and password for the user.

      Click **Register** when finished to create the user.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to create the user.

      .. automethod:: dioptra.client.users.UsersCollectionClient.create


