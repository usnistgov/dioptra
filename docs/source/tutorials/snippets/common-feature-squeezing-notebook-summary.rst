.. NOTICE
..
.. This software (or technical data) was produced for the U. S. Government under
.. contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
.. 52.227-14, Alt. IV (DEC 2007)
..
.. © 2021 The MITRE Corporation.

From here, you will follow the provided instructions to run the demo provided in the Jupyter notebook.
Running the first 6 blocks will set up the the environment.
Running block 7 will generate a new le_net model for classifying mnist images.
Similarly, running block 8 will initializes Tensorflow's pre-loaded weights for a mobilenet model that will be used to classify imagenet images.

Once the models are initialized and the environment is configured, you will be able to run the rest of the demo.
The demo is organized into pairs of pipelines, each pair representing a different evasion adversarial image generation attack.
Each block has a description explaining what steps it is performing and which parameters may be tuned.
Generally speaking, each pair contains an pipeline representing an undefended attack, followed by a pipeline that performs feature squeezing to attempt to defend against the adversarial technique employed in the previous block.
