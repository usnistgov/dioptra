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

.. _reference-ssl-toml:

ssl.toml Configuration Reference
================================

``config/ssl.toml`` configures server certificates and TLS connections for a Dioptra deployment.
For setup instructions, see :ref:`how-to-enabling-ssl-tls`.
For certificate requirements, see :ref:`reference-certificate-policy`.

Location and Path Rules
-----------------------

The file is located at ``config/ssl.toml`` within the deployment directory.
Paths in this file are relative to the deployment directory.

Unknown fields, invalid values, and unsupported configuration versions are rejected.

Top-Level Fields
----------------

.. _reference-ssl-schema-version:

schema_version
~~~~~~~~~~~~~~

:Type: Integer.
:Required value: ``1``.

Identifies the configuration format.
Other versions are rejected.

[public] Section
----------------

.. _reference-ssl-public-host:

host
~~~~

:Type: String.
:Required: Yes.

The DNS name or IP address that browsers and external clients use to reach the deployment.
The nginx server certificate must cover this name or address.
The deployment template sets this field from ``nginx_server_name``, which defaults to ``localhost``.

Use the following guidelines when choosing a value:

* Specify a hostname or IP address without a URL scheme, port, path, or wildcard.
* Use ``localhost`` for access from the deployment machine.
* If you use a hostname, it must resolve to the deployment's address.

Ports and bind addresses are configured in Compose.
Changing the hostname requires a certificate covering the new name; changing only the port does not.

For example, a deployment accessed at ``https://dioptra.example.org`` uses:

.. code:: toml

   [public]
   host = "dioptra.example.org"

[transport] Section
-------------------

.. _reference-ssl-key-exchange:

key_exchange
~~~~~~~~~~~~

:Type: String.
:Default: ``"default"``.

Controls the key-exchange method used for TLS connections.
Both modes require TLS 1.3.
The accepted values are:

``"default"``
   Lets the client and server negotiate the key-exchange method normally.
``"hybrid-required"``
   Requires ``X25519MLKEM768``.
   Connections fail if either side cannot support it.

**Compatibility**

The Python 3.11 images support ``"default"``.
The ``"hybrid-required"`` mode has these additional requirements:

* The Python API and Python clients require Python 3.15 or newer linked to OpenSSL with ``X25519MLKEM768`` support.
* nginx and its clients or upstream servers must also support and enforce this group.

.. seealso::

   For certificate algorithms and expiration requirements, see :ref:`reference-certificate-policy`.

[restapi] and [nginx] Sections
------------------------------

The ``[restapi]`` and ``[nginx]`` sections configure certificates for the API and nginx independently.
Both sections accept the fields described below.

Certificate and private key files use these paths, relative to the deployment directory:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Section
     - Server certificate
     - Private key
   * - ``[restapi]``
     - ``ssl/restapi/server.crt``
     - ``ssl/restapi/server.key``
   * - ``[nginx]``
     - ``ssl/nginx/server.crt``
     - ``ssl/nginx/server.key``

.. _reference-ssl-endpoint-source:

source
~~~~~~

:Type: String.
:Default: ``"generated"``.

Selects how the service's server certificate is obtained.
The accepted values are:

``"generated"``
   Dioptra creates missing server certificates during initialization and signs them with the deployment's CA.
``"supplied"``
   You provide the server certificate, any required intermediate certificates, and the associated private key.
   You also specify the root CA certificate in :ref:`trust_files <reference-ssl-endpoint-trust-files>`.

Changing this value after initialization requires :ref:`certificate replacement <how-to-replace-deployment-certificates>`.

.. _reference-ssl-endpoint-dns-sans:

dns_sans
~~~~~~~~

:Type: Array of DNS-name strings.
:Default: ``[]``.

Lists additional DNS names that the service's certificate must cover.
Dioptra includes these names in generated certificates and checks supplied certificates for them.

The following names are already required and do not need to be repeated in this array:

* For ``[restapi]``, the deployment's internal API hostname, ``<deployment-slug>-restapi``.
* For ``[nginx]``, the hostname in ``public.host``, when that value is a DNS name.

Adding names here does not configure DNS records or change the public hostname used to access Dioptra.

.. _reference-ssl-endpoint-ip-sans:

ip_sans
~~~~~~~

:Type: Array of IPv4 or IPv6 literal strings.
:Default: ``[]``.

Lists additional IPv4 or IPv6 addresses that the service's certificate must cover.
Dioptra includes these addresses in generated certificates and checks supplied certificates for them.

For ``[nginx]``, an IP address in ``public.host`` is already required and does not need to be repeated in this array.
Adding addresses here does not change the deployment's bind addresses or published ports, which are configured in Compose.

.. _reference-ssl-endpoint-trust-files:

trust_files
~~~~~~~~~~~

:Type: Array of path strings.
:Default: ``[]``.

Lists paths to public root CA certificates used to verify the service's server certificate.
These files must contain CA certificates, not server certificate bundles or private keys.

CA certificate files must be stored under ``ssl/ca-certificates/``, which Dioptra uses to distribute additional trusted CAs to its container services.
Each file must use PEM format and a ``.crt`` filename extension.
Specify paths relative to the deployment directory.

* When ``source = "supplied"``, specify the required root CA certificate files, even if the CA is already publicly trusted.
* When ``source = "generated"``, Dioptra selects its CA automatically. Conflicting entries are rejected.

For example, nginx can use a supplied certificate verified by ``ssl/ca-certificates/root-ca.crt``:

.. code:: toml

   [nginx]
   source = "supplied"
   trust_files = ["ssl/ca-certificates/root-ca.crt"]

Example
-------

This example uses Dioptra-generated certificates for both services, ``localhost`` as the public hostname, and the default TLS 1.3 key-exchange settings:

.. code:: toml

   schema_version = 1

   [public]
   host = "localhost"

   [transport]
   key_exchange = "default"

   [restapi]
   source = "generated"
   dns_sans = []
   ip_sans = []
   trust_files = []

   [nginx]
   source = "generated"
   dns_sans = []
   ip_sans = []
   trust_files = []

See :ref:`how-to-enabling-ssl-tls` to supply certificates for one or both endpoints.
