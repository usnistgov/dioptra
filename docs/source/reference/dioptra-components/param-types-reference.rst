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

.. _reference-dparameter-types:

Parameter Types
=================

Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 



Types
-----

This section is used to define a set of types.  Types describe the inputs and
outputs of task plugins, the outputs from artifact input parameter deserialization, and
global parameters.  They allow an additional kind of validation of the experiment: that
the inputs passed to task plugins are compatible with their parameter types.

The top-level structure of this section is a mapping from type name to type
definition:

.. code:: YAML

    types:
        type_name_a: type_definition_a
        type_name_b: type_definition_b

There are three kinds of types: *simple*, *structured*, and *union*.  These are
discussed in the following subsections.

There are a handful of `builtin <builtin_types_>`_ types as well, whose names
are reserved: authors must not try to redefine them.  These include ``string``,
``integer``, ``number``, ``boolean``, ``null``, and ``any``.

Simple Types
~~~~~~~~~~~~

A simple type is just a name.  The name can mean anything you want.  Simple
types are suitable when you want to express an opaque type, i.e. one where the
inner structure is unimportant with regards to type checking.  The actual
type used by the task plugin may be complex or simple, but the type system will
not know anything about it.  Simple types are the only types to support single
inheritance.  A simple type may be given a null definition, or a mapping with
an ``is_a`` key which maps to the name of its super-type:

.. code:: YAML

    types:
        my_simple_type:
        my_sub_type:
            is_a: my_simple_type

Structured Types
~~~~~~~~~~~~~~~~

Structured types support the definition of a few kinds of internal structure.
This type is necessary when more complex values with internal structure are
given, within task plugin invocations and as global parameter values.  The type
system needs to be able to evaluate the structure of these values for
compatibility with task plugin requirements.  So it is necessary to be able to
associate with a type, a description of its proper structure.  The three
supported structures are *list*, *tuple*, and *mapping*.

List Structured Types
^^^^^^^^^^^^^^^^^^^^^

A list is conceptually a sequence of values of homogenous type and arbitrary
length.  To define a list structure, one need only give an element type:

.. code:: YAML

        types:
            my_elt_type:
            my_list_type:
                list: my_elt_type

Tuple Structured Types
^^^^^^^^^^^^^^^^^^^^^^

A tuple is conceptually a sequence of values of heterogenous type and fixed
length, which may be zero.  To define a tuple structure, one needs to list all
the element types:

.. code:: YAML

    types:
        my_elt_type1:
        my_elt_type2:
        my_elt_type3:
        my_tuple_type:
            tuple: [my_elt_type1, my_elt_type2, my_elt_type3]

Mapping Structured Types
^^^^^^^^^^^^^^^^^^^^^^^^

A mapping conceptually associates keys with values.  Mapping types come in a
couple variants: *enumerated* and *key/value type*.

Enumerated Mapping Types
************************

In an enumerated mapping type, a fixed set of property names and types is
given, which may be empty.  All values of this type are mappings with exactly
that set of properties, i.e. all of the listed properties are required.  This
implies that keys must be strings, and value types may be heterogenous:

.. code:: YAML

    types:
        prop_type1:
        prop_type2:
        enum_mapping_type:
            mapping:
                prop_name1: prop_type1
                prop_name2: prop_type2

Key/Value-Type Mapping Types
****************************

In a key/value type mapping, a key type and value type are given.  Values of
this type must have keys and values of the given types, but the keys and values
themselves are unrestricted.  This type of mapping is appropriate when
requirements are more open:

.. code:: YAML

    types:
        my_value_type:
        my_mapping_type:
            mapping: [string, my_value_type]

There is a special requirement here that the key type must be either the
``string`` or ``integer`` `builtin type <builtin_types_>`_.

Union Types
~~~~~~~~~~~

A union type is a merger of other types.  To define a union type, one simply
lists the union member types:

.. code:: YAML

    types:
        my_type1:
        my_type2:
        my_union:
            union: [my_type1, my_type2]

Named and Anonymous Types
~~~~~~~~~~~~~~~~~~~~~~~~~

A name is optional, for most types.  If a type does not have a name, we
call it *anonymous*.  Anonymous types arise in two contexts: inline types and
type inference.  These are the subjects of following sections, but there are
some principles and consequences to bring up here.

- A name is a unique identifier for a type, within the scope of an
  experiment description.  A particular type name always refers to a unique
  type.  If two types have different names, they are different types.

- A simple type is *only* a name, therefore it cannot be anonymous.

- The only way to give a type a name is to map its name to its definition,
  directly under the top-level ``types`` key.  Therefore, a simple type
  definition cannot occur in any other place.

Inline Type Definitions
~~~~~~~~~~~~~~~~~~~~~~~

The various examples of type definitions given in previous sections were kept
simple, in that the elements of those types (where applicable) were references
to named types whose definitions were present at the top level.  This is the
only way to use a simple type, but it is not the only way to use the other
kinds of types.  Definitions of non-simple types may be nested inside other
non-simple type definitions.  This enables more convenient definition of
complex types.  An inline type which is nested within a complex type definition
has no means to assign the type a name; it is therefore always an anonymous
type.

The following example defines a list of lists:

.. code:: YAML

    types:
        elt_type:
        list_of_lists:
            list:
                list: elt_type

This is a nested mapping, string -> string -> list:

.. code:: YAML

    types:
        elt_type:
        nested_mapping:
            mapping:
                - string
                - mapping:
                    - string
                    - list: elt_type



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
   nparray_dict_or_str:
      union: [nparray_dict, string]

In this example we represent ``dict[str, list[np.ndarray]] | str`` as a type, but also represent
``np.ndarray``, ``list[np.ndarray]`` and ``dict[str, list[np.ndarray]]`` as their own types.
It may be desirable to structure a type like this, for example, if one plugin task returns a ``string``,
and another task returns a ``dict[str, list[np.ndarray]]``. By defining the type as above, the 
validation checker will properly allow the output of both of those tasks to be used as input to this
plugin task.
