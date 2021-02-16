.. _getting-started-installation:

Installation Guide
==================

This installation guide is divided into three parts, with the first part covering system requirements, the second part covering how to install the ``mitre-securing-ai`` Python package, and the third part covering how to setup a personal computer for test-driving the Securing AI Testbed architecture locally.
General instructions on how to use the Securing AI Ansible Collection to configure and deploy the Testbed in an on-premises server or cluster environment can be found in another section of the documentation.
.. TODO: Link to the on-prem deployment instructions once they are available.

Package Installation
--------------------

Requirements
^^^^^^^^^^^^

The minimum requirements for installing the ``mitre-securing-ai`` Python package on your host device are as follows:

- CPU: An x86-64 processor
- RAM: 4GB or higher
- Operating System: Windows 10, MacOS 10.14 or newer, Linux (Ubuntu 20.04 LTS recommended)
- Python 3.7 or above (3.7 and 3.8 are actively tested)

.. _quickstart-create-environment:

Creating a Conda Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A `Virtual Environment <https://en.wikipedia.org/wiki/Virtual_environment>`_ must be created to support various dependencies such as the `Python <https://www.python.org/>`_ modules and packages included in scripts within the project codebase.
The easiest way to accomplish this is using the pre-built configuration files included in the project codebase to create a `Conda Environment <https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html>`_.

There are two install options to start using `Conda Environments <https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html>`_,

.. tabbed:: Anaconda installation

   The following links will provide a installation package for version 2020.11 of `Anaconda <https://docs.anaconda.com/>`_ on your host machine (must meet all :ref:`quickstart-system-requirements`).

   - `Anaconda for Windows <https://repo.anaconda.com/archive/Anaconda3-2020.11-Windows-x86_64.exe>`_
   - `Anaconda for MacOS <https://repo.anaconda.com/archive/Anaconda3-2020.11-MacOSX-x86_64.pkg>`_
   - `Anaconda for Linux <https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh>`_

   If your host machine does not meet the :ref:`quickstart-system-requirements`, then go to the `Anaconda Installation Documents <https://docs.anaconda.com/anaconda/install/>`_ for more help.

.. tabbed:: Miniconda installation

   The following links will provide a installation package for the latest version of `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ on your host machine (must meet all :ref:`quickstart-system-requirements`).

   - `Miniconda for Windows <https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe>`_
   - `Miniconda for MacOS <https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.pkg>`_
   - `Miniconda for Linux <https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh>`_

   If your host machine does not meet the :ref:`quickstart-system-requirements`, then go to the `Miniconda Installation Documents <https://docs.conda.io/en/latest/miniconda.html>`_ for more help.

Preparing a Local Testbed environment
-------------------------------------

Requirements
^^^^^^^^^^^^

The minimum requirements for test-driving the Testbed architecture locally on your host device are as follows:

- CPU: Intel or AMD-based x86-64 processor with 4+ physical cores at 1.90GHz or higher (recommended)
- RAM: 16GB or higher (recommended)
- Operating System: Windows 10, MacOS 10.14 or newer, Linux (Ubuntu 20.04 LTS recommended)
- GNU/Linux-compatible environment, see :ref:`quickstart-gnu-linux-environment`
- Docker Desktop 3.1.0 or later (Windows/MacOS)

.. _quickstart-gnu-linux-environment:

GNU/Linux Environments
^^^^^^^^^^^^^^^^^^^^^^

A host device that uses a GNU/Linux environment can be the following:

- Most Linux distributions
- MacOS/OS X with Homebrew_
- Windows with the `Windows Subsystem for Linux`_
- A virtual machine running a Linux distribution

.. note::

   The Securing AI Lab was developed for use with native GNU/Linux environments.
   When using MacOS/OS X or Windows there is a chance you will encounter errors that are specific to your system's setup that are not covered in this documentation.
   To resolve such issues, first look at the external documentation linked (i.e. Homebrew_ and `Windows Subsystem for Linux`_) before submitting a bug report.
   Also, when using a virtual machine it is likely the performance of can be throttled because of the CPU and Memory allocations set at the time the virtual machine was configured.
   If performance becomes an issue when using a virtual machine, consider increasing the CPU and Memory resources allocated to the machine.

.. _Homebrew: https://brew.sh/
.. _Windows Subsystem for Linux: https://docs.microsoft.com/en-us/windows/wsl/
.. _quickstart-clone-repository:

Clone the Repository
^^^^^^^^^^^^^^^^^^^^

To clone the repository, open a new **Terminal** session for your operating system,

.. tabbed:: Windows

   Use the keyboard shortcut :kbd:`windows` + :kbd:`r` to open **Run**, then type ``wsl`` into the search bar and click *OK* to start a `Windows Subsystem for Linux`_ session.

.. tabbed:: MacOS

   Use the keyboard shortcut :kbd:`command` + :kbd:`space` to open the **Spotlight Search**, type ``Terminal`` into the search bar, and click the *Terminal* application under *Top Hit* at the top of your results.

.. tabbed:: Linux

   Use the keyboard shortcut :kbd:`ctrl` + :kbd:`alt` + :kbd:`t` to open the **Terminal**.

Next, navigate to the directory where you will clone the repository,

.. code-block:: sh

   # NOTE: Substitute path/to/your/directory with a path that exists on your device.
   cd path/to/your/directory

.. attention::

   Windows Subsystem for Linux (WSL) and MacOS users may encounter performance and file permission issues depending on the directory where the repository is cloned.
   This problem is due to the way that Docker is implemented on these operating systems.
   For WSL users, these issues may occur if you clone the repository within any folder on the Windows filesystem under ``/mnt/c``, while for MacOS users it may occur if the repository is cloned within the ``Downloads`` or ``Documents`` directory.
   For this reason, WSL and MacOS users are both encouraged to create and clone the repository into a projects directory in their home directory,

   .. code-block:: sh

      mkdir ~/Projects
      cd ~/Projects

Clone the repository to your local computer,

.. tabbed:: Clone with HTTPS

   .. code:: sh

      git clone https://gitlab.mitre.org/secure-ai/securing-ai-lab-components.git

.. tabbed:: Clone with SSH

   .. code:: sh

      git clone git@gitlab.mitre.org:secure-ai/securing-ai-lab-components.git

Finally, verify the repository was downloaded and is up to date,

.. code-block:: sh

   cd secure-ai-lab-components && git pull

The message *Already up to date.* should be echoed, verifying the repository was successfully cloned to your device.

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