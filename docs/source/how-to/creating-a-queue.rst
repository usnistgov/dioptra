
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


.. _how_to_create_a_queue:

How-To: Create a Queue
======================

In Dioptra, jobs are submitted to queues, which represent a computing environment. This
guide assumes that Dioptra is already installed and is accessible through the web browser,
and that the user is logged in.


1.  On the Dioptra Web UI, navigate to the **Queues** tab.

    .. figure:: /images/queues-page.png

2.  On the Queues page, click **Create**.
3.  Enter a name for the queue, select the group that should have access to the queue,
    and a description in the appropriate fields. *Note: the name should match the worker 
    the queue is associated with.*

    .. figure:: /images/queue-create.png

4.  Click **Confirm**.

    .. figure:: /images/queue-created.png

5.  If successful, the newly created queue should appear in the list.

