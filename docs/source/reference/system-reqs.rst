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

.. _reference-system-requirements:

System Requirements
=================

A reference page for system requirments. 



Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 

Most of the built-in demonstrations in the testbed assume the testbed is deployed on Unix-based operating systems (e.g., Linux, macOS).
Those familiar with the Windows Subsystem for Linux (WSL) should be able to deploy it on Windows, but this mode is not explicitly supported at this time.
Most included demos perform computationally intensive calculations requiring access to significant computational resources such as Graphics Processing Units (GPUs).
The architecture has been tested on a :term:`NVIDIA DGX` server with 4 GPUs.
The demonstrations also rely on publicly available datasets such as :term:`MNIST` handwritten digits, ImageNet, and Fruits360 that are not part of the testbed distribution.
The built-in demonstrations assume that relevant datasets have already been obtained and saved in the testbed's Data Storage container.