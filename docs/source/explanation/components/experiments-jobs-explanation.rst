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

.. _explanation-experiments-and-jobs:

Experiments and Jobs
====================

Summary: What is an Experiment?
-------------------------------

An **experiment** is a resource in Dioptra which is effectively a namespace for jobs. An experiment can have
a number of entrypoints associated with it, from which jobs under that experiment can be created. Experiments
as a resource are largely organizational, and can make it easier to filter jobs, provide access to users via 
groups, and reduce the number of entrypoints to sift through at job creation.

Summary: What is a Job?
-----------------------

A **job** in Dioptra is essentially an instance of an entrypoint. When creating a job, a user provides parameters
and artifact parameters specified as necessary by an entrypoint, and this set of workflow instructions (the :ref:`entrypoint <explanation-entrypoints>`), 
any parameter values, and any artifacts being passed as parameters, get sent to a queue, also selected by the user
at job creation.

When a worker listening to that queue claims the job, it attempts to execute the provided entrypoint using the 
parameter and artifact parameter values passed along with the entrypoint within the worker environment. 

Any logs generated during the lifetime of the job, along with any :ref:`metrics <explanation-metrics>` and artifacts created during one of the
steps of the job, are uploaded to the Dioptra RESTAPI and associated with the job (and are viewable from the **Job
Dashboard** page.)

Dioptra maintains a job history, recording the experiment, entrypoint, parameters, artifact parameters, logs, metrics
and generated artifacts for all jobs.


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`how-to-create-experiments` - Step-by-step guide on creating an experiment
* :ref:`Entrypoints Explanation <explanation-entrypoints>` - Explanation of entrypoints
* :ref:`how-to-running-jobs` - Step-by-step guide on running a job
