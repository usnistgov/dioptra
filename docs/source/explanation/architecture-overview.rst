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

.. _explanation-architecture-overview:


Architecture Overview
=====================

The Dioptra test platform is built on a microservices architecture.
It is designed to be deployed across several physical machines but is equally deployable on a local laptop.
The distributed deployment allows the core optimization algorithms to reside on machines with GPUs or other high-powered computational resources, while a local deployment will impose strong computational constraints.

The heart of the architecture is the core test platform Application Programming Interface (:term:`API`) that manages requests and responses with a human user via a reverse proxy.
The backend Data Storage component hosts datasets, registered models and artifacts, and experiment results and metrics.
As experiment jobs get submitted, the :term:`API` registers them on the Redis queue, which is watched by a worker pool of Docker containers provisioned with all necessary environment dependencies.
These worker containers run the plugins and coordinate job dependencies and record statistics, metrics, and any generated artifacts.

The user can interact with the :term:`API` via a web-based :term:`GUI` or Python client.

The architecture is built entirely from open-source resources making it easy for others to extend and improve upon.

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`how-to-running-experiments` - How to guides for creating resources with the Dioptra GUI / Python Client
* :ref:`Usage modes <explanation-usage-modes>` - Explanation on the GUI and Python client
* :ref:`Dioptra components explainers <explanation-dioptra-components>` - Explanation on Dioptra components
