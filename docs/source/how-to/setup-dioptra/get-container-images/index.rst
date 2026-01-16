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

.. _how-to-get-container-images:

Get the Container Images
========================

Dioptra runs as a set of Docker containers.
Before you can deploy Dioptra, you need container images for the core services (REST API, MLflow tracking, NGINX) and at least one worker image (PyTorch or TensorFlow).

There are two ways to obtain these images:

.. grid:: 2

   .. grid-item-card:: **Download Pre-built Images (Recommended)**
      :link: how-to-download-container-images
      :link-type: ref

      Pull pre-built images from the GitHub Container Registry.
      This is the fastest way to get started and includes signature verification for authenticity.

      *Best for: Most users*

   .. grid-item-card:: **Build Images Locally**
      :link: how-to-build-container-images
      :link-type: ref

      Build container images from the source repository.
      Only needed if you want to customize the images or cannot access the GitHub Container Registry.

      *Best for: Custom modifications, restricted environments*

Which Method Should I Use?
--------------------------

**Download pre-built images** if:

- You want to get started quickly
- The pre-built worker environments meet your needs

**Build images locally** if:

- You want to customize the container images
- You are in a restricted environment that cannot access the GitHub Container Registry

.. _how-to-get-container-images-registry-prefix:

Understanding Container Registry Prefixes
-----------------------------------------

Container images have a registry prefix that identifies where they came from.
This prefix affects how you configure your Dioptra deployment.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Method
     - Image Name Example
     - Registry Prefix
   * - Downloaded from :term:`GHCR`
     - ``ghcr.io/usnistgov/dioptra/nginx:1.0.0``
     - ``ghcr.io/usnistgov``
   * - Built locally
     - ``dioptra/nginx:dev``
     - *(empty)*

When you :ref:`prepare your deployment <how-to-prepare-deployment>`, you will set the ``container_registry`` template variable to match your images:

- **Downloaded images:** Set ``container_registry`` to ``ghcr.io/usnistgov``
- **Locally built images:** Leave ``container_registry`` empty (the default)

.. note::

   If you need to mix downloaded images with locally built images (e.g., using downloaded images for most services but a custom-built image for a specific worker), you will need to use Docker Compose override files to specify the correct image.
   See :ref:`how-to-using-docker-compose-overrides` for details.

.. toctree::
   :maxdepth: 1
   :caption: Table of Contents
   :hidden:

   download-container-images
   build-container-images
