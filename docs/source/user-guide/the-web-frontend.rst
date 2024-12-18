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

.. _user-guide-the-web-frontend:

The Web Frontend User's Guide
=============================

.. include:: /_glossary_note.rst

Dioptra provides a web-based user interface for running, tracking, and organizing machine learning experiments using the open-source technologies and architectures found in real-world AI applications. A demonstration of a simple Hello World example will be shown here.

**Please make sure to have completed these prerequisites for using the front end**: :doc:`/getting-started/building-the-containers`, :doc:`/getting-started/running-dioptra`, and :doc:`/getting-started/additional-configuration`


Using Dioptra (Hello World Example)
===================================

This guide is a walk-through for setting up and executing a simple “Hello World” example in the Dioptra frontend. It will familiarize the reader with some of the core concepts behind Dioptra. It assumes that the steps to configure and instantiate a Dioptra deployment have already been followed as outlined in the `Getting Started`_ section of the documentation.

.. _Getting Started: ../getting-started/building-the-containers

Create a Plugin
_______________

Plugins are Python packages that contain code and the metadata to define tasks to execute in a Dioptra job. They perform a variety of basic, low-level functions such as loading models, preparing data, and computing metrics, and implementing atomic portions of attacks and defenses. A plugin can contain one or more python files, each of which contains tasks. A plugin is needed in order to assign tasks for the “Hello World” example.

From the top menu, navigate to the Plugins page and then click "Create". Put "hello_world" for the plugin name and "public" for the group. If desired, add a description. Click "Confirm".

.. image:: /images/frontend-guide/plugin-create.png
   :width: 700

Click the expand arrow on the hello_world plugin row and then click "MANAGE HELLO_WORLD FILES".

.. image:: /images/frontend-guide/manage-files.png
   :width: 700

.. image:: /images/frontend-guide/hello-world-files.png
   :width: 700

On the hello_world files page, click "Create". For filename, put "init.py". The file contents cannot be empty, but the file is needed for packaging purposes, so add a space or comment. Click "save file".

.. image:: /images/frontend-guide/init-py.png
   :width: 700

Now, back on the hello_world files page, click "Create" again. Put "hello.py" for filename and put the following for file contents::

   import structlog
   from dioptra import pyplugs
   LOGGER = structlog.get_logger()
   @pyplugs.register
   def hello_world(greeting: str, name: str) -> str:
      message = f"{greeting}, {name}!"
      LOGGER.info(message)
      return message

Of note here is the `@pyplugs.register` decorator, which will add the `hello_world` function to the task plugin registry. The `structlog` logger will save the execution output in the logs for viewing at the end of this example.

In the task form section of the Create File form, put "hello_world" for the task name. Adding this task will allow the code to be called later.

Create 2 input parameters:

| **Name**: "greeting"
| **Type**: string
| Leave "required" checked and then click the "+" to add the parameter.

| **Name**: "name"
| **Type**: string
| Leave "required" checked and then click the "+" to add the parameter.

Create 1 output parameter:

| **Name**: "message"
| **Type**: string
| Click the plus to add the parameter.

Click "add task" and then "save file".

.. image:: /images/frontend-guide/hello-py.png
   :width: 700

Create an Entrypoint
____________________

An Entrypoint is a template for the execution of a Job within an Experiment. An Entrypoint may have one or more parameters that permit different values to be used when running a job. Entrypoints are composed of one or more Plugins declared within a Task Graph. The Task Graph describes how Entrypoint parameters are passed into a Plugin Parameter or how the output of one Plugin will be used as an input into a later Plugin.

To create an Entrypoint, navigate to the "Entrypoint" page from the top menu and then click “Create”. For the name, put “greeting” and select “public” for the group. In the "Task Graph" section, enter the following yaml::

   message:
     hello_world:
       greeting: $greeting
       name: $name

The task graph declares a configuration of the desired task(s) and parameter(s). This is used in conjunction with the `hello.py` plugin to produce the "hello world" message. The next step is to define these parameters and give them default values.

In the Parameters section enter the following 2 parameters and then click the "+" after each:
   
|   **Name**: "greeting" 
|   **Type**: string
|   **Default value**: "Hello"

|   **Name**: "name"
|   **Type**: string 
|   **Default value**: "Person"

For Queues, select "tensorflow_cpu" and for Plugins choose "hello_world". Lastly, click "submit entrypoint".

.. image:: /images/frontend-guide/entrypoint-create.png
   :width: 700

Create an Experiment
____________________

An Experiment is a collection of related Jobs. An Experiment registers what Entrypoints are available to run and serves to group related Jobs together for analysis. All Jobs must be contained within an Experiment.

From the top menu, navigate to the Experiments page and then click "create". Enter the following information:

|   **Name**: Demo Experiment
|   **Group**: public
|   **Description** (optional): Just a demo
|   **Entrypoints**: greeting

Then, click "submit experiment".

.. image:: /images/frontend-guide/experiment-create.png
   :width: 700

Create and Run a Job
____________________

Lastly, it's time to create the job necessary to run the Hello World example.

Click on the "Demo Experiment" link inside the Experiments table. Next, click "create" to open the job creation form. Use the following information to create a job:

|   **Description**: First run
|   **Queue**: tensorflow_cpu
|   **Entrypoint**: greeting
|   **Timeout**: 24h

Then, click "submit job". This will start execution of the example.

.. image:: /images/frontend-guide/job-create.png
   :width: 700

Using a terminal window with the Dioptra deployment folder as the active directory, check the output of the container log files by running `docker compose logs | grep tfcpu-01` and look for text like the following:

.. image:: /images/frontend-guide/docker-compose-log.png
   :width: 800
