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

.. _user-guide-api-reference-restapi:

Testbed REST API Reference
==========================

.. include:: /_glossary_note.rst

This page documents the endpoints and available :term:`HTTP` methods for the Dioptra :term:`REST` :term:`API`.
In addition to using this page, it is highly recommended that Testbed users also use the Swagger documentation that the :term:`REST` :term:`API` service automatically generates at runtime, which presents all of this page's information in an interactive format.
To access the Swagger documentation, just navigate to the web URL for the Testbed :term:`REST` :term:`API` service (omit the ``/api/v1`` part at the end of the web address).


Authentication
--------------

User authentication operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/auth/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/auth/.*


Artifacts
---------

Artifact management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/artifacts/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/artifacts/.*


Entrypoints
-----------

Entrypoint management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/entrypoints/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/entrypoints/.*


Experiments
-----------

Experiment management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/experiments/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/experiments/.*


Groups
------

Group management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/groups/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/groups/.*


Jobs
----

Job management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/jobs/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/jobs/.*


Models
------

Model management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/models/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/models/.*


PluginParameterTypes
--------------------

PluginParameterType management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/pluginParameterType/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/pluginParameterTypes/.*


Plugins
-------

Plugins management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/plugins/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/plugins/.*


Queues
------

Queues management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/queues/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/queues/.*


Tags
----

Tag management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/tags/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/tags/.*


Users
-----

User management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/users/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/users/.*


Workflows
---------

Workflow execution operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/v1/workflows/`` namespace.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/v1/workflows/.*
