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

Dioptra Overview
================

Dioptra is a software test platform for assessing the trustworthy characteristics of Artificial Intelligence (AI) models.

Dioptra is a modular, microservice-based environment for creating **reproducible, trackable, and reusable AI workflows**.
It is designed to **measure, analyze, and track AI risks**, making it particularly useful for addressing the "combinatorial explosion" of testing possibilities across attacks.

Dioptra Documentation
---------------------

Below are some useful guides to help get you started. To see the entire list of documentation topics, view the table of contents on the left sidebar.

.. rst-class:: header-on-a-card

Understand Dioptra
^^^^^^^^^^^^^^^^^^^

- :ref:`Motivation for Dioptra <explanation-why-use-dioptra>` - What is Dioptra for and how does it compare to other tools?
- :ref:`Workflow Architecture <explanation-workflow-architecture>` - Learn how all the high level Dioptra components orchestrate together to execute jobs

.. rst-class:: header-on-a-card

Use Dioptra
^^^^^^^^^^^

- :ref:`Follow the installation guide <explanation-install-dioptra>` to build the Docker containers and start the services
- :ref:`Run the Hello World tutorial <tutorial-hello-world-in-dioptra>` to make sure things are set up correctly

.. rst-class:: header-on-a-card

Dive Into the Details
^^^^^^^^^^^^^^^^^^^^^

- :ref:`Read through the Dioptra component explainers<explanation-dioptra-components>` to dive deeper on each part of the workflow architecture.
- Learn how to :ref:`customize your Dioptra deployment<how-to-setup-options>`
- Reference the :ref:`API endpoints <reference-testbed-rest-api-reference>` and learn how to use the :ref:`Python client <reference-python-client-methods>`
- :ref:`Progress through the intermediate tutorial <tutorial-learning-the-essentials>` to learn about complex workflows, artifacts, and more

About
-----

Dioptra is open-source software developed by the National Institute of Standards and Technology (NIST). Contributions and feedback are welcome from the community.
You can find the source code, license information, and more on the NIST `GitHub repository <https://github.com/usnistgov/dioptra>`__.



.. toctree::
   :maxdepth: -1
   :caption: What is Dioptra?
   :hidden:
   :titlesonly:

   explanation/dioptra-motivation/why-dioptra.rst
   explanation/dioptra-motivation/design-principles.rst
   explanation/dioptra-motivation/audience.rst
   explanation/architecture-overview.rst

.. toctree::
   :maxdepth: 2
   :caption: Setup
   :hidden:
   :titlesonly:

   how-to/setup-dioptra/install-dioptra-explanation.rst
   how-to/setup-dioptra/configure-setup/index.rst
   how-to/setup-dioptra/reference/index.rst

.. toctree::
   :maxdepth: 1
   :caption: Explainers
   :hidden:

   explanation/workflow-architecture-explanation
   explanation/components/index.rst
   explanation/usage-modes

.. toctree::
   :maxdepth: 1
   :caption: Tutorials
   :hidden:

   tutorials/hello_world/index.rst
   tutorials/essential_workflows/index.rst
   tutorials/advanced/index.rst

.. toctree::
   :maxdepth: 1
   :caption: How Tos
   :hidden:

   how-to/essential-workflows/index.rst
   how-to/import-content/index.rst
   how-to/advanced/index.rst


.. toctree::
   :maxdepth: 1
   :caption: Reference
   :hidden:

   reference/glossary
   reference/dioptra-components/index.rst
   reference/python-client/index.rst
   reference/api-reference-restapi
   reference/resource-import-reference
   reference/resource-search-language-reference
   reference/task-engine-reference
   dev-guide/contributing-documentation-guide
