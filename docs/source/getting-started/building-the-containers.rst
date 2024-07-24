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

.. _getting-started-building-the-containers:

Building the Containers
=======================

.. include:: /_glossary_note.rst

You will need to build several container images using the Dockerfiles in the Dioptra GitHub repository before you can run Dioptra for the first time.
This guide will walk you through the steps for building these images.

To begin, open a Terminal and clone the GitHub repository if you have not already done so.

.. tab-set::

   .. tab-item:: Clone with HTTPS

      .. code:: sh

         git clone https://github.com/usnistgov/dioptra.git

   .. tab-item:: Clone with SSH

      .. code:: sh

         git clone git@github.com:usnistgov/dioptra.git

Optionally, if you want to build the latest versions of the containers, you should first switch to the ``dev`` branch.

.. code:: sh

   # OPTIONAL: switch to the dev branch to get the latest container images
   git checkout -b dev origin/dev

Next, if you have extra CA certificates that you want to include during the build process, copy them into the ``docker/ca-certificates/`` folder.
This is something you may need to do if you are building the containers in a corporate environment that has its own certificate authority.
See the `docker/ca-certificates/README.md <https://github.com/usnistgov/dioptra/blob/main/docker/ca-certificates/README.md>`__ file for additional information.

Next, use the Makefile to build the container images.

.. code:: sh

   # NOTE: if make cannot find your python executable, you can specify it manually by
   #       prepending PY=/path/to/python3 to the command below
   # NOTE: the PyTorch and Tensorflow images may take a while to build
   make build-nginx build-mlflow-tracking build-restapi build-pytorch-cpu build-tensorflow-cpu

If you are running Dioptra on a host machine that has one or more CUDA-compatible GPUs, then it is recommended that you also build the GPU-enabled images:

.. code:: sh

   # NOTE: the PyTorch and Tensorflow images may take a while to build
   make build-pytorch-gpu build-tensorflow-gpu

Finally, run ``docker images`` to verify that the container images are now available with the ``dev`` tag.
You should see output that looks like the following,

.. margin::

   .. note::

      The ``IMAGE ID``, ``CREATED``, and ``SIZE`` fields in the ``docker images`` output will likely be different.

.. code:: text

   REPOSITORY                           TAG       IMAGE ID       CREATED         SIZE
   dioptra/nginx                        dev       17235f76d81c   3 weeks ago     243MB
   dioptra/restapi                      dev       f7e59af397ae   3 weeks ago     1.16GB
   dioptra/mlflow-tracking              dev       56c574822dad   3 weeks ago     1.04GB
   dioptra/pytorch-cpu                  dev       5309d66defd5   3 weeks ago     3.74GB
   dioptra/tensorflow2-cpu              dev       13c4784dd4f0   3 weeks ago     3.73GB

Your ``REPOSITORY`` and ``TAG`` columns should match up with the above list.
