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

.. _getting-started-downloading-the-containers:

Downloading the Container Images
================================

.. include:: /_glossary_note.rst

You will need several container images before you can run Dioptra for the first time. You can download pre-built images from the GitHub Container Repository (GHCR) using the instructions found here. Please note that GPU-enabled images cannot be downloaded from GHCR and must be built by following the process outlined in :doc:`../how-to/build-container-images`. 

Dioptra images have tags based on their branches. Select the appropriate tag for your use case, such as ``1.0.0`` or ``dev``. Replace ``$TAG`` with the desired tag for all commands in the rest of this guide.

In a Terminal window, use docker to pull the following core images:

.. code-block:: sh
    :caption: Pull Dioptra core images

    docker pull --platform linux/amd64 ghcr.io/usnistgov/dioptra/nginx:$TAG
    docker pull --platform linux/amd64 ghcr.io/usnistgov/dioptra/mlflow-tracking:$TAG
    docker pull --platform linux/amd64 ghcr.io/usnistgov/dioptra/restapi:$TAG

Then, select one or more of the following worker images depending on your needs.  

.. code-block:: sh
    :caption: Pull Dioptra worker image(s) 

    docker pull --platform linux/amd64 ghcr.io/usnistgov/dioptra/pytorch-cpu:$TAG
    docker pull --platform linux/amd64 ghcr.io/usnistgov/dioptra/tensorflow2-cpu:$TAG

Now, run ``docker images`` to verify that the container images are now available with the chosen tag.
The output will vary with your chosen tag, but assuming the ``1.0.0`` tag, you should see output that looks like the following:

.. code:: text

    REPOSITORY                                   TAG       IMAGE ID       CREATED         SIZE
    ghcr.io/usnistgov/dioptra/nginx              1.0.0     17235f76d81c   3 weeks ago     243MB
    ghcr.io/usnistgov/dioptra/restapi            1.0.0     f7e59af397ae   3 weeks ago     1.16GB
    ghcr.io/usnistgov/dioptra/mlflow-tracking    1.0.0     56c574822dad   3 weeks ago     1.04GB
    ghcr.io/usnistgov/dioptra/pytorch-cpu        1.0.0     5309d66defd5   3 weeks ago     3.74GB
    ghcr.io/usnistgov/dioptra/tensorflow2-cpu    1.0.0     13c4784dd4f0   3 weeks ago     3.73GB

.. note::

    The ``IMAGE ID``, ``CREATED``, and ``SIZE`` fields in the ``docker images`` output will likely be different.

In the case of the ``1.0.0`` tag, your ``REPOSITORY`` and ``TAG`` columns should match up with the above list.

It is recommended to verify the authenticity of the downloaded images before running Dioptra. Please see :doc:`../how-to/verify-container-images` for more information. 