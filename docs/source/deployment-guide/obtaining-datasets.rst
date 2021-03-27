.. _deployment-guide-obtaining-datasets:

How to Obtain Common Datasets: Fruits360, and ImageNet
=========================================================

Welcome! This tutorial will show you how to use the Kaggle API to
download datasets into your own personalized data repo.

Kaggle Setup:
-------------

To begin, please register an account with Kaggle:
https://www.kaggle.com/

This will allow you to join and access the following datasets and
challenges:

-  Fruits360 Classification Dataset :
   https://www.kaggle.com/moltean/fruits

-  ImageNet Classification Challenge :
   https://www.kaggle.com/c/imagenet-object-localization-challenge/data

You will also need to setup the Kaggle API via python pip install:

::

       pip3 install kaggle

If you are planning on running this notebook to download the dataset,
please ensure that the above instruction is completed within the
jupyther notebook environment.

Conda environment pip install
-----------------------------

If you are running the notebook within a local conda environment ex.
``conda-env-dataset-setup`` run the following commands to install Kaggle
within the conda environment:

::

       conda activate <conda_env_name>
       conda install pip3
       ~/.conda/envs/<conda_env_name>/bin/pip install kaggle

Downloading Kaggle JSON key:
----------------------------

Once you have login access to Kaggle and downloaded the Kaggle API
please follow the steps below to set your Kaggle user account:

-  From the Kaggle account page go to ``Account`` setings (upper right
   corner of Kaggle site after login.
-  Go to the ``API`` section and click on the ``Create New API Token``
   button to download a ``kaggle.json`` folder.
-  From your home directory create a ``.kaggle`` folder if it does not
   already exist.
-  Move the ``kaggle.json`` folder into ``.kaggle``.
-  Finally set the permissions of the ``kaggle.json`` file by running
   ``chmod 600 ~/.kaggle/kaggle.json``.

Downloading Kaggle Datasets
---------------------------

Next we will download the Kaggle datasets to a target directory and
unpack the files.

Please update the ``target_install_data_dir`` variable as needed to
change the data directory for the kaggle files.

Note that most of the examples will assume that the dataset has been
mounted in\ ``/nfs/data/`` in an s3 storage container.

Please keep track of the dataset storage location to link the data
directory to the appropriate location when launching the Secure AI
services.

.. code:: ipython3

    import os

    # Specify full storage path and dataset folder names here:
    target_install_data_dir = './kaggle_datasets/'
    fruits360_subdir = 'Fruits360-Kaggle-2019'
    imagenet_subdir = 'ImageNet-Kaggle-2017'


    fruits360_data_dir = os.path.abspath(target_install_data_dir + '/' + fruits360_subdir)
    imagenet_data_dir = os.path.abspath(target_install_data_dir + '/' + imagenet_subdir)


.. code:: bash

    %%bash -s "$fruits360_data_dir" "$imagenet_data_dir"
    echo "Creating fruits360 data dir: $1"
    echo "Creating imagenet data dir: $2"
    mkdir -p $1 $2

.. code:: bash

    %%bash -s "$fruits360_data_dir" "$imagenet_data_dir"
    cd $1
    kaggle datasets download -d moltean/fruits
    unzip fruits.zip
    rm fruits.zip

    cd $2
    kaggle competitions download -c imagenet-object-localization-challenge
    unzip imagenet-object-localization-challenge.zip
    tar -xvzf imagenet_object_localization_patched2019.tar.gz
    rm imagenet-object-localization-challenge.zip
    rm imagenet_object_localization_patched2019.tar.gz


.. parsed-literal::

    IOPub data rate exceeded.
    The notebook server will temporarily stop sending output
    to the client in order to avoid crashing it.
    To change this limit, set the config variable
    `--NotebookApp.iopub_data_rate_limit`.

    Current values:
    NotebookApp.iopub_data_rate_limit=1000000.0 (bytes/sec)
    NotebookApp.rate_limit_window=3.0 (secs)

    100%|██████████| 760M/760M [00:09<00:00, 79.7MB/s]
    100%|██████████| 155G/155G [46:00<00:00, 60.2MB/s]
