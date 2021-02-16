.. _tutorials-example-tensorflow-mnist-model-inversion:

Example: Tensorflow MNIST Model Inversion
=========================================

.. warning::

   The attack used in this demo is computationally expensive and will take a very long to complete if run using the CPUs found in a typical personal computer.
   For this reason, it is highly recommended that you run these demos on a CUDA-compatible GPU.

The demo provided in the Jupyter notebook ``demo.ipynb`` uses the Securing AI Testbed to run experiments that investigate the model inversion attack when launched on a neural network model trained on the MNIST dataset.

Using this Demo
---------------

The steps for getting your environment ready to run this demo depend on whether you intend to run the demo locally (i.e. on your personal computer) or on an existing on-prem deployment.
Navigate to the tab below that best describes your setup in order to proceed.

.. tabbed:: Local

   .. include:: snippets/common-local-setup-instructions.rst

   The startup sequence will take more time to finish the first time you use this demo, as you will need to download the MNIST dataset, initialize the Testbed API database, and synchronize the task plugins to the S3 storage.

   .. include:: snippets/common-setup-instructions.rst

   Before doing anything else, ensure that the first 4 code blocks are configured for your local environment.

   If you are running the demos locally and want to watch the output logs for the Tensorflow worker containers as you step through the demo, run ``docker-compose logs -f tfcpu-01 tfcpu-02`` in your terminal.

   .. include:: snippets/common-model-inversion-notebook-summary.rst

   .. include:: snippets/common-teardown-instructions.rst

   If you were watching the output logs, you will need to press :kbd:`Ctrl-C` to stop following the logs before you can run ``make teardown``.

.. tabbed:: On-Prem Deployment

   To run the demo on an on-prem deployment, all you need to do is download and start the **jupyter** service defined in this example's ``docker-compose.yml`` file.
   Open a terminal and navigate to this example's directory and run the **jupyter** startup sequence,

   .. code-block:: sh

      make jupyter

   .. include:: snippets/common-setup-instructions.rst

   Before doing anything else, ensure that the first 4 code blocks are configured for interacting with your on-prem deployment of the testbed architecture.

   .. include:: snippets/common-model-inversion-notebook-summary.rst

   .. include:: snippets/common-teardown-instructions.rst

Attacks
-------

Model Inversion (MIFACE) is an attack which attempts to discover a generic representative image of each class of the training set.
In the original paper, this was applied to facial recognition, where the attack would attempt to discover what a face looked like, given access to the model and the name of the person (where each person was their own class).
In this example, it is instead applied to MNIST handwritten data, and the attack attempts to discover a representative handwritten digit which might be considered an average of the training set's images for that class, without having access to the training set.

Model Inversion
^^^^^^^^^^^^^^^

**Paper:** https://dl.acm.org/doi/10.1145/2810103.2813677

--max_iter int         The maximum number of iterations for gradient descent.
--window_length int    The length of the window for checking whether the descent should be aborted.
--threshold float      The threshold for descent stopping criterion.
--learning_rate float  The learning rate for the gradient descent.

Viewing Results and Downloading Images
--------------------------------------

To view the results, under MLFlow, click the experiment associated with the attack, and scroll down.
A download will be available for ``testing_adversarial_miface.tar.gz``, which will contain one image per class, which is the attack's guess as to what the members of the original class would have looked like.
