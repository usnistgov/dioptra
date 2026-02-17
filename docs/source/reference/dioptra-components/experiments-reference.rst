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

.. _reference-experiments:

Experiments
=================


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-experiments-definition:

Experiment Definition
---------------------

An **Experiment** in Dioptra is a logical container that defines the scope of workflows that can be executed. The Experiment declares which Entrypoints can be used to execute workflows within this scope. Users create and submit Jobs within an Experiment using one of its declared Entrypoints, and the Experiment serves as the container for those Jobs.

.. _reference-experiments-attributes:

Experiment Attributes
---------------------

This section describes the attributes that define an Experiment.

.. _reference-experiments-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

- **Name**: (string) The display name for the Experiment. Must be unique within the owning Group.
- **Group**: (integer ID) The Group that owns this Experiment and controls access permissions.

.. _reference-experiments-optional-attributes:

Optional Attributes
~~~~~~~~~~~~~~~~~~~

- **Description**: (string, optional) A text description of the Experiment's purpose or scope. Defaults to empty.
- **Entrypoints**: (list of integer IDs, optional) A list of Entrypoint resources to associate with this Experiment. Jobs can only be created using Entrypoints that are associated with the Experiment.

.. _reference-experiments-system-managed-state:

System-Managed State
~~~~~~~~~~~~~~~~~~~~

The following attributes are automatically assigned by the system and cannot be set directly by the user.

- **ID**: Unique identifier assigned upon creation.
- **Created On**: Timestamp indicating when the Experiment was created.
- **Last Modified On**: Timestamp indicating when the Experiment was last modified.
- **Jobs**: List of Jobs that have been executed within this Experiment.

.. _reference-experiments-registration-interfaces:

Registration Interfaces
-----------------------

Experiments can be created programmatically via the Python Client or the REST API.
They can also be created through the web interface.

.. _reference-experiments-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Create an Experiment**

    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.create

.. _reference-experiments-rest-api:

Using REST API
~~~~~~~~~~~~~~

Experiments can be created directly via the HTTP API.

**Create Experiments**

See the :http:post:`POST /api/v1/experiments </api/v1/experiments/>` endpoint documentation for payload requirements.

.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Entrypoints Reference <reference-entrypoints>`
* :ref:`Plugins Reference <reference-plugins>`
