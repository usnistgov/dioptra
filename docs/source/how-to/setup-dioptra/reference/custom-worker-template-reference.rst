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

.. _reference-custom-worker-template:

Custom Worker Template Reference
=================================

This reference describes the template variables and generated files for the custom Dioptra worker cookiecutter template.

.. seealso::

   :ref:`how-to-creating-custom-workers` - Step-by-step guide for creating a custom worker container.

Template Variables
------------------

When running ``cookiecutter`` interactively, you will be prompted to set the following variable.

project_name
~~~~~~~~~~~~

**Default:** ``Custom Dioptra Worker``

A name for your custom worker project.
The template converts this name to a slug (lowercase, spaces and underscores replaced with hyphens) and uses it as the generated folder name.
For example, ``My NLP Worker`` produces a folder named ``my-nlp-worker``.

Interactive Prompt Example
--------------------------

When running ``cookiecutter`` interactively, you will see a prompt like the following.
The value between the square brackets ``[]`` shows the default answer.
Press Enter to accept the default, or type a new value.

.. code:: text

   project_name [Custom Dioptra Worker]: My NLP Worker

.. tip::

   If you make a mistake during the prompt, you can interrupt ``cookiecutter`` by pressing :kbd:`Ctrl+C`.
   If ``cookiecutter`` has already created a folder, remove it before starting over.

Non-Interactive Configuration
-----------------------------

To skip the interactive prompt, use ``--no-input`` and pass variable values directly.

.. note::

   Replace ``<branch-name>`` with the Dioptra branch that matches your deployment (e.g., ``main`` for releases).

**Use the default project name:**

.. code:: sh

   cookiecutter https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/custom-dioptra-worker --no-input

**Override the project name:**

.. code:: sh

   cookiecutter https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/custom-dioptra-worker --no-input \
     project_name="My NLP Worker"

Generated Folder Structure
--------------------------

The following tree shows all files created by the template.
The folder name is derived from the ``project_name`` variable.

.. code:: text

   my-nlp-worker/
   ├── ca-certificates/
   │   └── README.md
   ├── configs/
   │   └── aws-config
   ├── shellscripts/
   │   ├── entrypoint-worker.m4
   │   ├── healthcheck-worker.m4
   │   └── wait-for-it.sh
   ├── Dockerfile
   └── requirements.txt

Dockerfile
~~~~~~~~~~

Multi-stage Docker build file that produces the custom worker image.
The build process:

1. Installs system packages and configures the locale.
2. Bundles any CA certificates placed in ``ca-certificates/``.
3. Compiles shell script templates (``*.m4`` files) into executable scripts using `argbash <https://argbash.dev/>`__.
4. Creates a Python virtual environment and installs the packages listed in ``requirements.txt``.
5. Assembles the final image with the worker entrypoint, health check, and virtual environment.

The image is compatible with both ``amd64`` and ``arm64`` platforms and defaults to the host platform when building.

requirements.txt
~~~~~~~~~~~~~~~~

Lists the Python packages to install in the worker's virtual environment.
Must include ``dioptra-platform`` as a dependency.
Add additional packages here to make them available to the worker at runtime.

ca-certificates/
~~~~~~~~~~~~~~~~~

Place custom CA certificate files (``.crt``, PEM format) in this directory if the build environment requires them.
See the ``README.md`` inside this directory for details.

These certificates are used only during the Docker build process and are not included in the final image at runtime.

configs/
~~~~~~~~

**aws-config**
   AWS CLI configuration file copied to ``~dioptra/.aws/config`` in the final image.
   Sets the default AWS region (``us-east-1``), output format (``json``), and S3 signature version (``s3v4``).
   This is required for the worker to communicate with the S3-compatible storage backend (MinIO).

shellscripts/
~~~~~~~~~~~~~

Shell script templates that are compiled during the Docker build.

**entrypoint-worker.m4**
   Template for the container's entrypoint script.
   The compiled script waits for dependent services (Redis, MinIO, database, REST API) to become available, then starts the ``dioptra-worker-v1`` process.

**healthcheck-worker.m4**
   Template for the container's health check script.
   The compiled script verifies that the ``dioptra-worker-v1`` process is running.

**wait-for-it.sh**
   Utility script that tests TCP connectivity to a host and port.
   Used by the entrypoint script to wait for services before starting the worker.
