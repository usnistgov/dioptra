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

.. _explanation-queues-and-workers:

Queues and Workers
==================

Summary: What is a Queue?
-------------------------

A **queue** is a resource in Dioptra that represents a logical job queue. Workers watch a queue for new jobs to process. Entrypoints can
be assigned to any number of queues for which they are compatible.

When submitting a job, the user selects a queue for that job. Any worker listening to that queue can claim the job and then begin execution in its environment.

Summary: What is a Worker?
--------------------------

A **worker** is an environment for executing jobs. 

A worker should contain all of the requirements needed for a given entrypoint, such as any local files, 
python packages, or executables. Each worker listens to a single named
queue, and multiple workers can listen to the same queue.

By default, Dioptra provides several default worker environments that can be enabled during setup:
    * tensorflow-cpu - for systems that **do not have** a GPU present, which contains Tensorflow and ART as dependencies
    * tensorflow-gpu - for systems that **do have** a GPU present, which contains Tensorflow and ART as dependencies
    * pytorch-cpu - for systems that **do not have** a GPU present, which contains PyTorch and ART as dependencies
    * pytorch-gpu - for systems that **do have** a GPU present, which contains PyTorch and ART as dependencies

If a worker is enabled, creating a queue with the same name as the worker will allow jobs to be run in the corresponding worker container.

Additionally, custom workers can be created to watch queues with other names. These custom workers can provide different environments for jobs, which allows users to include their own requirements and packages.

See :ref:`how-to-creating-custom-workers` for more information.


.. rst-class:: fancy-header header-seealso

See Also 
---------
   
* :ref:`how-to-creating-custom-workers` - Guide for creating custom workers
* :ref:`how-to-create-queues` - Step-by-step guide on creating queues
* :ref:`Queues Reference <reference-queues>` - Queues reference page.

