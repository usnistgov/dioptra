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

.. _user-guide-the-basics:

The Basics
==========

.. include:: /_glossary_note.rst

The primary use case for Dioptra is the running, tracking, and organizing of machine learning security experiments using the open-source technologies and architectures found in real-world AI applications.
The Testbed supports this by providing the following capabilities.

#. A containerized micro-services architecture for running and tracking experiments that is straightforward to deploy on a wide range of computational environments
#. A modular workflow system with swappable units of work to enable low effort hypothesis testing and the rapid iteration of experiments

These capabilities rely on four types of components:

Testbed REST API
   The Testbed :term:`REST` :term:`API` is the heart of the micro-services architecture and is used to register experiments, submit jobs, log experimental results and artifacts, and access the model registry.

Task Plugins System
   The task plugins are the low-level building blocks of an experiment that can be installed and updated in the Testbed with zero downtime.

Software Development Kit (SDK)
   The software development kit is a developer-focused Python library for extending the Testbed's functionality via its plugin system.

Docker Images
   The Docker images are the concrete implementations of the individual components of the micro-services architecture.

Fundamental Units of an Experiment
----------------------------------

The following diagram illustrates the fundamental units of a Testbed experiment and their nesting hierarchy.

.. figure:: /images/experiment-components.svg
   :alt: The diagram showing the nesting of the fundamental building blocks of an experiment. There is a large block labeled "experiment," nested within it are smaller blocks labeled "entry point", and nested within those are several, even smaller blocks labeled "task". The tasks flow from one to the next via a sequence of arrows. The entry points also flow from one to the next via a sequence of arrows.

   Entry points are composed of tasks and an experiment is a collection of related entry point runs.

In essence, a testbed experiment is a sequence of entry points composed of tasks.
An entry point is a construct provided via the MLFlow library that consists of an executable script or binary with declared parameters.
The tasks within an entry point are calls to Python functions in a plugin registry, with the task execution order managed by the Prefect library.
The entry point executables are themselves run by a Testbed worker, which is a managed process within a Docker container that has been provisioned with all the necessary environment dependencies to support the job.

Job Submission
--------------

.. figure:: /images/api-entry-point-submission.svg

The above diagram illustrates the three steps of the Testbed job submission process,

#. Create an entry point by writing an executable script and preparing a configuration file that declares the script's variable parameters
#. Package the entry point files into a tarball or zip archive
#. Submit the job by uploading the entry point archive and your parameter choices to the Testbed API

After submission, a job's status can be monitored by querying the Testbed :term:`API` or by accessing the MLFlow dashboard [1]_ using a web browser.
The Testbed :term:`API` and MLFlow dashboard can also be used to review a job's results and download its artifacts for local inspection.

.. Footnotes

.. [1] The MLFlow dashboard is a web app provided by the MLFlow Tracking service. Whether or not it can be accessed depends on the details of your deployment.
