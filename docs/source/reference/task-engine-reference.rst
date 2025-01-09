====================================
 Declarative Experiment Description
====================================

This document describes the data structure used to represent an experiment.

.. contents::

Goals
=====

The goal of this declarative description is to describe a task graph in a
directed acyclic graph (DAG) topology.  The nodes of this graph correspond to
simple Python functions, where the outputs of some functions may be fed into
others as inputs.  The operation of the overall graph may be parameterized via
a set of name-value pairs.  This allows the invoker some control over what the
graph of functions does.

Structure and Format
====================

The structure described below is something which can be easily represented in
a file format like JSON or YAML, but one need not use either of those formats,
or any textual format at all.  The only requirement is that the structure be
obtained somehow.  It consists of a nesting of basic types, including lists,
dicts, ints, etc, in the structure prescribed below.  Nevertheless, to describe
the structure textually in this document, a familiar format is chosen: YAML.
Implementations may make different choices.

Notes on YAML
-------------

A full description of `YAML <https://yaml.org/>`_ is out of scope for this
document, but to help readers less familiar with the syntax, below are some
brief notes about how it works.

YAML can represent a data structure similar to JSON.  Whereas JSON's container
types include "array" and "object", in YAML these are called "sequence" and
"mapping".  YAML allows flexibility in how these types are serialized
(represented textually); these choices are called *styles*.  There are two
broad YAML styles, called *block style* and *flow style*.  The YAML snippets
given in this document will use either style, depending on what results in the
clearest presentation of the content.

Example YAML mapping, block style:

.. code:: YAML

    key1: value1
    key2: value2

Example YAML mapping, flow style:

.. code:: YAML

    {key1: value1, key2: value2}

Example YAML sequence, block style:

.. code:: YAML

    - value1
    - value2

Example YAML sequence, flow style:

.. code:: YAML

    [value1, value2]

Structure Description
=====================

The top level of the data structure is a mapping with a few prescribed keys,
which provide the basic ingredients for the experiment: types, parameters,
tasks, and a graph which links task invocations together:

.. code:: YAML

    types:
        "<type definitions here>"

    parameters:
        "<parameters here>"

    tasks:
        "<tasks here>"

    graph:
        "<graph here>"

The rest of the structural description describes what goes in each of those
four places.

Types
-----

This section is used to define a set of types.  Types describe the inputs and
outputs of task plugins, and global parameters.  They allow an additional kind
of validation of the experiment: that the inputs passed to task plugins are
compatible with their parameter types.

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

Parameters
----------

The value of the top-level ``parameters`` key must be a mapping.  The keys
of the mapping are the global parameter names.  They may map to any value,
where mapping values are treated specially.  If not a mapping, the value is
taken as the default value for the parameter.  If a mapping, it may have keys
"type" and/or "default".  The mapping form allows explicitly assigning a type
to the parameter.  If a type is not explicitly given, it will be inferred from
the default.  For example:

.. code:: YAML

    parameters:
        global_a:
        global_b: "foo"
        global_c:
            type: integer
            default: 5

Here, ``global_a`` has a null default value and null inferred type,
``global_b`` defaults to "foo" and is of string type, and ``global_c`` defaults
to 5 and is explicitly given the ``integer`` type.

Additional rules include:

- If both a default and type are given, they must be compatible.
- Each global parameter *must* have a type, therefore it must have either a
  default value (from which a type can be inferred), or an explicitly given
  type.

Tasks
-----

This section describes task plugins.  It gives them and their inputs and
outputs short names so they may be referred to, and to make subsequent usage
easier to write and understand.  Inputs and outputs are also assigned types, to
enable type-based validation of their invocations.

The value of the top-level ``tasks`` key is a mapping whose keys are the short
names of the task plugins, and whose values describe the task plugin.  Each
plugin description supports up to three keys: ``plugin``, ``inputs``, and
``outputs``.  The latter two keys are optional.

For example:

.. code:: YAML

    tasks:
        task_short_name1:
            plugin: org.example.plugin1
            inputs: "<input_definitions>"
            outputs: "<output_definitions>"
        task_short_name2:
            plugin: org.example.plugin2
            inputs: "<input_definitions>"
            outputs: "<output_definitions>"

Task Plugin
~~~~~~~~~~~

The ``plugin`` key is required, and describes a Python module plus a function
name, separated by dots.  This is mostly the same as what you would see in a
Python ``import`` statement, but with the addition of the function name.

.. note::

    Our implementation will accept plugin name with two components minimum.
    Giving fewer than two components will produce an error.

Task Inputs
~~~~~~~~~~~

A task plugin may or may not require any input.  If it requires input, that
input must be defined under the ``inputs`` key.  Every input must be given a
name and a type.  Inputs are defined in a list, which also gives them an
implicit ordering.  The ordering is important for positional invocations.

Each task plugin input may be defined in one of two ways: either a length 1
mapping which maps input name to type, or a longer form which allows giving
other information along with the name and type.

Short form input example:

.. code:: YAML

    tasks:
        my_task:
            plugin: org.example.plugin
            inputs:
                - input_name: type_name

Long form input example:

.. code:: YAML

    tasks:
        my_task:
            plugin: org.example.plugin
            inputs:
                - name: input_name
                  type: type_name
                  required: false

The long form is distinguished by the presence of the ``name`` key.  That means
if a task plugin input is named "name", the long form must be used.  The above
example also shows the ``required`` key.  Usage of this key is optional and
defaults to true, i.e. all defined task plugin inputs are required by default.
Long form must be used in order to define an input as optional.

Task Outputs
~~~~~~~~~~~~

A task plugin may or may not produce any output.  If it does, and its output(s)
will be needed to feed other task(s), then the output(s) must be defined.  They
require names so they may be referred to, and must also be assigned types so
that their usage can be validated against other types.  The value of the
``outputs`` property may be either a length 1 mapping or list of such.  Each
mapping maps an output name to a type.

If a list of mappings is given, then the plugin's output must be iterable (e.g.
like a list), and values from the iterable will be extracted and stored under
the given names.  If a list is given for ``outputs``, but the plugin's output
is not iterable, an error will occur.

If the lengths of the output names and plugin return value are not equal, then
the number of values which may be subsequently referred to is the shorter of
the two lengths.  If the number of defined outputs is less than the length of
the output iterable, this allows authors to extract only the first N outputs
from the iterable; they need not define all outputs.  On the other hand, if
there are more output definitions than outputs, then some output names will not
be defined (because there are no values to assign to them), and subsequent
attempts to refer to them will produce an error.

For example:

.. code:: YAML

    tasks:
        my_task:
            plugin: org.example.plugin
            outputs:
                result: number

Graph
-----

The ``graph`` section is where you describe invocations of the aforementioned
task plugins, and connect the outputs of some to the inputs of others, creating
the graph structure.

Graphs are composed of *steps*, and the value of the ``graph`` property is a
mapping from a step name to a description of the step.  Each step invokes a
task plugin, so the step description describes which plugin to invoke and how
to invoke it:

.. code:: YAML

    graph:
        step1:
            "step 1 description"
        step2:
            "step 2 description"

Steps
~~~~~

Each step invokes a task plugin, which is a Python function, and the way you
invoke Python functions depends on how they are written.  For example, they
may have positional-only or keyword-only arguments, or a combination of the
two.  A step description supports all of these styles.

.. important::
    It is recommended that of the invocation styles described below, the
    keyword style be used since the meaning of the argument values is clearer
    due to the naming of each argument.  It is also structurally simpler than
    the mixed style.

Positional Style Invocation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

A simple way to describe a positional style task plugin invocation is to map
the plugin short name to a list of positional arguments:

.. code:: YAML

    graph:
        step1:
            plugin1: [arg1, arg2]

The above will lookup "plugin1" in the tasks section to find the plugin,
and invoke it with positional parameters "arg1" and "arg2".  In order to enable
simple structures, one is permitted to use a simple non-map, non-list value as
well, and this will be interpreted the same as a length-one list.

Keyword Style Invocation
^^^^^^^^^^^^^^^^^^^^^^^^

Similarly to positional style, the keyword arg style maps a plugin short name
to a mapping of keyword arg names to values:

.. code:: YAML

    graph:
        step1:
            plugin1:
                keyword1: arg1
                keyword2: arg2

The above will lookup "plugin1" in the tasks section to find the plugin,
and invoke it with keyword arguments keyword1=arg1 and keyword2=arg2.

Mixed Style Invocation
^^^^^^^^^^^^^^^^^^^^^^

There is a longer form invocation description which supports both styles at the
same time, for a mixed style invocation.  It uses a mapping with prescribed
keys ``task``, ``args``, ``kwargs``:

.. code:: YAML

    graph:
        step1:
            task: plugin1
            args: [posarg1, posarg2]
            kwargs:
                keyword1: arg1
                keyword2: arg2

This is differentiated from the keyword arg style by the presence of the
``task`` key.  This will invoke plugin1 with positional args posarg1 and
posarg2, and keyword args keyword1=arg1 and keyword2=arg2.

Describing Argument Values
^^^^^^^^^^^^^^^^^^^^^^^^^^

In the invocation examples above, argument values were given as simple strings
to keep the presented data structures clear and free of clutter.  However, one
can use more than simple values as task plugin argument values.  It is possible
to use any kind of nested structure you like.  For example, a positional
argument could itself be a mapping, or the value of a keyword argument could be
a list:

.. code:: YAML

    graph:
        step1:
            plugin1:
                - prop1: value1
                  prop2: value2

The above example maps the plugin short name to a list, therefore this is a
positional invocation.  The list has one value in it, which is itself a
mapping: {prop1: value1, prop2: value2}.  The task plugin will be invoked
positionally, where its one positional argument will be a Python dict.

References
**********

An important aspect of describing an argument value is being able to refer to
another part of the experiment description.  This is how we make use of global
`parameters <Parameters_>`_, and refer to the outputs of other steps.

A reference is a string value which begins with a dollar sign.  To refer to a
global parameter, follow the dollar sign with the parameter name.  To refer to
the output of another step, follow the dollar sign with the step name, and if
necessary, the output name, separated from the step name by a dot.  For
example:

.. code:: YAML

    parameters:
        global: string

    tasks:
        plugin1:
            plugin: org.foo.bar.my_plugin
            inputs:
                - in: string
            outputs:
                value: number
        plugin2:
            plugin: com.bar.foo.another_plugin
            inputs:
                - in: number
            outputs:
                - name: string
                - age: integer

    graph:
        step1:
            plugin1: [$global]
        step2:
            plugin2: $step1.value

The above example demonstrates a reference to a parameter (``$global``), and
to an output of a step (``$step1.value``).  The value of ``global`` will be
passed in as a positional arg in step1, and the ``value`` output of step1 will
be passed in as a positional arg in step2.  Note that in step2, we take
advantage of the ability to treat a simple value the same as a length-one list.

If a step produces only one output, the output name may be omitted.  For
example, because step1 only produces one output, that output could have been
referred to more simply as ``$step1``.

If one wanted to use a string which starts with a dollar sign as an argument
value, the dollar sign may be escaped by doubling it, e.g. ``$$foo``.  This
need only be done when the dollar sign is the first character.  If it is in the
middle of the value, e.g. ``foo$bar``, the dollar sign should not be escaped.

References may occur anywhere in the description of an argument value.  The
whole structure is searched, and all references will be replaced with the
appropriate values before the task plugin is invoked.

Dependencies
^^^^^^^^^^^^

The references described above can imply dependencies among the steps.  If step
B requires as input the output of step A, then A must run first so that there
is an output to pass to B.  The task graph runner can work out for itself a
run order for the steps on that basis.

But sometimes there are order requirements which exist for other reasons.  A
task graph runner will not be able to infer these requirements by itself, so a
facility exists for describing them explicitly.  To express explicit
dependencies in a graph, add a ``dependencies`` key to a step description,
which maps to a list of step names.  For example:

.. code:: YAML

    graph:
        step1:
            plugin1: 1
        step2:
            plugin2: foo
            dependencies: [step1]

This will force step1 to run before step2.

Type Validation
===============

This section describes how types are used.  The larger goal of validation is to
ensure that the experiment definition is sensible and correct.  The goal of
type validation is to ensure that task plugins are always passed types of
values they know how to handle, i.e. is sensible with respect to data types.
This is not sufficient for correctness of course, but it helps.

All type validation is static, i.e. it is not based on any runtime
information about the task plugins.  Task plugin output values are not known.
It uses only the information given in the various definitions (tasks, types,
etc).

Type validation operates on types.  Where values are given, types must
therefore be inferred from them.  The resulting types are then subject to a
compatibility check to ensure each task plugin invocation makes sense.  Type
inference and compatibility checking are the basic foundation of type
validation.  These two operations are described in the following subsections.

Type Inference
--------------

Input values to a task plugin can come from a few different places: outputs of
other task plugins, global parameter values, and literal values given directly
in a task plugin invocation.  In all cases, the input values must be assigned
types, which are then compared to task plugin input requirements for
compatibility.  Types are statically obtained for invocation inputs as follows:

- Global parameter: explicitly declared type, if present.  If not present,
  a default value must be given, and a type is inferred from that.
- Task plugin output: the declared type of the output.
- Literal value: inferred from the value

Because task invocations support compositions of values and references, type
information may be obtained from multiple sources and combined into a single
argument type.

When types are given explicitly in task and global parameter definitions, a
type name is used which must refer to a type defined in the ``types`` section
of the experiment description.  That is a simple case.  Inferring a type from
a literal value is more complex, and is described in the next section.

Type Inference from Literals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Type inference from literals is based on Python types.  When experiment
description content comes from a file (e.g. YAML or JSON), there is a second
translation that can happen from the file format to Python.  In that case, it
is a two-step process: file -> Python value -> Type.  The first step is beyond
the scope of this document, but we will include YAML-specific caveats.  We will
focus only on the second step.

Before we can perform type inference, we need a fixed stable of simple types
which we will use as the targets of our inferences.  These are built into the
system and can't be overridden.

.. _builtin_types:

The following shows the simple types which are pre-defined in Dioptra, and
their corresponding Python types:

=========  ===========  ===========
Type Name  Python Type  Description
=========  ===========  ===========
string     str          text
integer    int          integers, subtype of number
number     float        floating point numbers
boolean    bool         true or false
null       None (type)  the null value
any        (fallback)   any value
=========  ===========  ===========

These types may be referred to using the above names (from column 1) without
defining the types first.  The ``any`` type is a special type which is used as
the inference result if nothing more specific could be inferred.

.. important::

    In YAML, ``null`` is interpreted as the null value.  Therefore, it *does
    not name the null type!*  To refer to the null type, use double quotes so
    that the YAML parser knows a string value is intended: ``"null"``.

In addition, types can be inferred from common Python data structures which are
comprised of values of the above types.  This results in anonymous structured
types as follows:

=================  ===========  =====================
Type               Python Type  Description
=================  ===========  =====================
anonymous mapping  Mapping      A mapping
anonymous tuple    Iterable     An iterable of values
=================  ===========  =====================

A tuple is inferred for iterables which are not one of the other listed
iterable types (e.g. strings and dicts).  This enables a sensible inference
result from Python lists and tuples.  List structured types are never inferred,
but tuples can be compatible with lists, so it is not a problem in practice.

The element types of the inferred type are inferred from the element types of
the mapping/iterable value.  Type inference will recurse throughout a complex
value, so it is possible to infer a complex type.  Mapping inference is more
complex and is described separately in the next section.

Inferring Mapping Types
^^^^^^^^^^^^^^^^^^^^^^^

In Python, mapping keys can be heterogenous and of any hashable type, and
anything can be a value.  Type inference tries to infer the most specific
mapping type it can, as follows:

#. A common base type is inferred from all key types.  If this type is
   ``string``, an enumerated mapping type is inferred.  The value type
   corresponding to each key type is inferred from the mapped value.
#. If the common base type of the keys is ``integer``, a key/value type mapping
   is inferred where the key type is integer.  The value type used is the union
   of all value types inferred from the mapping, or if all inferred value types
   were the same, then that type.
#. If the common base key type is neither string nor integer, ``any`` is
   inferred.
#. If the mapping is empty, an empty enumerated mapping type is inferred.

Type Compatibility
------------------

Type compatibility refers to whether a task plugin invocation argument of one
type may be legally passed as the value of a task parameter of a possibly
different type.  If A "is compatible with" B, then values of type A may be
passed to task parameters of type B.  This is not a symmetric concept: if A
is compatible with B, that does not mean that B is compatible with A.

There is a fixed set of compatibility rules, which hopefully agrees with
intuition.  To begin with:

- All types are compatible with ``any``
- ``any`` is incompatible with all structured types, and all simple types
  except ``any``
- All types are compatible with themselves
- A simple type is compatible with another simple type iff the first is the
  same as or a subtype of the second

The following subsections describe more complex compatibility criteria related
to structured and union types.

Union Compatibility
~~~~~~~~~~~~~~~~~~~

Compatibility rules related to union types are as follows:

- A union type is compatible with another type iff all member types of the
  union are compatible with the latter type
- A non-union type is compatible with a union type iff the non-union type is
  compatible with at least one member of the union
- The empty union is compatible with all types
- Only the empty union is compatible with the empty union

Structured Type Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compatibility rules related to structured types are as follows:

- Named structured types with different names are incompatible.  This is
  because the types could mean wildly different things, regardless of whether
  they are structurally compatible.  A structural inspection is only necessary
  if at least one of the types is anonymous.  (If the types are non-anonymous
  with equal names, the types are the same, so trivially compatible.)
- Lists are incompatible with tuples and mappings
- Tuples are incompatible with mappings
- Mappings are incompatible with tuples and lists
- Key/value type mappings are incompatible with enumerated mappings
- A list is compatible with another list iff the element type of the first
  list is compatible with the element type of the second
- A tuple type is compatible with another tuple type iff the number of element
  types of each tuple is equal, and corresponding element types are compatible
- A tuple type is compatible with a list type iff all tuple element types are
  compatible with the list element type
- An enumerated mapping type is compatible with another enumerated mapping type
  iff they have exactly the same property names, and corresponding property
  types are compatible
- A key/value type mapping is compatible with another key/value type mapping
  iff key types are compatible and value types are compatible
- An enumerated mapping type is compatible with a key/value type mapping iff
  the key type of the latter mapping is ``string``, and all value types of the
  former mapping are compatible with the value type of the latter mapping
- The empty enumerated mapping type is compatible with all string-keyed
  key/value type mappings.

Type Variance
-------------

"Type variance" refers to whether and how types are allowed to differ in
various contexts (typically related to programming languages).  An experiment
is analogous to a program in that functions are called, which are passed values
as arguments, and return values.  The relevant context for these experiments
is the task plugin invocations, and how task plugin invocation argument types
are allowed to differ from the parameter types.

An important question which comes up is usually expressed in terms of container
types: if type B is a subtype of A, should we allow a value of type list<B>
(i.e. "list of B") to be passed to a parameter of type list<A>?  This is not
always allowed in programming languages due to type safety: the callee, using
the list according to the list<A> type, could put instances of A or instances
of other subtypes of A (which are not B) into the list.  If the caller expects
their list to still be a list<B> after the call returns, there could be trouble
down the road.

In other words, there is the potential for the callee to side-effect its input
in ways which are unsafe.  If a task plugin changes an input and that input was
to be passed to multiple other task plugins, the other task plugins which are
subsequently passed that input will see the change.  One might in fact expect
that *any* change to an input would be unexpected to an experiment designer
using your plugin, who assumes that a plugin output would be passed undisturbed
to all downstream plugins.

We have adopted the assumption that task plugins will never side-effect their
inputs.  Therefore the covariant compatibility decision is safe under that
assumption.  It is not possible to enforce immutability of task inputs, since
task plugins are ordinary Python functions using ordinary Python types.  But we
encourage task plugin authors to treat their inputs immutably.  Instead of
changing an input, make a changed copy of the input and return that from the
plugin.
