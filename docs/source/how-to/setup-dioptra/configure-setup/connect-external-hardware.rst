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

.. _how-to-connecting-external-hardware-gpus:

Connecting External Hardware / GPUs
=====================

This how to guide explains how to connect external hardware / GPUs.


Prior Documentation Snippets
----------------------------


.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 


Assigning multiple GPUs per worker
##################################

To assign multiple GPUs to a worker, edit your ``docker-compose.override.yml`` file to change the ``NVIDIA_VISIBLE_DEVICES`` environment variable in the **tfgpu** and **pytorch-gpu** container blocks:

.. code:: yaml

   dioptra-deployment-tfcpu-01:
     environment:
       NVIDIA_VISIBLE_DEVICES: 0,1

To allow a worker to use all available GPUs, set ``NVIDIA_VISIBLE_DEVICES`` to ``all``:

.. code:: yaml

   dioptra-deployment-tfcpu-01:
     environment:
       NVIDIA_VISIBLE_DEVICES: all