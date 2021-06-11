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

.. _tutorials-example-tensorflow-mnist-classifier:

First Steps - MNIST Tensorflow Classifier
=========================================

This demo provides a practical example that you can run on your personal computer to see how Dioptra can be used to run a simple experiment on the transferability of the fast gradient method (FGM) evasion attack between two neural network architectures.
It can be used as a basic template for crafting your own custom scripts to run within the testbed.

Getting started
---------------

Everything you need to run this demo is packaged into a set of Docker images that you can obtain by opening a terminal, navigating to the root directory of the repository, and running ``make pull-latest``.
Once you have downloaded the images, navigate to this directory using the terminal and run the demo startup sequence:

.. code-block:: sh

   make demo

The startup sequence will take more time to finish the first time you use this demo, as you will need to download the MNIST dataset, initialize the Testbed API database, and synchronize the task plugins to the S3 storage.
Once the startup process completes, open up your web browser and enter http://localhost:38888 in the address bar to access the Jupyter Lab interface (if nothing shows up, wait 10-15 more seconds and try again).
Double click the ``work`` folder and open the ``demo.ipynb`` file.
From here, follow the provided instructions to run the demo provided in the Jupyter notebook.

To watch the output logs for the Tensorflow worker containers as you step through the demo, run ``docker-compose logs -f tfcpu-01 tfcpu-02`` in your terminal.

When you are done running the demo, close the browser tab containing this Jupyter notebook and shut down the services by running ``make teardown`` on the command-line.
If you were watching the output logs, you will need to press :kbd:`Ctrl-C` to stop following the logs before you can run ``make teardown``.

.. note::

   The contents that follows is also found in the corresponding Jupyter notebook for this demo.

Setup
-----

Below we import the necessary Python modules and ensure the proper environment variables are set so that all the code blocks will work as expected,

.. code-block::

   # Import packages from the Python standard library
   import os
   import pprint
   import time
   import warnings
   from pathlib import Path
   from typing import Tuple

   # Filter out warning messages
   warnings.filterwarnings("ignore")

   # Default address for accessing the RESTful API service
   RESTAPI_ADDRESS = "http://localhost:30080"

   # Set AI_RESTAPI_URI variable if not defined, used to connect to RESTful API service
   if os.getenv("AI_RESTAPI_URI") is None:
       os.environ["AI_RESTAPI_URI"] = RESTAPI_ADDRESS

   # Default address for accessing the MLFlow Tracking server
   MLFLOW_TRACKING_URI = "http://localhost:35000"

   # Set MLFLOW_TRACKING_URI variable, used to connect to MLFlow Tracking service
   if os.getenv("MLFLOW_TRACKING_URI") is None:
       os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI

   # Path to workflows archive
   WORKFLOWS_TAR_GZ = Path("workflows.tar.gz")

   # Import third-party Python packages
   import numpy as np
   import requests
   from mlflow.tracking import MlflowClient

   # Import utils.py file
   import utils

   # Create random number generator
   rng = np.random.default_rng(54399264723942495723666216079516778448)

Dataset
-------

We obtained a copy of the MNIST dataset as part of the startup process invoked by ``make demo``.
The training and testing images for the MNIST dataset are stored within the ``data/`` directory as PNG files that are organized into the following folder structure,

::

   data
   ├── testing
   │   ├── 0
   │   ├── 1
   │   ├── 2
   │   ├── 3
   │   ├── 4
   │   ├── 5
   │   ├── 6
   │   ├── 7
   │   ├── 8
   │   └── 9
   └── training
       ├── 0
       ├── 1
       ├── 2
       ├── 3
       ├── 4
       ├── 5
       ├── 6
       ├── 7
       ├── 8
       └── 9

The subfolders under ``data/training/`` and ``data/testing/`` are the classification labels for the images in the dataset.
This folder structure is a standardized way to encode the label information and many libraries can make use of it, including the Tensorflow library that we are using for this particular demo.

Testbed microservices
---------------------

Dioptra is composed of several micro-services that are used to manage job execution, artifact storage, and logging the results of experiments.
These services all run within separate containers that were instantiated via Docker images that you either built locally or pulled into your environment from a Docker image registry.
A high-level schematic showing how all of the images connect together to form the architecture of Dioptra is provided below.

.. figure:: /images/testbed-architecture.svg

The startup process for all of these services, including database initialization and synchronizing the task plugins into the Minio S3 storage service, was handled automatically when you invoked ``make demo``.

Submit and run jobs
-------------------

The entrypoints that we will be running in this example are implemented in the Python source files under ``src/`` and the ``MLproject`` file.
To run these entrypoints within the testbed architecture, we need to package those files up into an archive and submit it to the Testbed RESTful API to create a new job.
For convenience, the ``Makefile`` provides a rule for creating the archive file for this example, just run ``make workflows``,

.. code:: bash

   %%bash

   # Create the workflows.tar.gz file
   make workflows

``make workflows`` was invoked as part of the ``make demo`` startup procedure, so unless you edited the ``MLproject`` file or one of the files under ``src/``, you will likely see a message of *make: Nothing to be done for ‘workflows’*.

To connect with the endpoint, we will use a client class defined in the ``utils.py`` file that is able to connect with the Testbed RESTful API using the HTTP protocol.
We connect using the client below, which uses the environment variable ``AI_RESTAPI_URI`` to figure out how to connect to the Testbed RESTful API,

.. code-block::

   restapi_client = utils.SecuringAIClient()

We need to register an experiment under which to collect our job runs.
The code below checks if the relevant experiment named ``"mnist"`` exists.
If it does, then it just returns info about the experiment, if it doesn’t, it then registers the new experiment.

.. code-block::

   response_experiment = restapi_client.get_experiment_by_name(name="mnist")

   if response_experiment is None or "Not Found" in response_experiment.get("message", []):
       response_experiment = restapi_client.register_experiment(name="mnist")

   response_experiment

We also need to register the name of the queue that is being watched for our jobs.
The code below checks if the relevant queue named ``"tensorflow_cpu"`` exists.
If it does, then it just returns info about the queue, if it doesn’t, it then registers the new queue.

.. code-block::

   response_queue = restapi_client.get_queue_by_name(name="tensorflow_cpu")

   if response_queue is None or "Not Found" in response_queue.get("message", []):
       response_queue = restapi_client.register_queue(name="tensorflow_cpu")

   response_queue

Next, we need to train our model.
Depending on the specs of your computer, training either the shallow net model or the LeNet-5 model on a CPU can take 10-20 minutes or longer to complete.
If you are fortunate enough to have access to a dedicated GPU, then the training time will be much shorter.

.. code-block::

   # Submit training job for the shallow network architecture
   response_shallow_train = restapi_client.submit_job(
       workflows_file=WORKFLOWS_TAR_GZ,
       experiment_name="mnist",
       entry_point="train",
       entry_point_kwargs=" ".join([
           "-P model_architecture=shallow_net",
           "-P epochs=30",
           "-P register_model_name=mnist_shallow_net",
       ]),
   )

   print("Training job for shallow neural network submitted")
   print("")
   pprint.pprint(response_shallow_train)

   # Submit training job for the LeNet-5 network architecture
   response_le_net_train = restapi_client.submit_job(
       workflows_file=WORKFLOWS_TAR_GZ,
       experiment_name="mnist",
       entry_point="train",
       entry_point_kwargs=" ".join([
           "-P model_architecture=le_net",
           "-P epochs=30",
           "-P register_model_name=mnist_le_net",
       ]),
   )

   print("Training job for LeNet-5 neural network submitted")
   print("")
   pprint.pprint(response_le_net_train)

Now that we have two trained models (the shallow network and the LeNet-5 network), next we will apply the fast-gradient method (FGM) evasion attack on the shallow network to generate adversarial images.
Then, after we have the adversarial images, we will use them to evaluate some standard machine learning metrics against both models.
This will give us a sense of the transferability of the attacks between models.

This specific workflow is an example of jobs that contain dependencies, as the metric evaluation jobs cannot start until the adversarial image generation jobs have completed.
The testbed allows users to declare one-to-many job dependencies like this, which we will use to queue up jobs to start immediately after the previous jobs have concluded.
The code below illustrates this by doing the following:

#. A job is submitted that generates adversarial images based on the shallow net architecture (entry point **fgm**).
#. We wait until the job starts and a MLFlow identifier is assigned, which we check by polling the API until we see the id appear.
#. Once we have an id returned to us from the API, we queue up the metrics evaluation jobs and declare the job dependency using the ``depends_on`` option.
#. The message "Dependent jobs submitted" will display once everything is queued up.

.. code-block::

   def mlflow_run_id_is_not_known(response_fgm):
       return response_fgm["mlflowRunId"] is None and response_fgm["status"] not in [
           "failed",
           "finished",
       ]

   response_fgm_shallow_net = restapi_client.submit_job(
       workflows_file=WORKFLOWS_TAR_GZ,
       experiment_name="mnist",
       entry_point="fgm",
       entry_point_kwargs=" ".join(
           ["-P model_name=mnist_shallow_net", "-P model_version=1"]
       ),
   )

   print("FGM attack (shallow net architecture) job submitted")
   print("")
   pprint.pprint(response_fgm_shallow_net)
   print("")

   while mlflow_run_id_is_not_known(response_fgm_shallow_net):
       time.sleep(1)
       response_fgm_shallow_net = restapi_client.get_job_by_id(
           response_fgm_shallow_net["jobId"]
       )

   response_shallow_net_infer_shallow_net = restapi_client.submit_job(
       workflows_file=WORKFLOWS_TAR_GZ,
       experiment_name="mnist",
       entry_point="infer",
       entry_point_kwargs=" ".join(
           [
               f"-P run_id={response_fgm_shallow_net['mlflowRunId']}",
               "-P model_name=mnist_shallow_net",
               "-P model_version=1",
           ]
       ),
       depends_on=response_fgm_shallow_net["jobId"],
   )

   response_le_net_infer_shallow_net = restapi_client.submit_job(
       workflows_file=WORKFLOWS_TAR_GZ,
       experiment_name="mnist",
       entry_point="infer",
       entry_point_kwargs=" ".join(
           [
               f"-P run_id={response_fgm_shallow_net['mlflowRunId']}",
               "-P model_name=mnist_le_net",
               "-P model_version=1",
           ]
       ),
       depends_on=response_fgm_shallow_net["jobId"],
   )

   print("Dependent jobs submitted")

We can poll the status of the dependent jobs using the code below.
We should see the status of the jobs shift from "queued" to "started" and eventually become "finished".

.. code-block::

   response_shallow_net_infer_shallow_net = restapi_client.get_job_by_id(
       response_shallow_net_infer_shallow_net["jobId"]
   )
   response_le_net_infer_shallow_net = restapi_client.get_job_by_id(
       response_le_net_infer_shallow_net["jobId"]
   )

   pprint.pprint(response_shallow_net_infer_shallow_net)
   print("")
   pprint.pprint(response_le_net_infer_shallow_net)

We can similiarly run an FGM-based evasion attack using the LeNet-5 architecture as our starting point.
The following code is very similar to the code we just saw, all we’ve done is swap out the entry point keyword argument that requests the shallow net architecture with a version that requests the LeNet-5 architecture.

.. code-block::

   response_fgm_le_net = restapi_client.submit_job(
       workflows_file=WORKFLOWS_TAR_GZ,
       experiment_name="mnist",
       entry_point="fgm",
       entry_point_kwargs=" ".join(
           ["-P model_name=mnist_le_net", "-P model_version=1"]
       ),
   )

   print("FGM attack (LeNet-5 architecture) job submitted")
   print("")
   pprint.pprint(response_fgm_le_net)
   print("")

   while mlflow_run_id_is_not_known(response_fgm_le_net):
       time.sleep(1)
       response_fgm_le_net = restapi_client.get_job_by_id(response_fgm_le_net["jobId"])

   response_shallow_net_infer_le_net_fgm = restapi_client.submit_job(
       workflows_file=WORKFLOWS_TAR_GZ,
       experiment_name="mnist",
       entry_point="infer",
       entry_point_kwargs=" ".join(
           [
               f"-P run_id={response_fgm_le_net['mlflowRunId']}",
               "-P model_name=mnist_shallow_net",
               "-P model_version=1",
           ]
       ),
       depends_on=response_fgm_le_net["jobId"],
   )

   response_le_net_infer_le_net_fgm = restapi_client.submit_job(
       workflows_file=WORKFLOWS_TAR_GZ,
       experiment_name="mnist",
       entry_point="infer",
       entry_point_kwargs=" ".join(
           [
               f"-P run_id={response_fgm_le_net['mlflowRunId']}",
               "-P model_name=mnist_le_net",
               "-P model_version=1",
           ]
       ),
       depends_on=response_fgm_le_net["jobId"],
   )

   print("Dependent jobs submitted")

Like before, we can monitor the status of the dependent jobs by querying the API using the code block below.

.. code-block::

   response_shallow_net_infer_le_net_fgm = restapi_client.get_job_by_id(
       response_shallow_net_infer_le_net_fgm["jobId"]
   )
   response_le_net_infer_le_net_fgm = restapi_client.get_job_by_id(
       response_le_net_infer_le_net_fgm["jobId"]
   )

   pprint.pprint(response_shallow_net_infer_le_net_fgm)
   print("")
   pprint.pprint(response_le_net_infer_le_net_fgm)

Congratulations, you’ve just run your first experiment using Dioptra!

Querying the MLFlow Tracking Service
------------------------------------

Currently the Testbed API can only be used to register experiments and start jobs, so if users wish to extract their results programmatically, they can use the :py:class:`~mlflow.tracking.MlflowClient` class from the :py:mod:`mlflow` Python package to connect and query their results.
Since we captured the run ids generated by MLFlow, we can easily retrieve the data logged about one of our jobs and inspect the results.
To start the client, we simply need to run,

.. code-block::

   mlflow_client = MlflowClient()

The client uses the environment variable ``MLFLOW_TRACKING_URI`` to figure out how to connect to the MLFlow Tracking Service, which we configured near the top of this notebook.
To query the results of one of our runs, we just need to pass the run id to the client’s ``get_run()`` method.
As an example, let’s query the run results for the FGM attack applied to the LeNet-5 architecture,

.. code-block::

   fgm_run_le_net = mlflow_client.get_run(response_fgm_le_net["mlflowRunId"])

If the request completed successfully, we should now be able to query data collected during the run.
For example, to review the collected metrics, we just use,

.. code-block::

   pprint.pprint(fgm_run_le_net.data.metrics)

To review the run’s parameters, we use,

.. code-block::

   pprint.pprint(fgm_run_le_net.data.params)

To review the run’s tags, we use,

.. code-block::

   pprint.pprint(fgm_run_le_net.data.tags)

There are many things you can query using the MLFlow client.
`The MLFlow documentation gives a full overview of the methods that are available <https://www.mlflow.org/docs/latest/python_api/mlflow.tracking.html#mlflow.tracking.MlflowClient>`__.

Cleanup
-------

To clean up, you simply need to close the browser tab containing the Jupyter notebook and shut down the services by running ``make teardown`` on the command-line.
