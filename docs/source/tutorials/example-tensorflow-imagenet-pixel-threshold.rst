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
