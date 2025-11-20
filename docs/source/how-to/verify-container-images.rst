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

.. _how-to-verify-container-images:

Verifying Downloaded Container Images
=====================================

When building container images, Dioptra also produces cryptographic artifacts for image verification. These artifacts can be used to ensure the integrity of the images. It is recommended to do so.

In order to perform the verification process in this guide, ``cosign`` (`<https://github.com/sigstore/cosign>`__) must be installed. Optionally, ``jq`` (`<https://jqlang.org/>`__) can be used for easier key path retrieval.

Step 1: Determine the relevant public key
-----------------------------------------

In the root of the dioptra repository is the file ``verify.json``. This contains the ``key_path`` to the relevant public key. For quick retrieval, run the following from the dioptra root directory:

.. code:: sh

    KEY_PATH=$(jq -r '.key_path' verify.json)

Step 2: Use cosign to verify the image
--------------------------------------

Run ``cosign verify`` for the image(s) and tag(s) you wish to verify. We will use ``nginx:1.0.0`` as the image and tag in this example. It is recommended to perform the following action for each image:

.. code:: sh

    cosign verify --key "$KEY_PATH" ghcr.io/usnistgov/dioptra/nginx:1.0.0

The output should look similar to this:

.. code:: sh

    Verification for ghcr.io/usnistgov/dioptra/nginx:1.0.0 --
    The following checks were performed on each of these signatures:
        - The cosign claims were validated
        - Existence of the claims in the transparency log was verified offline
        - The signatures were verified against the specified public key

    [{"critical":{"identity":{"docker-reference":"ghcr.io/ghcr.io/usnistgov/dioptra/nginx"},"image":{"docker-manifest-digest":"sha256:531d71113540f892bc896bb99dcb7d250abd0b38de122600aa4409463c94b9e7"},"type":"cosign container image signature"},"optional":null}]

If so, the image has been successfully verified.