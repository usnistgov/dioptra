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

.. _getting-started-examples:

Examples
========

There are multiple examples_ available for Dioptra that demonstrate its capabilities across different models, datasets, adversarial attacks, and adversarial defenses.
Here you will find instructions on how to prepare your environment for running an example and a table that lists what is available.

.. _examples: https://github.com/usnistgov/dioptra/blob/main/examples

Setup
-----

To prepare your environment for running the examples_, follow the linked instructions below:

1. :ref:`Clone the repository and build the included containers <getting-started-building-the-containers>`
2. :ref:`Apply the provided cookiecutter template and run Dioptra <getting-started-running-dioptra>`
3. :ref:`Create and activate the Python virtual environment for the Dioptra examples and download the datasets using the download_data.py script <getting-started-acquiring-datasets-using-the-download-script>`
4. `Edit the docker-compose.yml file to mount the data folder in the worker containers. <https://github.com/usnistgov/dioptra/blob/main/examples/README.md#mounting-the-data-folder-in-the-worker-containers>`_
5. :ref:`Initialize and start Dioptra <getting-started-running-dioptra-init-deployment>`
6. `Register the custom task plugins for Dioptra's examples and demos <https://github.com/usnistgov/dioptra/blob/main/examples/README.md#registering-custom-task-plugins>`_
7. `Register the queues for Dioptra's examples and demos <https://github.com/usnistgov/dioptra/blob/main/examples/README.md#registering-queues>`_
8. `Start JupyterLab and open the demo Jupyter notebook (ipynb file extension) <https://github.com/usnistgov/dioptra/blob/main/examples/README.md#starting-jupyter-lab>`_

Steps 1–3 and 6–7 only need to be run once.
Returning users only need to repeat Steps 4 (if you stopped Dioptra using ``docker compose down``) and 8 (if you stopped the ``jupyter lab`` process).

List of Examples
----------------

The current list of examples_ for Dioptra is provided in the table below.
It is recommended that newcomers start with the `Tensorflow MNIST Classifier`_ example.

.. _Tensorflow MNIST Classifier: https://github.com/usnistgov/dioptra/tree/main/examples/tensorflow-mnist-classifier

.. list-table::
   :widths: 15 15 20 20 25 25 20
   :header-rows: 1

   * - Name
     - Library
     - Models
     - Dataset
     - Attacks
     - Defenses
     - GPU
   * - `Tensorflow MNIST Classifier`_
     - Tensorflow
     - | ShallowNet,
       | LeNet
     - :term:`MNIST`
     - :term:`FGM`
     -
     - No
   * - `Tensorflow MNIST Pixel Threshold <https://github.com/usnistgov/dioptra/tree/main/examples/tensorflow-mnist-pixel-threshold>`_
     - Tensorflow
     - | ShallowNet,
       | LeNet
     - :term:`MNIST`
     - Pixel Threshold
     -
     - No
   * - `Tensorflow MNIST Model Inversion <https://github.com/usnistgov/dioptra/tree/main/examples/tensorflow-mnist-model-inversion>`_
     - Tensorflow
     - | ShallowNet,
       | LeNet
     - :term:`MNIST`
     - Model Inversion
     -
     - No
   * - `Tensorflow MNIST Feature Squeezing <https://github.com/usnistgov/dioptra/tree/main/examples/tensorflow-mnist-feature-squeezing>`_
     - Tensorflow
     - | ShallowNet,
       | LeNet
     - :term:`MNIST`
     - | :term:`FGM`,
       | Feature Squeezing,
       | :term:`CW`,
       | Deepfool,
       | :term:`JSMA`
     -
     - No
   * - `Tensorflow Backdoor Poisoning <https://github.com/usnistgov/dioptra/tree/main/examples/tensorflow-backdoor-poisoning>`_
     - Tensorflow
     - LeNet
     - :term:`MNIST`
     - Backdoor Poisoning
     - | Spatial Smoothing,
       | JPEG Compression,
       | Gaussian Augmentation
     - No
   * - `PyTorch MNIST Membership Inference <https://github.com/usnistgov/dioptra/tree/main/examples/pytorch-mnist-membership-inference>`_
     - PyTorch
     - LeNet
     - :term:`MNIST`
     - Membership Inference
     -
     - No
   * - `Tensorflow ImageNet ResNet50 Demo <https://github.com/usnistgov/dioptra/tree/main/examples/tensorflow-imagenet-resnet50-fgm>`_
     - Tensorflow
     - ResNet50
     - ImageNet
     - | :term:`FGM`,
       | Pixel Threshold
     - | *(FGM only)*
       | Spatial Smoothing,
       | JPEG Compression,
       | Gaussian Augmentation
     - Yes
   * - `Tensorflow Adversarial Patch Demo <https://github.com/usnistgov/dioptra/tree/main/examples/tensorflow-adversarial-patches>`_
     - Tensorflow
     - | LeNet *(MNIST)*,
       | VGG16 *(Fruits 360)*,
       | ResNet50 *(ImageNet)*
     - | :term:`MNIST`,
       | Fruits 360,
       | ImageNet
     - Adversarial Patch
     - | Spatial Smoothing,
       | JPEG Compression,
       | Gaussian Augmentation,
       | Adversarial Training
     - | Yes
       | *(Fruits 360, ImageNet only)*
   * - `PyTorch Detectron2 Demo <https://github.com/usnistgov/dioptra/tree/main/examples/pytorch-detectron2-demo>`_
     - PyTorch
     - RetinaNet
     - Road Signs
     - Backdoor Poisoning
     -
     - Yes
