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

.. _reference-users:

Users
=====

.. contents:: Contents
   :local:
   :depth: 2

.. _reference-users-definition:

User Definition
---------------

A **User** in Dioptra represents an account that provides authenticated access to resources such as entrypoints, plugins,
jobs, and experiments. Registering a User also creates a public personal Group initially named after the username.


.. _reference-users-attributes:

User Attributes
---------------

This section describes the attributes that define a User.

.. _reference-users-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

* **Username**: (string) The name of the user. Used for authentication.
* **Password**: (string) A password for the user. Used for authentication.
* **Email**: (string) The email address of the user.

.. _reference-users-system-managed-state:

System-Managed State
~~~~~~~~~~~~~~~~~~~~

- **ID**: (integer) Unique identifier assigned upon creation.
- **Groups**: (list of Group references) Groups accessible to the current User. Because all current Groups are public, this
  includes non-deleted public Groups even when the User is not a member. Each reference contains the Group ``id``, ``name``,
  creator ``user``, and ``url``.
- **Created On**: (timestamp) When the User was created.
- **Last Modified On**: (timestamp) When the User was last modified.
- **Last Login On**: (timestamp) When the User last logged in.
- **Password Expires On**: (timestamp) When the User's password will expire.

.. _reference-users-personal-group:

Personal Group
--------------

User registration creates a public personal Group with the User as its creator, initial member, administrator, and owner.
The Group's initial name matches the username, but later username changes do not automatically rename the Group. A
personal Group is public in the current release; it is not a private workspace.

.. _reference-users-registration-interfaces:


Registration Interfaces
-----------------------

Users can be created programmatically via the Python Client or the REST API.
They can also be :ref:`created through the web interface <how-to-create-users-and-groups>` .

.. _reference-users-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Create a User**

    .. automethod:: dioptra.client.users.UsersCollectionClient.create
        :noindex:


.. _reference-users-rest-api:

Using REST API
~~~~~~~~~~~~~~

Users can be created directly via the HTTP API.

**Create Users**

See the :http:post:`POST /api/v1/users </api/v1/users/>` endpoint documentation for payload requirements.


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`how-to-create-users-and-groups`
* :ref:`Users and Groups Explanation <explanation-users-and-groups>`
