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

.. _how-to-creating-custom-workers:

Create a Custom Worker Container
=================================

This guide walks through creating a custom Dioptra worker container using the provided cookiecutter template.
A custom worker lets you include Python packages or other software that is not available in the standard Dioptra worker images.

Prerequisites
-------------

* :ref:`how-to-prepare-deployment` completed
* `cookiecutter <https://cookiecutter.readthedocs.io/>`__ installed (``pip install cookiecutter``)
* `Docker <https://docs.docker.com/get-docker/>`__ installed and running

Custom Worker Creation
----------------------

.. rst-class:: header-on-a-card header-steps

Step 1: Generate the Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run ``cookiecutter`` to generate a new project from the custom worker template:

.. code:: sh

   cookiecutter https://github.com/usnistgov/dioptra \
     --checkout <branch-name> \
     --directory cookiecutter-templates/custom-dioptra-worker

Replace ``<branch-name>`` with the Dioptra branch that matches your deployment (e.g., ``main`` for releases).

You will be prompted for a project name.
The name you provide is used to create the project folder (converted to lowercase with hyphens).

.. code:: text

   project_name [Custom Dioptra Worker]: My NLP Worker

This creates a folder named ``my-nlp-worker/`` containing the files needed to build a custom worker image.
See the :ref:`reference-custom-worker-template` for a full description of the generated files.

.. rst-class:: header-on-a-card header-steps

Step 2: Add Python Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open ``requirements.txt`` in the generated project folder.
By default it contains only ``dioptra-platform``, which is required for the worker to function:

.. code:: text

   dioptra-platform

Add any additional Python packages your worker needs.
For example, to include the ``textattack`` package:

.. code:: text

   dioptra-platform
   textattack

.. note::

   The ``dioptra-platform`` package must remain in ``requirements.txt``.
   It provides the worker process and task engine that Dioptra requires.

.. rst-class:: header-on-a-card header-steps

Step 3: Build the Docker Image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

From inside the generated project folder, build the Docker image:

.. code:: sh

   cd my-nlp-worker
   docker build -t my-nlp-worker:dev .

Choose an image name and tag that you will recognize when configuring your deployment.

.. note::

   If your build environment requires custom CA certificates (for example, in a corporate network that intercepts HTTPS traffic), see the ``ca-certificates/README.md`` file in the generated project for instructions.

.. rst-class:: header-on-a-card header-steps

Step 4: Verify the Image
~~~~~~~~~~~~~~~~~~~~~~~~~~

Confirm the image was built successfully:

.. code:: sh

   docker images | grep my-nlp-worker

You should see the image listed with the tag you specified.

Advanced Customization
----------------------

The template is designed for users who need to add Python packages to the worker environment.
If you need to install operating system packages, add scripts, or include other files in the container, you can edit the ``Dockerfile`` directly.

.. rst-class:: header-on-a-card header-seealso

See Also
--------

- `Dockerfile reference <https://docs.docker.com/reference/dockerfile/>`__ - General reference to consult when customizing Docker images
- :ref:`how-to-integrating-custom-containers` - Add the custom worker to your Dioptra deployment
- :ref:`reference-custom-worker-template` - Template variables and generated folder structure
- :ref:`how-to-using-docker-compose-overrides` - Docker Compose override file basics
