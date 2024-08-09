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
..
.. Parts of this documentation are adapted from the work,
.. https://github.com/mlflow/mlflow/blob/370850c1a97e78bb8c551651a0cb13d5300639ba/docs/source/projects.rst,
.. distributed under the terms of the Apache License, 2.0, see the copyright notice below.
..
.. Copyright 2018 Databricks, Inc.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     https://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

.. _user-guide-entry-points:

Entry Points
============

.. include:: /_glossary_note.rst

.. tip::

   Instructions for how to create your own entry points are available in the :doc:`Creating a New Entry Point guide <custom-entry-points>`.

What is an Entry Point?
-----------------------

.. figure:: /images/entry-point-components.svg

The term *entry point*, in the context of running experiment jobs, refers to executable scripts or binaries that are paired with information about their parameters.
Entry points are the fundamental unit of work within the Testbed, where each job submitted to the Testbed selects one entry point to run.
Dioptra derives its modularity in part by establishing a convention for how to compose new entry points.
The convention is identifying related units of work, for example applying one out of many evasion attacks to generate a batch of adversarial images, and then ensuring they are interchangeable with one another by implementing the corresponding executable scripts to share a common set of inputs and outputs.
This guided the construction of all the example experiments distributed as part of this project.
The :term:`SDK` library and the task plugins system are both provided to help Testbed users apply this convention to their own experiments.

.. note::

   This particular usage for the term *entry point* `originates with the MLFlow library <https://mlflow.org/docs/latest/projects.html#overview>`_, and we have adopted it for this project since Dioptra uses MLFlow_ on the backend to provide job tracking capabilities.

Each implementation of a Testbed entry point requires, at minimum, two separate files, a :term:`YAML` formatted ``MLproject`` file, and an executable Python script that can set its internal parameters via command-line options (e.g. :py:mod:`argparse` and :py:mod:`click`).
These files are the topics of the following sections.

MLproject Specifications
------------------------

As was mentioned before, the ``MLproject`` file is a plain text file in :term:`YAML` syntax that declares an entry point's executable command and its available parameters.
An example of an ``MLproject`` file is below,

.. code-block:: yaml

   name: My Project

   entry_points:
     train:
       parameters:
         data_dir: { type: path, default: "/nfs/data" }
         image_size: { type: string, default: "28,28,1" }
       command: >
         python src/train.py
         --data-dir {data_dir}
         --image-size {image_size}
     infer:
       parameters:
         run_id: { type: string }
         image_size: { type: string, default: "28,28,1" }
       command: >
         python src/infer.py
         --run-id {run_id}
         --image-size {image_size}

As we can see, there are two entry points in this ``MLproject`` file, `train` and `infer`.
If we submit a job that selects the `train` entry point and use its default parameters, we will end up running the following command in the Testbed environment,

.. code-block:: sh

   python src/train.py --data-dir /nfs/data --image-size 28,28,1

Users should note that each of the declared parameters must specify a data type.
You can specify just the data type by writing the following in your ``MLproject`` file,

.. code-block:: yaml

   parameter_name: data_type

A default value, in contrast, is not required, but users are encouraged to try and provide one wherever possible.
There are two equivalent ways to specify both a data type and a default value in the ``MLproject`` file,

.. code-block:: yaml

   # Short syntax
   parameter_name: {type: data_type, default: value}

   # Long syntax
   parameter_name:
     type: data_type
     default: value

The ``MLproject`` file supports four parameter types, some of which are handled in a special way (for example, the `path` data type will download certain files to local storage).
Any undeclared parameters are treated as `string`.
The parameter types are:

string
   A text string.

float
   A real number.
   The parameter will be checked if it is a number at runtime.

path
   A path on the local file system.
   Any relative ``path`` parameters will be converted to absolute paths.
   Any paths passed as distributed storage |URI|\s (``s3://``, ``dbfs://``, ``gs://``, etc.) will be downloaded to local files.
   Use this type for programs that can only read local files.

uri
   A |URI| for data either in a local or distributed storage system.
   Relative paths are converted to absolute paths, as in the `path` type.
   Use this type for programs that know how to read from distributed storage (e.g., programs that use the :py:mod:`boto3` package to directly access S3 storage).

Executable Script
-----------------

The entry point script, in principle, is just an executable Python script that accepts command-line options, so Testbed users can get started quickly by using their preexisting Python scripts.
However, if users wish to make use of the Testbed's powerful job tracking and task plugin capabilities, they will need to adopt the Testbed's standard for writing entry point scripts outlined in this section.

.. attention::

   The Testbed :term:`SDK`, in a planned future release, will be extending the ``MLproject`` specification to facilitate the templated generation of entry point scripts.
   Users will have an easier time migrating their scripts to this new approach if they follow the Testbed's standard for entry point scripts when :doc:`creating their own entry points <custom-entry-points>`.

Setting Parameters
~~~~~~~~~~~~~~~~~~

The :py:mod:`click` library should be used to create command-line interfaces for their Python scripts and to convert data types that aren't supported by the ``MLproject`` file (:py:class:`bool` and :py:class:`list`, for instance).
The following is a short example based on the `train` entry point from the ``MLproject`` examples we considered earlier in this guide,

.. code-block:: python

   # src/train.py
   import os

   import click
   from dioptra.sdk.utilities.contexts import plugin_dirs
   from dioptra.sdk.utilities.logging import (
       StderrLogStream,
       StdoutLogStream,
       attach_stdout_stream_handler,
       clear_logger_handlers,
       configure_structlog,
       set_logging_level,
   )


   def _coerce_comma_separated_ints(ctx, param, value):
       return tuple(int(x.strip()) for x in value.split(","))

   @click.command()
   @click.option(
       "--data-dir",
       type=click.Path(
           exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
       ),
       help="Root directory for shared datasets",
   )
   @click.option(
       "--image-size",
       type=click.STRING,
       callback=_coerce_comma_separated_ints,
       help="Dimensions for the input images",
   )
   def train(data_dir, image_size):
       ...


   if __name__ == "__main__":
       log_level = os.getenv("DIOPTRA_JOB_LOG_LEVEL", default="INFO")
       as_json = True if os.getenv("DIOPTRA_JOB_LOG_AS_JSON") else False
   
       clear_logger_handlers(get_prefect_logger())
       attach_stdout_stream_handler(as_json)
       set_logging_level(log_level)
       configure_structlog()
   
       with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
           _ = train()


Here, Click is validating our inputs by checking if ``--image-size`` is passed a string and if ``--data-dir`` points to a directory that exists and is readable.
We also define a callback function for ``--image-size`` that will convert a string of comma-separated integers into a :py:class:`tuple`, i.e. transform ``"28,28,1"`` into ``(28, 28, 1)``.
The code underneath the ``if __name__ == "__main__":`` block at the end ensures that the ``python src/train.py`` command specified in the ``MLproject`` file will call the ``train()`` function and use the values passed via the ``--data-dir`` and ``--image-size`` command-line options.

.. important::

   While most of the code underneath the ``if __name__ == "__main__":`` block is for configuring the script's logger, the context created by ``with plugin_dirs():`` plays a different and very important role, which will be discussed :doc:`in the following guide on task plugins <task-plugins>`.

This small example only scratches the surface of what Click can do.
Testbed users are encouraged to peruse the Click documentation to learn more about its features: https://click.palletsprojects.com/en/7.x/

MLFlow - Tracking Runs
~~~~~~~~~~~~~~~~~~~~~~

Every entry point script needs to invoke :py:func:`mlflow.start_run()` to create an active run context for MLFlow and it should be done near the top of their entry point function.
This context is needed when logging results and artifacts to the MLFlow Tracking service.
The following example shows how this context would be started in the ``train()`` function from the previous section.

.. code-block:: python

   import mlflow

   # Truncated...
   def train(data_dir, image_size):
       # Only use this when training a model
       mlflow.autolog()

       # Start the active run context for MLFlow
       with mlflow.start_run() as active_run:
           flow = init_flow()
           state = flow.run(parameters=dict(data_dir=data_dir, image_size=image_size))

       return state

Within this context block, the ``active_run`` variable will contain a :py:class:`mlflow.entities.Run` object that provides metadata about the run that is useful to have available.
MLFlow functions like :py:func:`mlflow.log_param`, :py:func:`mlflow.log_metric`, and :py:func:`mlflow.log_artifact` will be able to infer the current run automatically and be able to log their data to the appropriate place.
Please note that the ``init_flow()`` function is :ref:`introduced in the following section <entry-points-prefect-task-execution>`.

Testbed users are encouraged to peruse the MLflow Tracking documentation to learn more about the tracking context and the kinds of things you can do when it's active: https://mlflow.org/docs/latest/tracking.html.

.. _entry-points-prefect-task-execution:

Prefect - Task Execution
~~~~~~~~~~~~~~~~~~~~~~~~

The main work done within an entry point needs to use the :py:class:`~prefect.Flow` class from the Prefect_ library to create a context for assembling the entry point script's task workflow.
Prefect is a modern workflow library that is aimed at helping data scientists set up task execution graphs with minimal changes to their existing code, and in Dioptra it provides a framework for wiring :doc:`task plugins <task-plugins>` together.
The following example shows the beginnings of a :py:class:`~prefect.Flow` context to be run by the ``train()`` function in the previous section.

.. _entry-points-prefect-task-execution-code:

.. code-block:: python

   from prefect import Flow, Parameter
   from dioptra import pyplugs

   _PLUGINS_IMPORT_PATH: str = "dioptra_builtins"


   def init_flow() -> Flow:
       with Flow("Image Resizer") as flow:
           data_dir, image_size = Parameter("data_dir"), Parameter("image_size")
           resize_output = pyplugs.call_task(
               f"{_PLUGINS_IMPORT_PATH}.data",
               "images",
               "resize",
               data_dir=training_dir,
               image_size=image_size,
           )
           ...

This example illustrates the requirement that all the input parameters for an entry point need to be declared as such using the :py:class:`prefect.Parameter` class.
It also introduces us to our first task plugin call with :py:func:`.pyplugs.call_task`.
The anatomy of this call will be discussed in the :doc:`next section of the user guide <task-plugins>`, so for now, users just need to know that this is how task plugins are used within the Testbed, and that the Testbed standard is to have **all** function calls within the :py:class:`~prefect.Flow` context be invocations of :py:func:`.pyplugs.call_task`.

.. Links

.. _MLFlow: https://mlflow.org
.. _Prefect: https://www.prefect.io

.. Aliases

.. |URI| replace:: :term:`URI`
