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

.. _getting-started-running-dioptra:

Running Dioptra
===============

.. include:: /_glossary_note.rst

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
   python -m pip install --upgrade pip cruft jinja2

   # Run cruft and set the template's variables
   cruft create https://github.com/usnistgov/dioptra --checkout $DIOPTRA_BRANCH \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment

Cruft will now run and prompt you to configure the deployment. See the :ref:`Applying the template <getting-started-running-dioptra-applying-the-template>` section for detailed description of each prompt.

We recommend identifying a location to store datasets you will want to use with Dioptra at this point and setting the ``datasets_directory`` variable accordingly. See the :ref:`Downloading the datasets <getting-started-acquiring-datasets>` section for more details.

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

.. _getting-started-running-dioptra-applying-the-template:

Applying the template
---------------------

Create the folder where you plan to keep the deployment folder and change into it so that it becomes your working directory.
Next, run cruft and apply the Dioptra Deployment template.

.. code:: sh

   # To use the template published on the dev branch, use '--checkout dev' instead
   cruft create https://github.com/usnistgov/dioptra --checkout main \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment

.. margin::

   .. note::

      If you make a mistake, such as accidentally accepting a default or making a typo, it is recommended that you interrupt cruft and start over.
      To interrupt the cruft prompts at any time, press :kbd:`Ctrl + C`, then check if cruft has created a new folder in your working directory (if present, the folder's name will be a `"slugified" <https://www.stackbit.com/blog/what-is-a-content-slug>`__ version of the **deployment_name** variable).
      If it has, remove it.
      To start over, re-run the ``cruft`` command.

You will now be asked to set the variables needed to customize the generated configuration files.
In most cases you can just use the default value, but there are a few that you may need to customize.
Below is a full list of the variables, their default values, and explanations of what they mean.

- **deployment_name:** A name to associate with the deployment.
  The template will `"slugify" <https://www.stackbit.com/blog/what-is-a-content-slug>`__ the deployment name you provide and use it to name files, folders, and in configuration settings.
  For example, it will be used to name the main folder created by the template.
  (default: ``Dioptra deployment``)
- **container_registry:** This is only needed if you are building and pushing Dioptra container images to your own Docker registry.
  As an example, if you are using a Docker registry `hosted on a hypothetical JFrog Artifactory instance <https://www.jfrog.com/confluence/display/JFROG/Getting+Started+with+Artifactory+as+a+Docker+Registry>`__ at the URL ``acme-dockerv2-virtual.jfrog.io``, then you would answer ``acme-dockerv2-virtual.jfrog.io``.
  Otherwise, leave this blank.
  (default: *empty string*)
- **container_tag:** This should match the tags of the Dioptra container images you will be using (if you are using Docker, you can see the available tags by running ``docker images``).
  If you built the images manually, the images will have the ``dev`` tag.
  (default: ``dev``)
- **docker_compose_path:** This should match the way you invoke Docker Compose on the host machine.
  If you are running an up-to-date version of Docker with the Compose plugin, then you should answer ``docker compose``.
  If instead `you installed Docker Compose v2 in a standalone manner <https://docs.docker.com/compose/install/other/>`__, then this should be the absolute path to the ``docker-compose`` binary, for example ``/usr/local/bin/docker-compose``.
  (default: ``docker compose``)
- **systemd_required_mounts:** This applies only if you are deploying Dioptra on a Linux distribution that uses systemd, such as Ubuntu, Fedora, or Red Hat Enterprise Linux, otherwise leave this blank.
  The "required mounts" would be the storage devices mounted on the host machine, which may include NFS volumes or block storage volumes, that must be accessible before the Dioptra application containers can start.
  This list should include all the devices that store the container images, runtime files, and volume data for Dioptra.
  Run ``sudo systemctl list-units -t mount`` to print the full list of mounted devices for your virtual machine.
  The names you should use are in the first column labeled UNIT.
  Multiple mounts should be separated by spaces, i.e. ``data.mount var.mount``.
  (default: *empty string*)
- **nginx_server_name:** If you are hosting Dioptra on an remote machine, such as a virtual private server, then this will either be a domain name like ``dioptra.example.org`` or the IP address you use to access the machine.
  If you are running Dioptra on your personal computer or laptop, then answer ``_``.
  (default: ``dioptra.example.org``)
- **nginx_expose_ports_on_localhost_only:** Choosing ``True`` will generate a ``docker-compose.yml`` file that binds the NGINX ports to the loopback interface (localhost, 127.0.0.1).
  In this configuration, you will need to use port forwarding via SSH or a firewall in order to access the services.
  If ``False``, the NGINX ports will be exposed on all available network interfaces.
  Dioptra currently does not have an access control system, so for now it is recommended that you choose ``True`` on remote machines and use SSH or firewall rules to manage access.
  If you are running Dioptra on your personal computer or laptop, also choose ``True``.
  (default: ``True``)
- **postgres_container_tag:** Sets the version of postgres to be used in the deployment.
  For a full list of available versions, visit the *Tags* tab on the `postgres image page on Docker Hub <https://hub.docker.com/_/postgres>`__.
  (default: ``15``)
- **pgadmin_default_email:** This email address will be used to create the default account on the `pgadmin4 app <https://www.pgadmin.org/docs/pgadmin4/latest/index.html>`__.
  (default: ``dioptra@example.com``)
- **num_tensorflow_cpu_workers:** Sets the number of Tensorflow CPU workers to use in your Dioptra deployment.
  Each worker is dedicated to watching a named queue and running one job at a time.
  (default: ``1``)
- **num_tensorflow_gpu_workers:** Sets the number of Tensorflow GPU workers to use in your Dioptra deployment.
  Each worker is assigned a dedicated GPU, watches a named queue, and runs one job at a time.
  The combined number of Tensorflow and PyTorch GPU workers cannot be greater than the number of GPUs available on the host machine.
  (default: ``0``)
- **num_pytorch_cpu_workers:** Sets the number of PyTorch CPU workers to use in your Dioptra deployment.
  Each worker is dedicated to watching a named queue and running one job at a time.
  (default: ``1``)
- **num_pytorch_gpu_workers:** Sets the number of PyTorch GPU workers to use in your Dioptra deployment.
  Each worker is assigned a dedicated GPU, watches a named queue, and runs one job at a time.
  The combined number of Tensorflow and PyTorch GPU workers cannot be greater than the number of GPUs available on the host machine.
  (default: ``0``)
- **datasets_directory:** Sets the datasets directory to be mounted into all worker containers in your Dioptra deployment.
  The provided directory will be mounted to `/dioptra/data` in each worker container.
  If an empty string is provided, no dataset directory will be mounted.
  If the provided path is not valid, the `init-deployment.sh` script will fail.
  More advanced configurations can be achieved by modifying the `docker-compose.override.yml` file.
  (default: ``""``)

Example
~~~~~~~

Below is an example of what it looks like to customize some of the template variables after invoking the template using ``cruft``.

.. margin::

   .. note::

      The words between the square brackets ``[]`` show the default answer for each question.

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

Updating the template
---------------------

The cruft tool makes it easy to fetch the latest updates to the template:

.. code:: sh

   # Activate the virtual environment (if not active)
   source .venv/bin/activate

   # Fetch the updates
   # (If using a different branch, replace "main" with that branch's name)
   cruft update --checkout main

Cookiecutter variables can also be updated via cruft:

.. code:: sh

   # Activate the virtual environment (if not active)
   source .venv/bin/activate

   # Update the datasets_directory variable
   # (If using a different branch, replace "main" with that branch's name)
   cruft update --checkout main \
     --variables-to-update '{ "datasets_directory": "/path/to/dioptra/data" }'

Be sure to run `init-deployment.sh` again after updating the template.

Folder organization
-------------------

.. margin::

   .. note::

      The *dioptra-deployment* prefix prepended to the files in the ``envs/`` and ``secrets/`` folders assumes the default value for the **deployment_name** variable.
      Setting this variable to a different value would alter the filename prefixes.

The following tree-like diagram shows the files created by the template.
The annotations explain the purpose of the configuration files.
Note that this diagram includes server certificates and private keys for the NGINX and Postgres services, which may or may not apply to your use case.

.. code:: text

   .
   ├── config
   │   ├── db
   │   │   └── init-db.sh                                       <- Postgres initialization script that creates the accounts and databases used in the Dioptra app.
   │   ├── minio
   │   │   ├── builtin-plugins-readonly-policy.json             <- A Minio access policy. Configures a readonly role for the dioptra_builtins/ folder in the plugins bucket.
   │   │   ├── builtin-plugins-readwrite-policy.json            <- A Minio access policy. Configures a readwrite role for the dioptra_builtins/ folder in the plugins bucket.
   │   │   ├── custom-plugins-readonly-policy.json              <- A Minio access policy. Configures a readonly role for the dioptra_custom/ folder in the plugins bucket.
   │   │   ├── custom-plugins-readwrite-policy.json             <- A Minio access policy. Configures a readwrite role for the dioptra_custom/ folder in the plugins bucket.
   │   │   ├── dioptra-readonly-policy.json                     <- A Minio access policy. Configures a readonly role for all folders and buckets created and used by Dioptra.
   │   │   ├── mlflow-tracking-readwrite-policy.json            <- A Minio access policy. Configures a readwrite role for the artifacts/ folder in the mlflow-tracking bucket.
   │   │   ├── plugins-readonly-policy.json                     <- A Minio access policy. Configures a readonly role for the dioptra_builtins/ and dioptra_custom/ folders in the plugins bucket.
   │   │   ├── workflow-downloadonly-policy.json                <- A Minio access policy. Configures a downloadonly role for the workflow bucket.
   │   │   └── workflow-uploadonly-policy.json                  <- A Minio access policy. Configures a uploadonly role for the for the workflow bucket.
   │   └── nginx
   │       ├── http_dbadmin.conf                                <- (HTTP) Configures Nginx to serve the pgadmin4 dashboard over http connections.
   │       ├── http_default.conf                                <- (HTTP) Configures the basic defaults for Nginx to use when serving content over http connections.
   │       ├── http_minio.conf                                  <- (HTTP) Configures Nginx to serve the Minio service over http connections.
   │       ├── http_mlflow.conf                                 <- (HTTP) Configures Nginx to serve the MLflow Tracking service over http connections.
   │       ├── http_proxy.conf                                  <- (HTTP) Configures the general reverse proxy settings for Nginx when serving content over http connections, including how Nginx modifies the request header fields.
   │       ├── http_restapi.conf                                <- (HTTP) Configures Nginx to serve the Dioptra REST API service over http connections.
   │       ├── https_dbadmin.conf                               <- (HTTPS) Configures Nginx to serve the pgadmin4 dashboard over https connections.
   │       ├── https_default.conf                               <- (HTTPS) Configures the basic defaults for Nginx to use when serving content over https connections, which includes setting the path to the server certificate and private key.
   │       ├── https_minio.conf                                 <- (HTTPS) Configures Nginx to serve the Minio service over https connections.
   │       ├── https_mlflow.conf                                <- (HTTPS) Configures Nginx to serve the MLflow Tracking service over https connections.
   │       ├── https_proxy.conf                                 <- (HTTPS) Configures the general reverse proxy settings for Nginx when serving content over https connections, including how Nginx modifies the request header fields.
   │       ├── https_restapi.conf                               <- (HTTPS) Configures Nginx to serve the Dioptra REST API service over https connections.
   │       └── stream_db.conf                                   <- Configures Nginx to proxy tcp requests to the Postgres database. This is a simple passthrough, so any SSL encryption must be enabled in the Postgres service itself, see ssl/db/README.md for more info.
   ├── envs
   │   ├── ca-certificates.env                                  <- Sets common environment variables that applications use to find extra CA certificates. Safe to commit to a git repo.
   │   ├── dioptra-deployment-db.env                            <- Sets environment variables that customize the Postgres database. Safe to commit to a git repo.
   │   ├── dioptra-deployment-dbadmin.env                       <- Sets environment variables that customize the pgadmin4 dashboard. Safe to commit to a git repo.
   │   ├── dioptra-deployment-mlflow-tracking.env               <- Sets environment variables that customize the MLflow Tracking service. Safe to commit to a git repo.
   │   ├── dioptra-deployment-restapi.env                       <- Sets environment variables that customize the Dioptra REST API service. Safe to commit to a git repo.
   │   ├── dioptra-deployment-worker-cpu.env                    <- Sets environment variables that customize the CPU-based Dioptra workers. Safe to commit to a git repo.
   │   └── dioptra-deployment-worker.env                        <- Sets environment variables that customize the Dioptra workers. Safe to commit to a git repo.
   ├── scripts
   │   ├── templates
   │   │   ├── dioptra.service.j2                               <- A Jinja2 template used to generate the systemd/dioptra.service file.
   │   │   ├── dot-env.j2                                       <- A Jinja2 template used to generate a .env file containing a list of environment variables and associated passwords.
   │   │   ├── minio-accounts.env.j2                            <- A Jinja2 template used to generate the secrets/dioptra-deployment-minio-accounts.env file.
   │   │   └── postgres-passwd.env.j2                           <- A Jinja2 template used to generate the secrets/postgres-passwd.env file.
   │   ├── copy-extra-ca-certificates.m4                        <- Used in the init-deployment.sh and init-named-volumes.m4 scripts to inject the extra CA certificates in the ssl/ca-certificates folder into the services.
   │   ├── file-copy.m4                                         <- Used in the init-named-volumes.m4 script to handle file copying. Emits logging information and sets appropriate access and ownership permissions.
   │   ├── git-clone.m4                                         <- Used in the init-named-volumes.m4 script to handle cloning git repositories. Emits logging information and sets appropriate access and ownership permissions.
   │   ├── generate_password_templates.py                       <- Used in the init-named-volumes.m4 script to generate random passwords to secure Dioptra's services.
   │   ├── globbed-copy.m4                                      <- Used in the init-named-volumes.m4 script to handle globbed file copying. Emits logging information and sets appropriate access and ownership permissions.
   │   ├── init-minio.sh                                        <- Used in the init-deployment.sh script to set the Minio policies in config/minio.
   │   ├── init-named-volumes.m4                                <- Used in the init-deployment.sh script to prepare the named storage volumes used by each container. Actions include copying in configuration files and setting file access and ownership permissions.
   │   ├── init-scripts.sh                                      <- Used in the init-deployment.sh script to translate this folder's *.m4 files into executable bash scripts using argbash.
   │   ├── manage-postgres-ssl.m4                               <- Used in the init-deployment.sh script to enable and disable SSL in Postgres.
   │   └── set-permissions.m4                                   <- Used in the init-named-volumes.m4 script to set appropriate access and ownership permissions.
   ├── secrets
   │   ├── dioptra-deployment-minio-accounts.env                <- Secrets file containing sensitive passwords generated by the scripts/generate_password_templates.py script. NOT SAFE TO SHARE OR COMMIT TO A GIT REPO.
   │   └── postgres-passwd.env                                  <- Secrets file containing sensitive passwords generated by the scripts/generate_password_templates.py script. NOT SAFE TO SHARE OR COMMIT TO A GIT REPO.
   ├── ssl
   │   ├── ca-certificates
   │   │   └── README.md                                        <- README file explaining the folder's purpose and which files need to be copied here.
   │   ├── db
   │   │   ├── server.crt                                       <- MUST BE COPIED HERE MANUALLY. The server certificate for enabling encrypted traffic to the Postgres database.
   │   │   ├── server.key                                       <- MUST BE COPIED HERE MANUALLY. The private key for enabling encrypted traffic to the Postgres database. NOT SAFE TO SHARE OR COMMIT TO A GIT REPO.
   │   │   └── README.md                                        <- README file explaining the folder's purpose and which files need to be copied here.
   │   └── nginx
   │       ├── server.crt                                       <- MUST BE COPIED HERE MANUALLY. The server certificate for enabling HTTPS in the Nginx webserver.
   │       ├── server.key                                       <- MUST BE COPIED HERE MANUALLY. The private key for enabling HTTPS in the Nginx webserver. NOT SAFE TO SHARE OR COMMIT TO A GIT REPO.
   │       └── README.md                                        <- README file explaining the folder's purpose and which files need to be copied here.
   ├── systemd
   │   └── dioptra.service                                      <- A systemd service that can be used to manage the full Dioptra application generated by the scripts/generate_password_templates.py script.
   ├── .env                                                     <- A list of secrets (passwords) mapped to environment variables generated by the scripts/generate_password_templates.py script. NOT SAFE TO SHARE OR COMMIT TO A GIT REPO.
   ├── .gitignore                                               <- A list of patterns that configures the files and directories that git should ignore. Used if the deployment configuration is placed under version control with git.
   ├── docker-compose.init.yml                                  <- Used in the init-deployment.sh script to initialize the deployment.
   ├── docker-compose.override.yml.template                     <- A template for overriding portions of the docker-compose.yml for custom configurations.
   ├── init-deployment.sh                                       <- The deployment initialization script. Used to generate random passwords, copy configuration files into named volumes, configure Minio policies, and enable/disable SSL in the NGINX and Postgres services.
   └── README.md                                                <- README file that explains how to initialize and run Dioptra using the provided scripts and configuration files.

Additional configuration
------------------------

The generated template takes care of most of the configuration work for you.
However, depending on your use case, you may need to complete some additional steps before you initialize and boot up the deployment for the first time.
The following subsections explain how to:

- Copy extra CA certificates into the containers
- Copy the certificate-key pairs that enable SSL/TLS encrypted connections in the NGINX and Postgres services
- Mount additional folders in the worker containers, for example a folder that contains your datasets
- Assign GPUs to specific worker containers
- Integrate custom containers in the Dioptra deployment

In addition to the above, you may want to further customize the Docker Compose configuration via the ``docker-compose.override.yml`` file to suit your needs, such as allocating explicit CPUs you want each container to use.
An example template file (``docker-compose.override.yml.template``) is provided as part of the deployment as a starting point.
This can be copied to ``docker-compose.override.yml`` and modified.
See the `Compose specification documentation <https://docs.docker.com/compose/compose-file/>`__ for the full list of available options.
See the `Merge and override documentation <https://docs.docker.com/compose/compose-file/13-merge/>`__ for details on using multiple Compose files.

Adding extra CA certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The deployment initialization scripts will look for extra CA certificates in the ``ssl/ca-certificates/`` folder and copy and bundle them into named volumes so they are available at runtime.
Only CA certificate files copied into the ``ssl/ca-certificates/`` folder that meet the following criteria will be bundled:

- Each CA certificate file must be in the PEM format.
  The PEM format encodes the certificate using base64 and stores it in a plain text file between two lines, ``-----BEGIN CERTIFICATE-----`` and ``-----END CERTIFICATE-----``.
- Each file should include one, and only one, CA certificate.
  Do not bundle multiple CA certificates together.
- Each PEM-formatted CA certificate file **must** have the file extension ``crt``, for example ``ca-root.crt``.
  If your CA certificate has a different file extension (such as ``pem``), rename it to ``crt`` after copying to this folder.

For further information about including extra CA certificates, please see the ``README.md`` file in the ``ssl/ca-certificates/`` folder.

.. _running-dioptra-enabling-ssl-tls-in-nginx-and-postgres:

Enabling SSL/TLS in NGINX and Postgres
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the deployment initialization scripts are directed to enable SSL/TLS in the NGINX and/or Postgres services, it will scan the ``ssl/db/`` and ``ssl/nginx/`` folders for server certificate(s) and private key(s).
The server certificate must be named ``server.crt`` and the private key must be named ``server.key`` when copying them into the ``ssl/db/`` and ``ssl/nginx/`` folders.
This applies even when you are using a different certificate-key pair for each service.
As an example, if the certificate and key files start in the folder ``/home/username/certs`` with different names, you would copy the files as follows,

.. code:: sh

   # These commands assume you are in the folder you just created using cookiecutter.
   cp /home/username/certs/db.crt ./ssl/db/server.crt
   cp /home/username/certs/db.key ./ssl/db/server.key
   cp /home/username/certs/nginx.crt ./ssl/nginx/server.crt
   cp /home/username/certs/nginx.key ./ssl/nginx/server.key

.. margin::

   .. important::

      The NGINX SSL/TLS disabled and enabled tabs are just snippets.
      The snippets omit the lines that come both before and after the ``healthcheck:`` and ``ports:`` sections.
      **Do not delete these surrounding lines in your actual file!**

If you are enabling SSL/TLS in the NGINX service, you will also need to comment/uncomment a few lines in the ``docker-compose.yml`` file that configure the NGINX service's published ports and health check test.
Open the file in a text editor, find the block for the NGINX service (the block starts with ``dioptra-deployment-nginx:`` if you used the default value for **deployment_name**), and edit its ports and health check test to match the appropriate YAML snippet below.

.. tab-set::

   .. tab-item:: NGINX SSL/TLS disabled

      .. code:: yaml

         dioptra-deployment-nginx:
           healthcheck:
             test:
               [
                 "CMD",
                 "/usr/local/bin/healthcheck.sh",
                 "http://localhost:30080",
                 "http://localhost:35000",
                 "http://localhost:35050/login",
                 "http://localhost:39000",
                 "http://localhost:39001",
                 # "https://localhost:30443",
                 # "https://localhost:35000",
                 # "https://localhost:35050/login",
                 # "https://localhost:39000",
                 # "https://localhost:39001",
               ]
           ports:
             - 127.0.0.1:80:30080/tcp
             # - 127.0.0.1:443:30443/tcp
             - 127.0.0.1:35432:5432/tcp
             - 127.0.0.1:35000:35000/tcp
             - 127.0.0.1:35050:35050/tcp
             - 127.0.0.1:39000:39000/tcp
             - 127.0.0.1:39001:39001/tcp

   .. tab-item:: NGINX SSL/TLS enabled

      .. code:: yaml

         dioptra-deployment-nginx:
           healthcheck:
             test:
               [
                 "CMD",
                 "/usr/local/bin/healthcheck.sh",
                 "http://localhost:30080",
                 # "http://localhost:35000",
                 # "http://localhost:35050/login",
                 # "http://localhost:39000",
                 # "http://localhost:39001",
                 "https://localhost:30443",
                 "https://localhost:35000",
                 "https://localhost:35050/login",
                 "https://localhost:39000",
                 "https://localhost:39001",
               ]
           ports:
             - 127.0.0.1:80:30080/tcp
             - 127.0.0.1:443:30443/tcp
             - 127.0.0.1:35432:5432/tcp
             - 127.0.0.1:35000:35000/tcp
             - 127.0.0.1:35050:35050/tcp
             - 127.0.0.1:39000:39000/tcp
             - 127.0.0.1:39001:39001/tcp

For further information about adding the certificate-key pairs, please see the ``README.md`` files in the ``ssl/db`` and ``ssl/nginx/`` folders.

.. _running-dioptra-mounting-folders-in-the-worker-containers:

Mounting folders in the worker containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``docker-compose.yml`` file generated by the cookiecutter template only supports mounting a single datasets directory from the host machine into worker containers.
A more advanced configuration can be achieved via the ``docker-compose.override.yml`` file.
A template is generated by cookiecutter and can be copied from `docker-compose.override.yml.template` to `docker-compose.override.yml` for modification.

Common reasons for mounting additional folders in the worker containers include:

1. Your datasets are stored in a folder on your host machine or in an NFS share
2. You want to make other artifacts available to the worker containers, such as pre-trained models

An example that illustrates how to mount a folder on the host machine and a folder in an NFS share is shown in the subsections below.

Mounting a folder on the host machine
#####################################

For this example, let's assume the datasets are stored on the host machine under the absolute path ``/home/data`` and that we want to make these available in the worker containers under the absolute path ``/dioptra/data``.
We also want to make the folders read-only to prevent a job from accidentally modifying or deleting the data.
To do this, first verify that the folder ``/home/data`` and all of its files are world-readable.
If they are not, you can fix this as follows:

.. code:: sh

   find /home/data -type d -print0 | xargs -0 chmod o=rx
   find /home/data -type f -print0 | xargs -0 chmod o=r

Next, copy ``docker-compose.override.yml`` to ``docker-compose.override.yml.template``, open it with a text editor and find the blocks for the worker containers.
The worker container blocks will have **tfcpu**, **tfgpu**, **pytorch-cpu**, or **pytorch-gpu** in their names.
Append the line ``- "/home/data:/dioptra/data:ro"`` to the ``volumes:`` subsections.

.. code:: yaml

   dioptra-deployment-tfcpu-01:
     volumes:
       - "/home/data:/dioptra/data:ro"

Mounting a folder on an NFS share
#################################

.. margin::

   .. note::

      If you are mounting an NFS share, don't forget to change the IP address and exported directory to match your setup.

For this example, let's assume the datasets are stored on a NFS version 4 server with IP address 10.0.0.10 and in the exported directory ``/dioptra/data`` and that we want to make these available in the worker containers under the absolute path ``/dioptra/data``.
First, we need to configure a named NFS volume in the ``docker-compose.override.yml`` file so that Docker knows where the NFS server is and which exported directory to use.
Copy ``docker-compose.override.yml.template`` to ``docker-compose.override.yml``, open it with a text editor and find the **top-level** ``volumes:`` section (this should **not** be nested under the ``services:`` section) near the bottom of the file and add the following:

.. code:: yaml

   volumes:
     dioptra-data:
       driver: local
       driver_opts:
         type: nfs
         o: "addr=10.0.0.10,auto,rw,bg,nfsvers=4,intr,actimeo=1800"
         device: ":/dioptra/data"

.. margin::

   .. note::

      The NFS share does not need to be mounted on the host machine in order for the worker containers to have access to an exported directory.

Next, verify that the exported directory ``/dioptra/data`` and all of its files are world-readable.
If they are not, access the NFS share and update the file access permissions.
For example, if the NFS share is also mounted on the host machine at ``/dioptra/data``, then you would run:

.. code:: sh

   find /dioptra/data -type d -print0 | xargs -0 chmod o=rx
   find /dioptra/data -type f -print0 | xargs -0 chmod o=r

Next, find the blocks for the worker containers in ``docker-compose.override.yml``.
The worker container blocks will have **tfcpu**, **tfgpu**, **pytorch-cpu**, or **pytorch-gpu** in their names.
Append the line ``- "dioptra-data:/dioptra/data:ro"`` to the ``volumes:`` subsection.
The ``:ro`` at the end will mount the NFS share as read-only within the worker container to prevent a job from accidentally modifying or deleting the data.

.. code:: yaml

   dioptra-deployment-tfcpu-01:
     volumes:
       - "dioptra-data:/dioptra/data:ro"

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

Integrating custom containers
#############################

In some instances, you may want to utilize custom containers in the Dioptra environment.
For this example, let's assume you have a container named ``custom-container`` that has a ``dev`` tag associated with it.
To add this container to the deployment, nest the following code block in the ``services:`` section before the **top-level** ``volumes:`` section of the to the ``docker-compose.override.yml`` file:

.. code:: yaml

     custom-container:
       image: custom-container:dev
       restart: always
       hostname: custom-container
       healthcheck:
         test:
           - CMD
           - /usr/local/bin/healthcheck.sh
         interval: 30s
         timeout: 60s
         retries: 5
         start_period: 80s
       environment:
         AWS_ACCESS_KEY_ID: ${WORKER_AWS_ACCESS_KEY_ID}
         AWS_SECRET_ACCESS_KEY: ${WORKER_AWS_SECRET_ACCESS_KEY}
         DIOPTRA_RESTAPI_DATABASE_URI: ${DIOPTRA_RESTAPI_DATABASE_URI}
       command:
         - --wait-for
         - dioptra-deployment-redis:6379
         - --wait-for
         - dioptra-deployment-minio:9001
         - --wait-for
         - dioptra-deployment-db:5432
         - --wait-for
         - dioptra-deployment-mlflow-tracking:5000
         - --wait-for
         - dioptra-deployment-restapi:5000
         - tensorflow_cpu
       env_file:
         - ./envs/ca-certificates.env
         - ./envs/dioptra-deployment-worker.env
         - ./envs/dioptra-deployment-worker-cpu.env
       networks:
         - dioptra
       volumes:
         - "worker-ca-certificates:/usr/local/share/ca-certificates:rw"
         - "worker-etc-ssl:/etc/ssl:rw"
         - "/local/path/to/data:/dioptra/data:ro"

.. _getting-started-running-dioptra-init-deployment:

Initializing the deployment
---------------------------

The ``init-deployment.sh`` script is the main tool for initializing the deployment and automates the following steps:

- Generates the random passwords used to secure access to Dioptra's services.
- Copies and bundles the extra CA certificates for the containers
- Copies the configuration files in ``config/`` folder and the server certificates and private keys into named volumes
- Sets the appropriate file and folder access permissions in the named volumes
- Creates the Minio S3 accounts and configures their access permissions
- Syncs the built-in task plugins from the Dioptra GitHub repository with the appropriate Minio S3 bucket
- Enables SSL/TLS in the Postgres service (if applicable)

This script should be executed if this is the first time you are starting the deployment **or** if you have changed at least one of the files in the ``config/`` or ``ssl/`` directory.
If you run ``./init-deployment.sh --help``, you will print the script's help message:

.. code:: text

   Utility that prepares the deployment initialization scripts.

   Usage: init-deployment.sh [--enable-nginx-ssl] [--enable-postgres-ssl]
                             [--branch <arg>]
                             [--worker-ssl-service [tfcpu|pytorchcpu]] [-h|--help]
           --enable-nginx-ssl: Enable the SSL-enabled configuration settings for nginx image
           --enable-postgres-ssl: Enable the SSL-enabled configuration settings for postgres
                                  image
           --branch: The Dioptra GitHub branch to use when syncing the built-in task plugins
                     and the frontend files (default: 'main')
           --python: Command for invoking the Python interpreter. Must be Python 3.11 or
                     greater, and the jinja2 package must be installed.
                     (default: 'python')
           --worker-ssl-service: Image to use when bootstrapping the SSL named volumes for
                                 the worker containers, must be 'tfcpu' or 'pytorchcpu'
                                 (default: 'tfcpu')
           -h, --help: Prints help

As a rule of thumb, use the ``--enable-nginx-ssl`` option if you copied a server certificate and private key into the ``ssl/nginx/`` folder and use the ``--enable-postgres-ssl`` option if you copied a server certificate and private key into the ``ssl/db/`` folder.
In addition, if you wish to sync the plugins from a different Dioptra GitHub branch, such as the main branch, use the ``--branch <arg>`` option.
Otherwise, you do not need to specify any of the other options when running the script.

As an example, if you copied a server certificate and private key into both the ``ssl/nginx/`` and ``ssl/db/`` folders, then you would run the following to initialize the deployment:

.. code:: sh

   # (If using a different branch, replace "main" with that branch's name)
   ./init-deployment.sh --branch main --enable-nginx-ssl --enable-postgres-ssl

You should see a series of log messages as the initialization scripts run.
If you do not see any error messages while the script runs, then initialization is complete and you are ready to start the deployment.

Please note that you need to specify the ``--enable-nginx-ssl`` and ``--enable-postgres-ssl`` options **each time** you run the ``init-deployment.sh`` script.
If you omit them on a subsequent run, then SSL/TLS will be disabled for the services.
To enable SSL/TLS again, simply re-run the script with the options included.

Starting the deployment
-----------------------

There are two options for starting the Dioptra deployment, using Docker Compose directly and using systemd.

Using Docker Compose
~~~~~~~~~~~~~~~~~~~~

Run the following in the generated folder to start the deployment using Docker Compose.

.. code:: sh

   docker compose up -d

Using systemd
~~~~~~~~~~~~~

.. note::

   This will only work if you are deploying Dioptra on a Linux distribution that uses systemd, such as Ubuntu, Fedora, or Red Hat Enterprise Linux.

Run the following to install the Dioptra systemd service generated by the template.

.. code:: sh

   sudo cp ./systemd/dioptra.service /etc/systemd/system

Next, use systemd to start the deployment.

.. code:: sh

   sudo systemctl start dioptra

Finally, enable the Dioptra systemd service so that the deployment will survive reboots.

.. code:: sh

   sudo systemctl enable dioptra

Managing the deployment
-----------------------

Run the following in the generated folder to check the status of the deployment.

.. code:: sh

   docker compose ps

Run the following in the generated folder to check the status of the application logs.

.. code:: sh

   docker compose logs -f

Use :kbd:`Ctrl + C` to stop following the logs.

Run the following in the generated folder to restart the deployment.

.. tab-set::

   .. tab-item:: Docker Compose

      .. code:: sh

         # Using Docker Compose v2
         docker compose restart

   .. tab-item:: systemd

      .. code:: sh

         systemctl restart dioptra

Run the following in the generated folder to stop the deployment.

.. tab-set::

   .. tab-item:: Docker Compose

      .. code:: sh

         docker compose down

   .. tab-item:: systemd

      .. code:: sh

         systemctl stop dioptra

Run the following to prevent the deployment from restarting on reboot (systemd only),

.. code:: sh

   systemctl disable dioptra
