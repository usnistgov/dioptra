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

.. _tutorials-example-hello-world:

Hello World!
============

This demo provides a baseline skeleton example for user entry point customization and job submission.
It can be used as a basic template for crafting your own demos to run within the architecture.

Getting started
---------------

Everything you need to run this demo is packaged into a set of Docker images that you can obtain by opening a terminal, navigating to the root directory of the repository, and running ``make pull-latest``.
Once you have downloaded the images, navigate to this directory using the terminal and run the demo startup sequence:

.. code:: bash

   make demo

Once the startup process completes, open up your web browser and enter ``http://localhost:38888`` in the address bar to access the Jupyter Lab interface (if nothing shows up, wait 10 to 15 more seconds and try again).
Double click the ``work`` folder and open the ``demo.ipynb`` file.
From here, follow the provided instructions to run the demo provided in the Jupyter notebook.

To watch the output logs for the Tensorflow worker containers as you step through the demo, run ``docker-compose logs -f tfcpu-01 tfcpu-02`` in your terminal.

When you are done running the demo, close the browser tab containing this Jupyter notebook and shut down the services by running ``make teardown`` on the command-line.
If you were watching the output logs, you will need to press Ctrl+C to stop following the logs before you can run ``make teardown``.

Importing Packages
------------------

Below we import the necessary Python modules and ensure the proper environment variables are set so that all the code blocks will work as expected,

.. code:: python3

    # Import packages from the Python standard library
    import os
    import pprint
    import time
    import warnings
    from pathlib import Path
    from typing import Tuple
    
    # Filter out warning messages
    warnings.filterwarnings("ignore")
    
    # Please enter custom username here.
    USERNAME = "howard"
    
    # Experiment name (note the username_ prefix convention)
    EXPERIMENT_NAME = f"{USERNAME}_basic"
    
    # Address for connecting the docker container to exposed ports on the host device
    HOST_DOCKER_INTERNAL = "host.docker.internal"
    # HOST_DOCKER_INTERNAL = "172.17.0.1"
    
    # Testbed API ports
    RESTAPI_PORT = "30080"
    MLFLOW_TRACKING_PORT = "35000"
    
    # Default address for accessing the RESTful API service
    RESTAPI_ADDRESS = (
        f"http://{HOST_DOCKER_INTERNAL}:{RESTAPI_PORT}"
        if os.getenv("IS_JUPYTER_SERVICE")
        else f"http://localhost:{RESTAPI_PORT}"
    )
    
    # Override the AI_RESTAPI_URI variable, used to connect to RESTful API service
    os.environ["AI_RESTAPI_URI"] = RESTAPI_ADDRESS
    
    # Default address for accessing the MLFlow Tracking server
    MLFLOW_TRACKING_URI = (
        f"http://{HOST_DOCKER_INTERNAL}:{MLFLOW_TRACKING_PORT}"
        if os.getenv("IS_JUPYTER_SERVICE")
        else f"http://localhost:{MLFLOW_TRACKING_PORT}"
    )
    
    # Override the MLFLOW_TRACKING_URI variable, used to connect to MLFlow Tracking service
    os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI
    
    # Base API address
    RESTAPI_API_BASE = f"{RESTAPI_ADDRESS}/api"
    
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

Submit and run jobs
-------------------

The entrypoints that we will be running in this example are implemented in the Python source files under ``src/`` and the ``MLproject`` file.
To run these entrypoints within the testbed architecture, we need to package those files up into an archive and submit it to the Testbed RESTful API to create a new job.
For convenience, the ``Makefile`` provides a rule for creating the archive file for this example, just run ``make workflows``,

.. code:: bash

    %%bash
    
    # Create the workflows.tar.gz file
    make workflows

To connect with the endpoint, we will use a client class defined in the ``utils.py`` file that is able to connect with the Testbed RESTful API using the HTTP protocol.
We connect using the client below, which uses the environment variable ``AI_RESTAPI_URI`` to figure out how to connect to the Testbed RESTful API,

.. code:: python3

    restapi_client = utils.SecuringAIClient()

We need to register an experiment under which to collect our job runs.
The code below checks if the relevant experiment exists.
If it does, then it just returns info about the experiment, if it doesn’t, it then registers the new experiment.

.. code:: python3

    response_experiment = restapi_client.get_experiment_by_name(name=EXPERIMENT_NAME)
    
    if response_experiment is None or "Not Found" in response_experiment.get("message", []):
        response_experiment = restapi_client.register_experiment(name=EXPERIMENT_NAME)
    
    response_experiment

.. parsed-literal::

    {'experimentId': 1,
     'lastModified': '2021-03-30T01:45:12.313505',
     'name': 'howard_basic',
     'createdOn': '2021-03-30T01:45:12.313505'}

We also need to register the name of the queue that is being watched for our jobs.
The code below checks if the relevant queue named ``"tensorflow_cpu"`` exists.
If it does, then it just returns info about the queue, if it doesn’t, it then registers the new queue.

.. code:: python3

    response_queue = restapi_client.get_queue_by_name(name="tensorflow_cpu")
    
    if response_queue is None or "Not Found" in response_queue.get("message", []):
        response_queue = restapi_client.register_queue(name="tensorflow_cpu")
    
    response_queue

.. parsed-literal::

    {'name': 'tensorflow_cpu',
     'lastModified': '2021-03-30T01:45:12.907876',
     'createdOn': '2021-03-30T01:45:12.907876',
     'queueId': 1}

Baseline Demo: Defining Job Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here we will submit a basic job through MLflow.

.. code:: python3

    # Helper function
    def mlflow_run_id_is_not_known(response):
        return response["mlflowRunId"] is None and response["status"] not in [
            "failed",
            "finished",
        ]
    
    
    # Submit baseline job
    basic_job = restapi_client.submit_job(
        workflows_file=WORKFLOWS_TAR_GZ,
        experiment_name=EXPERIMENT_NAME,
        entry_point="hello_world",
        entry_point_kwargs=" ".join([
        ]),
    )
    
    print("Basic job submitted.")
    print("")
    pprint.pprint(basic_job)
    
    # Retrieve mlflow run_id
    while mlflow_run_id_is_not_known(basic_job):
        time.sleep(1)
        basic_job = restapi_client.get_job_by_id(basic_job["jobId"])

.. parsed-literal::

    Basic job submitted.
    
    {'createdOn': '2021-03-30T01:53:02.434870',
     'dependsOn': None,
     'entryPoint': 'hello_world',
     'entryPointKwargs': None,
     'experimentId': 1,
     'jobId': 'b53f207c-820d-4a09-8f0c-ff55ac603c09',
     'lastModified': '2021-03-30T01:53:02.434870',
     'mlflowRunId': None,
     'queueId': 1,
     'status': 'queued',
     'timeout': '24h',
     'workflowUri': 's3://workflow/f6afa0d7875b4996b885616e0082457f/workflows.tar.gz'}

Now we can query the job to view its output:

.. code:: python3

    # Next we can see the baseline output from the job:
    mlflow_client = MlflowClient()
    basic_job_query  = mlflow_client.get_run(basic_job["mlflowRunId"])
    
    pprint.pprint(basic_job_query.data.params)
    pprint.pprint(basic_job_query.data.tags)

.. parsed-literal::

    {'output_log_string': "'Hello World'"}
    {'mlflow.project.entryPoint': 'hello_world',
     'mlflow.source.name': '/work/tmp2kojr5cq',
     'mlflow.source.type': 'PROJECT',
     'mlflow.user': 'securingai',
     'securingai.dependsOn': 'None',
     'securingai.jobId': 'b53f207c-820d-4a09-8f0c-ff55ac603c09',
     'securingai.queue': 'tensorflow_cpu'}

To customize job parameters, add ``"-P job_property=<job_value>"`` to the ``entry_point_kwargs`` field in the job submission script:

.. code:: python3

    # Submit baseline job:
    basic_job = restapi_client.submit_job(
        workflows_file=WORKFLOWS_TAR_GZ,
        experiment_name=EXPERIMENT_NAME,
        entry_point="hello_world",
        entry_point_kwargs=' '.join([
            '-P output_log_string="Hello_again!"'
        ]),
    )
    
    print("Basic job submitted.")
    print("")
    pprint.pprint(basic_job)
    
    # Retrieve mlflow run_id
    while mlflow_run_id_is_not_known(basic_job):
        time.sleep(1)
        basic_job = restapi_client.get_job_by_id(basic_job["jobId"])

.. parsed-literal::

    Basic job submitted.
    
    {'createdOn': '2021-03-30T01:53:11.643763',
     'dependsOn': None,
     'entryPoint': 'hello_world',
     'entryPointKwargs': '-P output_log_string="Hello_again!"',
     'experimentId': 1,
     'jobId': '4e9ce987-0b2f-4919-8f3f-7e7e1b679f48',
     'lastModified': '2021-03-30T01:53:11.643763',
     'mlflowRunId': None,
     'queueId': 1,
     'status': 'queued',
     'timeout': '24h',
     'workflowUri': 's3://workflow/c5fba44682fc4d10893cc6a6f568d70e/workflows.tar.gz'}

Next we can see the baseline output from the job.
The output has changed due to the new user parameter.

.. code:: python3

    mlflow_client = MlflowClient()
    basic_job_query  = mlflow_client.get_run(basic_job["mlflowRunId"])
    
    pprint.pprint(basic_job_query.data.params)

.. parsed-literal::

    {'output_log_string': "'Hello_again!'"}
