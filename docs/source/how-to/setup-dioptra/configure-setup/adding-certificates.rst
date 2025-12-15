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

.. _how-to-adding-certificates:

Adding Certificates
=====================

This how to guide explains how to add certifications.


Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 


Adding extra CA certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The deployment initialization scripts will look for extra CA certificates in the ``ssl/ca-certificates/`` folder and copy and bundle them into named volumes so they are available at runtime.
Only CA certificate files copied into the ``ssl/ca-certificates/`` folder that meet the following criteria will be bundled:

- Each CA certificate file must be in the PEM format.
  The PEM format encodes the certificate using base64 and stores it in a plain text file between two lines, ``-----BEGIN CERTIFICATE-----`` and ``-----END CERTIFICATE-----``.
- Each file should include one, and only one, CA certificate.
  Do not bundle multiple CA certificates together.
- Each PEM-formatted CA certificate file **must** have the file extension ``crt``, for example ``ca-root.crt``.
  If your CA certificate has a different file extension (such as ``pem``), rename it to ``crt`` after copying to this folder.

For further information about including extra CA certificates, please see the ``README.md`` file in the ``ssl/ca-certificates/`` folder.