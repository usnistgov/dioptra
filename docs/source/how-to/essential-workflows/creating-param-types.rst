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

.. _how-to-create-parameter-types:

Create Parameter Types
========================

This how-to explains how to build custom :ref:`Plugin Param Types <explanation-plugin-parameter-types>` in Dioptra. 


Prerequisites
-------------

.. tabs:: 

   .. group-tab:: GUI

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.

   .. group-tab:: Python Client

      * :ref:`how-to-prepare-deployment` -  A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.

.. _how-to-create-param-types-param-type-creation-workflow:

Parameter Type Creation Workflow
--------------------------------

Follow these steps to create and register a new parameter type. You can perform these actions via the Graphical User Interface (GUI) or programmatically using the Python Client.

.. rst-class:: header-on-a-card header-steps


Step 1: Create the Parameter Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Register a parameter type for use in dioptra.

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Plugin Parameters** tab. Click **Create**. 
      
      Enter a *name*, *description*, select a *group* for the type, enter a *structure* (see :ref:`Parameter Type Structures <explanation-plugin-parameter-types-structures>`) if applicable, then click **Confirm**.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to create the parameter type.

      .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.create
         :noindex:

.. rst-class:: fancy-header header-seealso

See Also 
---------

* :ref:`Parameter Types Explanation <explanation-plugin-parameter-types>` - Understand parameter types, structures, and their role in dioptra.
* :ref:`Parameter Types Reference <reference-parameter-types>` - Reference page for parameter types.