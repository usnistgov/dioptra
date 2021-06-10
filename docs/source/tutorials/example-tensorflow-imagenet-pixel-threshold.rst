.. NOTICE
..
.. This software (or technical data) was produced for the U. S. Government under
.. contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
.. 52.227-14, Alt. IV (DEC 2007)
..
.. © 2021 The MITRE Corporation.

.. _tutorials-example-tensorflow-imagenet-pixel-threshold:

Tensorflow ImageNet Pixel Threshold
===================================

.. warning::

   This demo assumes that you have access to an on-prem deployment of Dioptra that provides a copy of the ImageNet dataset and a CUDA-compatible GPU.
   This demo cannot be run on a typical personal computer.

The demo provided in the Jupyter notebook ``demo.ipynb`` uses Dioptra to run experiments that investigate the effects of the pixel threshold attack when launched on a neural network model trained on the ImageNet dataset.

Using this Demo
---------------

To run the demo on an on-prem deployment, all you need to do is download and start the **jupyter** service defined in this example's ``docker-compose.yml`` file.
Open a terminal and navigate to this example's directory and run the **jupyter** startup sequence,

.. code-block:: sh

   make jupyter

.. include:: snippets/common-setup-instructions.rst

Before doing anything else, ensure that the first 4 code blocks are configured for interacting with your on-prem deployment of the testbed architecture.

.. include:: snippets/common-imagenet-pixel-threshold-notebook-summary.rst

.. include:: snippets/common-teardown-instructions.rst

Attacks
-------

The Pixel Threshold attack is an evasion attack which tries to deceive the classifier by changing a limited number of pixels in a test image.
It does this through differential evolution - each iteration seeks to decrease the accuracy of the model on the image while keeping changes limited to a certain threshold of pixels.
In this example it is applied to ImageNet in an attempt to get the model to misclassify images.

Pixel Threshold
^^^^^^^^^^^^^^^

**Paper:** https://arxiv.org/abs/1906.06026

--th int  The maximum number of pixels it is allowed to change.
--es int  If 0, then use the CMA-ES strategy, or if 1, use the DE strategy for evolution.

Viewing Results and Downloading Images
--------------------------------------

To view the results, under MLFlow, click the experiment associated with the attack, and scroll down.
A download will be available for ``adv_testing.tar.gz``, which will contain a transformed dataset of the input to the evasion attack.
Note that this particular attack will output the original image if it is unsuccessful in changing the classification of the image, rather than outputting a modified version.
