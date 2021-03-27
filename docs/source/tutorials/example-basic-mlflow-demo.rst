Tensorflow Basic MLflow demo
============================

This notebook contains a lightweight demonstration of the current
Securing AI Lab demo setup with MLflow

Setup
-----

Below we import the necessary Python modules and ensure the proper
environment variables are set so that all the code blocks will work as
expected,

.. code:: ipython3

    # Import packages from the Python standard library
    import os
    import pprint
    import time
    import warnings
    from pathlib import Path
    from typing import Tuple



    # Please enter custom username here.
    USERNAME = "howard"

    # Filter out warning messages
    warnings.filterwarnings("ignore")

    # Default address for accessing the RESTful API service
    RESTAPI_ADDRESS = "http://localhost:30080"

    # Base API address
    RESTAPI_API_BASE = f"{RESTAPI_ADDRESS}/api"

    # Default address for accessing the MLFlow Tracking server
    MLFLOW_TRACKING_URI = "http://localhost:35000"

    # Path to workflows archive
    WORKFLOWS_TAR_GZ = Path("workflows.tar.gz")

    # Experiment name (note the username_ prefix convention)
    EXPERIMENT_NAME = f"{USERNAME}_basic"


    # Set MLFLOW_TRACKING_URI variable, used to connect to MLFlow Tracking service
    if os.getenv("MLFLOW_TRACKING_URI") is None:
        os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI

    # Import third-party Python packages
    import numpy as np
    import requests
    from mlflow.tracking import MlflowClient

    # Import utils.py file
    import utils

    # Create random number generator
    rng = np.random.default_rng(54399264723942495723666216079516778448)

Check that the Makefile works in your environment by executing the
``bash`` code block below,

.. code:: bash

    %%bash

    # Running this will just list the available rules defined in the demo's Makefile.
    make


.. parsed-literal::

    [1mAvailable rules:[m

    [36mclean              [m Remove temporary files
    [36mdata               [m Download and prepare MNIST dataset
    [36minitdb             [m Initialize the RESTful API database
    [36mservices           [m Launch the Minio S3 and MLFlow Tracking services
    [36mteardown           [m Destroy service containers
    [36mworkflows          [m Create workflows tarball


.. parsed-literal::

    /home/hhuang/.conda/envs/tensorflow-mnist-classifier/lib/python3.7/site-packages/ipykernel/ipkernel.py:287: DeprecationWarning: `should_run_async` will not call `transform_cell` automatically in the future. Please pass the result to `transformed_cell` argument and any exception that happen during thetransform in `preprocessing_exc_tuple` in IPython 7.17 and above.
      and should_run_async(code)


Submit and run jobs
-------------------

The jobs that we will be running are implemented in the Python source
files under ``src/``, which will be executed using the entrypoints
defined in the ``MLproject`` file. To get this information into the
architecture, we need to package those files up into an archive and
upload it to the lab API. For convenience, the ``Makefile`` provides a
rule for creating the archive file, just run ``make workflows``,

.. code:: bash

    %%bash

    # Create the workflows.tar.gz file
    make workflows


.. parsed-literal::

    tar czf workflows.tar.gz src/load_model_dataset.py src/log.py src/hello_world.py MLproject
    chmod 644 workflows.tar.gz


.. parsed-literal::

    /home/hhuang/.conda/envs/tensorflow-mnist-classifier/lib/python3.7/site-packages/ipykernel/ipkernel.py:287: DeprecationWarning: `should_run_async` will not call `transform_cell` automatically in the future. Please pass the result to `transformed_cell` argument and any exception that happen during thetransform in `preprocessing_exc_tuple` in IPython 7.17 and above.
      and should_run_async(code)


To connect with the endpoint, we will use a client class defined in the
``utils.py`` file that is able to connect with the lab’s RESTful API
using the HTTP protocol. We connect using the client below,

.. code:: ipython3

    restapi_client = utils.SecuringAIClient(address=RESTAPI_API_BASE)


.. parsed-literal::

    /home/hhuang/.conda/envs/tensorflow-mnist-classifier/lib/python3.7/site-packages/ipykernel/ipkernel.py:287: DeprecationWarning: `should_run_async` will not call `transform_cell` automatically in the future. Please pass the result to `transformed_cell` argument and any exception that happen during thetransform in `preprocessing_exc_tuple` in IPython 7.17 and above.
      and should_run_async(code)


We need to register an experiment under which to collect our job runs.
The code below checks if the relevant experiment named ``"basic"``
exists. If it does, then it just returns info about the experiment, if
it doesn’t, it then registers the new experiment.

Baseline Demo: Defining Job Parameters:
=======================================

Here we will submit a basic job through MLflow.

.. code:: ipython3

    response_experiment = restapi_client.get_experiment_by_name(name=EXPERIMENT_NAME)

    if response_experiment is None or "Not Found" in response_experiment.get("message", []):
        response_experiment = restapi_client.register_experiment(name=EXPERIMENT_NAME)

    response_experiment




.. parsed-literal::

    {'experimentId': 17,
     'name': 'howard_basic',
     'lastModified': '2020-12-11T10:58:54.178417',
     'createdOn': '2020-12-11T10:58:54.178417'}



.. code:: ipython3

    # Submit baseline job:
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


    def mlflow_run_id_is_not_known(response):
        return response["mlflowRunId"] is None and response["status"] not in [
            "failed",
            "finished",
        ]

    # Retrieve mlflow run_id
    while mlflow_run_id_is_not_known(basic_job):
        time.sleep(1)
        basic_job = restapi_client.get_job_by_id(basic_job["jobId"])



.. parsed-literal::

    Basic job submitted.

    {'createdOn': '2021-03-27T09:17:20.586719',
     'dependsOn': None,
     'entryPoint': 'hello_world',
     'entryPointKwargs': None,
     'experimentId': 17,
     'jobId': 'f1a56642-6ff2-41c1-8ed2-b24094fb889f',
     'lastModified': '2021-03-27T09:17:20.586719',
     'mlflowRunId': None,
     'queueId': 1,
     'status': 'queued',
     'timeout': '24h',
     'workflowUri': 's3://workflow/ab94c87e786d49a1925b9269be5a39c3/workflows.tar.gz'}


Now we can query the job to view its output:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython3

    # Next we can see the baseline output from the job:

    mlflow_client = MlflowClient()
    basic_job_query  = mlflow_client.get_run(basic_job["mlflowRunId"])

    pprint.pprint(basic_job_query.data.params)
    pprint.pprint(basic_job_query.data.tags)


.. parsed-literal::

    {'output_log_string': "'Hello World'"}
    {'mlflow.project.entryPoint': 'hello_world',
     'mlflow.source.name': '/work/tmprljlc28b',
     'mlflow.source.type': 'PROJECT',
     'mlflow.user': 'securingai',
     'securingai.dependsOn': 'None',
     'securingai.jobId': 'f1a56642-6ff2-41c1-8ed2-b24094fb889f',
     'securingai.queue': 'tensorflow_cpu'}


To customize job parameters:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``-P job_property=<job_value>`` to the entry_point_kwargs field in
the job submission script

.. code:: ipython3

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

    {'createdOn': '2021-03-27T09:17:39.315095',
     'dependsOn': None,
     'entryPoint': 'hello_world',
     'entryPointKwargs': '-P output_log_string="Hello_again!"',
     'experimentId': 17,
     'jobId': 'c1b7bdec-3955-4552-89be-7d4d1ab5c16a',
     'lastModified': '2021-03-27T09:17:39.315095',
     'mlflowRunId': None,
     'queueId': 1,
     'status': 'queued',
     'timeout': '24h',
     'workflowUri': 's3://workflow/25f5726bb3294904abe6eab24d9b852d/workflows.tar.gz'}


.. code:: ipython3

    # Next we can see the baseline output from the job. The output has changed due to the new user parameter.

    mlflow_client = MlflowClient()
    basic_job_query  = mlflow_client.get_run(basic_job["mlflowRunId"])

    pprint.pprint(basic_job_query.data.params)


.. parsed-literal::

    {'output_log_string': "'Hello_again!'"}
