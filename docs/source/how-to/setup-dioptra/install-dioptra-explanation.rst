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

.. _explanation-install-dioptra:

Install Dioptra
===============

This page provides a high-level overview of the Dioptra installation process and the concepts behind its deployment architecture.

Overview 
----------

Installing Dioptra is the process of **orchestrating a suite of microservices** into a functional environment. Dioptra runs as a collection of interconnected Docker containers that handle different aspects of the system, such as experiment tracking, task execution, and data storage. 

Once these containers are active, Dioptra services become accessible through a REST API and a web-based Graphical User Interface (GUI).

The Installation Workflow
-------------------------

There are two fundamental phases to getting Dioptra running:

1. **Phase 1: Acquire Container Images.** You must obtain the Dioptra container images on your local system. These images contain the environment for the REST API, the frontend, and the Dioptra workers. See :ref:`how-to-get-container-images`.
2. **Phase 2: Create a Deployment.** You create a local deployment directory that configures the specific settings, credentials, and hardware allocations for your instance. See :ref:`how-to-prepare-deployment`.

.. note::

   The Docker containers and the deployment configurations are decoupled. You can maintain multiple deployments for the same set of images, and both the containers and the deployments can be :ref:`updated <how-to-update-deployment>` independently as new versions are released.

System Requirements
-------------------------

Before beginning the installation, ensure your host environment meets the following requirements:

* **Operating System:** A Linux-based environment is recommended.
* **Docker & Docker Compose:** The engine used to manage and run the Dioptra container suite.
* **Python 3.11+:** Required on the host machine to execute the ``cruft`` deployment template tools.
* **Git:** Required by ``cruft`` to clone the Dioptra repository. Users will only need to directly invoke Git commands if they plan to build the containers *or* if they want to verify the signing key of downloaded images.

Understanding Deployments
-------------------------

In Dioptra, a **Deployment** is a specific, configured instance of the software tailored for a particular use case. This architecture allows users to maintain multiple isolated environments on a single host. 

Each deployment exists in its own directory and maintains its own:

* **Credentials:** Unique passwords, secret keys, and security certificates.
* **Configuration:** Specific port mappings and hardware resource allocations.
* **Persistence:** Dedicated storage volumes for databases and experiment artifacts.

Flexible Configuration
-------------------------

Dioptra is designed to be portable, supporting both local workstations and cloud-based environments with multi-user support. The :ref:`deployment can be customized <how-to-setup-options>` to meet specific project needs, including:

* Mounting external data volumes for large datasets.
* Integrating custom CA certificates for secure networking.
* Enabling GPU-accelerated workers for demanding machine learning tasks.


.. admonition:: Learn More 

   See :ref:`how-to-setup-options` for available deployment configuration options. 

Installation Guides
---------------------

Follow the steps detailed in the guides below to install Dioptra. 

.. container:: wide-lightly-shaded

    .. toctree::
       :maxdepth: 2

       get-container-images/index
       prepare-deployment
       update-deployment