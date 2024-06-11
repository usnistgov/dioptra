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

.. _user-guide-custom-entry-points:

Creating a New Entry Point
==========================

.. include:: /_glossary_note.rst

What are the basic steps?
-------------------------

.. figure:: /images/entry-point-customization.svg

.. tip::

   When creating a new entrypoint, users may also find it helpful to create their own python task plugins in combination with existing builtin task plugins.
   Instructions for developing local and builtin tasks can be found in the following guide: :ref:`user-guide-custom-task-plugins`.
   The following sections will assume that all task plugins already exist somewhere (either locally or as a builtin), and are ready for use in our entry point python script.

Entry point development generally involves creating a Python script, that is then executed by its associated command within the MLproject file.

The general development work can be divided as follows:

- Developing the Python entry point script:

  - Identifying tasks that will need to run in sequence (i.e. download_image -> process_image -> log_image) and their associated parameters.
  - Identifying which parameters will need to be provided by user and setting the appropriate MLflow command line arguments with Click.
  - Prefect Flow pipeline input initialization, chaining user/command line inputs to the Prefect Flow pipeline.
  - Constructing the Flow pipeline using existing local and builtin tasks.

- Linking Python script parameters to the MLproject file:

  - Updating the entry point section with new/existing Python scripts.
  - Creating the parameters section.
  - Linking the parameters to the Python script command.

In the given example folder directory, the files that will need to be created/modified are marked with an asterisk:

.. code-block:: none

   example_dir/
   ├── src/
   │   ├── <custom_entrypoint_script>.py *Main entry point script we will need to create and edit.
   │   ├── <Other src code>
   │   └── custom_local_task_plugins.py
   ├── ...
   └── MLproject *MLproject file we will also need to edit.

We will start by defining the ``<custom_entrypoint_script>.py`` file followed by the ``MLproject`` file.

Developing the Python Entry Point Script: Defining Tasks and Parameters
-----------------------------------------------------------------------

Let us assume we want to do the following tasks in a new python script, called ``process_artifacts.py``:

1. Call built-in task ``A`` to load artifacts from an existing mlrun.
2. Call custom task ``B`` to process the artifacts.
3. Call built-in task ``C`` to log and store the processed artifacts.

Our flow pipeline will involve the following plugins called in sequence: ``task A -> task B -> task C``

For the job parameters we'll need to provide:

1. The mlrun ID string containing the artifacts to be downloaded. Let us call it ``runID_A``.
2. Associated target parameters for controlling processing behavior. Let us call it ``process_parameter_B``.
3. Storage ID tag for task ``C``. Let us call it ``storage_name_C``.


Now that we have identified all the parameters we will need to provide to each task, we will need to setup the proper Click commands in our script so that it will request those parameters when it is executed.

Please refer to :ref:`user-guide-entry-points` for more information on setting up command line arguments with Click.

After Click parameter setup, we will need to pass the parameters into our flow pipeline.

Developing the Python Entry Point Script: Passing Job Parameters into a Given Flow
-----------------------------------------------------------------------------------

Let us call our flow pipeline ``process_artifacts_flow``.
With this we will need to do the following steps to initialize the flow in our main body of the script:

1. Create an instance of the flow in our main script: ex. ``flow: Flow = process_artifacts_flow()``
2. Pass our parameters into the ``flow.run()`` call.
3. Define the ``process_artifacts_flow`` task pipeline.

We should have something similar to the example below (after defining our :py:func:`click.command` line inputs):

.. code-block::

   # START OF PYTHON SCRIPT
   !/usr/bin/env python
   import ...

   # Local tasks plugins must be directly imported similar to local Python src functions.
   from .custom_local_task_plugins import task_B

   @click.command(_
   @click.option(
   ... # Setup + info for parameter A.
   )
   ... # Repeat for parameters B and C.
   def process_artifacts(runID_A, process_parameter_B, storage_name_C):
       with mlflow.start_run() as active_run:

           # Extra initialization steps as needed
           default_process_parameter_B2 = <Some Default Value based on B1>

           flow: Flow = process_artifacts_flow()
           # Execute the flow run with our given input parameters
           state = flow.run(
               parameters=dict(runID_A=runID_A,
                               process_parameter_B=process_parameter_B,
                               process_parameter_B2=default_process_parameter_B2,
                               storage_name_C=storage_name_C
                               )
           )

   # Define the flow pipeline here:
   def process_artifacts_flow() -> Flow:
       with Flow("<Description of What this Flow Does Here>") as flow:
           ...
           # Flow definition here
           ...
       return flow

   if __name__ == "__main__":
       process_artifacts()

Here we can see that we've transferred the parameters for tasks A-C through into process_artifacts_flow's ``flow.run()`` call.

This call will take in all job associated parameters needed for running each task and transfer it to our flow pipeline.
Users are also allowed to initialize and pass through additional parameter values as needed into the ``flow.run()`` call, such as the secondary parameters that can be set by default or calculated based on other input parameters.

Developing the Python Entry Point Script: Creating a Flow Pipeline
------------------------------------------------------------------

Next, we will define the flow pipeline itself.
We will start with the input parameters we need to provide to the current Flow.
Here we will define the name of each parameter and their associated parameter information:

.. code-block::

   def init_hello_world_flow() -> Flow:
       with Flow("<Description of What this Flow Does Here>") as flow:
           (
               runID_A,
               process_parameter_B,
               process_parameter_B2,
               storage_name_C,
           ) = (
               Parameter("This is Parameter A + optional information"),
               Parameter("This is Parameter B + optional information"),
               Parameter("Parameter B2"),
               Parameter("Parameter C"),
           )
           ... // Perform Tasks A->C
       return flow

The first set of variables defines which parameters are passed through the ``flow.run()`` call.
The second set of ``Parameter()`` declarations defines what each parameter is effectively called the during the flow execution.

.. tip::

   It is important to note that each of these variables are effectively now Flow parameters and thus any values they contain can only be accessed once they are passed into a given task during execution.
   For example, if a user were to attempt a ``print(runID_A)`` within the task flow block, they will get back a message similar to ``Parameter("This is Parameter A + optional information")``.
   The only way to view what ``runID_A`` actually contains is to invoke the ``print(runID_A)`` call within task_A's plugin code itself.
   Once ``task_A`` is executed in the pipeline, the corresponding parameter value will be accessed and printed by that task.

Now that our parameters are all available in our Flow pipeline, we can setup our task calls as follows:

.. code-block::

   def process_artifacts_flow() -> Flow:
       with Flow("<Description of What this Flow Does Here>") as flow:
           (
               ... # parameter init.
           )

           // Call task A, get artifacts download location.
           artifact_location = pyplugs.call_task(
               f"{_PLUGINS_IMPORT_PATH}.random", "dataset_downloads", "task_A", parameter_A=runID_A
           )

           // Call task B, get processed artifacts location.
           processed_artifact_location = task_B(
               artifact_location=artifact_location,
               process_parameter_B=process_parameter_B,
               process_parameter_B2=process_parameter_B2,
           )

           // Call task C.
           pyplugs.call_task(
               f"{_PLUGINS_IMPORT_PATH}.random", "dataset_storage", "task_C",
                  storage_name_C=storage_name_C,
                  processed_artifact_location=processed_artifact_location
           )
       return flow


Here we can see there are some differences between how local and builtin tasks are called:

- Any local defined tasks (like ``task_B``) must be imported and executed similar to a regular python function call.
- Builtin tasks must be called using the format: ``pyplugs.call_task(f"{_PLUGINS_IMPORT_PATH}.random","<task_dir>" ,"<task_name>", <task_parameters> )``

Users can refer to :ref:`user-guide-task-plugins-collection` to see our builtin task plugin directories and :ref:`user-guide-custom-task-plugins` for how to create local and builtin plugins.

.. tip::

   For this example, the input and output parameters link up nicely so that the task dependencies follow ``task A->B->C`` in order.
   However, should any intermediate tasks not have preceding dependencies, they can be run out of order. Those will require their preceding tasks to be declared as well.
   Please refer to :ref:`user-guide-task-plugins` for more information.

We now have our fully developed entry point script:

.. code-block::

   # START OF PYTHON SCRIPT
   !/usr/bin/env python
   import ...

   # Local tasks plugins must be directly imported.
   from .custom_local_task_plugins import task_B

   @click.command(_
   ... # Setup for parameters A-C
   def process_artifacts(runID_A, process_parameter_B, storage_name_C):
       with mlflow.start_run() as active_run:

           # Extra initialization steps as needed
           default_process_parameter_B2 = <Some Default Value based on B1>

           flow: Flow = process_artifacts_flow()
           # Execute the flow run with our given input parameters
           state = flow.run(
               parameters=dict(runID_A=runID_A,
                               process_parameter_B=process_parameter_B,
                               process_parameter_B2=default_process_parameter_B2,
                               storage_name_C=storage_name_C
                               )
           )

   # Define the flow pipeline here:
   def init_hello_world_flow() -> Flow:
       with Flow("<Description of What this Flow Does Here>") as flow:
           (
               runID_A,
               process_parameter_B,
               process_parameter_B2,
               storage_name_C,
           ) = (
               Parameter("This is Parameter A + optional information"),
               Parameter("This is Parameter B + optional information"),
               Parameter("Parameter B2"),
               Parameter("Parameter C"),
           )

           // Call task A, get artifacts download location.
           artifact_location = pyplugs.call_task(
               f"{_PLUGINS_IMPORT_PATH}.random", "dataset_downloads", "task_A", parameter_A=runID_A
           )

           // Call task B, get processed artifacts location.
           processed_artifact_location = task_B(
               artifact_location, process_parameter_B, process_parameter_B2
           )

           // Call task C.
           pyplugs.call_task(
               f"{_PLUGINS_IMPORT_PATH}.random", "dataset_storage", "task_C", parameter_C=storage_name_C
           )
       return flow

   if __name__ == "__main__":
       process_artifacts()

Next we will need to add our new entry point script to the MLproject file.

Adding the New Entry Point to MLproject File:
---------------------------------------------

Assuming we will want to create an entry point called ``process_artifacts`` to invoke our ``process_artifacts.py`` script with the same job parameter names, we will create the following example below to link our script to our MLproject file:

.. code-block::

   name: example_mlflow_project_name_here

   entry_points:
     process_parameters:
       parameters:
         runID_A:  {type: string, default: ""}
         process_parameter_B:  {type: int, default: 30}
         storage_name_C:  {type: string, default: "processed_artifacts.tar.gz"}
       command: >
         python src/process_artifacts.py
         --runID-A {runID_A}
         --process-parameter-B {process_parameter_B}
         --storage-name-C  {storage_name_C}

Effectively, the ``process_parameters`` entry point will now invoke the ``src/process_parameters.py`` script with the associated job parameters now forwarding to their counterpart command line arguments.

Please refer to :ref:`user-guide-entry-points` for more details regarding MLproject specifications.
