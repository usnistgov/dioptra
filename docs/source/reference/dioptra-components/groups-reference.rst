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
======


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-groups-definition:

Group Definition
----------------

A **Group** owns and controls access to Dioptra resources and provides a resource context for the web interface and API.

.. warning::

   All groups are public. Authenticated users can read and write resources in public groups even without direct membership.
   Stored member permissions are not currently enforced for public-group resources. Owner checks are enforced for group
   rename and deletion.

.. _reference-groups-attributes:

Group Attributes
----------------

The natural key for a Group is ``(creator, name)``. Names must be unique for each creator, including names held by deleted
groups, but two different users can create groups with the same name. The qualified display form is
``creator-username/group-name``.

.. _reference-groups-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

* **Name**: (string) The name of the group.
* **User**: (User) The permanent creator of the group.
* **Public**: (boolean) Whether the group is publicly accessible. Only ``true`` is currently supported.

.. _reference-groups-system-managed-state:

System-Managed State
~~~~~~~~~~~~~~~~~~~~

- **ID**: (integer) Unique identifier assigned upon creation.
- **Created On**: (timestamp) Indicates when the Group was created.
- **Last Modified On**: (timestamp) Indicates when the Group was last modified.

.. _reference-groups-personal-group:

Personal Groups
---------------

Registering a User automatically creates a public personal Group whose initial name matches the username. The creator is
added as the initial member, administrator, and owner. "Personal" describes how the Group is created; it does not mean the
Group is private.

Changing a username does not automatically rename the personal Group. Users can create additional public Groups, and a
new Group created in the web interface becomes the active group context.

.. _reference-groups-membership:

Group Membership
----------------

Members of a Group have stored resource permission flags and may also have manager roles. In the current public-only
implementation, the resource permission flags do not restrict authenticated-user access to resources in public Groups.

.. _reference-groups-member-permissions:

Member Permissions
~~~~~~~~~~~~~~~~~~

* **Read**: (boolean) Stored permission for reading resources in the Group.
* **Write**: (boolean) Stored permission for creating or modifying resources in the Group.

These permission fields are reserved for the developing group permission model and are not currently enforced for
public-group resources.

.. _reference-groups-manager-roles:

Manager Roles
~~~~~~~~~~~~~~~~~~

* **Owner**: (boolean) Whether the manager can rename or delete the Group.
* **Admin**: (boolean) Whether the manager has the administrator role. Additional administrator operations are not yet
  exposed.

.. _reference-groups-administration:

Group Administration
--------------------

Only an owner can rename or delete a Group. A rename must remain unique among all Groups created by the same User. Each
User must retain at least one owned Group, so deleting a User's final owned Group is rejected.

Deleting a Group marks the Group and its resources as deleted. Deletion does not make the Group name available for reuse.

Groups without a remaining active owner are deleted with their resources in the account deletion transaction.

.. _reference-groups-archives:

Deleted Group Archives
----------------------

On the Groups page, enable **Show Deleted** and select **Browse Deleted Resources** for a deleted Group. The archive at
``/groups/<id>/archive`` displays the Group's qualified name and a read-only banner. It does not change the active Group.

Choose a resource type to browse a paginated list, then select **View record** to inspect its JSON representation.
The archive has no resource creation, editing, import, or deletion controls.

Deleted-resource listing is currently available for experiments, queues, entrypoints, and plugin parameter types. The
resource selector also offers plugins, jobs, artifacts, and models, but their list endpoints currently exclude deleted
resources. Show-deleted support for those types is deferred to the artifact work; an empty list for one of those types does
not establish that the deleted Group had no such resources.

Tags are retained records and have no individual delete marker. For resource types with draft support, **My retained
drafts** shows the current User's new-resource and modification drafts. Drafts are also retained records, not individually
deleted resources; drafts belonging to other Users are not included.

API clients can read a deleted Group with ``GET /api/v1/groups/<id>?showDeleted=true``. Supported resource lists use an
explicit ``groupId`` together with ``showDeleted=true`` to include deleted resources. Draft lists also accept
``showDeleted=true``; for drafts, this permits reading retained drafts in deleted Groups while preserving creator scoping.
Tags are queried by ``groupId`` and do not use an individual deletion flag.

.. _reference-groups-registration-interfaces:

Registration Interfaces
-----------------------

Groups can be created and managed through the web interface and the REST API. Group creation currently accepts only public
Groups. The Python client can list Groups and retrieve a Group by ID, but it does not currently expose create, rename, or
delete operations.


.. rst-class:: fancy-header header-seealso

See Also
---------

- :ref:`Users Reference <reference-users>`
- :ref:`Users and Groups Explanation <explanation-users-and-groups>`
- :ref:`Create Users and Groups <how-to-create-users-and-groups>`
