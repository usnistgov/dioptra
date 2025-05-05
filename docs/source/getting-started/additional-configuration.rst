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

.. _getting-started-additional-configuration:

Additional Configuration
========================

.. include:: /_glossary_note.rst

In order to begin using Dioptra, a few additional setup steps are required - mainly creating a user account and creating a queue. Optionally, it is also possible to import resources into a deployment to get started with pre-built examples.

Register Accounts
_________________

Dioptra is designed to be run in a multi-user environment, therefore accounts are needed even when running locally. The Dioptra worker account is created automatically during the deployment process using the `.env` file credentials located in the Dioptra deployment folder. To create a user account, first open a web browser to `http://localhost/register`. Enter the desired credentials and click "Register". Then, log in to that user account.

.. image:: /images/frontend-guide/register-user.png
   :width: 400

Create a Queue
______________

Queues are an organizational tool used to manage submitted jobs. The workers that were instantiated when creating the Dioptra deployment watch a Queue and process jobs one at a time in sequence. A Queue is needed to submit the “Hello World” job to, so the next step is to register one.

From the top menu, navigate to the Queues page and then click "Create". For the queue name, put "tensorflow_cpu" and "public" for the group. "tensorflow_cpu" is required for the queue name because it is what the deployment workers are watching. To finish creating the queue, add a description if desired, then click "Confirm".

.. image:: /images/frontend-guide/queue-create.png
   :width: 700


Import Resources
________________

It is possible to import resources (including Plugins, Entrypoints, and PluginParameterTypes) into a Dioptra instance. This is a convenient way to get started with pre-built examples.

A python script is provided in the deployment directory. To import the resources from the `extra` directory from the `main` branch of the Dioptra repository, simple run:

.. code:: sh

  python import_resources.py --git-url https://github.com/usnistgov/dioptra --git-branch main

You will be prompted for the additional username and password you created in a previous step. The `--help` flag can be passed to display the help dialog.

See the :ref:`Resource Import Reference <reference-resource-import-reference>` section for more details on importing resources.
