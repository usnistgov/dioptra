
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


.. _how_to_create_a_user:

How-To: Use Complex Plugin Parameter Types
=====================

Simple Types
------------

Dioptra supports structured plugin parameter types. Some builtin types are 
provided, such as ``null``, ``string``, ``any``, ``integer``, ``number``, and
``boolean``.

Simple types can also represent declared classes. For example, it is possible
to represent a ``numpy`` array  as a type, and give it a name like ``nparray``
without a structure. This  acts effectively as a placeholder for the class and
the validation checker will not attempt to expand the type further.


Lists
-----

Dioptra type structures support defining a type as a list of a single type.

For example, we can represent the type of the parameter to this function:

.. code-block:: python
   
   def integer_processor(x: list[int]) -> list[int]:
      return x

as

.. code-block:: yaml
   
   list: integer

A structure defined like this will represent a list of integers. 


Tuples
------

Dioptra type structures also support defining a type as a tuple of multiple types.
This is useful particularly for representing the output of a function which returns
multiple values.


For example, we can represent the type of the output of this function:

.. code-block:: python
   
   def zero_giver() -> tuple[int, float, str]:
      return 0, 0.0, "0"

as

.. code-block:: yaml
   
   tuple: [integer, number, string]

A structure defined like this will represent a tuple containing three elements, 
an integer, a floating point value, and a string.


Mappings
--------

Dioptra type structures also support defining a type as a mapping. This would
generally be used to represent dictionaries.

For example, we can represent the output of this function:

.. code-block:: python
   
   def accuracy(correct: int, total: int) -> dict[str, float]:
      return {
         "name": "accuracy",
         "value": float(correct)/float(total),
      }


as

.. code-block:: yaml
   
   mapping:
      name: string
      value: number

A type like this represents a mapping which specifically has two fields, ``name``
and ``value``, and defines the ``name`` field as a string, and the ``value`` field
as a floating point.

Alternatively, we can represent the output of this function:

.. code-block:: python
   
   def counts(things: list[str]) -> dict[str, int]:
      return { thing:len(thing) for thing in things }


as

.. code-block:: yaml

   mapping: [string, integer]

This mapping structure indicates that the keys of the mapping should always be strings,
and the values of the mapping should always be integers.


Unions
------

It is often useful to define the type of a parameter as one of a set of types. For these
cases, it is possible to use a union structure. 

We can represent the input to this function:

.. code-block:: python
   
   def stringify_or_zero(something: str | int | None) -> str:
      return str(something) if sometihng is not None else "0"

as

.. code-block:: yaml

   union: [string, integer, null]

A definition such as this represents a type that can be either a string, an integer, or ``None``
value.



Registered Type References
--------------------------

Finally, Dioptra type structures support referencing other types, both builtin and user defined,
and the validation checker will expand the structures to perform granular validation that the
declared input to a parameter matches the declared type of what's being passed in.

For example, we can represent the input to this function:

.. code-block:: python

   import numpy as np

   def sum(my_array: list[np.ndarray]) -> np.ndarray:
      return np.array(float(np.sum(my_array)))


as

.. code-block:: yaml

   nparray:
   list_of_nparray:
      list: [nparray]

Note that as a simple type, ``nparray`` has no defined structure, and is just a placeholder
for the ``np.ndarray`` class.

Furthermore, it is not necessary that every type be used in an entrypoint - some types can 
exist just to hold a structure and be referenced by other types.

The input to this function:

.. code-block:: python
   
   def my_len(arrs: dict[str, list[np.ndarray]] | str) -> str:
      return len(arrs) if isinstance(arr, str) else len(arrs["arr"])


can be represented as


.. code-block:: yaml

   nparray: 
   list_of_nparray:
      list: [nparray]
   nparray_dict:
      mapping: [str, list_of_nparray]
   nparray_dict_or_none:
      union: [nparray_dict, string]

In this example we represent ``dict[str, list[np.ndarray]] | str`` as a type, but also represent
``np.ndarray``, ``list[np.ndarray]`` and ``dict[str, list[np.ndarray]]`` as their own types.
It may be desirable to structure a type like this, for example, if one plugin task returns a ``string``,
and another task returns a ``dict[str, list[np.ndarray]]``. By defining the type as above, the 
validation checker will properly allow the output of both of those tasks to be used as input to this
plugin task.
