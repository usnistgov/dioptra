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

.. _explanation-users-and-groups:

Users and Groups
================

Summary: What is a User?
------------------------

A **user** is an account that provides authenticated access to Dioptra resources, such as entrypoints, plugins, jobs, and
experiments. User accounts provide attribution for actions taken within Dioptra and are the basis for group membership and
management roles.

Currently, only password authentication is supported.

Summary: What is a Group?
-------------------------

A **group** owns and controls access to Dioptra resources. Resource lists and creation forms use a group context to determine
which resources to display and where new resources are created.

Registering a user automatically creates a public personal group whose initial name matches the username. The new user is
the group's creator, initial member, administrator, and owner. A personal group is not private; users can also create
additional public groups.

Group names must be unique among groups created by the same user, but different users can create groups with the same name.
The Dioptra web interface uses ``creator-username/group-name`` as the qualified display form when a name must be unambiguous.

.. warning::

   All groups created in this release are public. Any authenticated user can read and write resources in a public group,
   even without being a member. Member permission flags are represented in the data model but are not currently enforced
   for public-group resources. Group administration is different: only an owner can rename or delete a group.

Group Membership and Ownership
------------------------------

Group membership records contain read and write permission flags. Manager records contain the ``admin`` and ``owner``
roles. These fields support a future permission model, but they are not access boundaries for resources in public groups
in the current release.

Ownership is enforced for group-level administration. Only an owner can rename or delete a group, and every user must
retain at least one owned group. Deleting a group also marks its resources as deleted.

Active Group Context
--------------------

The web interface maintains one active group context per user and browser tab. The selection is stored for the lifetime
of the tab and survives navigation and page reloads in that tab. A different browser tab can use a different active group.

The header switcher lists groups created by the logged-in user. Select **View Other Groups** to open the Groups page,
where all available public groups can be inspected and selected as context. Resource tables are filtered by the active
group, and new resources and GUI resource imports use that group unless the operation explicitly identifies another one.

Opening an existing resource changes the active context to the resource's owning group. The switcher is disabled while
viewing or editing that resource so the displayed resource and its group context cannot diverge. Leaving the detail route
unlocks the switcher.

The active group is a web interface concept. REST API and Python client operations that require a group use an explicit
group ID rather than the browser's active context.


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`how-to-create-users-and-groups` - Step-by-step guide on creating users and groups.
* :ref:`Users Reference <reference-users>` - Reference page for users.
* :ref:`Groups Reference <reference-groups>` - Reference page for groups.
