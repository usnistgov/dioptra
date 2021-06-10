.. NOTICE
..
.. This software (or technical data) was produced for the U. S. Government under
.. contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
.. 52.227-14, Alt. IV (DEC 2007)
..
.. © 2021 The MITRE Corporation.

.. _deployment-guide-system-requirements:

System Requirements
===================

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
