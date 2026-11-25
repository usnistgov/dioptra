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

.. _reference-deployment-folder:

Deployment Folder Reference
===========================

This reference describes the files and folders created by the Dioptra deployment cookiecutter template and deployment initialization.
Understanding this structure will help you customize and troubleshoot your deployment.

.. seealso::

   :ref:`how-to-prepare-deployment` - Step-by-step guide for customizing your deployment.

.. note::

   The *dioptra-deployment* prefix used in file and service names throughout this document assumes the default value for the **deployment_name** template variable.
   If you set this variable to a different value, the prefixes will change accordingly.

Folder Tree
-----------

The following tree shows the deployment layout, including certificate files and private state created by initialization.

.. code:: text

   .
   ├── .ssl-private/
   │   ├── ca/
   │   │   ├── ca.crt
   │   │   └── ca.key
   │   ├── deployment-state.json
   │   └── operations/
   ├── config/
   │   ├── db/
   │   │   └── init-db.sh
   │   ├── rustfs/
   │   │   └── mlflow-tracking-readwrite-policy.json
   │   ├── ssl.toml
   │   └── nginx/
   │       ├── http_*.conf
   │       ├── https_*.conf
   │       └── stream_db.conf
   ├── envs/
   │   ├── ca-certificates.env
   │   ├── dioptra-deployment-db.env
   │   ├── dioptra-deployment-dbadmin.env
   │   ├── dioptra-deployment-mlflow-tracking.env
   │   ├── dioptra-deployment-restapi.env
   │   ├── dioptra-deployment-worker-cpu.env
   │   └── dioptra-deployment-worker.env
   ├── scripts/
   │   ├── templates/
   │   │   ├── dioptra.service.j2
   │   │   ├── dot-env.j2
   │   │   ├── rustfs-accounts.env.j2
   │   │   └── postgres-passwd.env.j2
   │   ├── copy-extra-ca-certificates.m4
   │   ├── file-copy.m4
   │   ├── generate_password_templates.py
   │   ├── git-clone.m4
   │   ├── globbed-copy.m4
   │   ├── init-rustfs.sh
   │   ├── init-named-volumes.m4
   │   ├── init-scripts.sh
   │   ├── manage_ssl.py
   │   ├── manage-postgres-ssl.m4
   │   └── set-permissions.m4
   ├── secrets/
   │   ├── dioptra-deployment-rustfs-accounts.env
   │   └── postgres-passwd.env
   ├── ssl/
   │   ├── ca-certificates/
   │   │   ├── dioptra-local-ca.crt
   │   │   └── README.md
   │   ├── db/
   │   │   └── README.md
   │   ├── restapi/
   │   │   ├── server.crt
   │   │   └── server.key
   │   └── nginx/
   │       ├── server.crt
   │       ├── server.key
   │       └── README.md
   ├── systemd/
   │   └── dioptra.service
   ├── .env
   ├── .gitignore
   ├── docker-compose.init.yml
   ├── docker-compose.override.yml.template
   ├── docker-compose.yml
   ├── init-deployment.sh
   └── README.md

config/ Directory
-----------------

Contains service and certificate configuration files.

config/ssl.toml
~~~~~~~~~~~~~~~

Configures the deployment hostname and certificates for the REST API and nginx, including whether Dioptra generates the certificates or uses certificates you supply.
See :ref:`reference-ssl-toml` for the available settings.

config/db/
~~~~~~~~~~

**init-db.sh**
   PostgreSQL initialization script that creates the database accounts and databases used by Dioptra.

config/rustfs/
~~~~~~~~~~~~~~

These JSON files define access policies for the RustFS S3 storage service:

**mlflow-tracking-readwrite-policy.json**
   Configures a readwrite role for the ``artifacts/`` folder in the mlflow-tracking bucket.

config/nginx/
~~~~~~~~~~~~~

NGINX reverse proxy configuration files:

**http_*.conf**
   Configure NGINX to serve each service over HTTP connections:

   - ``http_default.conf`` - Basic NGINX defaults for HTTP
   - ``http_proxy.conf`` - General reverse proxy settings, including request header modifications
   - ``http_restapi.conf`` - Dioptra REST API service
   - ``http_mlflow.conf`` - MLflow Tracking service
   - ``http_rustfs.conf`` - RustFS S3 service
   - ``http_dbadmin.conf`` - pgadmin4 dashboard

**https_*.conf**
   Configure NGINX to serve each service over HTTPS connections:

   - ``https_default.conf`` - HTTPS defaults, including paths to server certificate and private key
   - ``https_proxy.conf`` - Reverse proxy settings for HTTPS
   - ``https_restapi.conf``, ``https_mlflow.conf``, ``https_rustfs.conf``, ``https_dbadmin.conf`` - HTTPS versions of each service

**stream_db.conf**
   Configures NGINX to proxy TCP requests to the PostgreSQL database. This is a simple passthrough. Any SSL encryption must be enabled in the PostgreSQL service itself.

envs/ Directory
---------------

Contains environment variable files that configure each service. **These files are safe to commit to version control.**

**ca-certificates.env**
   Sets environment variables that applications use to find extra CA certificates.

   - ``AWS_CA_BUNDLE``
   - ``CURL_CA_BUNDLE``
   - ``NODE_EXTRA_CA_CERTS``
   - ``REQUESTS_CA_BUNDLE``
   - ``SSL_CERT_FILE``

**dioptra-deployment-db.env**
   Customizes the PostgreSQL database service.

   - ``POSTGRES_HOST_AUTH_METHOD``
   - ``POSTGRES_PASSWORD_FILE``

**dioptra-deployment-dbadmin.env**
   Customizes the pgadmin4 dashboard.

   - ``PGADMIN_DEFAULT_EMAIL``
   - ``PGADMIN_DISABLE_POSTFIX``
   - ``PGADMIN_LISTEN_PORT``

**dioptra-deployment-mlflow-tracking.env**
   Customizes the MLflow Tracking service.

   - ``MLFLOW_S3_ENDPOINT_URL``

**dioptra-deployment-restapi.env**
   Customizes the Dioptra REST API service.

   - ``DIOPTRA_RESTAPI_ENV``
   - ``DIOPTRA_RESTAPI_SECRET_KEY_FILE``
   - ``DIOPTRA_TLS_ALLOWED_AUTHORITIES``
   - ``MLFLOW_S3_ENDPOINT_URL``
   - ``MLFLOW_TRACKING_URI``
   - ``RQ_REDIS_URI``

**dioptra-deployment-worker-cpu.env**
   Sets Intel MKL/OpenMP threading optimizations for CPU-based Dioptra workers.

   - ``KMP_AFFINITY``
   - ``KMP_BLOCKTIME``
   - ``KMP_SETTINGS``
   - ``OMP_PROC_BIND``

**dioptra-deployment-worker.env**
   Customizes all Dioptra workers (both CPU and GPU).

   - ``MLFLOW_TRACKING_URI``
   - ``MLFLOW_S3_ENDPOINT_URL``
   - ``RQ_REDIS_URI``
   - ``DIOPTRA_API``

scripts/ Directory
------------------

Contains deployment initialization scripts and ``manage_ssl.py`` for certificate maintenance.

scripts/templates/
~~~~~~~~~~~~~~~~~~

Jinja2 templates used to generate configuration files:

**dioptra.service.j2**
   Template for generating the systemd service file.

**dot-env.j2**
   Template for generating the ``.env`` file containing environment variables and passwords.

**rustfs-accounts.env.j2**
   Template for generating RustFS account credentials.

**postgres-passwd.env.j2**
   Template for generating PostgreSQL passwords.

scripts/ (root)
~~~~~~~~~~~~~~~

**generate_password_templates.py**
   Python script that generates random passwords to secure Dioptra's services.

**init-deployment.sh** (see Root Directory section)
   Main initialization script.

**manage_ssl.py**
   Deployment certificate initialization, validation, replacement and recovery.
   See :ref:`reference-manage-ssl`.

**init-rustfs.sh**
   Sets RustFS policies defined in ``config/rustfs/``.

**init-scripts.sh**
   Translates ``.m4`` files into executable bash scripts using argbash.

**\*.m4 files**
   M4 macro files used during initialization:

   - ``copy-extra-ca-certificates.m4`` - Injects extra CA certificates
   - ``file-copy.m4`` - Handles file copying with logging and permissions
   - ``git-clone.m4`` - Handles git repository cloning
   - ``globbed-copy.m4`` - Handles globbed file copying
   - ``init-named-volumes.m4`` - Prepares named storage volumes
   - ``manage-postgres-ssl.m4`` - Enables/disables PostgreSQL SSL
   - ``set-permissions.m4`` - Sets file/folder access permissions

secrets/ Directory
------------------

.. warning::

   Files in this directory contain sensitive passwords. **DO NOT commit these files to version control or share them.**

**dioptra-deployment-rustfs-accounts.env**
   RustFS account credentials generated by the initialization script.

   - ``RUSTFS_ACCESS_KEY``
   - ``RUSTFS_SECRET_KEY``
   - ``RUSTFS_MLFLOW_TRACKING_USER``
   - ``RUSTFS_MLFLOW_TRACKING_PASSWORD``
   - ``RUSTFS_MLFLOW_TRACKING_POLICIES``
   - ``RUSTFS_RESTAPI_USER``
   - ``RUSTFS_RESTAPI_PASSWORD``
   - ``RUSTFS_RESTAPI_POLICIES``
   - ``RUSTFS_WORKER_USER``
   - ``RUSTFS_WORKER_PASSWORD``
   - ``RUSTFS_WORKER_POLICIES``

**postgres-passwd.env**
   PostgreSQL passwords generated by the initialization script.

   - ``POSTGRES_PASSWORD``
   - ``POSTGRES_USER``
   - ``POSTGRES_DB``

ssl/ Directory
--------------

Contains service certificates, private keys, and public CA certificates.
The generated CA's private key is stored separately under ``.ssl-private/``.

ssl/ca-certificates/
~~~~~~~~~~~~~~~~~~~~

Contains public root CA certificates trusted by Dioptra's services.
``dioptra-local-ca.crt`` is the public certificate for Dioptra's generated CA.
Additional certificates use PEM format and ``.crt`` filenames.
See :ref:`how-to-adding-certificates` for details.

ssl/db/
~~~~~~~

Place the PostgreSQL server certificate (``server.crt``) and private key (``server.key``) here to enable encrypted database connections.
See :ref:`how-to-enabling-ssl-tls` for details.

.. warning::

   The private key file (``server.key``) is sensitive. **DO NOT commit it to version control.**

ssl/restapi/ and ssl/nginx/
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each directory contains ``server.crt``, holding the server certificate followed by any required intermediate certificates, and ``server.key``, holding its matching private key.
Initialization creates these files for generated certificates or validates files you supply.
Directory modes are ``0700``, private keys ``0600`` and public certificates ``0644``.
See :ref:`how-to-enabling-ssl-tls` for initial setup and :ref:`how-to-replace-deployment-certificates` for replacing existing certificates.

.. warning::

   The private key file (``server.key``) is sensitive. **DO NOT commit it to version control.**

.ssl-private/ Directory
-----------------------

Contains the generated CA, certificate installation records, and files used for recovery.
These files are owned by the deployment user.
The directory and its subdirectories use mode ``0700``.
Private keys and installation and operation records use ``0600``.

**ca/ca.key and ca/ca.crt**
   The private key and public certificate for Dioptra's generated CA.
   The key is used to issue deployment certificates.

**deployment-state.json**
   Records the installed certificates and the status of certificate operations.
   Managed by ``manage_ssl.py``.

**operations/**
   Stores replacement certificates and keys, together with the previous files needed to resume or undo a certificate operation.
   See :ref:`how-to-recover-certificate-operation` before changing or removing these files.

.. _reference-deployment-certificate-backups:

Certificate Backups
-------------------

Retain a protected backup of the following files and directories:

* ``config/ssl.toml``
* ``.ssl-private/``
* ``ssl/restapi/``
* ``ssl/nginx/``
* The public CA certificate files used by the deployment under ``ssl/ca-certificates/``.

Backups containing private keys require the same restricted access as the live files.
Do not commit these backups to version control or share them with users configuring certificate trust.
The generated CA's private key is needed to issue new certificates using the same CA.

systemd/ Directory
------------------

**dioptra.service**
   A systemd service file for managing the Dioptra deployment on Linux systems that use systemd (Ubuntu, Fedora, RHEL, etc.).

Root Directory
--------------

**.env**
   Contains secrets (passwords) mapped to environment variables. Generated by the initialization script.
   These variables are referenced in ``docker-compose.yml`` using ``${VARIABLE}`` syntax.

   - ``DIOPTRA_RESTAPI_DATABASE_URI``
   - ``DIOPTRA_MLFLOW_TRACKING_DATABASE_URI``
   - ``DIOPTRA_WORKER_USERNAME``
   - ``DIOPTRA_WORKER_PASSWORD``
   - ``RUSTFS_ACCESS_KEY``
   - ``RUSTFS_SECRET_KEY``
   - ``RUSTFS_KMS_STATIC_SECRET_KEY``
   - ``MLFLOW_SERVER_ALLOWED_HOSTS``
   - ``MLFLOW_TRACKING_AWS_ACCESS_KEY_ID``
   - ``MLFLOW_TRACKING_AWS_SECRET_ACCESS_KEY``
   - ``PGADMIN_DEFAULT_PASSWORD``
   - ``POSTGRES_USER_DIOPTRA_PASSWORD``
   - ``RESTAPI_AWS_ACCESS_KEY_ID``
   - ``RESTAPI_AWS_SECRET_ACCESS_KEY``
   - ``WORKER_AWS_ACCESS_KEY_ID``
   - ``WORKER_AWS_SECRET_ACCESS_KEY``

   .. warning::

      **DO NOT commit this file to version control.**

**.gitignore**
   Configures files and directories that git should ignore if the deployment is placed under version control.

**docker-compose.init.yml**
   Docker Compose file used during the initialization process.

**docker-compose.override.yml.template**
   Template for creating custom Docker Compose overrides. Copy to ``docker-compose.override.yml`` and modify.
   See :ref:`how-to-data-mounts`, :ref:`how-to-gpu-enabled-workers`, and :ref:`how-to-integrating-custom-containers` for common customizations.

**docker-compose.yml**
   Main Docker Compose file that defines all Dioptra services.

**init-deployment.sh**
   Main deployment initialization script. See :ref:`reference-init-deployment-script` for command-line options and usage examples.

**README.md**
   Instructions for initializing and running Dioptra.
