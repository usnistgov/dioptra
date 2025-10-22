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

.. how-to-add-a-dataset:

How-To: Add a Dataset to a Dioptra Deployment
=============================================

.. include:: /_glossary_note.rst

To make data or other resources available to your experiments, they must be placed in a location accessible to your workers.

Dataset Placement
-----------------

.. highlight:: text

The datasets should be downloaded and organized in the same directory on the host machine that is running Dioptra.
This folder can be stored anywhere on your host machine's filesystem (:ref:`this folder will then need to be mounted into the worker containers <running-dioptra-mounting-folders-in-the-worker-containers>`).
For the sake of this documentation, we assume that the datasets are stored in the ``/dioptra/data`` directory so that it matches with the filepath also used in the examples.

To use the aforementioned datasets with the Dioptra examples, they will need to be organized in the ``/dioptra/data`` folder in a specific way, which the `download_data.py <https://github.com/usnistgov/dioptra/blob/main/examples/scripts/download_data.py>`_ script will handle automatically for you.

.. _getting-started-acquiring-datasets-using-the-download-script:

Using the Download Script
-------------------------

Dioptra provides the `examples/scripts/download_data.py <https://github.com/usnistgov/dioptra/blob/main/examples/scripts/download_data.py>`_ script to simplify the download and organization of these datasets. This script uses `tensorflow_datasets (tfds) <https://www.tensorflow.org/datasets/api_docs/python/tfds>`_ as source of open source datasets and to download and prepare the data for use.

.. important::
   The provided download_data.py is not the only way to acquire datasets for use in Dioptra.
   It is simply a convenient tool to access a wide variety of publicly available datasets.

To list the available datasets, run:
.. code-block:: sh
   uv run ./examples/scripts/download_data.py list
.. code-block:: sh

Then, to run download a dataset directly to the ``/dioptra/data`` directory, run:
.. code-block:: sh
   uv run ./examples/scripts/download_data.py --data-dir /dioptra/data download DATASET_NAME
.. code-block:: sh

For the full list of options, run ``uv run ./examples/scripts/download_data.py -h`` to display the script's help message.
