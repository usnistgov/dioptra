# Tensorflow Backdoor Poisoning Demos

> [!CAUTION]
> **DEPRECATED**
>
> This example is obsolete and will not work with the v1.0.0 release of Dioptra. It is
> retained for reference only. It may be ported to work with v1.0.0 in the future.

This demo provides three different versions of a backdoor poisoning attack with image preprocessing defense.
The three available ipython demos explore the following poisoning attacks:

-   `demo-mnist-poison-backdoor-baseline.ipynb`: Basic backdoor poisoning via training data mislabeling.
-   `demo-mnist-poison-backdoor-adv-embedding.ipynb`: Model backdoor poisoning using the adversarial embedding technique to add a secondary backdoor training objective to the model.
-   `demo-mnist-poison-backdoor-clean-label.ipynb`: Advanced backdoor poisoning using a clean label technique to generate hidden poisons from a proxy model.

Users are welcome to run the demos in any order.
Please note that the clean label backdoor attack takes the longest time to complete.
For more information regarding attack and defense parameters, please see the attack and defense sections of the [MLflow Entrypoint Overview](#MLflow-Entrypoint-Overview) section.

Each of these attacks also explore the following preprocessing defenses from their associated defense entry points:

-   Spatial Smoothing: Smooths out an image by passing a median filter through neighboring pixel values in images.
-   Gaussian Augmentation: Adds gaussian noise to an image.
-   JPEG Compression: Applies an image compression algorithm over the image.

## Running the example

To prepare your environment for running this example, follow the linked instructions below:

1.  [Create and activate a Python virtual environment and install the necessary dependencies](../README.md#creating-a-virtual-environment)
2.  [Download the MNIST dataset using the download_data.py script.](../README.md#downloading-datasets)
3.  [Follow the links in these User Setup instructions](../../README.md#user-setup) to do the following:
    -   Build the containers
    -   Use the cookiecutter template to generate the scripts, configuration files, and Docker Compose files you will need to run Dioptra
4.  [Edit the docker-compose.yml file to mount the data folder in the worker containers](../README.md#mounting-the-data-folder-in-the-worker-containers)
5.  [Initialize and start Dioptra](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html#initializing-the-deployment)
6.  [Register the custom task plugins for Dioptra's examples and demos](../README.md#registering-custom-task-plugins)
7.  [Register the queues for Dioptra's examples and demos](../README.md#registering-queues)
8.  [Start JupyterLab and open `demo.ipynb`](../README.md#starting-jupyter-lab)

Steps 1–4 and 6–7 only need to be run once.
**Returning users only need to repeat Steps 5 (if you stopped Dioptra using `docker compose down`) and 8 (if you stopped the `jupyter lab` process)**.
## MLflow Entrypoint Overview

The available MLflow entry points used by the poisoning demos and their associated parameters can be viewed inside of the `src/Mlproject` file.
