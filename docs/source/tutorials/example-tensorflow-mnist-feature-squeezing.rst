.. _tutorials-example-tensorflow-mnist-feature-squeezing:

Example: MNIST Tensorflow Feature Squeezing
===========================================

Introduction
------------

.. warning::

   Some of the attacks in this demo, *deepfool* and *CW* in particular, are computationally expensive and will take a very long to complete if run using the CPUs found in a typical personal computer.
   For this reason, it is highly recommended that you run these demos on a CUDA-compatible GPU.

The demo provided in the Jupyter notebook ``demo_production.ipynb`` uses the Securing AI Testbed to run experiments that investigate the effectiveness of the feature-squeezing defense against a series of evasion attacks against a neural network model.

Using this Demo
---------------

The steps for getting your environment ready to run this demo depend on whether you intend to run the demo locally (i.e. on your personal computer) or on an existing on-prem deployment.
Navigate to the tab below that best describes your setup in order to proceed.

.. tabbed:: Local

   Everything you need to run this demo locally is packaged into a set of Docker images that you can obtain by opening a terminal, navigating to the root directory of the repository, and running `make pull-latest`.
   Once you have downloaded the images, stay in the terminal and navigate to this example's directory and run the demo startup sequence,

   .. code-block:: sh

      make demo

   The startup sequence will take more time to finish the first time you use this demo, as you will need to download the MNIST dataset, initialize the Testbed API database, and synchronize the task plugins to the S3 storage.

   .. include:: snippets/common-setup-instructions.rst

   If you are running the demos locally and want to watch the output logs for the Tensorflow worker containers as you step through the demo, run `docker-compose logs -f tfcpu-01 tfcpu-02` in your terminal.

   .. include:: snippets/common-feature-squeezing-notebook-summary.rst

   .. include:: snippets/common-teardown-instructions.rst
   If you were watching the output logs, you will need to press :kbd:`Ctrl-C` to stop following the logs before you can run ``make teardown``.

.. tabbed:: On-Prem Deployment

   To run the demo on an on-prem deployment, all you need to do is download and start the **jupyter** service defined in this example's ``docker-compose.yml`` file.
   Open a terminal and navigate to this example's directory and run the **jupyter** startup sequence,

   .. code-block:: sh

      make jupyter

   .. include:: snippets/common-setup-instructions.rst
   If necessary, also change the queue variable from ``tensorflow_gpu`` to the appropriate queue name registered in your on-prem deployment.
   If you are unsure which queue you should be submitting jobs to, contact your Testbed system administrator.

   .. include:: snippets/common-feature-squeezing-notebook-summary.rst

   .. include:: snippets/common-teardown-instructions.rst

Attacks
-------

This demo includes a series of adversarial image generation techniques to test the feature squeezing defense against.
The parameters for each attack are listed below, along with a link to the paper describing each attack.
These parameters will help you to tune your attacks.

Carlini Wagner (L2 Distance Metric)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Paper:** https://arxiv.org/abs/1608.04644

--confidence float         Confidence of adversarial examples: a higher value produces examples that are farther away, from the original input, but classified with higher confidence as the target class. [default: 0.01]
--learning_rate float      The initial learning rate for the attack algorithm. Smaller values produce better results but are slower to converge. [default: 0.01]
--binary_search_steps int  Number of times to adjust constant with binary search (positive value). If binary_search_steps is large, then the algorithm is not very sensitive to the value of initial_const. [default: 10]
--max_iter int             Maximum number of iterations. Increasing this may increase attack success rate but has a computational cost. [default: 10]
--initial_const float      The initial trade-off constant c to use to tune the relative importance of distance and confidence. If ``binary_search_steps`` is large, the initial constant is not important. [default: 0.01]
--max_halving int          Maximum number of halving steps in the line search optimization. [default: 5]
--max_doubling int         Maximum number of doubling steps in the line search optimization. [default: 5]

Carlini Wagner (Linf Distance Metric)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Paper:** https://arxiv.org/abs/1608.04644

--confidence float     Confidence of adversarial examples: a higher value produces examples that are farther away, from the original input, but classified with higher confidence as the target class. [default: 0.01]
--learning_rate float  The initial learning rate for the attack algorithm. Smaller values produce better results but are slower to converge. [default: 0.01]
--max_iter int         Maximum number of iterations. Increasing this may increase attack success rate but has a computational cost. [default: 10]
--max_halving int      Maximum number of halving steps in the line search optimization. [default: 5]
--max_doubling int     Maximum number of doubling steps in the line search optimization. [default: 5]
--eps float            An upper bound for the L_0 norm of the adversarial perturbation. [default: 0.3]

Jacobian Saliency Map Attack
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Paper:** https://arxiv.org/abs/1511.07528

--theta float  Amount of Perturbation introduced to each modified feature per step (can be positive or negative). [default: 0.1]
--gamma float  Maximum fraction of features being perturbed (between 0 and 1). [default: 1.0]

Fast Gradient Method
^^^^^^^^^^^^^^^^^^^^

**Paper:** https://arxiv.org/abs/1412.6572

--eps float            Attack step size. [default: 0.3]
--eps_step float       Step size of input variation for minimal perturbation computation. [default: 0.1]
--targeted bool        Indicates whether the attack is targeted (True) or untargeted (False). [default: False]
--num_random_init int  Number of random initializations within the epsilon ball. For ``random_init=0`` starting at the original input. [default: 0]
--minimal bool         Indicates if computing the minimal perturbation (True). If True, also define eps_step for the step size and eps for the maximum perturbation. [default: False]

Deepfool
^^^^^^^^

**Paper:** https://arxiv.org/abs/1511.04599

--max_iter int   Maximum number of iterations. [default: 100]
--epsilon float  Overshoot parameter. [default: 0.00001]
--nb_grads int   Number of class gradients to compute. [default: 10]

Defense
-------

This demo implements a portion of the feature squeezing defense described in the paper found here: https://arxiv.org/abs/1704.01155.
``feature_squeezing.py`` applies the color-depth squeezing defense in order to attempt to reduce the feature space of images shown to the classifier.
In the case of color images, this defense is applied uniformly across each color channel.
For example, setting the bit-depth to 2 on an RGB image will set the max color depth of Red, Blue, and Green all to 2.

--bit-depth int  An integer between 1-8 that defines the color depth of the squeezed image. [default: 8]

Viewing Results and Downloading Images
--------------------------------------

Results for each run may be viewed through the MLFlow dashboard, by default located at http://localhost:35000 (your own deployment may have mlflow in a different location, contact your system administrator for more information).
To view your experiment runs, first navigate to your own experiment on the left hand side of the screen (If you've followed this readme up to now, it should be named ``{user_id}_feature_squeeze``).
Jobs will be listed at the center of the screen.
If you wish to download sample images, you can get them by doing the following:

#. Select a job representing either an attack or defense (e.g. ``tmpw7vlt3g1:cw_inf`` or ``tmpo8milqlo:feature_squeeze``)
#. Navigate to the bottom of the page, to the "Artifacts" section
#. Select the file you wish to download (in this case, testing_adversarial.tar.gz)
#. Click the download icon on the top right corner of the Artifacts box.
