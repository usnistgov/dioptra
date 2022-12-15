.. contents::

====================================
 Declarative Experiment Description
====================================

This document describes the data structure used to represent an experiment.

Goals
=====

The goal of this declarative description is to describe a task graph in a DAG
topology.  The nodes of this graph correspond to simple Python functions,
where the outputs of some functions may be fed into others as inputs.  The
operation of the overall graph may be parameterized via a set of name-value
pairs.  This allows the invoker some control over what the graph of functions
does.

Structure and Format
====================

The structure described below is something which can be easily represented in
a file format like JSON or YAML, but one need not use either of those formats,
or any textual format at all.  The only requirement is that the structure be
obtained somehow.  It consists of a nesting of basic types, including lists,
dicts, ints, etc, in the structure prescribed below.  Nevertheless, to describe
the structure textually in this document, a familiar format is chosen: YAML.
Implementations may make different choices.

Structure Description
=====================

The top level of the data structure is a mapping with a few prescribed keys,
which provide the basic ingredients for the experiment: parameters, tasks,
and a graph which links task invocations together:

.. code:: YAML

    parameters:
        "<parameters here>"

    tasks:
        "<tasks here>"

    graph:
        "<graph here>"

The rest of the structural description describes what goes in each of those
three places.

Parameters
----------

The value of the top-level ``parameters`` key may take one of two forms: a
list or a mapping.  A list value must include the names of all parameters, and
provides no facility for giving them default values.  For example:

.. code:: YAML

    parameters:
        - param1
        - param2

Invokers must provide a value for each parameter.  A mapping allows the author
to give default values:

.. code:: YAML

    parameters:
        param1: 1
        param2: foo
        param3:

Defaults are optional: the ``param3`` parameter does not have a default value.
In YAML terms, the value of that key is null.  That results in an ambiguity:
what if you wanted the default to be null?  To resolve this, a special mapping
value is supported, which includes a ``default`` key.  It is a longer form
which allows resolution of this ambiguity:

.. code:: YAML

    parameters:
        param1:
            default: 1
        param2: foo
        param3:
            default:

This means the same thing for ``param1`` and ``param2``, but gives ``param3`` a
default value of null.  When using the mapping special form with ``default``,
the parameter is *always* defaulted.

Tasks
-----

This section describes task plugins, and gives them and their outputs short
names to make subsequent usage easier to write and understand.  The value of
the top-level ``tasks`` key is a mapping whose keys are the short names of the
task plugins, and whose values describe the task plugin.  For example:

.. code:: YAML

    tasks:
        plugin1:
            plugin: org.foo.bar.my_plugin
            outputs: value
        plugin2:
            plugin: com.bar.foo.another_plugin
            outputs: [name, age]
        plugin3:
            plugin: my.other.cool.plugin

Each plugin description supports up to two keys, ``plugin`` and ``outputs``.

Task Plugin
~~~~~~~~~~~

The ``plugin`` key is required, and describes a Python module plus a function
name, separated by dots.  This is mostly the same as what you would see in a
Python ``import`` statement, but with the addition of the function name.

.. note::

    Our implementation will accept plugin name with two components minimum.
    Giving fewer than two components will produce an error.

Task Outputs
~~~~~~~~~~~~

A task plugin may or may not produce any output.  If it does, and its output(s)
will be needed to feed other task(s), then the output(s) must be named, so that
they may be referred to.  The value of the ``outputs`` property may be either a
string or list of strings.  If a string is given, the output may be referred to
via that name.  If a list of strings is given, then the plugin's output must be
iterable (e.g. a like a list), and values from the iterable will be extracted
and stored under the given names.  If a list is given for ``outputs``, but the
plugin's output is not iterable, an error will occur.

If the lengths of the output names and plugin return value are not equal, then
the number of values which may be subsequently referred to is the shorter of
the two lengths.  If the number of output names is less than the length of the
output iterable, this allows authors to extract only the first N outputs from
the iterable; they need not name all outputs.  On the other hand, if there are
more names than outputs, then some names will not be defined (because there are
no values to assign to them), and subsequent attempts to refer to them will
produce an error.

The distinction between lists and non-lists for ``outputs`` means you need to
keep in mind what the task plugin will produce.  ``[foo]`` and ``foo`` mean
different things.  Don't use a list unless you want to extract values from an
iterable.

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
        - global

    tasks:
        plugin1:
            plugin: org.foo.bar.my_plugin
            outputs: value
        plugin2:
            plugin: com.bar.foo.another_plugin
            outputs: [name, age]

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
