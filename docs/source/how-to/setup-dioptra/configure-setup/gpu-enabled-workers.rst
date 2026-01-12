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

.. _how-to-gpu-enabled-workers:

Configure GPU Workers
=====================

This guide explains how to assign one or more GPUs to Dioptra worker containers for GPU-accelerated machine learning workloads.

Prerequisites
-------------

* :ref:`how-to-prepare-deployment` - A configured Dioptra deployment with GPU workers enabled
* :ref:`how-to-using-docker-compose-overrides` - Override file created (for custom GPU assignments)
* NVIDIA GPU(s) with drivers installed on the host machine
* `NVIDIA Container Toolkit <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html>`__ installed
* GPU worker containers built (see :ref:`how-to-build-containers`)

.. note::

   GPU workers are configured during template creation using the ``num_tensorflow_gpu_workers`` and ``num_pytorch_gpu_workers`` variables.
   By default, each GPU worker is assigned a dedicated GPU.

GPU Configuration
-----------------

.. rst-class:: header-on-a-card header-steps

Step 1: Verify GPU Availability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify that the host machine has GPUs available and the NVIDIA drivers are installed:

.. code:: sh

   nvidia-smi

This should display information about your GPU(s). Note the GPU indices (0, 1, 2, etc.) for use in configuration.

.. rst-class:: header-on-a-card header-steps

Step 2: Assign GPUs to Workers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To customize GPU assignments beyond the default one-GPU-per-worker configuration, open ``docker-compose.override.yml`` and add blocks for the GPU worker containers.
GPU worker names include **tfgpu** or **pytorchgpu**.

.. note::

   In the examples below, replace ``<deployment-name>`` with your deployment's slugified name (default: ``dioptra-deployment``).

**To assign specific GPUs to a worker:**

.. code:: yaml

   services:
     <deployment-name>-tfgpu-01:
       environment:
         NVIDIA_VISIBLE_DEVICES: 0

     <deployment-name>-pytorchgpu-01:
       environment:
         NVIDIA_VISIBLE_DEVICES: 1

**To assign multiple GPUs to a single worker:**

.. code:: yaml

   services:
     <deployment-name>-tfgpu-01:
       environment:
         NVIDIA_VISIBLE_DEVICES: 0,1

**To allow a worker to use all available GPUs:**

.. code:: yaml

   services:
     <deployment-name>-tfgpu-01:
       environment:
         NVIDIA_VISIBLE_DEVICES: all

.. warning::

   The combined number of TensorFlow and PyTorch GPU workers cannot be greater than the number of GPUs available on the host machine (unless you assign the same GPU to multiple workers, which may cause resource contention).

.. rst-class:: header-on-a-card header-steps

Step 3: Restart the Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply your changes by restarting the deployment:

.. code:: sh

   docker compose down
   docker compose up -d

Verify that the GPU workers started correctly:

.. code:: sh

   docker compose ps

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`how-to-using-docker-compose-overrides` - Docker Compose override file basics
* :ref:`how-to-prepare-deployment` - Full deployment customization
* :ref:`how-to-data-mounts` - Mount data volumes into worker containers
* :ref:`how-to-integrating-custom-containers` - Add custom containers
