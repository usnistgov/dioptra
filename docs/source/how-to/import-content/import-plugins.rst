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

.. _how-to-import-plugins:

Import Resources
================

This how-to explains how to import Resources (:ref:`Plugins <plugins-explanation>`, :ref:`Entrypoints <entrypoints-explanation>`, and  :ref:`Entrypoints <plugin-parameter-types-explanation>`)to a Dioptra deployment
from an external source which declares Resources via a :ref:`Resource Import TOML <reference-resource-import-syntax>` file.


Prerequisites
-------------

.. tabs:: 

   .. group-tab:: GUI

      * :ref:`how-to-prepare-deployment` - A deployment of Dioptra is required.
      * :ref:`tutorial-setup-dioptra-in-the-gui` - Access Dioptra services in the GUI, create a user, and login.

   .. group-tab:: Python Client

      * :ref:`how-to-prepare-deployment` -  A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client in a Jupyter Notebook.


.. _how-to-import-plugins-import-resource-workflow:

Resource Import Workflow
------------------------

Follow these steps to import resources (plugins and entrypoints) into Dioptra.

.. note::

    There are several name conflict resolution strategies for imported resources, which apply to all import options:

    * **Fail** - The import will fail if there is a name conflict.
    * **Update** - The previously registered resources will be updated with new definitions.
    * **Overwrite** - The previously registered resources will be deleted, and new resources will be created.


.. rst-class:: header-on-a-card header-steps


Step 1: Select the source to import from. (GUI only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Import resources from a Git repository.

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, click the wrench symbol on the navigation bar. 
      
      Select Import Resources from the drop down. Select the either **GIT REPO**, **UPLOAD ARCHIVE** or **UPLOAD DIRECTORY** depending on where you would
      like to import resources from.

      If using a Git repository, enter the URL to the branch of the Git repository containing the resources to import. (For example - ``https://github.com/usnistgov/dioptra.git#main``)

      If using an archive, click **Archive File Upload** and select a tar file containing the files.

      If using a directory, click **Directory Upload** and select the directory containing the files.

.. rst-class:: header-on-a-card header-steps

Step 2: Import the Resources.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tabs::

   .. group-tab:: GUI

      Select a group to import these resources under.

      .. note:: 
          Dioptra does not currently support the creation of additional groups. All resources are under the same default public group.

      Enter the path to the TOML file. (For example - ``extra/dioptra.toml``)

      Select a name conflict resolution strategy.

      Select **IMPORT**.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to import the resources.

      .. automethod:: dioptra.client.workflows.WorkflowsCollectionClient.import_resources


See Also 
---------

* :ref:`Resource Import: reference <reference-resource-import-syntax>` - More information on syntax requirements for the Resource Import file
* :ref:`Plugins: reference <reference-plugins>` - More information on syntax requirements for Plugins
* :ref:`Entrypoints: reference <reference-entrypoints>` - More information on syntax requirements for Entrypoints

