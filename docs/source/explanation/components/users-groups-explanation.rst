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

A user is an account which provides access to other resources (entrypoints, plugins, jobs, experiments, etc.). Users
of Dioptra must be logged in to be able to read and write to the various resources. Users are useful for segregating
permissions and providing attribution for actions taken within dioptra. 

Currently, only password authentication is supported.


Summary: What is a Group?
-------------------------

A group controls access to other resources. Plugins/entrypoints/jobs/etc. created under a single
group are available to users who are part of that group. Currently, there is a single public group
which all resources are created under - this will change in a future release of Dioptra.

.. note::

    Dioptra does not currently support the creation of additional groups. All resources are under the same default public group.

.. rst-class:: fancy-header header-seealso

See Also 
---------
   
* :ref:`how-to-create-users-and-groups` - Step-by-step guide on creating users.
