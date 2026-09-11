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

This how-to explains how to create :ref:`Users and Groups <explanation-users-and-groups>` in Dioptra.


Prerequisites
-------------

.. tabs:: 

   .. group-tab:: GUI

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.

   .. group-tab:: Python Client

      * :ref:`how-to-prepare-deployment` -  A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.

.. _how-to-create-users-user-creation-workflow:

User Creation Workflow
----------------------

Follow these steps to create and register a new user. You can perform these actions through the graphical user interface
(GUI) or programmatically using the Python client.

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

      Registration also creates a public personal group whose initial name matches the username. The new user is the
      group's creator, initial member, administrator, and owner.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to create the user.

      .. automethod:: dioptra.client.users.UsersCollectionClient.create
         :noindex:

      The registration response includes the new public personal group. It can also include other public groups that are
      accessible to the user.

Group Creation Workflow
-----------------------

Follow these steps to create an additional group and use it as the active resource context.

.. warning::

   All groups created in this release are public. Authenticated users can read and write resources in public groups even
   when they are not members.

.. rst-class:: header-on-a-card header-steps

Step 1: Create the Group
~~~~~~~~~~~~~~~~~~~~~~~~

In the Dioptra GUI, select **Groups**, and then select **Create**. Enter a name for the group. The **Public** setting is
enabled and cannot currently be disabled. Select **Submit** to create the group.

The new group becomes the active group context. Its name must be unique among groups created by the same user, but a group
created by another user can have the same name.

The Python client can list groups and retrieve a group by ID, but it does not currently expose group creation. Use the GUI
or the ``POST /api/v1/groups/`` REST API endpoint to create a group.

.. rst-class:: header-on-a-card header-steps

Step 2: Select or Manage a Group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The header group switcher lists groups created by the logged-in user. Select **View Other Groups** to browse all available
public groups. On the Groups page, select **Set Context** to make a group active. Resource lists and creation forms then use
that group.

Select a row to open the Group Admin page. Every authenticated user can inspect a public group, but only an owner can
rename or delete it. Deleting a group also marks its resources as deleted. A user cannot delete their final owned group.

Resource list and creation URLs include ``groupId`` so reloads and browser Back/Forward restore context. The interface
refreshes available groups when the tab regains focus and falls back to an available group if the selected group was
deleted elsewhere.

Browse a Deleted Group
----------------------

1. Open **Groups** and enable **Show Deleted**.
2. Find the deleted group and select **Browse Deleted Resources**.
3. Select a supported resource type, such as experiments or queues, then use **View record** to inspect a read-only JSON
   record.
4. For supported resource types, enable **My retained drafts** to inspect your own saved drafts.

The archive does not change your active group. Tags and drafts are retained records rather than individually deleted
resources. See :ref:`reference-groups-archives` for API access and supported resource types.

Deleted plugins, jobs, artifacts, and models are not yet returned by their list endpoints, even though the archive selector
offers those types. Their show-deleted support will be added with the artifact work.

.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Users and Groups <explanation-users-and-groups>` - Understand what users and groups are for.
* :ref:`Users Reference <reference-users>` - Reference page for users.
* :ref:`Groups Reference <reference-groups>` - Reference page for groups.
