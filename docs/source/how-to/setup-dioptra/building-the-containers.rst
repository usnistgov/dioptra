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

.. _how-to-build-containers:

Build the Container Images
==========================

This guide explains how to build the Dioptra container images from the source repository.
After completing these steps, you will have local container images ready for deployment.

Prerequisites
-------------

* `Docker Engine <https://docs.docker.com/engine/install/>`__ installed and running
* `Git <https://git-scm.com/downloads>`__ installed
* A terminal with access to Docker commands

Building the Images
-------------------

.. rst-class:: header-on-a-card header-steps

Step 1: Clone the Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clone the Dioptra GitHub repository if you have not already done so.

.. tab-set::

   .. tab-item:: Clone with HTTPS

      .. code:: sh

         git clone https://github.com/usnistgov/dioptra.git

   .. tab-item:: Clone with SSH

      .. code:: sh

         git clone git@github.com:usnistgov/dioptra.git

Change into the cloned repository directory:

.. code:: sh

   cd dioptra

.. note::

   To build the latest development versions of the containers, switch to the ``dev`` branch:

   .. code:: sh

      git checkout -b dev origin/dev

.. rst-class:: header-on-a-card header-steps

Step 2: Add CA Certificates (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are building the containers in a corporate environment that uses its own certificate authority, copy your CA certificates into the ``docker/ca-certificates/`` folder before building.

.. code:: sh

   cp /path/to/your/ca-certificate.crt docker/ca-certificates/

See the `docker/ca-certificates/README.md <https://github.com/usnistgov/dioptra/blob/main/docker/ca-certificates/README.md>`__ file for additional information.

.. rst-class:: header-on-a-card header-steps

Step 3: Build the Container Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the Makefile to build the container images:

.. code:: sh

   make build-nginx build-mlflow-tracking build-restapi build-pytorch-cpu build-tensorflow-cpu

.. note::

   The PyTorch and TensorFlow images may take a while to build.

.. tip::

   If ``make`` cannot find your Python executable, specify it manually by prepending ``PY=/path/to/python3`` to the command.

.. rst-class:: header-on-a-card header-steps

Step 4: Build GPU Images (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you plan to run GPU-accelerated workers, build the GPU-enabled images.
These images require a host machine with CUDA-compatible GPUs and the `NVIDIA Container Toolkit <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html>`__ to be useful.

.. code:: sh

   make build-pytorch-gpu build-tensorflow-gpu

.. rst-class:: header-on-a-card header-steps

Step 5: Verify the Images
~~~~~~~~~~~~~~~~~~~~~~~~~

Run ``docker images`` to verify that the container images are available with the ``dev`` tag:

.. code:: sh

   docker images | grep dioptra

You should see output similar to the following:

.. code:: text

   REPOSITORY                  TAG       IMAGE ID       CREATED         SIZE
   dioptra/nginx               dev       17235f76d81c   3 weeks ago     243MB
   dioptra/restapi             dev       f7e59af397ae   3 weeks ago     1.16GB
   dioptra/mlflow-tracking     dev       56c574822dad   3 weeks ago     1.04GB
   dioptra/pytorch-cpu         dev       5309d66defd5   3 weeks ago     3.74GB
   dioptra/tensorflow2-cpu     dev       13c4784dd4f0   3 weeks ago     3.73GB

.. note::

   The ``IMAGE ID``, ``CREATED``, and ``SIZE`` fields will vary. Verify that the ``REPOSITORY`` and ``TAG`` columns match.

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`how-to-prepare-deployment` - Set up a deployment using your built images
* :ref:`how-to-adding-certificates` - Add CA certificates to a running deployment
* :ref:`how-to-gpu-enabled-workers` - Configure GPU workers in your deployment
