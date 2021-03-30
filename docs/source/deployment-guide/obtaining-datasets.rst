.. _deployment-guide-obtaining-datasets:

How to Obtain Common Datasets
=============================

This guide provides instructions on how to obtain common datasets to use for an on-premises deployment.

Kaggle Datasets
---------------

Kaggle_ is a website and a company that provides a platform for hosting data science competitions and publishing public datasets.
We recommend using their API to help with automating the download of any datasets from the site for an on-premises deployment.
In order to run all of the examples distributed with the Securing AI Testbed, you will need to download the following datasets and challenges from Kaggle_:

-  **Fruits360 Classification Dataset:** https://www.kaggle.com/moltean/fruits
-  **ImageNet Classification Challenge:** https://www.kaggle.com/c/imagenet-object-localization-challenge/data

.. _Kaggle: https://www.kaggle.com

Setup
~~~~~

Register an account with Kaggle at https://www.kaggle.com/ so that you can access their content.
Next, install the Python ``kaggle`` package so that you can use Python to access the API,

.. tabbed:: Pip

   .. code-block:: sh

      # User-level install
      python -m pip install --user kaggle

.. tabbed:: Conda + Pip

   .. code-block:: sh

      # Conda virtual environment install
      conda create -n kaggle python=3 pip
      conda activate kaggle
      python -m pip install kaggle

Finally, you will need to generate a Kaggle API Token for authentication purposes by following these steps,

#. From your Kaggle account page go to ``Account`` settings (upper right corner of Kaggle site after login)
#. Navigate to the ``API`` section and click on the **Create New API Token** button to generate an API token and download it as a ``kaggle.json`` file
#. Create a ``~/.kaggle`` folder in your home directory if it does not already exist and move the ``kaggle.json`` file you downloaded into the ``~/.kaggle`` directory
#. Restrict the access permissions for the ``kaggle.json`` file by running ``chmod 600 ~/.kaggle/kaggle.json``.

Data Download Script
~~~~~~~~~~~~~~~~~~~~

In your terminal, navigate to the root directory where you plan to store the datasets.
This should be a storage device that can be mounted inside a Docker container, such as an NFS share with plenty of storage space available.
Then, from that directory, run the following bash script to download the data.

.. code-block:: bash

    #!/bin/bash

    # Define parameters
    target_install_data_dir=$(pwd)/kaggle_datasets
    fruits360_data_dir=${target_install_data_dir}/Fruits360-Kaggle-2019
    imagenet_data_dir=${target_install_data_dir}/ImageNet-Kaggle-2017

    # Create the dataset directories
    echo "Creating fruits360 data dir: ${fruits360_data_dir}"
    echo "Creating imagenet data dir: ${imagenet_data_dir}"
    mkdir -p ${fruits360_data_dir} ${imagenet_data_dir}

    # Download the Fruits360 dataset
    cd ${fruits360_data_dir}
    kaggle datasets download -d moltean/fruits
    unzip fruits.zip
    rm fruits.zip

    # Download the ImageNet dataset
    cd ${imagenet_data_dir}
    kaggle competitions download -c imagenet-object-localization-challenge
    unzip imagenet-object-localization-challenge.zip
    tar -xzf imagenet_object_localization_patched2019.tar.gz
    rm imagenet-object-localization-challenge.zip
    rm imagenet_object_localization_patched2019.tar.gz
