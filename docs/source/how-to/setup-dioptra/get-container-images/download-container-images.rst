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

.. _how-to-download-container-images:

Download the Container Images
=============================

This guide explains how to download pre-built Dioptra container `images <https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/>`__ from the GitHub Container Registry (:term:`GHCR`) and verify their authenticity.
After completing these steps, you will have container images ready for deployment.

.. include:: /_glossary_note.rst

Prerequisites
-------------

* `Docker Engine <https://docs.docker.com/engine/install/>`__ installed and running
* A terminal with access to Docker commands
* (Optional) `cosign <https://github.com/sigstore/cosign>`__ installed for image verification
* (Optional) `jq <https://jqlang.org/>`__ for easier key path retrieval

.. _how-to-download-container-downloading-the-images:

Downloading the Images
----------------------

Obtain the container images for the core Dioptra services.

.. rst-class:: header-on-a-card header-steps

Step 1: Choose Your Build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dioptra images are tagged based on release versions and branches. Choose the appropriate build tag for your use case:

- **Release tags** (e.g., ``1.2.0``): Stable releases recommended for production use
- **Branch tags** (e.g., ``dev``): Latest development builds

.. margin:: 

   .. note:: 
      
      The latest stable release ID (e.g. 1.1.0) can be identified by looking in the top left corner of any `published documentation page <https://pages.nist.gov/dioptra/>`__. 

**Steps** 

1. **Set the** ``TAG`` **environment variable**:

.. tabs::

   .. group-tab:: Stable Releases


      .. code:: sh

         export TAG="1.2.0"

   .. group-tab:: Developer Builds


      .. code:: sh

         export TAG="dev"

.. rst-class:: header-on-a-card header-steps

Step 2: Pull the Core Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Steps** 

1. Pull the core Dioptra images:

.. code:: sh

   docker pull ghcr.io/usnistgov/dioptra/nginx:$TAG
   docker pull ghcr.io/usnistgov/dioptra/mlflow-tracking:$TAG
   docker pull ghcr.io/usnistgov/dioptra/restapi:$TAG

.. rst-class:: header-on-a-card header-steps

Step 3: Pull Worker Images
~~~~~~~~~~~~~~~~~~~~~~~~~~

You will need at least one worker image to run Jobs in Dioptra. 
Each image comes equipped with different dependencies and is configured for different hardware (CPU vs GPU).

**Steps** 

1. Pull one (or more) worker images depending on your needs. 

**CPU workers:**

.. code:: sh

   docker pull ghcr.io/usnistgov/dioptra/pytorch-cpu:$TAG
   docker pull ghcr.io/usnistgov/dioptra/tensorflow2-cpu:$TAG

**GPU workers (optional):**

.. code:: sh

   docker pull ghcr.io/usnistgov/dioptra/pytorch-gpu:$TAG
   docker pull ghcr.io/usnistgov/dioptra/tensorflow2-gpu:$TAG

.. rst-class:: header-on-a-card header-steps

Step 4: Verify the Images Exist Locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run ``docker images`` to verify that the container images are available with your chosen tag:

.. code:: sh

   docker images | grep ghcr.io/usnistgov/dioptra

You should see output similar to the following (assuming the ``1.0.0`` tag):

.. code:: text

   REPOSITORY                                   TAG       IMAGE ID       CREATED         SIZE
   ghcr.io/usnistgov/dioptra/nginx              1.0.0     17235f76d81c   3 weeks ago     243MB
   ghcr.io/usnistgov/dioptra/restapi            1.0.0     f7e59af397ae   3 weeks ago     1.16GB
   ghcr.io/usnistgov/dioptra/mlflow-tracking    1.0.0     56c574822dad   3 weeks ago     1.04GB
   ghcr.io/usnistgov/dioptra/pytorch-cpu        1.0.0     5309d66defd5   3 weeks ago     3.74GB
   ghcr.io/usnistgov/dioptra/tensorflow2-cpu    1.0.0     13c4784dd4f0   3 weeks ago     3.73GB

.. note::

   The ``IMAGE ID``, ``CREATED``, and ``SIZE`` fields will vary.
   Verify that the ``REPOSITORY`` and ``TAG`` columns match your expected images.

Verifying Image Authenticity (Recommended)
------------------------------------------

Dioptra container images are cryptographically signed.
Verifying these signatures confirms that the images you downloaded are authentic and have not been tampered with.

The public key needed for verification is stored in the Dioptra repository.

.. rst-class:: header-on-a-card header-steps

Step 5: Locate the Public Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `Dioptra repository <https://github.com/usnistgov/dioptra>`__ root contains a ``verify.json`` file that specifies the path to the public key.

Retrieve the key path in one of three ways:

**Steps**


.. tabs::

   .. tab:: Curl GitHub API 

      **Steps**

      1. Export branch corresponding to your build 

      .. tabs::

         .. group-tab:: Stable Releases


            .. code:: sh

               export BRANCH_NAME="main"

         .. group-tab:: Developer Builds


            .. code:: sh

               export BRANCH_NAME="dev"

      2. Obtain the key path using curl

      .. tab-set::

         .. tab-item:: Using jq

            .. code:: sh

               export KEY_PATH=$(curl -sL "https://raw.githubusercontent.com/usnistgov/dioptra/refs/heads/$BRANCH_NAME/verify.json" | jq -r '.key_path')
               echo $KEY_PATH

         .. tab-item:: Without jq (less reliable)

            .. code:: sh

               export KEY_PATH=$(curl -sL "https://raw.githubusercontent.com/usnistgov/dioptra/refs/heads/$BRANCH_NAME/verify.json" | grep 'key_path' | sed 's/.*": "\(.*\)".*/\1/')
               echo $KEY_PATH

   .. tab:: Clone Dioptra

      These instructions utilize **jq**

      **Steps**

      1. Clone the Dioptra repository (if not already done)

         .. tab-set::

            .. tab-item:: Clone with HTTPS

               .. code:: sh

                  git clone https://github.com/usnistgov/dioptra.git

            .. tab-item:: Clone with SSH

               .. code:: sh

                  git clone git@github.com:usnistgov/dioptra.git
               
      2. Use **jq** to obtain the key path from ``verify.json`` 

         .. code:: sh

            cd dioptra
            KEY_PATH=$(jq -r '.key_path' verify.json)
            echo $KEY_PATH

   .. tab:: Find path in browser

      1. Open ``verify.json`` in GitHub here: `<https://github.com/usnistgov/dioptra/blob/main/verify.json>`__ (ensure you are on the right branch)
      2. Copy the value of the ``key_path`` field (e.g. "**keys/dioptra.pub**")
      3. Export the copied value to an environment variable 

         .. code:: sh

            export KEY_PATH="keys/dioptra.pub" 

.. rst-class:: header-on-a-card header-steps

Step 6: Verify Each Image
~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``cosign verify`` to verify each downloaded image.
Run this command for each image - ensure you have set your image tag as an environment variable first:

.. tabs::

   .. tab:: NGINX

      .. code:: sh

         cosign verify --key "$KEY_PATH" ghcr.io/usnistgov/dioptra/nginx:$TAG

   .. tab:: Rest API

      .. code:: sh

         cosign verify --key "$KEY_PATH" ghcr.io/usnistgov/dioptra/restapi:$TAG

   .. tab:: MLFlow Tracking

      .. code:: sh

         cosign verify --key "$KEY_PATH" ghcr.io/usnistgov/dioptra/mlflow-tracking:$TAG
   
   .. tab:: Optional Images

      .. tabs::
            
         .. tab:: PyTorch CPU

            .. code:: sh

               cosign verify --key "$KEY_PATH" ghcr.io/usnistgov/dioptra/pytorch-cpu:$TAG


         .. tab:: Tensorflow CPU

            .. code:: sh

               cosign verify --key "$KEY_PATH" ghcr.io/usnistgov/dioptra/tensorflow2-cpu:$TAG


         .. tab:: PyTorch GPU

            .. code:: sh

               cosign verify --key "$KEY_PATH" ghcr.io/usnistgov/dioptra/pytorch-gpu:$TAG


         .. tab:: Tensorflow GPU

            .. code:: sh

               cosign verify --key "$KEY_PATH" ghcr.io/usnistgov/dioptra/tensorflow2-gpu:$TAG


Successful verification produces output similar to:

.. code:: text

   Verification for ghcr.io/usnistgov/dioptra/nginx:1.0.0 --
   The following checks were performed on each of these signatures:
       - The cosign claims were validated
       - Existence of the claims in the transparency log was verified offline
       - The signatures were verified against the specified public key

   [{"critical":{"identity":{"docker-reference":"ghcr.io/usnistgov/dioptra/nginx"},"image":{"docker-manifest-digest":"sha256:531d71113540f892bc896bb99dcb7d250abd0b38de122600aa4409463c94b9e7"},"type":"cosign container image signature"},"optional":null}]

Repeat this step for each image you downloaded.

.. tip::

   To verify all CPU images at once, you can use a loop:

   .. code:: sh

      for IMAGE in nginx restapi mlflow-tracking pytorch-cpu tensorflow2-cpu; do
        cosign verify --key "$KEY_PATH" "ghcr.io/usnistgov/dioptra/$IMAGE:$TAG"
      done

   If you also downloaded GPU images, add them to the loop:

   .. code:: sh

      for IMAGE in nginx restapi mlflow-tracking pytorch-cpu tensorflow2-cpu pytorch-gpu tensorflow2-gpu; do
        cosign verify --key "$KEY_PATH" "ghcr.io/usnistgov/dioptra/$IMAGE:$TAG"
      done

.. warning::

   If verification fails, do not use the image.
   Re-download the image and try again.
   If verification continues to fail, report the issue at https://github.com/usnistgov/dioptra/issues.

.. warning::

   Downloaded images have a different registry prefix than locally built images.
   See :ref:`how-to-get-container-images-registry-prefix` for implications when configuring your deployment.



Next Steps 
------------

Once you have finished downloading the container images, move onto the next step: :ref:`how-to-prepare-deployment`

.. rst-class:: header-on-a-card header-seealso
   
See Also
--------

* :ref:`how-to-prepare-deployment` - Configure and start your Dioptra deployment
* :ref:`how-to-build-container-images` - Build images locally for customization
* :ref:`how-to-get-container-images-registry-prefix` - Understanding registry prefixes
