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

.. _reference-dioptra-api:

dioptra-api Command Reference
=============================

This reference describes the ``dioptra-api`` command supplied by the ``dioptra-platform`` Python package for developers running the REST API directly.
It covers subcommands, options, environment precedence, platform support and exit behavior.
Shared settings and key-file requirements are listed in :ref:`reference-api-configuration`.

.. contents:: Contents
   :local:
   :depth: 1

Syntax
------

.. code:: text

   dioptra-api [--help] COMMAND [OPTIONS]

Square brackets indicate optional arguments.
Replace ``COMMAND`` with a subcommand from the following table.

Command Summary
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 50 30

   * - Command
     - Purpose
     - Platforms
   * - :ref:`init-key <reference-dioptra-api-init-key>`
     - Create a persistent signing key or preserve an existing valid key.
     - POSIX, and native Windows with ``--development``.
   * - :ref:`dev <reference-dioptra-api-dev>`
     - Run development policy with Flask's development server.
     - POSIX and native Windows.
   * - :ref:`prod <reference-dioptra-api-prod>`
     - Run production policy with Gunicorn.
     - POSIX only.

``--help`` lists the group or subcommand's own options and exits with status zero.
The launch commands also accept the native server options described below.

.. _reference-dioptra-api-init-key:

init-key
--------

``init-key`` creates a cryptographically random persistent key without selecting an API mode, constructing Flask or connecting to backing services.
It preserves existing valid contents and ownership on reruns and never rotates or overwrites a key.

Syntax
~~~~~~

.. code:: text

   dioptra-api init-key [--development] [--key-file PATH] [--help]

Options
~~~~~~~

.. program:: dioptra-api init-key

.. option:: --key-file <path>

   Select the persistent signing-key path.
   If omitted, use the environment or per-user path under `Key-Path Precedence`_.

.. option:: --development

   Permit native Windows initialization with the reduced filesystem guarantees in :ref:`reference-api-signing-key`.
   Disabled by default. POSIX checks remain unchanged.

.. option:: --help

   Display command help and exit.

Examples
~~~~~~~~

.. code:: sh

   dioptra-api init-key --key-file ~/.local/share/dioptra/restapi/secret-key

Native Windows requires ``dioptra-api init-key --development``.

Output and Exit Status
~~~~~~~~~~~~~~~~~~~~~~

Creation or valid preservation returns zero and reports the key path.
Invalid content, unsafe paths, unsupported platform use and initialization failures return nonzero.

Initialization and Reruns
~~~~~~~~~~~~~~~~~~~~~~~~~

On POSIX, initialization creates or repairs the API-owned immediate parent to ``0700`` and the key file to ``0600``.
A custom path authorizes restricting its immediate parent.
Other API data may share that directory.
Missing higher ancestors are created under the process umask, while existing higher ancestors retain their permissions.
Permission repairs report the path and old/new modes without displaying key material.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Condition
     - Result
   * - No key exists.
     - Create and publish a complete key without replacing an existing file.
   * - An existing key is valid.
     - Preserve its contents and ownership. Repair POSIX permissions when needed.
   * - Existing contents are invalid.
     - Return an error and preserve the contents. POSIX permission repairs may already have occurred.
   * - Another initializer has completed creation.
     - Validate and preserve its key without automatic retries.
   * - Initialization is interrupted or finalization fails.
     - Protected temporary files or staging links may remain. A complete published key is preserved, even when the command reports failure.

Inspect any reported temporary files or staging links before rerunning initialization.
An observed extra link causes an error with rerun guidance.
Do not replace the final key to resolve it.

.. _reference-dioptra-api-dev:

dev
---

``dev`` selects development policy and runs Flask with the resolved Dioptra application.
It selects ``dev`` even when ``DIOPTRA_RESTAPI_ENV=prod`` is inherited.
The selected key must already exist.

Syntax
~~~~~~

.. code:: text

   dioptra-api dev [--key-file PATH] [--debug | --no-debug] [FLASK_RUN_OPTIONS]

Options
~~~~~~~

.. program:: dioptra-api dev

.. option:: --key-file <path>

   Select an existing signing key.
   If omitted, use the environment or per-user path under `Key-Path Precedence`_.

.. option:: --debug, --no-debug

   Enable or disable debug mode.
   If omitted, use ``FLASK_DEBUG``, then the enabled development default.
   See the precedence rule below.

.. option:: FLASK_RUN_OPTIONS

   Native Flask host, port, reload, debugger, threading and TLS options.
   Unspecified values retain Flask's defaults.

.. option:: --help

   Display the Dioptra subcommand's own help and exit.

Examples
~~~~~~~~

.. code:: sh

   dioptra-api dev --host 127.0.0.1 --port 5000 --no-reload

Output and Exit Status
~~~~~~~~~~~~~~~~~~~~~~

Configuration or key validation errors return nonzero before server dispatch.
After dispatch, Flask controls server operation and exit behavior.

Debug Precedence
~~~~~~~~~~~~~~~~

Debug mode uses these sources, in descending priority.

1. Explicit ``--debug`` or ``--no-debug``.
2. ``FLASK_DEBUG``.
3. The development default, ``True``.

``FLASK_DEBUG`` accepts the :ref:`environment boolean vocabulary <reference-api-environment-settings>`.
An explicit flag overrides even an invalid inherited value.
Native reload and debugger options remain independent of debug-mode selection.

Server Options and Restrictions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The application is fixed to Dioptra's resolved factory.
Positional application arguments and ``--app`` replacements are rejected.
See Flask's `run command documentation <https://flask.palletsprojects.com/en/stable/cli/#run-the-development-server>`__ for native option behavior.

.. _reference-dioptra-api-prod:

prod
----

``prod`` selects production policy and runs Gunicorn with the resolved Dioptra application.
It selects ``prod`` regardless of an inherited ``DIOPTRA_RESTAPI_ENV`` value.
The selected signing key must already exist, and native Windows is unsupported.
Production requires a TLS server certificate and matching private key, plus a configured list of hostnames or IP addresses that the API accepts in requests.

Syntax
~~~~~~

.. code:: text

   dioptra-api prod [--key-file PATH] [GUNICORN_OPTIONS]

Options
~~~~~~~

The TLS certificate and private-key paths can also be set in a Gunicorn configuration file.

.. program:: dioptra-api prod

.. option:: --key-file <path>

   Select an existing API signing key, separate from the TLS private key.
   If omitted, use the environment or per-user path under `Key-Path Precedence`_.

.. option:: --certfile <path>

   Path to a PEM file containing the server certificate followed by any required intermediate certificates.

.. option:: --keyfile <path>

   Path to the matching TLS private key.
   This differs from ``--key-file``, which selects the API signing key.

.. option:: -c <path>, --config <path>

   Path to a Gunicorn configuration file.
   Gunicorn's normal configuration precedence applies.

.. option:: -b <address>, --bind <address>

   Address on which the API listens, such as ``127.0.0.1:8000``.
   If omitted, Gunicorn's configured value or default applies.
   Accepted request hostnames and IP addresses are configured separately through :ref:`DIOPTRA_TLS_ALLOWED_AUTHORITIES <reference-api-transport-settings>`.

.. option:: GUNICORN_OPTIONS

   Additional Gunicorn options, such as worker count and timeouts.
   Unspecified values use Gunicorn's configuration or defaults.

.. option:: --help

   Display the Dioptra subcommand's own help and exit.

Examples
~~~~~~~~

This example uses an existing certificate for ``localhost`` at ``pki/server/api.crt``, its private key at ``pki/server/api.key``, and an API signing key initialized with :ref:`dioptra-api init-key <reference-dioptra-api-init-key>`.

.. code:: sh

   export DIOPTRA_TLS_ALLOWED_AUTHORITIES='["localhost:8000"]'
   dioptra-api prod --certfile pki/server/api.crt --keyfile pki/server/api.key \
     --bind 127.0.0.1:8000 --workers 2

The API is available at ``https://localhost:8000``.

Output and Exit Status
~~~~~~~~~~~~~~~~~~~~~~

Configuration or key validation errors return nonzero before server dispatch.
After dispatch, Gunicorn controls server operation and exit behavior.

Server Options and Restrictions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Positional applications, configured WSGI replacements and Paste dispatch are rejected.
Gunicorn retains its native signal handling.
Ordinary worker forks share the resolved configuration.
Preload is an explicit native option.
Relative signing-key paths and the default SQLite path are resolved before Gunicorn changes directory.
Native re-execution repeats launcher resolution from the original invocation directory.
See the `Gunicorn settings reference <https://docs.gunicorn.org/en/stable/settings.html>`__ for native options.

Production HTTPS Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Production requires TLS 1.3 and a readable server certificate and matching private key.
The command checks these requirements after loading Gunicorn's configuration and stops before accepting connections if they are not met.

Set ``DIOPTRA_TLS_ALLOWED_AUTHORITIES`` to a JSON list of hostnames or IP addresses accepted in requests.
Include the port when it differs from 443, for example ``["localhost:8000"]``.
The server certificate must cover the hostname or IP address clients use.
See :ref:`REST API Configuration Reference <reference-api-transport-settings>` for request-host validation and reverse-proxy settings.

Certificate Inputs
~~~~~~~~~~~~~~~~~~

Provide a server certificate and matching private key before starting the API.
You can use certificates from your certificate provider or create your own with ``dioptra-ssl``.
See its :ref:`create-ca <reference-dioptra-ssl-create-ca>` and :ref:`issue <reference-dioptra-ssl-issue>` command examples.

Clients must trust the CA that issued the server certificate.
See :ref:`how-to-adding-certificates` for browser and Python-client instructions.
Keep the CA's private key separate from the API's server certificate and private key.

Key-Path Precedence
-------------------

All three commands select the key path from these sources, in descending priority.

1. ``--key-file PATH``.
2. ``DIOPTRA_RESTAPI_SECRET_KEY_FILE``.
3. ``~/.local/share/dioptra/restapi/secret-key``.

An empty or invalid selected path causes an error and stops key-path selection.
Relative paths use the invocation directory, and ``~`` is expanded.
See :ref:`reference-api-signing-key` for content and filesystem requirements.

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`reference-api-configuration` lists shared environment settings and key requirements.
* :ref:`reference-api-application-factory` describes Python application construction.
