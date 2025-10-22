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

How-To: Add a Dataset
=====================

To make datasets or other resources available when running experiments, they must be placed in a directory accessible to your workers.
This directory can be stored anywhere on your host machine's filesystem and then (:ref:`mounted into the worker containers <running-dioptra-mounting-folders-in-the-worker-containers>`).

Once the dataset directory is configured as part of the Dioptra deployment, adding data is as simple as placing the data into that directory.
Data added to the datasets directory is immediately accessible to plugin tasks by referencing the ``/dioptra/data`` location.

Dioptra provides the `examples/scripts/download_data.py <https://github.com/usnistgov/dioptra/blob/main/examples/scripts/download_data.py>`_ script to simplify the download and organization of datasets. This script uses `tensorflow_datasets (tfds) <https://www.tensorflow.org/datasets/api_docs/python/tfds>`_ as source of publicly-available datasets and to download and prepare the data for use.

.. important::
   The provided download_data.py script is not the only way to acquire datasets for use in Dioptra.
   It is simply a convenient tool to access a wide variety of publicly available datasets.

To list the available datasets, run:

.. code-block:: sh
   uv run ./examples/scripts/download_data.py list
.. code-block:: sh

Then, to download and add a dataset directly to the ``/dioptra/data`` directory, run:

.. code-block:: sh
   uv run ./examples/scripts/download_data.py --data-dir /dioptra/data download DATASET_NAME
.. code-block:: sh

For the full list of options, run ``uv run ./examples/scripts/download_data.py -h`` to display the script's help message.
