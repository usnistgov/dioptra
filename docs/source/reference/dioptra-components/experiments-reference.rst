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

Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 


Structure Description
=====================

The top level of the data structure is a mapping with a few prescribed keys,
which provide the basic ingredients for the experiment: types, parameters, artifact
input parameters, tasks, a graph which links task invocations together, and the artifact
output declaration:

.. code:: YAML

    types:
        "<type definitions here>"

    parameters:
        "<parameters here>"

    artifact_inputs:
        "<artifact input parameters here>"

    tasks:
        "<tasks here>"

    graph:
        "<graph here>"

    artifact_outputs:
        "artifact output declaration here"


The rest of the structural description describes what goes in each of those six places.




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