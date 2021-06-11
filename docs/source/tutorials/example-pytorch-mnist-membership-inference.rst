.. _tutorials-example-pytorch-mnist-membership-inference:

PyTorch MNIST Membership Inference
==================================

The demo provided in the Jupyter notebook ``demo.ipynb`` uses Dioptra to run experiments that investigate the membership inference attack when launched on a neural network model trained on the MNIST dataset.

Using this Demo
---------------

The steps for getting your environment ready to run this demo depend on whether you intend to run the demo locally (i.e. on your personal computer) or on an existing on-prem deployment.
Navigate to the tab below that best describes your setup in order to proceed.

.. tabbed:: Local

   .. include:: snippets/common-local-setup-instructions.rst

   The startup sequence will take more time to finish the first time you use this demo, as you will need to download the MNIST dataset, initialize the Testbed API database, and synchronize the task plugins to the S3 storage.

   .. include:: snippets/common-setup-instructions.rst

   Before doing anything else, ensure that the first 4 code blocks are configured for your local environment. your deployment of the testbed architecture.

   If you are running the demos locally and want to watch the output logs for the PyTorch worker containers as you step through the demo, run ``docker-compose logs -f pytorchcpu-01 pytorchcpu-02`` in your terminal.

   .. include:: snippets/common-membership-inference-notebook-summary.rst

   .. include:: snippets/common-teardown-instructions.rst

   If you were watching the output logs, you will need to press :kbd:`Ctrl-C` to stop following the logs before you can run ``make teardown``.

.. tabbed:: On-Prem Deployment

   To run the demo on an on-prem deployment, all you need to do is download and start the **jupyter** service defined in this example's ``docker-compose.yml`` file.
   Open a terminal and navigate to this example's directory and run the **jupyter** startup sequence,

   .. code-block:: sh

      make jupyter

   .. include:: snippets/common-setup-instructions.rst

   Before doing anything else, ensure that the first 4 code blocks are configured for interacting with your on-prem deployment of the testbed architecture.

   .. include:: snippets/common-membership-inference-notebook-summary.rst

   .. include:: snippets/common-teardown-instructions.rst

Attacks
-------

Membership Inference is an attack which attempts to classify items as either part of the training set or not.
It does this by training a model on training and testing data, and the model's outputs for both of them, and then attempts to classify new data based on the original model's classification of that data.

The membership inference attack does not have specific parameters, as the main variable is the model used to classify the data as "training" or "testing".
The input to this attack is a full model which classifies an image as part of the training set or not, written for PyTorch.

Viewing Results
---------------

The result of this example is simply the accuracy of the model that is trained to determine whether an image was part of the original training set.
