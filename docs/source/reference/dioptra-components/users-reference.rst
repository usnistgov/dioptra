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

A **User** in Dioptra represents an account which provides access to other resources (entrypoints, plugins, jobs, experiments, etc.). 


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
- **Groups**: (List of Group IDs)  List of groups that the user is in. Determines access to resources. Each user is in the Public Group by default.
- **Created On**: (timestamp) When the User was created.
- **Last Modified On**: (timestamp) When the User was last modified.
- **Last Login On**: (timestamp) When the User last logged in.
- **Password Expires On**: (timestamp) When the User's password will expire.

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


.. _reference-users-rest-api:

Using REST API
~~~~~~~~~~~~~~

Users can be created directly via the HTTP API.

**Create Users**

See the :http:post:`POST /api/v1/users </api/v1/users/>` endpoint documentation for payload requirements.


.. _reference-users-retrieval-interfaces:

Retrieval Interfaces
--------------------

Users can be retrieved via the Python Client or the REST API.

.. _reference-users-retrieval-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Get a list of Users**

    .. automethod:: dioptra.client.users.UsersCollectionClient.get

**Get the currently logged in User**

    .. automethod:: dioptra.client.users.UsersCollectionClient.get_current

**Get a specific User by ID**

    .. automethod:: dioptra.client.users.UsersCollectionClient.get_by_id

.. _reference-users-retrieval-rest-api:

Using REST API
~~~~~~~~~~~~~~

**Get a list of Users**

See the :http:get:`GET /api/v1/users </api/v1/users/>` endpoint documentation for payload requirements.

**Get the currently logged in User**

See the :http:get:`GET /api/v1/users/current </api/v1/users/current>` endpoint documentation for payload requirements.

**Get a specific user by ID**

See the :http:get:`GET /api/v1/users/{int:id} </api/v1/users/{id}>` endpoint documentation for payload requirements.



.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`How To Create a User <how_to_create_a_user>`
* :ref:`Users and Groups Explanation <explanation-users-and-groups>`
