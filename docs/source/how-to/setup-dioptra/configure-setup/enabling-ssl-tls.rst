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

.. _how-to-enabling-ssl-tls-in-nginx-and-postgres:

Enabling SSL/TLS in NGINX and Postgres
=====================

This how to guide explains how to enable SSL / TLS in NGINX / Postgres. 


Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 


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