**What goes here:** a generic explanation of how to setup and run each of the demos, including accessing the Jupyter notebooks, etc.

The Secure AI Testbed has multiple demos you can perform locally. The following steps will help you choose and run any demo provided:

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
