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

.. _reference-workflows-client-methods:

Workflows Client Methods
========================

This page lists all relevant methods for Dioptra Workflows that are available via the Python Client.

.. contents:: Contents
   :local:
   :depth: 2


Requirements
------------

- :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
- :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized


.. _reference-workflows-client-methods-resource-management:

Workflows - Resource Management
-------------------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods can be executed via ``client.workflows.METHOD_NAME()``.

Import Resources
~~~~~~~~~~~~~~~~

   .. automethod:: dioptra.client.workflows.WorkflowsCollectionClient.import_resources

Commit Draft (Should we delete? Drafts are not implemented yet)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   .. automethod:: dioptra.client.workflows.WorkflowsCollectionClient.commit_draft


.. _reference-workflows-client-methods-analysis-validation:

Workflows - Analysis and Validation
-----------------------------------

These methods allow for the validation of entrypoint parameters and the analysis of plugin task signatures within the workflow context.

Validate Entrypoint
~~~~~~~~~~~~~~~~~~~

   .. automethod:: dioptra.client.workflows.WorkflowsCollectionClient.validate_entrypoint

Analyze Plugin Task Signatures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   .. automethod:: dioptra.client.workflows.WorkflowsCollectionClient.analyze_plugin_task_signatures

