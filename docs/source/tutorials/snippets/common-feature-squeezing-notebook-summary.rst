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

From here, you will follow the provided instructions to run the demo provided in the Jupyter notebook.
Running the first 6 blocks will set up the the environment.
Running block 7 will generate a new le_net model for classifying mnist images.
Similarly, running block 8 will initializes Tensorflow's pre-loaded weights for a mobilenet model that will be used to classify imagenet images.

Once the models are initialized and the environment is configured, you will be able to run the rest of the demo.
The demo is organized into pairs of pipelines, each pair representing a different evasion adversarial image generation attack.
Each block has a description explaining what steps it is performing and which parameters may be tuned.
Generally speaking, each pair contains an pipeline representing an undefended attack, followed by a pipeline that performs feature squeezing to attempt to defend against the adversarial technique employed in the previous block.
