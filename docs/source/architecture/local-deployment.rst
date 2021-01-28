.. _architecture-local-deployment:

Local Deployment
================

Before :ref:`architecture-local-deployment-perform` of the Secure AI Lab, make sure to first complete the following sections of the :ref:`overview-quickstart`:

- :ref:`quickstart-clone-repository`
- :ref:`quickstart-create-environment`
- :ref:`quickstart-build-images`

.. _architecture-local-deployment-perform:

Performing a Local Deployment
-----------------------------

The Secure AI Lab has multiple demos you can perform locally. The following steps will help you choose and run any demo provided:

1. Navigate to the root directory of the project codebase.

   .. code-block:: bash

      cd path/to/secure-ai-lab-components

   **NOTE**: You must substitute the code snippet ``path/to/`` with the true path for the project codebase on your device. This should be the same path used in step 2 of :ref:`Clone the Repository <quickstart-clone-repository>`.

2. Echo a list of demos you can try.

   .. code-block:: bash

      ls examples

3. Navigate to the target demo directory.

   .. code-block:: bash

      cd example/name-of-demo

   **NOTE**: The ``name-of-demo`` must be listed when using ``ls examples``.


4. Source the run file for the demo in the current shell.

   .. code-block:: bash

      source run-demo.sh

   This will check for the required Conda Environment, create one if needed, and run the demo with Jupyter Notebook in your default browser.

5. Exit Jupyter Notebook when your done running the demo by closing the open tab in your default browser.

6. Deactivate the Conda Environment.

   .. code-block:: bash

      conda deactivate
