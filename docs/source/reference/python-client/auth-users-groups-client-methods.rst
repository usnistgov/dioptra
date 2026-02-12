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

.. _reference-auth-client-methods:

Auth, Users, and Groups Client Methods
=================

This page lists all relevant methods for Dioptra Authentication, User management, and Group management that are available via the Python Client.

.. contents:: Contents
   :local:
   :depth: 2


Requirements
-------------

- :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
- :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized


.. _reference-auth-client-methods:

Authentication Methods
----------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods can be executed via ``client.auth.METHOD_NAME()``.

Login
~~~~~

    .. automethod:: dioptra.client.auth.AuthCollectionClient.login

Logout
~~~~~

    .. automethod:: dioptra.client.auth.AuthCollectionClient.logout


.. _reference-users-client-methods:

Users - General Methods
-----------------------

These methods relate to general user management and retrieval. They can be executed via ``client.users.METHOD_NAME()``.

Get All Users
~~~~~~~~~~~~~

    .. automethod:: dioptra.client.users.UsersCollectionClient.get

Create User
~~~~~~~~~~~

    .. automethod:: dioptra.client.users.UsersCollectionClient.create

Get User by ID
~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.users.UsersCollectionClient.get_by_id

Change User Password by ID
~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.users.UsersCollectionClient.change_password_by_id


.. _reference-users-current-client-methods:

Users - Current User Methods
----------------------------

These methods interact specifically with the currently authenticated user session (the user logged in via the client).

Get Current User
~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.users.UsersCollectionClient.get_current

Modify Current User
~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.users.UsersCollectionClient.modify_current_user

Change Current User Password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.users.UsersCollectionClient.change_current_user_password

Delete Current User
~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.users.UsersCollectionClient.delete_current_user


.. _reference-groups-client-methods:

Groups Methods
---------------------

These methods relate to group management and retrieval. They can be executed via ``client.groups.METHOD_NAME()``.

.. important::
    
    Groups are only partially implemented in Dioptra currently. All users are created under a single "Public" group. At this time, the creation of custom groups is not yet supported. 

Get All Groups
~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.groups.GroupsCollectionClient.get

Get Group by ID
~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.groups.GroupsCollectionClient.get_by_id


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`How to set up the Python Client <how-to-set-up-the-python-client>`
* :ref:`Explanation: Users and Groups <explanation-users-and-groups>`