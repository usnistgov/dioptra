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

.. _reference-deployment-template:

Deployment Template Reference
=============================

This reference describes the template variables used by the Dioptra deployment cookiecutter template.
These variables control how the deployment configuration files are generated.

.. seealso::

   :ref:`how-to-prepare-deployment` - Step-by-step guide for customizing your deployment.

Template Variables
------------------

When using ``cruft`` interactively (Method 1 in the how-to guide), you will be prompted to set the following variables.
In most cases, you can accept the default value, but some variables may need customization based on your environment.

deployment_name
~~~~~~~~~~~~~~~

**Default:** ``Dioptra deployment``

A name to associate with the deployment.
The template will `"slugify" <https://www.stackbit.com/blog/what-is-a-content-slug>`__ the deployment name you provide and use it to name files, folders, and configuration settings.
For example, it will be used to name the main folder created by the template (``dioptra-deployment`` for the default value).

container_registry
~~~~~~~~~~~~~~~~~~

**Default:** *empty string*

This is only needed if you are building and pushing Dioptra container images to your own Docker registry.
As an example, if you are using a Docker registry `hosted on a JFrog Artifactory instance <https://www.jfrog.com/confluence/display/JFROG/Getting+Started+with+Artifactory+as+a+Docker+Registry>`__ at the URL ``acme-dockerv2-virtual.jfrog.io``, then you would answer ``acme-dockerv2-virtual.jfrog.io``.
Otherwise, leave this blank.

container_tag
~~~~~~~~~~~~~

**Default:** ``dev``

This should match the tags of the Dioptra container images you will be using.
If you are using Docker, you can see the available tags by running ``docker images``.
If you built the images manually using the build commands in the repository, the images will have the ``dev`` tag.

docker_compose_path
~~~~~~~~~~~~~~~~~~~

**Default:** ``docker compose``

This should match the way you invoke Docker Compose on the host machine.
If you are running an up-to-date version of Docker with the Compose plugin, then you should answer ``docker compose``.
If instead `you installed Docker Compose v2 in a standalone manner <https://docs.docker.com/compose/install/other/>`__, then this should be the absolute path to the ``docker-compose`` binary, for example ``/usr/local/bin/docker-compose``.

systemd_required_mounts
~~~~~~~~~~~~~~~~~~~~~~~

**Default:** *empty string*

This applies only if you are deploying Dioptra on a Linux distribution that uses systemd, such as Ubuntu, Fedora, or Red Hat Enterprise Linux.
Otherwise, leave this blank.

The "required mounts" are the storage devices mounted on the host machine, which may include NFS volumes or block storage volumes, that must be accessible before the Dioptra application containers can start.
This list should include all the devices that store the container images, runtime files, and volume data for Dioptra.

To find the mount names for your system, run:

.. code:: sh

   sudo systemctl list-units -t mount

The names you should use are in the first column labeled UNIT.
Multiple mounts should be separated by spaces, for example: ``data.mount var.mount``.

nginx_server_name
~~~~~~~~~~~~~~~~~

**Default:** ``dioptra.example.org``

If you are hosting Dioptra on a remote machine, such as a virtual private server, then this will either be a domain name like ``dioptra.example.org`` or the IP address you use to access the machine.
If you are running Dioptra on your personal computer or laptop, then answer ``_`` (underscore).

nginx_expose_ports_on_localhost_only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Default:** ``True``

Choosing ``True`` will generate a ``docker-compose.yml`` file that binds the NGINX ports to the loopback interface (localhost, 127.0.0.1).
In this configuration, you will need to use port forwarding via SSH or a firewall in order to access the services from another machine.
If ``False``, the NGINX ports will be exposed on all available network interfaces.

**Recommendations:**

- **Personal computer or laptop:** Choose ``True``
- **Remote server with SSH access:** Choose ``True`` and use SSH port forwarding
- **Remote server without SSH (not recommended):** Choose ``False``, but ensure you have firewall rules in place

.. important::

   Dioptra currently does not have a comprehensive access control system, so it is recommended to choose ``True`` on remote machines and use SSH or firewall rules to manage access.

postgres_container_tag
~~~~~~~~~~~~~~~~~~~~~~

**Default:** ``15``

Sets the version of PostgreSQL to be used in the deployment.
For a full list of available versions, visit the *Tags* tab on the `postgres image page on Docker Hub <https://hub.docker.com/_/postgres>`__.

pgadmin_default_email
~~~~~~~~~~~~~~~~~~~~~

**Default:** ``dioptra@example.com``

This email address will be used to create the default account on the `pgadmin4 app <https://www.pgadmin.org/docs/pgadmin4/latest/index.html>`__, which provides a web interface for database administration.

num_tensorflow_cpu_workers
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Default:** ``1``

Sets the number of TensorFlow CPU workers to use in your Dioptra deployment.
Each worker is dedicated to watching a named queue and runs one job at a time.
Increase this number if you need to run multiple TensorFlow CPU jobs concurrently.

num_tensorflow_gpu_workers
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Default:** ``0``

Sets the number of TensorFlow GPU workers to use in your Dioptra deployment.
Each worker is assigned a dedicated GPU, watches a named queue, and runs one job at a time.

.. warning::

   The combined number of TensorFlow and PyTorch GPU workers cannot be greater than the number of GPUs available on the host machine.

num_pytorch_cpu_workers
~~~~~~~~~~~~~~~~~~~~~~~

**Default:** ``1``

Sets the number of PyTorch CPU workers to use in your Dioptra deployment.
Each worker is dedicated to watching a named queue and runs one job at a time.
Increase this number if you need to run multiple PyTorch CPU jobs concurrently.

num_pytorch_gpu_workers
~~~~~~~~~~~~~~~~~~~~~~~

**Default:** ``0``

Sets the number of PyTorch GPU workers to use in your Dioptra deployment.
Each worker is assigned a dedicated GPU, watches a named queue, and runs one job at a time.

.. warning::

   The combined number of TensorFlow and PyTorch GPU workers cannot be greater than the number of GPUs available on the host machine.

datasets_directory
~~~~~~~~~~~~~~~~~~

**Default:** *empty string*

Sets the datasets directory to be mounted into all worker containers in your Dioptra deployment.
The provided directory will be mounted to ``/dioptra/data`` in each worker container.
If an empty string is provided, no dataset directory will be mounted.
If the provided path is not valid, the ``init-deployment.sh`` script will fail.

More advanced configurations (such as mounting multiple directories or NFS shares) can be achieved by modifying the ``docker-compose.override.yml`` file.
See :ref:`how-to-data-mounts` for details.

.. seealso::

   :ref:`how-to-download-data` - Information about downloading example datasets.

Interactive Prompt Example
--------------------------

When using ``cruft`` interactively (Method 1), you will see prompts like the following.
The values between the square brackets ``[]`` show the default answer for each question.
Press Enter to accept the default, or type a new value.

.. code:: text

   deployment_name [Dioptra deployment]: Dioptra deployment
   container_registry []:
   container_tag [dev]: dev
   docker_compose_path [docker compose]: docker compose
   systemd_required_mounts []:
   nginx_server_name [dioptra.example.org]: _
   Select nginx_expose_ports_on_localhost_only:
   1 - True
   2 - False
   Choose from 1, 2 [1]: 1
   postgres_container_tag [15]: 15
   pgadmin_default_email [dioptra@example.com]: dioptra@example.com
   num_tensorflow_cpu_workers [1]: 1
   num_tensorflow_gpu_workers [0]: 0
   num_pytorch_cpu_workers [1]: 1
   num_pytorch_gpu_workers [0]: 0
   datasets_directory []: /path/to/dioptra/data

.. tip::

   If you make a mistake during the interactive prompts (such as accepting a default by accident or making a typo), you can interrupt ``cruft`` by pressing :kbd:`Ctrl+C`.
   If ``cruft`` has already created a folder (check your working directory), remove it before starting over.
   The folder name will be a slugified version of the **deployment_name** variable.

Non-Interactive Configuration
-----------------------------

For automated deployments or when you want to avoid interactive prompts, you can use one of these methods.

.. note::

   Replace ``<branch-name>`` with the Dioptra branch that matches your container images (e.g., ``main`` for releases, ``dev`` for development builds).

**Use all defaults:**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input

**Override specific values on the command line:**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input \
     --extra-context '{"datasets_directory": "~/datasets", "nginx_server_name": "_"}'

**Override values from a JSON file:**

Create a file named ``overrides.json``:

.. code:: json

   {
     "deployment_name": "My Dioptra Deployment",
     "datasets_directory": "/data/ml-datasets",
     "nginx_server_name": "_",
     "num_tensorflow_cpu_workers": "2"
   }

Then run:

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input \
     --extra-context-file overrides.json
