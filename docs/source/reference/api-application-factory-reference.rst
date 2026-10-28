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

.. _reference-api-application-factory:

REST API Application Factory Reference
======================================

This reference describes ``create_app`` and ``load_config`` for developers constructing REST API applications.
It covers their parameters, return values, validation, input precedence and supported overrides.
Shared environment defaults and key-file constraints are listed in :ref:`reference-api-configuration`; command usage is listed in :ref:`reference-dioptra-api`.

.. contents:: Contents
   :local:
   :depth: 2

create_app
----------

   .. autofunction:: dioptra.restapi.create_app

Input Forms
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Call form
     - Behavior
   * - ``settings=None``
     - Resolve configuration using ``env``, ``overrides`` and the current environment.
   * - Resolved ``settings`` with ``env=None`` and ``overrides=None``.
     - Validate that instance without ambient configuration resolution.
   * - Resolved ``settings`` with any non-``None`` ``env`` or ``overrides``.
     - Raise ``ValueError``. An empty overrides mapping also conflicts.

With supplied settings, a present ``DIOPTRA_RESTAPI_ENV`` is ignored and produces a warning.
Supplied settings are an alternative input form, not another precedence level.

.. _reference-api-mode-precedence:

Mode Precedence
~~~~~~~~~~~~~~~

When ``create_app`` resolves configuration (``settings=None``), it selects the mode from these sources, in descending priority.
The same rule applies to ``load_config``.

.. list-table::
   :header-rows: 1
   :widths: 15 40 45

   * - Priority
     - Source
     - When selected
   * - 1
     - ``env`` argument.
     - The argument is not ``None``.
   * - 2
     - ``DIOPTRA_RESTAPI_ENV``.
     - ``env`` is omitted or ``None``.

There is no default mode.
The selected value must be ``dev`` or ``prod``; missing, empty or unsupported values raise ``ValueError``.
An invalid explicit argument does not fall back to the environment variable.
For example, ``env=""`` fails even when ``DIOPTRA_RESTAPI_ENV=prod``.
Platform restrictions are listed in :ref:`reference-api-configuration`.

load_config
-----------

   .. autofunction:: dioptra.restapi.config.load_config

.. _reference-api-typed-overrides:

Typed Overrides
~~~~~~~~~~~~~~~

For each setting, resolution uses these sources in descending priority.

1. The typed value in ``overrides``.
2. Its named environment variable, when supported.
3. The packaged default.

An invalid selected value is rejected without falling back.
Override keys use the resolved attribute names below.
Environment defaults and value constraints are defined in :ref:`reference-api-environment-settings`.

.. list-table:: Overrides with environment inputs
   :header-rows: 1
   :widths: 45 55

   * - Attribute
     - Environment variable
   * - ``SECRET_KEY_FILE``
     - ``DIOPTRA_RESTAPI_SECRET_KEY_FILE``
   * - ``LOGIN_DISABLED``
     - ``DIOPTRA_LOGIN_DISABLED``
   * - ``SESSION_PROTECTION``
     - ``DIOPTRA_SESSION_PROTECTION``
   * - ``REMEMBER_COOKIE_DURATION``
     - ``DIOPTRA_REMEMBER_COOKIE_DURATION``
   * - ``REMEMBER_COOKIE_SECURE``
     - ``DIOPTRA_REMEMBER_COOKIE_SECURE``
   * - ``SQLALCHEMY_DATABASE_URI``
     - ``DIOPTRA_RESTAPI_DATABASE_URI``
   * - ``DIOPTRA_CORS_ORIGIN``, ``DIOPTRA_SWAGGER_PATH``, ``DIOPTRA_BASE_URL``, ``DIOPTRA_MAX_PAGE_SIZE``
     - Same name as the attribute.
   * - ``RQ_REDIS_URI``, ``MLFLOW_TRACKING_URI``
     - Same name as the attribute.
   * - ``DIOPTRA_RESTAPI_LOG_AS_JSON``, ``DIOPTRA_RESTAPI_LOG_LEVEL``
     - Same name as the attribute.

Override values use Python types rather than environment-string conversion.

* Boolean overrides require Python booleans.
* Integer overrides require integers and reject booleans.

.. list-table:: Additional Python value rules
   :header-rows: 1
   :widths: 40 60

   * - Attribute
     - Accepted values
   * - ``SECRET_KEY_FILE``
     - Nonempty string or ``pathlib.Path``; explicit ``None`` is invalid.
   * - ``SESSION_PROTECTION``
     - ``basic``, ``strong`` or Python ``None``. Strings are case-insensitive; ``"none"`` becomes ``None``.
   * - ``DIOPTRA_SWAGGER_PATH``
     - Documentation-path string, or Python ``False`` to disable API documentation.
   * - ``DIOPTRA_BASE_URL``
     - Nonempty scheme string, or Python ``None`` for the unset default.

.. list-table:: Python-only overrides
   :header-rows: 1
   :widths: 35 25 40

   * - Attribute
     - Default
     - Constraints
   * - ``DEBUG``
     - ``True`` in dev; ``False`` in prod.
     - Boolean; production rejects ``True``.
   * - ``TESTING``
     - ``False``
     - Boolean; does not select a mode or relax production/platform policy.
   * - ``REMEMBER_COOKIE_NAME``
     - ``dioptra_remember_token``
     - Nonempty string.
   * - ``SQLALCHEMY_TRACK_MODIFICATIONS``
     - ``False``
     - Boolean.
   * - ``USE_MOCK_EQUIVALENCY``
     - ``False``
     - Boolean; no current API consumer.

``CONFIG_NAME`` and ``SECRET_KEY`` cannot be overridden directly.
Mode selection sets ``CONFIG_NAME``; the protected file supplies ``SECRET_KEY``.
Other unsupported names are also rejected.
