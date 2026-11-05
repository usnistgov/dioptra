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

.. _explanation-plugin-parameter-types:

Plugin Parameter Types
======================

**Plugin parameter types** are primarily used to validate that the outputs of one plugin are compatible with the inputs of another. 
Plugin parameter types also ensure compatibility among plugins and artifacts, similar to how types are used 
in modern programming languages to check that a function's parameters are compatible with the received input.

When plugin function tasks are created, each parameter is assigned a parameter type 
from the list of registered types. Similarly, each output of the function is assigned a
parameter type. During validation of an entrypoint, these types are used to verify
compatibility between the inputs and outputs of different steps, including artifact loading
and usage.

.. _explanation-parameter-type-systems:

Entrypoint Types and Python Annotations
----------------------------------------

Dioptra uses three related descriptions of types. They serve different purposes:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Description
     - Where it is declared
     - What it controls
   * - Entrypoint parameter type
     - The ``parameterType`` of a standard entrypoint parameter
     - How a default or job-provided string value is converted before execution
   * - Plugin parameter type
     - A registered type assigned to a plugin task input or output
     - Static compatibility checks between declared types in a task graph
   * - Python type annotation
     - An argument or return annotation in the plugin's Python source
     - Information for developers and suggestions when Dioptra analyzes a plugin signature

Standard entrypoint parameters accept ``string``, ``float``, ``integer``,
``boolean``, ``list``, and ``mapping``. For example, an ``integer`` parameter
converts the string ``"5"`` to the Python integer ``5``. A ``list`` parameter
parses a JSON array, and a ``mapping`` parameter parses a JSON object.
Selecting ``list`` alone does not specify the types of its elements.

These names are not interchangeable with registered plugin parameter types.
An entrypoint parameter uses ``float``, while the corresponding builtin plugin
parameter type is ``number``. A plugin input that accepts a list of numbers can
use a registered type such as ``numbers`` with the structure
``{"list": "number"}``.

Python annotations can help populate plugin task metadata. For example:

.. code-block:: python

   from dioptra import pyplugs

   @pyplugs.register
   def scale(values: list[float], factor: float) -> list[float]:
       return [value * factor for value in values]

Signature analysis suggests ``number`` for ``factor`` and a name such as
``list_float`` for the list annotation. The suggested name does not define a
list structure: review the registered type and supply its structure if element
types matter. The plugin's input and output metadata are the declarations used
for graph validation.

Python does not enforce these annotations when calling a function. Likewise,
Dioptra's static graph checks compare declared types and types inferred from
configured values; they do not inspect the contents of every object produced
by a plugin. A simple registered type named
``nparray``, for example, does not validate an array's shape or dtype. The plugin
implementation must honor its declared input and output contracts and perform
any additional value checks its task requires.

See :ref:`explanation-entrypoints` for standard and artifact parameters, and
:ref:`how-to-create-parameter-types` for registering plugin parameter types.


.. _explanation-plugin-parameter-types-structures:

Parameter Type Structures
-------------------------

Parameter Types can have structures that allow for a more fine-grained
validation of plugin inputs and outputs within an endpoint.

Simple Types
~~~~~~~~~~~~

Simple types do not have a structure - they act as atomic
units for building structures, but can also be used as types themselves.

Some builtin types are provided:

   * ``null`` - represents a ``None`` type in python
   * ``string`` - represents a ``str`` type in python
   * ``any`` - allows any type to be passed
   * ``integer`` - represents an ``int`` type in python
   * ``number`` - represents a  ``float`` type in python
   * ``boolean`` - represents a ``bool`` type in python

Simple types can also represent declared classes. For example, it is possible
to represent a ``numpy`` array  as a type, and give it a name like ``nparray``
without a structure.


Lists
~~~~~

Dioptra type structures support defining a type as a list of a single type.

For example, the type of the parameter to this function:

.. code-block:: python
   
   def integer_processor(x: list[int]) -> list[int]:
      return x

can be represented as

.. code-block:: json
   
   { "list": "integer" }

and describes a list of integers. 


Tuples
~~~~~~

Dioptra type structures also support defining a type as a tuple of multiple types.
This is useful particularly for representing the output of a function that returns
multiple values.


For example, the type of the output of this function:

.. code-block:: python
   
   def zero_giver() -> tuple[int, float, str]:
      return 0, 0.0, "0"

can be represented as

.. code-block:: json
   
   { "tuple": ["integer", "number", "string"] }

and describes a tuple containing three elements: 
an integer, a floating point value, and a string.


Mappings
~~~~~~~~

Dioptra type structures also support defining a type as a mapping. This would
generally be used to represent dictionaries.

For example, the output of this function:

.. code-block:: python
   
   def accuracy(correct: int, total: int) -> dict[str, str | float]:
      return {
         "name": "accuracy",
         "value": float(correct)/float(total),
      }


can be represented as

.. code-block:: json

   { 
      "mapping": {
         "name": "string",
         "value": "number"
      }
   }

and describes a mapping with two fields, ``name``
and ``value``. It defines the ``name`` field as a string, and the ``value`` field
as a floating point.

Alternatively, the output of this function:

.. code-block:: python
   
   def counts(things: list[str]) -> dict[str, int]:
      return { thing:len(thing) for thing in things }


can be represented as

.. code-block:: json

   { 
      "mapping": [
         "string",
         "integer"
      ]
   }

and indicates that the mapping keys should always be strings and the values should always be integers.


Unions
~~~~~~

It is often useful to define the type of a parameter as one of a set of types. For these
cases, it is possible to use a union structure. 

The input to this function:

.. code-block:: python
   
   def stringify_or_zero(something: str | int | None) -> str:
      return str(something) if something is not None else "0"

can be represented as

.. code-block:: json

   { "union": ["string", "integer", "null"] }

and this definition represents a type that can be either a string, an integer, or ``None``
value.


Registered Type References
~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, Dioptra type structures support referencing other types, including both builtin and user defined types.
The validation process will expand the structures and granularly validate that a parameter's declared input type matches the declared argument type.

For example, the input to this function:

.. code-block:: python

   import numpy as np

   def sum(my_array: list[np.ndarray]) -> np.ndarray:
      return np.array(float(np.sum(my_array)))


can be represented as two separate types.

The first, ``nparray`` with no structure.

And the second, ``list_of_nparray`` with the following structure:

.. code-block:: json

   { "list" : "nparray" }


Note that as a simple type, ``nparray`` has no defined structure, and is just a placeholder
for the ``np.ndarray`` class.

Furthermore, it is not necessary that every type be used in an entrypoint - some types can 
exist just to hold a structure or be referenced by other types.

The input to this function:

.. code-block:: python
   
   def my_len(arrs: dict[str, list[np.ndarray]] | str) -> int:
      return len(arrs) if isinstance(arrs, str) else len(arrs["arr"])


can be represented with the following types:

* ``nparray`` with no structure.
* ``list_of_nparray`` with the structure:

.. code-block:: json

   { "list" : "nparray" }

* ``nparray_dict`` with the structure:

.. code-block:: json

   { "mapping" : ["string", "list_of_nparray"] }

* ``nparray_dict_or_string`` with the structure:

.. code-block:: json

   { "union" : ["nparray_dict", "string"] }


Note that the Python function uses a complex union type, ``dict[str, list[np.ndarray]] | str``. The example 
not only defines that complex type, but also explicitly defines the subtypes of it, including the 
``list_of_nparray`` (``list[np.ndarray]``) and ``nparray_dict`` (``dict[str, list[np.ndarray]]``) as their own types.
Defining these subtypes is optional, and the ``nparray_dict_or_string`` could be simply defined as follows:

.. code-block:: json

   { 
      "union" : [
         { 
            "mapping" : [
               "string", 
               { "list" : "nparray" }
            ]
         }, 
         "string"
      ]
   }


 
but by defining these subtypes as their own types, they can potentially be used to define other complex types
or for other plugin function task definitions. 

A potential use for a type structure a type like this might occur if one
task returns a ``string``, and another task returns a ``dict[str, list[np.ndarray]]``. By defining the
type as above, the validation process will allow the output of both tasks to be used as input
to a task using the above definition.

.. rst-class:: fancy-header header-seealso

See Also 
---------

* :ref:`how-to-create-parameter-types` - Learn how to create parameter types
* :ref:`Parameter Types Reference <reference-parameter-types>` - Parameter Types Reference page.
