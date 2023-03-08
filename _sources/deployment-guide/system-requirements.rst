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

.. _deployment-guide-system-requirements:

System Requirements
===================

.. include:: /_glossary_note.rst

Single Machine
--------------

The minimum and recommended system requirements for standing up an on-premises deployment on a single host machine are as follows:

CPU
   Intel or AMD-based x86-64 processor with 8+ physical cores at 1.90GHz or higher (minimum), Intel Xeon Processor with 20+ physical cores at 2.2GHz or higher (recommended)
GPU
   1 Nvidia Tesla K80 (Kepler) GPU (minimum), 2+ Nvidia Tesla V100 (Volta) GPUs or better (recommended)
RAM
   2GB per physical core (minimum), 4GB per physical core or higher (recommended)
NFS Mount [optional]
   1TB of shared storage (minimum), 2TB or more shared storage (recommended)
Local Storage
   500GB/1TB solid state drive (minimum with NFS/minimum no NFS), 1TB/2TB solid state drive or better (recommended with NFS/recommended without NFS)
Operating System
   Ubuntu 20.04 LTS (recommended)
Docker Engine
   `Stable release <https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository>`__
Other Recommendations
   Remote SSH access

The NFS mount is intended for the storing and sharing of large datasets, which are mounted as read-only folders in the Testbed Workers.
While it is optional for a single machine deployment, we recommend that you consider setting up a NFS share anyway as a future-proofing step, as it will make it easier to switch to a distributed deployment if the need arises.

Maintainers of GPU-capable host machines should also `follow these directions to enable GPU access in the containers <https://docs.docker.com/config/containers/resource_constraints/#gpu>`_
