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

.. _reference-groups:

Groups
=================


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-groups-definition:

Group Definition
----------------

A **Group** in Dioptra controls access to other resources for users.

.. note::

   Groups are not yet fully implemented in Dioptra. Currently there is a single `public` group that all users have full permissions on. The ability to create new groups as well as manage group permissions and roles will be added in a future release.

.. _reference-groups-attributes:

Group Attributes
----------------

.. _reference-groups-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

* **Name**: (string) The name of the group.
* **Creator**: (User) The creator of the group.

.. _reference-groups-system-managed-state:

System-Managed State
~~~~~~~~~~~~~~~~~~~~

- **ID**: (integer) Unique identifier assigned upon creation.
- **Created On**: (timestamp) Indicates when the Group was created.
- **Last Modified On**: (timestamp) Indicates when the Group was last modified.

.. _reference-groups-membership:

Group Membership
----------------

Members of a group have permissions which define their access to resources in that group, as well as roles which define
their control over the group.

.. _reference-groups-member-permissions:

Member Permissions
~~~~~~~~~~~~~~~~~~



* **Read**: (boolean) Whether the member can read resources in this group.
* **Write**: (boolean) Whether the member can modify/create resources in this group.
* **Share Read**: (boolean) Whether the member can share Read permissions for resources in the group.
* **Share Write**: (boolean) Whether the member can share Read+Write permissions for resources in the group.

.. _reference-groups-manager-roles:

Manager Roles
~~~~~~~~~~~~~~~~~~

* **Owner**: (boolean) Whether the member is the owner of the group.
* **Admin**: (boolean) Whether the member is an administrator of the group.

.. _reference-groups-registration-interfaces:

Registration Interfaces
--------------------

Custom groups cannot be created in Dioptra at this time. 


.. rst-class:: fancy-header header-seealso

See Also
---------

- :ref:`Users Reference <reference-users>`
