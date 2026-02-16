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

.. _reference-parameter-types:

Plugin Parameter Types
======================

.. contents:: Contents
   :local:
   :depth: 2

.. _reference-parameter-types-definition:

Plugin Parameter Type Definition
--------------------------------

A **Plugin Parameter Type** in Dioptra represents a type used for the validation of an entrypoint, ensuring
compatibility for plugin input, output, as well as artifact usage.


.. _reference-parameter-types-attributes:

Plugin Parameter Type Attributes
--------------------------------

This section describes the attributes that define a Plugin Parameter Type.


.. _reference-parameter-types-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

* **Name**: (string) The name of the type. 
* **Group**: (integer ID) The Group that owns this Plugin Parameter Type and controls access permissions.
* **Description**: (string) A description of the type.
* **Structure**: (string) A string representing the structure of the type as a JSON object.

.. _reference-queues-system-generated-attributes:

System-Generated Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following attributes are automatically assigned by the system and cannot be set directly by the user.

- **ID**: Unique identifier assigned upon creation.
- **Created On**: Timestamp indicating when the Experiment was created.
- **Last Modified On**: Timestamp indicating when the Experiment was last modified.




Built-in Types
~~~~~~~~~~~~~~

Some builtin types are provided:

   * ``null`` - represents a ``None`` type in python
   * ``string`` - represents a ``str`` type in python
   * ``any`` - allows any type to be passed
   * ``integer`` - represents an ``int`` type in python
   * ``number`` - represents a  ``float`` type in python
   * ``boolean`` - represents a ``bool`` type in python

.. _reference-parameter-types-type-structure-syntax:

Type Structure Syntax
~~~~~~~~~~~~~~~~~~~~~

Simple Types
++++++++++++

Simple types can be represented with the following empty structure:

.. code:: json

   {}

Lists
+++++

A type representing a list of other types ``type_x`` can be represented as follows:

.. code:: json

   { "list" : "type_x"}

Union
+++++

A type representing a union of other types ``type_x`` and ``type_y`` can be represented as follows:

.. code:: json

   { "union": ["type_x", "type_y"] }

Tuples
++++++

A type representing a tuple of other types ``type_x`` and ``type_y`` can be represented as follows:

.. code:: json

   { "tuple": ["type_x", "type_y"] }



Mapping
+++++++

A type representing a mapping from one type ``type_x`` to another ``type_y`` can be represented as follows:

.. code:: json

   { "mapping": ["type_x", "type_y"] }

Alternatively, instead of mapping one type to another, a mapping of strings (``key1`` and ``key2``) to various types (``type_x`` and ``type_y``) can be described as follows:

.. code:: json

   { 
      "mapping": {
         "key1": "type_x",
         "key2": "type_y"
      }
   }



.. _reference-parameter-types-registration-interfaces:

Registration Interfaces
-----------------------

Plugin Parameter Types can be created programmatically via the Python Client or the REST API.
They can also be :ref:`created through the web interface <how-to-create-parameter-types>` .


.. _reference-parameter-types-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Create a Plugin Parameter Type**

    .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.create


.. _reference-parameter-types-rest-api:

Using REST API
~~~~~~~~~~~~~~


Plugin Parameter Types can be created directly via the HTTP API.

**Create Plugin Parameter Types**

See the :http:post:`POST /api/v1/pluginParameterTypes </api/v1/pluginParameterTypes/>` endpoint documentation for payload requirements.



.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`How To Create Plugin Parameter Types <how-to-create-parameter-types>`
* :ref:`Plugin Parameter Types Explanation <explanation-plugin-parameter-types>`
