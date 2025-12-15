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

.. _reference-entrypoints:

Entrypoints
=================

Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 


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

.. _task_outputs-label:

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

Artifact Input Parameters
-------------------------
Artifact input parameters are similar to :ref:`parameters-label`, but use artifacts from other
jobs as input values. The artifacts are deserialized and the output values from this
deserialization are made available similar to any result from a task. The value of the
top-level ``artifact_inputs`` key must be a mapping.  The keys 
of the mapping are the artifact input parameter names.  The artifact input parameter
names map to ouput values in an identical manner to what is described in
:ref:`task_outputs-label`. For example:

.. code:: YAML

    artifact_inputs:
        artifact1:
            result: Path
        foo: 
            - bar: integer
            - baz: string

Here, ``artifact1`` has a single output value using a custom type of ``Path`` and ``foo``
has two output values of ``bar`` which is an integer value and ``baz`` which is a string
value.

Additional rules include:

- All artifacts *must* have one or more outputs.


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

Artifact Outputs
----------------
Artifact outputs are declared and can use the result of any other artifact, parameter, or
task as input for serialization. All artifacts are serialized at the end of the job. The
value of the top-level ``artifact_outputs`` key must be a mapping.  The keys 
of the mapping are the names of the artifacts to be serialized and the values are the
declarative description for what should be the ``contents``, the ``name`` of the class
implementing ``ArtifactTaskInterface`` which should be used to serialize and
deserialize the artifact, and any optional ``args`` that should be passed to the
serialize method for the handler.

For example:

.. code:: YAML

    artifact_outputs:
        artifact1:
            contents: $task1.result2
            task:
                name: Result2Serializer
                args:
                    foo: arg1

Here, ``artifact1`` is the name of an artifact that has as its ``contents`` the value of
``result2`` from the output of ``task1``. The ``name`` of the ``ArtifactTaskInterface``
to use is a class called ``Result2Serializer`` and this particular implementation has a
single extra argument called ``foo`` and a value of ``arg1`` which has been provided in
this example.

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
