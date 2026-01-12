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

This reference describes the files and folders created by the Dioptra deployment cookiecutter template.
Understanding this structure will help you customize and troubleshoot your deployment.

.. seealso::

   :ref:`how-to-prepare-deployment` - Step-by-step guide for customizing your deployment.

.. note::

   The *dioptra-deployment* prefix used in file and service names throughout this document assumes the default value for the **deployment_name** template variable.
   If you set this variable to a different value, the prefixes will change accordingly.

Folder Tree
-----------

The following tree shows all files created by the template with annotations explaining their purpose.

.. code:: text

   .
   ├── config/
   │   ├── db/
   │   │   └── init-db.sh
   │   ├── minio/
   │   │   ├── builtin-plugins-readonly-policy.json
   │   │   ├── builtin-plugins-readwrite-policy.json
   │   │   ├── custom-plugins-readonly-policy.json
   │   │   ├── custom-plugins-readwrite-policy.json
   │   │   ├── dioptra-readonly-policy.json
   │   │   ├── mlflow-tracking-readwrite-policy.json
   │   │   ├── plugins-readonly-policy.json
   │   │   ├── workflow-downloadonly-policy.json
   │   │   └── workflow-uploadonly-policy.json
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
   │   │   ├── minio-accounts.env.j2
   │   │   └── postgres-passwd.env.j2
   │   ├── copy-extra-ca-certificates.m4
   │   ├── file-copy.m4
   │   ├── generate_password_templates.py
   │   ├── git-clone.m4
   │   ├── globbed-copy.m4
   │   ├── init-minio.sh
   │   ├── init-named-volumes.m4
   │   ├── init-scripts.sh
   │   ├── manage-postgres-ssl.m4
   │   └── set-permissions.m4
   ├── secrets/
   │   ├── dioptra-deployment-minio-accounts.env
   │   └── postgres-passwd.env
   ├── ssl/
   │   ├── ca-certificates/
   │   │   └── README.md
   │   ├── db/
   │   │   └── README.md
   │   └── nginx/
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

Contains configuration files that are copied into named volumes during deployment initialization.

config/db/
~~~~~~~~~~

**init-db.sh**
   PostgreSQL initialization script that creates the database accounts and databases used by Dioptra.

config/minio/
~~~~~~~~~~~~~

These JSON files define access policies for the Minio S3 storage service:

**builtin-plugins-readonly-policy.json**
   Configures a readonly role for the ``dioptra_builtins/`` folder in the plugins bucket.

**builtin-plugins-readwrite-policy.json**
   Configures a readwrite role for the ``dioptra_builtins/`` folder in the plugins bucket.

**custom-plugins-readonly-policy.json**
   Configures a readonly role for the ``dioptra_custom/`` folder in the plugins bucket.

**custom-plugins-readwrite-policy.json**
   Configures a readwrite role for the ``dioptra_custom/`` folder in the plugins bucket.

**dioptra-readonly-policy.json**
   Configures a readonly role for all folders and buckets created and used by Dioptra.

**mlflow-tracking-readwrite-policy.json**
   Configures a readwrite role for the ``artifacts/`` folder in the mlflow-tracking bucket.

**plugins-readonly-policy.json**
   Configures a readonly role for the ``dioptra_builtins/`` and ``dioptra_custom/`` folders in the plugins bucket.

**workflow-downloadonly-policy.json**
   Configures a download-only role for the workflow bucket.

**workflow-uploadonly-policy.json**
   Configures an upload-only role for the workflow bucket.

config/nginx/
~~~~~~~~~~~~~

NGINX reverse proxy configuration files:

**http_*.conf**
   Configure NGINX to serve each service over HTTP connections:

   - ``http_default.conf`` - Basic NGINX defaults for HTTP
   - ``http_proxy.conf`` - General reverse proxy settings, including request header modifications
   - ``http_restapi.conf`` - Dioptra REST API service
   - ``http_mlflow.conf`` - MLflow Tracking service
   - ``http_minio.conf`` - Minio S3 service
   - ``http_dbadmin.conf`` - pgadmin4 dashboard

**https_*.conf**
   Configure NGINX to serve each service over HTTPS connections (used when SSL/TLS is enabled):

   - ``https_default.conf`` - HTTPS defaults, including paths to server certificate and private key
   - ``https_proxy.conf`` - Reverse proxy settings for HTTPS
   - ``https_restapi.conf``, ``https_mlflow.conf``, ``https_minio.conf``, ``https_dbadmin.conf`` - HTTPS versions of each service

**stream_db.conf**
   Configures NGINX to proxy TCP requests to the PostgreSQL database. This is a simple passthrough; any SSL encryption must be enabled in the PostgreSQL service itself.

envs/ Directory
---------------

Contains environment variable files that configure each service. **These files are safe to commit to version control.**

**ca-certificates.env**
   Sets environment variables that applications use to find extra CA certificates.

**dioptra-deployment-db.env**
   Customizes the PostgreSQL database service.

**dioptra-deployment-dbadmin.env**
   Customizes the pgadmin4 dashboard.

**dioptra-deployment-mlflow-tracking.env**
   Customizes the MLflow Tracking service.

**dioptra-deployment-restapi.env**
   Customizes the Dioptra REST API service.

**dioptra-deployment-worker-cpu.env**
   Customizes CPU-based Dioptra workers.

**dioptra-deployment-worker.env**
   Customizes all Dioptra workers (both CPU and GPU).

scripts/ Directory
------------------

Contains initialization scripts used by ``init-deployment.sh``.

scripts/templates/
~~~~~~~~~~~~~~~~~~

Jinja2 templates used to generate configuration files:

**dioptra.service.j2**
   Template for generating the systemd service file.

**dot-env.j2**
   Template for generating the ``.env`` file containing environment variables and passwords.

**minio-accounts.env.j2**
   Template for generating Minio account credentials.

**postgres-passwd.env.j2**
   Template for generating PostgreSQL passwords.

scripts/ (root)
~~~~~~~~~~~~~~~

**generate_password_templates.py**
   Python script that generates random passwords to secure Dioptra's services.

**init-deployment.sh** (see Root Directory section)
   Main initialization script.

**init-minio.sh**
   Sets Minio policies defined in ``config/minio/``.

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

**dioptra-deployment-minio-accounts.env**
   Minio account credentials generated by the initialization script.

**postgres-passwd.env**
   PostgreSQL passwords generated by the initialization script.

ssl/ Directory
--------------

Contains SSL/TLS certificates and private keys.

ssl/ca-certificates/
~~~~~~~~~~~~~~~~~~~~

Place extra CA certificates here if your environment uses an internal certificate authority.
See :ref:`how-to-adding-certificates` for details.

ssl/db/
~~~~~~~

Place the PostgreSQL server certificate (``server.crt``) and private key (``server.key``) here to enable encrypted database connections.
See :ref:`how-to-enabling-ssl-tls` for details.

.. warning::

   The private key file (``server.key``) is sensitive. **DO NOT commit it to version control.**

ssl/nginx/
~~~~~~~~~~

Place the NGINX server certificate (``server.crt``) and private key (``server.key``) here to enable HTTPS.
See :ref:`how-to-enabling-ssl-tls` for details.

.. warning::

   The private key file (``server.key``) is sensitive. **DO NOT commit it to version control.**

systemd/ Directory
------------------

**dioptra.service**
   A systemd service file for managing the Dioptra deployment on Linux systems that use systemd (Ubuntu, Fedora, RHEL, etc.).

Root Directory
--------------

**.env**
   Contains secrets (passwords) mapped to environment variables. Generated by the initialization script.

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
