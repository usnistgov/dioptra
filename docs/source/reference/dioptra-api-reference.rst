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

Command Summary
---------------

.. code:: text

   dioptra-api [--help] COMMAND [OPTIONS]

.. list-table::
   :header-rows: 1
   :widths: 20 50 30

   * - Command
     - Purpose
     - Platforms
   * - ``init-key``
     - Create a persistent signing key or preserve an existing valid key.
     - POSIX; native Windows with ``--development``.
   * - ``dev``
     - Run development policy with Flask's development server.
     - POSIX and native Windows.
   * - ``prod``
     - Run production policy with Gunicorn.
     - POSIX only.

``--help`` lists the group or subcommand's own options and exits with status zero.
The launch commands also accept the native server options described below.

Key-Path Precedence
-------------------

All three commands select the key path from these sources, in descending priority.

1. ``--key-file PATH``.
2. ``DIOPTRA_RESTAPI_SECRET_KEY_FILE``.
3. ``~/.local/share/dioptra/restapi/secret-key``.

An empty or invalid selected path causes an error; it does not fall back to another source.
Relative paths use the invocation directory, and ``~`` is expanded.
See :ref:`reference-api-signing-key` for content and filesystem requirements.

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

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Option
     - Default
     - Behavior
   * - ``--key-file PATH``
     - Environment or per-user path.
     - Select the persistent key path.
   * - ``--development``
     - Disabled.
     - Permit native Windows initialization with the reduced filesystem guarantees in :ref:`reference-api-signing-key`. POSIX checks remain unchanged.
   * - ``--help``
     - None.
     - Display command help and exit.

Initialization and Reruns
~~~~~~~~~~~~~~~~~~~~~~~~~

On POSIX, initialization creates or repairs the API-owned immediate parent to ``0700`` and the key file to ``0600``.
A custom path authorizes restricting its immediate parent; other API data may share that directory.
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
     - Preserve its contents and ownership; repair POSIX permissions when needed.
   * - Existing contents are invalid.
     - Return an error and preserve the contents. POSIX permission repairs may already have occurred.
   * - Another initializer has completed creation.
     - Validate and preserve its key without automatic retries.
   * - Initialization is interrupted or finalization fails.
     - Protected temporary files or staging links may remain. A complete published key is preserved, even when the command reports failure.

Inspect any reported temporary files or staging links before rerunning initialization.
An observed extra link causes an error with rerun guidance; do not replace the final key to resolve it.

Exit Behavior
~~~~~~~~~~~~~

Creation or valid preservation returns zero and reports the key path.
Invalid content, unsafe paths, unsupported platform use and initialization failures return nonzero.

Example
~~~~~~~

.. code:: sh

   dioptra-api init-key --key-file ~/.local/share/dioptra/restapi/secret-key

Native Windows requires ``dioptra-api init-key --development``.

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

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Option
     - Default
     - Behavior
   * - ``--key-file PATH``
     - Environment or per-user path.
     - Select an existing signing key.
   * - ``--debug / --no-debug``
     - ``FLASK_DEBUG``, then enabled.
     - Enable or disable debug mode; see the precedence rule below.
   * - ``FLASK_RUN_OPTIONS``
     - Flask defaults.
     - Forward native host, port, reload, debugger, threading and TLS options.
   * - ``--help``
     - None.
     - Display the Dioptra subcommand's own help and exit.

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

Exit Behavior
~~~~~~~~~~~~~

Configuration or key validation errors return nonzero before server dispatch.
After dispatch, Flask controls server operation and exit behavior.

Example
~~~~~~~

.. code:: sh

   dioptra-api dev --host 127.0.0.1 --port 5000 --no-reload

.. _reference-dioptra-api-prod:

prod
----

``prod`` selects production policy and runs Gunicorn with the resolved Dioptra application.
It selects ``prod`` regardless of an inherited ``DIOPTRA_RESTAPI_ENV`` value.
The selected key must already exist, and native Windows is unsupported.

Syntax
~~~~~~

.. code:: text

   dioptra-api prod [--key-file PATH] [GUNICORN_OPTIONS]

Options
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Option
     - Default
     - Behavior
   * - ``--key-file PATH``
     - Environment or per-user path.
     - Select an existing signing key.
   * - ``GUNICORN_OPTIONS``
     - Gunicorn defaults/configuration.
     - Forward native config-file, bind, worker, timeout and TLS options.
   * - ``--help``
     - None.
     - Display the Dioptra subcommand's own help and exit.

Server Options and Restrictions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Positional applications, configured WSGI replacements and Paste dispatch are rejected.
Gunicorn retains its native signal handling.
Ordinary worker forks share the resolved configuration; preload is an explicit native option.
Relative key paths and the default SQLite path are resolved before Gunicorn changes directory.
Native re-execution repeats launcher resolution from the original invocation directory.
See the `Gunicorn settings reference <https://docs.gunicorn.org/en/stable/settings.html>`__ for native options.

Exit Behavior
~~~~~~~~~~~~~

Configuration or key validation errors return nonzero before server dispatch.
After dispatch, Gunicorn controls server operation and exit behavior.

Example
~~~~~~~

.. code:: sh

   dioptra-api prod --bind 127.0.0.1:8000 --workers 2

See Also
--------

* :ref:`reference-api-configuration` lists shared environment settings and key requirements.
* :ref:`reference-api-application-factory` describes Python application construction.
