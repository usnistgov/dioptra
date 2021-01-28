.. _overview-quickstart:

Lab Quickstart
==============

The following guidelines are the necessary steps to prepare a successful :ref:`architecture-local-deployment` of the Securing AI Lab or use of `The Lab REST API <restapi-index>`_ or `The Lab SDK <sdk-index>`_.

- :ref:`quickstart-system-requirements`
- :ref:`quickstart-clone-repository`
- :ref:`quickstart-create-environment`
- :ref:`quickstart-build-images`

.. _quickstart-system-requirements:

System Requirements
-------------------

For the installation and deployment of the Secure AI Lab links to work your host device must meet the following requirements:

- Python 3.8 is installed
- Uses a 64-bit operating system
- Uses a GNU/Linux command line tools. See :ref:`quickstart-gnu-linux-environment`.

.. _quickstart-gnu-linux-environment:

GNU/Linux Environments
^^^^^^^^^^^^^^^^^^^^^^

A host device that uses a GNU/Linux environment can be the following:

- Most Linux distributions
- MacOS/OS X with Homebrew_
- Windows with the `Windows Subsystem for Linux`_
- A virtual machine running a Linux distribution

**NOTE**: The Securing AI Lab was developed for use with native GNU/Linux environments.
When using MacOS/OS X or Windows there is a chance you will encounter errors that are specific to your system's setup that are not covered in this documentation.
To resolve such issues, first look at the external documentation linked (i.e. Homebrew_ and `Windows Subsystem for Linux`_) before posting a Submitting an Issue to the repository.
Also, when using a virtual machine it is likely the performance of can be throttled because of the CPU and Memory allocations set at the time the virtual machine was configured.
If performance becomes an issue when using a virtual machine, consider increasing the CPU and Memory resources allocated to the machine.

.. _Homebrew: https://brew.sh/
.. _Windows Subsystem for Linux: https://docs.microsoft.com/en-us/windows/wsl/
.. _quickstart-clone-repository:

Clone the Repository
--------------------

To clone the repository:

1. Open a new **Terminal** (Linux or MacOS) or **Powershell** with Window Subsystem for Linux (Windows) session.

   **Linux**
   Use the keyboard shortcut ``Ctrl+Alt+T`` to open the **Terminal**.

   **MacOS**
   1. Use the keyboard shortcut ``Command+Space`` to open the **Spotlight Search**.
   2. Type ``Terminal`` into the search bar that appears.
   3. Double-click the *Terminal* application under *Top Hit* at the top of your results and **Terminal** will open.

   **Windows**
   1. Use the keyboard shortcut ``Windows+R`` to open **Run**.
   2. Type ``powershell`` into the search bar and click *OK* to open the **Powershell**.

2. Navigate to the directory you wish to clone the repository too.

   .. code-block:: bash

      cd path/to/your/directory

   **NOTE**: You must substitute the code snippet ``path/to/your/directory`` with a path that exists on your device.

3. Clone the repository.

   .. code-block:: bash

      git clone https://gitlab.mitre.org/secure-ai/securing-ai-lab-components.git

4. Verify the repository was downloaded and is up to date.

   .. code-block:: bash

      cd secure-ai-lab-components && git pull

   The message *Already up to date.* should be echoed, verifying the repository was successfully cloned to your device.

.. _quickstart-create-environment:

Creating a Conda Environment
----------------------------

A `Virtual Environment <https://en.wikipedia.org/wiki/Virtual_environment>`_ must be created to support various dependencies such as the `Python <https://www.python.org/>`_ modules and packages included in scripts within the project codebase.
The easiest way to accomplish this is using the pre-built configuration files included in the project codebase to create a `Conda Environment <https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html>`_.

There are two install options to start using `Conda Environments <https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html>`_.
First, you can :ref:`install the full version of Anaconda <quickstart-install-anaconda>`.
Alternatively you may :ref:`install the the minimal version of Anaconda <quickstart-install-miniconda>` known as Miniconda.

.. _quickstart-install-anaconda:

Installing Anaconda
^^^^^^^^^^^^^^^^^^^

**NOTE**: If you have installed the Miniconda by following the instructions in :ref:`quickstart-install-miniconda` then skip directly to :ref:`quickstart-config-environment`.

To following links will provide a installation package for version 2020.11 of `Anaconda <https://docs.anaconda.com/>`_ on your host machine (must meet all :ref:`quickstart-system-requirements`).

- `Anaconda for Windows <https://repo.anaconda.com/archive/Anaconda3-2020.11-Windows-x86_64.exe>`_
- `Anaconda for MacOS <https://repo.anaconda.com/archive/Anaconda3-2020.11-MacOSX-x86_64.pkg>`_
- `Anaconda for Linux <https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh>`_

If your host machine does not meet the :ref:`quickstart-system-requirements` then go to the `Anaconda Installation Documents <https://docs.anaconda.com/anaconda/install/>`_ for more help.

.. _quickstart-install-miniconda:

Installing Miniconda
^^^^^^^^^^^^^^^^^^^^

**NOTE**: If you have installed the full version of Anaconda by following the instructions in :ref:`quickstart-install-anaconda` then skip directly to :ref:`quickstart-config-environment`.

To following links will provide a installation package for the latest version of `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ on your host machine (must meet all :ref:`quickstart-system-requirements`).

- `Miniconda for Windows <https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe>`_
- `Miniconda for MacOS <https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.pkg>`_
- `Miniconda for Linux <https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh>`_

If your host machine does not meet the :ref:`quickstart-system-requirements` then go to the `Miniconda Installation Documents <https://docs.conda.io/en/latest/miniconda.html>`_ for more help.

.. _quickstart-using-vpn:

.. Using a Virtual Private Network
.. -------------------------------

.. It's possible that when using a Virtual Private Network you can encounter an error

.. ``CondaHTTPError: HTTP 000 CONNECTION FAILED for url <https://conda.anaconda.org/conda-forge/osx-64/repodata.json>
.. Elapsed: -

.. An HTTP error occurred when trying to retrieve this URL.
.. HTTP errors are often intermittent, and a simple retry will get you on your way.
.. 'https://conda.anaconda.org/conda-forge/osx-64'``

.. _quickstart-config-environment:

Using Pre-made Configuration Files to Create a Conda Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Throughout the project codebase, there are a multitude of files named `environment.yml`.
These `YAML <https://en.wikipedia.org/wiki/YAML>`_ files or rather configuration files can be used as parameters when `creating a Conda Environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands>`__.

Demo-specific instructions for creating a suitable environment will be provided in the examples contained within :ref:`tutorial-index`, but the following example outlines the generic steps that can be taken to `create a Conda Environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands>`__:

1. Navigate to the directory where the desired *environment.yml* (the pre-made configuration file) file is located.

   .. code-block:: bash

      cd Path/To/Your/Directory

2. Create a Conda Environment with a pre-made configuration file.

   .. code-block:: bash

      conda env create --file environment.yml

3. Activate the newly created Conda Environment.

   .. code-block:: bash

      conda activate name-of-the-environment

   **NOTE**: The *name-of-the-environment* used for the demos provided in the project codebase can be found be inspecting the specific *environment.yml* file for the tag labeled *name*.

.. _quickstart-build-images:

Pulling the Latest Docker Images
--------------------------------

The last step to setup the Secure AI Lab is to build the necessary docker images used by the repositories various tutorials.

**NOTE**: The following steps will only work if you are attempting to use the *master* branch of the repository.
If you are a developer using a separate branch please see :ref:`dev-guide-build-dev-images`.

1. Navigate the the root directory of the project.

   .. code-block:: bash

      cd path/to/secure-ai-lab-components

   **NOTE**: You must substitute the code snippet ``path/to/`` with the true path for the project codebase on your device.
   This should be the same path used in step 2 of :ref:`Clone the Repository <quickstart-clone-repository>`.

2. Pull the latest vendor, Continuous Integration (CI), and lab images.
   These are most current images that are pre-built to be used by the *master* branch.

   .. code-block:: bash

      make pull-latest-hub pull-latest-ci pull-latest-lab
