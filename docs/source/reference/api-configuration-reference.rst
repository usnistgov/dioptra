.. _reference-api-configuration:

REST API Configuration Reference
================================

This reference lists the REST API's operating modes, environment variables, defaults and signing-key requirements.
It serves developers and deployment maintainers configuring the API.
Command syntax is documented in :ref:`reference-dioptra-api`.
Python construction and overrides are documented in :ref:`reference-api-application-factory`.

.. contents:: Contents
   :local:
   :depth: 2

Operating Modes
---------------

The API requires an explicit operating mode.
The ``dioptra-api dev`` and ``dioptra-api prod`` commands select their corresponding modes regardless of an inherited ``DIOPTRA_RESTAPI_ENV`` value.
Python callers can select the mode through an argument or that environment variable.
See :ref:`reference-api-mode-precedence`.

.. list-table:: Mode policies
   :header-rows: 1
   :widths: 30 35 35

   * - Property
     - ``dev``
     - ``prod``
   * - Packaged server
     - Flask development server.
     - Gunicorn.
   * - Platforms
     - POSIX and native Windows.
     - POSIX only.
   * - Debugging default
     - Enabled. May be disabled.
     - Disabled. Enabling it is rejected.
   * - Authentication
     - Enabled. May be disabled explicitly.
     - Enabled. Disabling it is rejected.
   * - CORS
     - Enabled for the configured origin.
     - The development CORS configuration is not applied.
   * - Session and remember cookies
     - The ``Secure`` attribute is optional for local HTTP development.
     - Both cookies require the ``Secure`` attribute. Disabling it is rejected.
   * - Packaged transport
     - Local HTTP is permitted.
     - Gunicorn must serve HTTPS using TLS 1.3.
   * - Signing key
     - An existing persistent key file is required.
     - An existing protected key file is required.

Debug flags and server selection do not infer a mode.
Missing, empty or unsupported modes fail configuration validation.

.. _reference-api-environment-settings:

Environment Variables
---------------------

The API reads these variables for each new configuration resolution.
An existing application retains its resolved settings.
Python callers can supply :ref:`typed overrides <reference-api-typed-overrides>` with higher priority.

Boolean values accept case-insensitive ``true``, ``false``, ``1`` and ``0``, ignoring surrounding whitespace.
Empty or other boolean values are invalid.
Integer settings accept whole numbers, such as ``1000``.
Decimal fractions (``1000.0``) and scientific notation (``1e3``) are rejected.

Mode and Key Selection
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Variable
     - Default
     - Accepted values
   * - ``DIOPTRA_RESTAPI_ENV``
     - None.
     - ``dev`` or ``prod``. Required when the caller does not select a mode.
   * - ``DIOPTRA_RESTAPI_SECRET_KEY_FILE``
     - ``~/.local/share/dioptra/restapi/secret-key``
     - A nonempty path to an existing key. See :ref:`reference-api-signing-key`.

Authentication and Cookies
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Variable
     - Default
     - Accepted values
   * - ``DIOPTRA_LOGIN_DISABLED``
     - ``false``
     - Boolean. ``true`` is rejected in production.
   * - ``DIOPTRA_SESSION_PROTECTION``
     - ``strong``
     - Case-insensitive ``basic``, ``strong`` or ``none``. ``none`` disables session protection.
   * - ``DIOPTRA_REMEMBER_COOKIE_DURATION``
     - ``1209600`` seconds.
     - Integer duration in seconds.
   * - ``DIOPTRA_REMEMBER_COOKIE_SECURE``
     - ``false`` in development, ``true`` in production.
     - Boolean. ``false`` is rejected in production.

The ``Secure`` attribute restricts cookies to HTTPS connections.
Production enforces ``SESSION_COOKIE_SECURE = True`` and ``REMEMBER_COOKIE_SECURE = True`` for session and remember cookies.
Python overrides that disable either setting are rejected.

.. _reference-api-transport-settings:

Production HTTPS Settings
~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: DIOPTRA_TLS_ALLOWED_AUTHORITIES

   Hostnames and IP addresses that clients use to reach the API.
   The API checks each request's ``Host`` header against this list.

   Production requires a nonempty JSON array, for example ``["localhost:8000", "dioptra.example.org"]``.

   * Include the port when it differs from 443. Omitting it is equivalent to specifying ``:443``.
   * Enclose IPv6 addresses in square brackets, for example ``[::1]:8000``.
   * Hostname comparisons ignore letter case.

   Requests with a malformed ``Host`` header or a value outside this list receive HTTP 400.

Generated deployments configure this list automatically.
When running the API directly, set it before starting :ref:`dioptra-api prod <reference-dioptra-api-prod>`.

Reverse Proxies
^^^^^^^^^^^^^^^

A reverse proxy must connect to the API over HTTPS, verify its server certificate, and send an allowed hostname and port in the ``Host`` header.
``Forwarded`` and ``X-Forwarded-*`` headers do not override the request's scheme, hostname, or port.
The generated nginx configuration handles these settings automatically.

See :ref:`dioptra-api prod <reference-dioptra-api-prod>` for TLS options and :ref:`ssl.toml key_exchange <reference-ssl-key-exchange>` for deployment key-exchange settings.

API Presentation and Pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Variable
     - Default
     - Accepted values
   * - ``DIOPTRA_CORS_ORIGIN``
     - ``http://localhost:5173``
     - Nonempty origin string used in development.
   * - ``DIOPTRA_SWAGGER_PATH``
     - ``/``
     - Flask-RESTX documentation-path string.
   * - ``DIOPTRA_BASE_URL``
     - Unset.
     - Nonempty URL scheme string, such as ``https``, passed as Flask-RESTX's ``url_scheme``.
   * - ``DIOPTRA_MAX_PAGE_SIZE``
     - ``1000``
     - Integer of at least ``10``.

Connections and Logging
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Variable
     - Default
     - Accepted values
   * - ``DIOPTRA_RESTAPI_DATABASE_URI``
     - Absolute SQLite URI for ``dioptra.db`` in the invocation directory.
     - Nonempty SQLAlchemy database URI used in both API modes.
   * - ``RQ_REDIS_URI``
     - ``redis://``
     - Nonempty Redis URI with the ``redis``, ``rediss`` or ``unix`` scheme.
   * - ``MLFLOW_TRACKING_URI``
     - MLflow's ``get_tracking_uri()`` result.
     - Nonempty SDK-supported URI passed to the API's MLflow client.
   * - ``DIOPTRA_RESTAPI_LOG_AS_JSON``
     - ``false``
     - Boolean.
   * - ``DIOPTRA_RESTAPI_LOG_LEVEL``
     - ``INFO``
     - Python logging level name normalized to uppercase.

.. _reference-api-signing-key:

Signing-Key Files
-----------------

API startup reads an existing key.
It never creates a key, repairs its permissions or selects a fallback file after a failure.
Use :ref:`dioptra-api init-key <reference-dioptra-api-init-key>` to provision it before startup.
Keep the file out of source control and avoid displaying its contents in output or logs.

Path and Content
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Property
     - Requirement
   * - Path resolution
     - Expand ``~`` and normalize relative paths against the invocation directory without following symbolic links. Embedded environment-variable expressions are not expanded.
   * - File contents
     - Exactly 64 lowercase ASCII hexadecimal characters, optionally followed by one LF.
   * - Key generation
     - The hexadecimal text represents 32 cryptographically random bytes. Format validation does not establish the entropy of supplied material.
   * - Flask value
     - The 64-character text, without the optional LF, is used as ``SECRET_KEY``.

Filesystem Requirements
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Platform
     - Startup requirements
   * - POSIX
     - The effective API account owns the immediate parent with mode ``0700`` and the regular, single-link file with mode ``0400`` or ``0600``. Symlinks in the file or parent path are rejected. Protected read-only files and volume mounts are supported.
   * - Native Windows development
     - The same content format and detectable link/file-type checks apply. POSIX ownership, permissions and no-follow descriptor enforcement are unavailable. Owner-only Windows ACLs are not established.
   * - Native Windows production
     - Unsupported.

Missing, unreadable, malformed or unsafe key files stop startup.
The initializer's permission repairs and interrupted-initialization behavior are documented in :ref:`reference-dioptra-api-init-key`.

Retired Environment Variables
-----------------------------

The presence of either variable below causes an error, even when its replacement or a Python override is supplied.
Diagnostics identify setting names without printing credential values.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Retired variable
     - Replacement
   * - ``DIOPTRA_DEPLOY_SECRET_KEY``
     - Provision a key file and select its path with ``DIOPTRA_RESTAPI_SECRET_KEY_FILE``.
   * - ``DIOPTRA_RESTAPI_DEV_DATABASE_URI``
     - ``DIOPTRA_RESTAPI_DATABASE_URI`` in every operating mode.
