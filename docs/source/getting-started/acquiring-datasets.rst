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

.. _getting-started-acquiring-datasets:

Downloading Datasets
====================

.. include:: /_glossary_note.rst

When running any of the examples or custom experiments, it will be necessary to acquire datasets for training.
A list of datasets used in the examples is presented below, along with instructions on how to use our `download_data.py <https://github.com/usnistgov/dioptra/blob/main/examples/scripts/download_data.py>`_ CLI tool to acquire them.

Datasets
--------

* MNIST Handwritten Digit Dataset
    * https://www.kaggle.com/datasets/hojjatk/mnist-dataset
    * http://yann.lecun.com/exdb/mnist/

* Fruits360
    * https://github.com/Horea94/Fruit-Images-Dataset
    * https://www.kaggle.com/code/vneogi199/fruits360/input

* ImageNet
    * https://image-net.org/download-images
    * https://www.kaggle.com/competitions/imagenet-object-localization-challenge/data

* Road Signs
    * https://www.kaggle.com/datasets/andrewmvd/road-sign-detection

Kaggle Datasets
---------------

When downloading Kaggle Datasets either through the custom scripts Dioptra provides or through the browser interface, users will need to sign in to Kaggle, and also agree to the rules of the competition, even if the competition has finished.

Furthermore, users of the CLI tool will need to setup a Kaggle API token to be able to access some of these datasets.
More information on the Kaggle API tokens can be found here: https://www.kaggle.com/docs/api.

Dataset Placement
-----------------

.. highlight:: text

The datasets should be downloaded and organized in the same directory on the host machine that is running Dioptra.
This folder can be stored anywhere on your host machine's filesystem (:ref:`this folder will then need to be mounted into the worker containers <running-dioptra-mounting-folders-in-the-worker-containers>`).
For the sake of this documentation, we assume that the datasets are stored in the ``/dioptra/data`` directory so that it matches with the filepath also used in the examples.

To use the aforementioned datasets with the Dioptra examples, they will need to be organized in the ``/dioptra/data`` folder in a specific way, which the `download_data.py <https://github.com/usnistgov/dioptra/blob/main/examples/scripts/download_data.py>`_ script will handle automatically for you.
The required directory structure for each of the datasets is described below.

For MNIST, the data needs to be in this format::

    dioptra/
    └── data/
        └── Mnist/
            ├── training/
            │   ├── 0/
            │   │   ├── 00002.png
            │   │   ├── 00005.png
            │   │   ...
            │   ├── 1/
            │   ├── 2/
            │   ...
            └── testing/
                ├── 0/
                │   ├── 00001.png
                │   ├── 00021.png
                │   ...
                ├── 1/
                ├── 2/
                ...

For Fruits360, the data needs to be in this format::

    dioptra/
    └── data/
        └── Fruits360/
            ├── training/
            │   ├── Apple Braeburn/
            │   │   ├── 0_100.png
            │   │   ├── 1_100.png
            │   │   ...
            │   ├── Apple Crimson Snow/
            │   ├── Apple Golden 1/
            │   ...
            └── testing/
                ├── Apple Braeburn/
                │   ├── 3_100.png
                │   ├── 4_100.png
                │   ...
                ├── Apple Crimson Snow/
                ├── Apple Golden 1/
                ...

For ImageNet, the data needs to be in this format::

    dioptra/
    └── data/
        └── ImageNet-Kaggle/
            ├── metadata/
            │   ├── image_sets/
            │   └── synset_mapping.txt
            ├── training/
            │   ├── annotations/
            │   │   ├── n01440764/
            │   │   │   ├── n01440764_10040.xml
            │   │   │   ├── n01440764_10048.xml
            │   │   │   ...
            │   │   ├── n01443537/
            │   │   ...
            │   └── images/
            │       ├── n01440764/
            │       │   ├── n01440764_10040.JPEG
            │       │   ├── n01440764_10048.JPEG
            │       │   ...
            │       ├── n01443537/
            │       ...
            └── testing/
                ├── annotations/
                │   ├── n01440764/
                │   │   ├── n01440764_10030.xml
                │   │   ├── n01440764_10031.xml
                │   │   ...
                │   ├── n01443537/
                │   ...
                └── images/
                    ├── n01440764/
                    │   ├── n01440764_10030.JPEG
                    │   ├── n01440764_10031.JPEG
                    │   ...
                    ├── n01443537/
                    ...

Please note that the testing folder in the above tree structure is actually the ``val/`` folder in the dataset on Kaggle, as the actual testing set does not come with labels.

For the Road Signs Detection dataset, the data needs to be in this format::

    dioptra/
    └── data/
        └── Road-Sign-Detection-v2/
            ├── training/
            │   ├── annotations/
            │   │   ├── 00000_road2.xml
            │   │   ├── 00000_road3.xml
            │   │   ...
            │   └── images/
            │       ├── 00000_road2.png
            │       ├── 00000_road3.png
            │       ...
            └── testing/
                ├── annotations/
                │   ├── 00000_road0.xml
                │   ├── 00000_road1.xml
                │   ...
                └── images/
                    ├── 00000_road0.png
                    ├── 00000_road1.png
                    ...

.. _getting-started-acquiring-datasets-using-the-download-script:

Using the Download Script
-------------------------

Dioptra provides the `examples/scripts/download_data.py <https://github.com/usnistgov/dioptra/blob/main/examples/scripts/download_data.py>`_ script to simplify the download and organization of these datasets.
To get started, it is recommended that you create a virtual environment to manage the script's dependencies.
Open a terminal, clone the repository, navigate into the ``dioptra`` folder, then run the following:

.. code-block:: sh

   # Move into the examples folder of cloned repo
   cd ./examples

   # Create a new virtual environment at ./examples/.venv
   python -m venv .venv

   # Activate the virtual environment
   source .venv/bin/activate

   # Install the dependencies
   python -m pip install -r ./scripts/venvs/examples-setup-requirements.txt

Then, to run this script and download a dataset directly to the ``/dioptra/data`` directory, simply use the following:

.. code-block:: sh

   python ./scripts/download_data.py --output /dioptra/data DATASET_NAME

For the full list of options and available datasets, run ``python ./scripts/download_data.py -h`` to display the script's help message::

    Usage: download_data.py [OPTIONS] COMMAND [ARGS]...

      Fetch a dataset used in Dioptra's examples and demos.

    Options:
      --output DIRECTORY            The path to the folder where the example
                                    datasets are stored. Defaults to the current
                                    working directory.
      --overwrite / --no-overwrite  Fetch the data even if the target folder
                                    already exists and overwrite any existing data
                                    files. By default the program will exit early
                                    if the target folder already exists.
      -h, --help                    Show this message and exit.

    Commands:
      fruits360  Fetch the Fruits 360 dataset hosted on Kaggle.
      imagenet   Fetch the ImageNet Object Localization Challenge dataset...
      mnist      Fetch the MNIST dataset.
      roadsigns  Fetch the Road Signs Detection dataset hosted on Kaggle.

Please note that some of the datasets have additional options that can be viewed by running ``python ./scripts/download_data.py DATASET -h``.
For example, running ``python ./scripts/download_data.py fruits360 -h`` displays the help message for the Fruits 360 dataset shown below::

    Usage: download_data.py fruits360 [OPTIONS]

      Fetch the Fruits 360 dataset hosted on Kaggle.

      This downloader uses the Kaggle API and requires the use of an API token.
      For instructions on how to obtain and use a Kaggle API token, see
      https://github.com/Kaggle/kaggle-api#api-credentials.

    Options:
      --remove-zip / --no-remove-zip  Remove/keep the dataset zip file after
                                      extracting it. By default it will be
                                      removed.
      -h, --help                      Show this message and exit.

Some example usages are shown below.

Example usage: MNIST
~~~~~~~~~~~~~~~~~~~~

.. code-block:: sh

   python ./scripts/download_data.py --output /dioptra/data --overwrite mnist

Downloads the MNIST dataset to ``/dioptra/data/Mnist``, overwriting an existing dataset at that location if it exists.

Example usage: Fruits360
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: sh

   python ./scripts/download_data.py --output /dioptra/data --no-overwrite fruits360 --no-remove-zip

Downloads the Fruits360 dataset to ``/dioptra/data/Fruits360``, without overwriting an existing dataset at that location if it exists.

.. important::

   If you receive a 403 error when downloading the Fruits360 dataset, it is likely that you need to accept the rules of the competition for the dataset you are downloading on the Kaggle website.

Example usage: ImageNet
~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

   The ImageNet downloader is currently under construction and does not yet function as described here.

.. code-block:: sh

   python ./scripts/download_data.py --output /dioptra/data --overwrite imagenet --remove-zip

Downloads the ImageNet dataset to ``/dioptra/data/ImageNet-Kaggle``, overwriting the existing dataset at that location, and removing the zip file downloaded in the process.

.. important::

   If you receive a 403 error when downloading the ImageNet dataset, it is likely that you need to accept the rules of the competition for the dataset you are downloading on the Kaggle website.

Example usage: Road Signs
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: sh

   python ./scripts/download_data.py --output /dioptra/data --overwrite roadsigns --no-remove-zip

Downloads the Road Signs dataset to ``/dioptra/data/Road-Signs-Detection-v2``, overwriting the existing dataset at that location, but leaving the zip file downloaded in the process.

.. important::

   If you receive a 403 error when downloading the Road Signs dataset, it is likely that you need to accept the rules of the competition for the dataset you are downloading on the Kaggle website.
