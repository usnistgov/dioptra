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

.. _how-to-quick-setup:

Quick Setup
=====================

This how to is a minimal guide to getting Dioptra up and running with default settings. 



Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 



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



The Dioptra GitHub repository provides a `Cookiecutter <https://cookiecutter.readthedocs.io/en/latest/>`__ template in the ``cookiecutter-templates/cookiecutter-dioptra-deployment/`` folder that you can use to generate the scripts, configuration files, and Docker Compose files needed to run Dioptra on a single machine.
This guide will show you how to apply the template, run the initialization script, and start the application services for the first time.

Prerequisites
-------------

- `Bash v5 or higher <https://tiswww.case.edu/php/chet/bash/bashtop.html>`__
- `Python 3.11 or higher <https://www.python.org/>`__
- `Cruft 2.15.0 or higher <https://cruft.github.io/cruft/>`__
- `Docker Engine 20.10.13 or higher <https://docs.docker.com/engine/install/>`__
- `Docker Compose <https://docs.docker.com/compose/install/>`__
- Dictionary of words at ``/usr/share/dict/words`` (``apt-get install wamerican``)
- :ref:`Working builds of the Dioptra container images <getting-started-building-the-containers>`

Quickstart
----------

The minimal terminal commands needed to configure and run a fresh installation of Dioptra are provided below.
This will generate a setup that is appropriate for testing Dioptra on your personal computer or laptop.

.. code:: sh

   # Set the Dioptra branch to use for your deployment
   # (If using a different branch, replace "main" with that branch's name)
   export DIOPTRA_BRANCH=main

   # Move to the base directory where you plan to store your Dioptra
   # configuration folder
   mkdir -p /path/to/deployments/folder  # Create it if it doesn't exist
   cd /path/to/deployments/folder

   # Create a virtual environment and install cruft and Jinja2
   python -m venv venv-deploy
   source venv-deploy/bin/activate
   python -m pip install --upgrade pip cruft jinja2 requests

Next, run cruft to begin the deployment process. The following command will run cruft and use all of the default template values except for the `datasets_directory`. If you wish to configure the deployment in a different manner, see the :ref:`Applying the template <getting-started-running-dioptra-applying-the-template>` section for detailed description of the template values and how to configure them. 

We recommend identifying a location to store datasets you will want to use with Dioptra at this point and setting the `datasets_directory` variable accordingly. See the :ref:`Downloading the datasets <getting-started-acquiring-datasets>` section for more details.

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout main \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input \
     --extra-context '{"datasets_directory": "/datasets"}'


Once you have configured your deployment, continue following the instructions for initializing and starting your deployment below.

.. code:: sh

   # Move into the new folder created by the template. The new folder's name
   # is based on the deployment_name variable. The default name for the folder
   # is dioptra-deployment.
   cd dioptra-deployment

   # Initialize Dioptra using the init-deployment.sh script
   ./init-deployment.sh --branch $DIOPTRA_BRANCH

   # Start Dioptra
   docker compose up -d

When you are done using Dioptra, navigate back to the configuration folder ``/path/to/deployments/folder/dioptra-deployment`` in your terminal and run,

.. code:: sh

   # Stop Dioptra
   docker compose down

The rest of this page is a detailed walk-through of the above commands, which includes information about more advanced topics, such as :ref:`enabling SSL/TLS for the NGINX and postgres services <running-dioptra-enabling-ssl-tls-in-nginx-and-postgres>` and :ref:`how to mount additional folders in the worker containers <running-dioptra-mounting-folders-in-the-worker-containers>`.
