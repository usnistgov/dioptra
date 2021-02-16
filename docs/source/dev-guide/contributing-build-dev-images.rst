.. _dev-guide-build-dev-images:

Building Development Docker Images
==================================

**NOTE**: The following steps are intended for developers that are using a branch that is **NOT** the *master* branch of the repository. If you are using the *master* branch please see :ref:`quickstart-build-images`.

.. _dev-guide-build-branch-images-step-1:

1. Navigate to the root directory of the project codebase.

   .. code-block:: bash

      cd path/to/secure-ai-lab-components

   **NOTE**: You must substitute the code snippet ``path/to/`` with the true path for the project codebase on your device. This should be the same path used in :ref:`Clone the Repository: Step 2 <quickstart-clone-repository-step-2>`.

2. Echo a list of all branches for the repository.

   .. code-block:: bash

      git branch -a

3. Checkout a branch.

   -  **Checkout Remote Branch**
      If the desired branch begins with ``remotes/origin/`` it is a remote branch.

      .. code-block:: sh

         git checkout -b new-name-for-local-branch remotes/origin/name-of-remote-branch

      This will create and checkout a local branch with the name you substituted for ``new-name-for-local-branch`` that is a copy of the remote branch ``remotes/origin/name-of-remote-branch``.

   -  **Checkout Local Branch**
      If the desired branch does *NOT* begin with ``remotes/origin/`` it is a local branch that you have already created on your host device.

      .. code-block:: sh

         git checkout name-of-local-branch

      **NOTE**: The ``remotes/origin/name-of-remote-branch`` and ``name-of-local-branch`` must be listed when using:

      .. code-block:: sh

         git branch -a

4. Pull the latest vendor, Continuous Integration (CI), and lab images from the MITRE artifactory and retag them.

   .. code-block:: sh

      make pull-latest-hub pull-latest-ci pull-latest-lab


5. Echo a list of all demos that can be run locally in the project codebase.

   .. code-block:: sh

      ls examples

6. Navigate to the target demo directory.

   .. code-block:: sh

      cd example/name-of-demo

   **NOTE**: The ``name-of-demo`` must be listed when using:

   .. code-block:: sh

      ls examples

7. Modify the Docker configuration file.

   .. code-block:: sh

      sed -E -e 's/(securing-ai\/.*):latest/\1:dev/g' -i .backup docker-compose.yml

   **NOTE**: To revert the changes made to the configuration file use the command:

   .. code-block:: sh

      mv docker-compose.yml.backup docker-compose.yml

8. Navigate back to the root directory of the to the root directory of the project codebase.

   .. code-block:: sh

      cd ../..

   **NOTE**: Alternatively, use the same commands as in :ref:`Building the Docker Images for Separate Branches: Step 1 <dev-guide-build-branch-images-step-1>`.

9. Repeat steps 5-8 for each example that will be run on the current branch.

10. Build all the Docker images for in the project.

   .. code-block:: sh

      make build-all
