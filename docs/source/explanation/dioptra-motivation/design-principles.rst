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

.. _explanation-design-principles:


Design Principles
=================

Dioptra was designed with the following use cases and key properties in mind.

Use Cases
~~~~~~~~~

We envision the following primary use cases for Dioptra:

* **Model Testing**:

  * *1st party* - Assess AI models throughout the development lifecycle
  * *2nd party* - Assess AI models during acquisition or in an evaluation lab environment
  * *3rd party* - Assess AI models during auditing or compliance activities

* **Research**: Aid trustworthy AI researchers in tracking experiments
* **Evaluations and Challenges**: Provide a common platform and resources for participants
* **Red-Teaming**: Expose models and resources to a red team in a controlled environment

Key Properties
~~~~~~~~~~~~~~

Dioptra strives for the following key properties:

* **Reproducible**: Dioptra automatically creates snapshots of resources so experiments can be reproduced and validated
* **Traceable**: The full history of experiments and their inputs are tracked
* **Extensible**: Support for expanding functionality and importing existing Python packages via a plugin system
* **Interoperable**: A type system promotes interoperability between plugins
* **Modular**: New experiments can be composed from modular components in a simple yaml file
* **Secure**: Dioptra provides user authentication with access controls coming soon
* **Interactive**: Users can interact with Dioptra via an intuitive web interface
* **Shareable and Reusable**: Dioptra can be deployed in a multi-tenant environment so users can share and reuse components
