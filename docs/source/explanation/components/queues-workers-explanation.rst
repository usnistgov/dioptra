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
================

Summary: What is a Worker?
--------------------------

A **worker** is an environment in which a job can be executed. 

A worker should contain all of the requirements needed for a given entrypoint, such as any local files, 
python packages, or executables needed as part of the job. Each worker listens to a single named
queue, and multiple workers can listen to the same queue.

By default, Dioptra provides several default worker environments which can be enabled during setup:
    * tensorflow_cpu - for systems which do not have a GPU present, which contains Tensorflow and ART as dependencies
    * tensorflow_gpu - for systems which do have a GPU present, which contains Tensorflow and ART as dependencies
    * pytorch_cpu - for systems which do not have a GPU present, which contains PyTorch and ART as dependencies
    * pytorch_gpu - for systems which do have a GPU present, which contains PyTorch and ART as dependencies

Creating queues with these names, as long as the corresponding worker is enabled, will allow jobs to be run in these worker containers.

Additionally, custom workers can be created which watch queues of other names and provide different environments for the jobs to run in,
allowing for additional requirements and packages to be included.

See :ref:`how-to-using-custom-workers` for more information.

Summary: What is a Queue?
-------------------------

A **queue** is a resource in Dioptra which represents a logical job queue for workers watching that queue to take from. Entrypoints can
be assigned a number of queues they are compatible with.

When a job is submitted, a queue is selected for that job to be added to. Any worker listening to that queue can claim the job from the
queue, and execute the job in its environment.


.. rst-class:: fancy-header header-seealso

See Also 
---------
   
* :ref:`how-to-using-custom-workers` - Guide for creating custom workers
* :ref:`how-to-create-queues` - Step-by-step guide on creating queues



