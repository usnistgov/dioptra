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

Dioptra provides a web-based user interface for running, tracking, and organizing machine learning experiments using the open-source technologies and architectures found in real-world AI applications. Here we will demonstrate a simple Hello World example.

**Prerequisites for using the front end**: :doc:`/getting-started/building-the-containers` and :doc:`/getting-started/running-dioptra`


Using Dioptra (Hello World Example)
===================================

This guide will walk you through setting up and executing a simple “Hello World” example in the Dioptra frontend. It will familiarize you with some of the core concepts behind Dioptra. It assumes you have already followed the steps to configure and instantiate a Dioptra deployment outlined in the `Getting Started`_ section of the documentation.

.. _Getting Started: ../getting-started/building-the-containers

Register Accounts
_________________

Dioptra is designed to be run in a multi-user environment, so we need to set up accounts even if we are running locally. First, we need to get the credentials to create the dioptra worker account so that the worker containers can access the system and run our job. In the dioptra deployment folder, there is a `.env` file. Inside, find the two variables: `DIOPTRA_WORKER_USERNAME` and `DIOPTRA_WORKER_PASSWORD`. Now, open a web browser to `localhost/register`. Enter the values into the form to create a dioptra worker account. Add an email address.

.. image:: /images/frontend-guide/register-worker.png
   :width: 400
   :alt: Register Dioptra worker

After creating the dioptra-worker user, click "Signup" and register a separate user account. Then, log in to that second user account.

.. image:: /images/frontend-guide/register-user.png
   :width: 400

Create a Queue
______________

Queues are an organizational tool used to manage submitted jobs. The workers that were instantiated when creating your Dioptra deployment watch a Queue and process jobs one at a time in sequence. We will need a Queue to submit our “Hello World” job to, so let’s register one.

From the top menu, navigate to the Queues page and then click "Create". For the queue name, put "tensorflow_cpu" and "public" for the group. "tensorflow_cpu" is required for the queue name because it is what the deployment workers are watching. Public is the default permissions group and allows other users (if any) of a Dioptra instance to access this resource. On a shared system, consider creating another group to control access for real jobs, but for our hello world demo, "public" is fine. To finish creating our queue add a description if desired, then click "Confirm".

.. image:: /images/frontend-guide/queue-create.png
   :width: 700

Create a Plugin
_______________

Plugins are Python packages that contain code and the metadata to define Tasks that you wish to execute in a Dioptra job. They perform a variety of basic, low-level functions such as loading models, preparing data, and computing metrics, and implementing atomic portions of attacks and defenses. A plugin can contain one or more python files, each of which contains tasks. We will need a new plugin for our “Hello World” example, in order to assign tasks, so let’s create one.

From the top menu, navigate to the Plugins page and then click "Create". Put "hello_world" for the plugin name and "public" for the group. If desired, add a description. Click "Confirm".

.. image:: /images/frontend-guide/plugin-create.png
   :width: 700

Click the expand arrow on the hello_world plugin row and then click "MANAGE HELLO_WORLD FILES".

.. image:: /images/frontend-guide/manage-files.png
   :width: 700

.. image:: /images/frontend-guide/hello-world-files.png
   :width: 700

On the hello_world files page, click "Create". For filename, put "init.py". The file contents cannot be empty, but we need the file for packaging purposes, so add a space or comment. Click "save file".

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

Of note here is the `@pyplugs.register` decorator, which will add our `hello_world` function to the task plugin registry. The `structlog` logger will allow us to see the output of our execution in the logs at the end of this example.

In the task form section, put "hello_world" for the task name. Adding this task will allow us to call the code later.

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

Entrypoints are executable scripts or binaries that are paired with information about their parameters. They are the fundamental units of work within the Testbed, where each job submitted to the Testbed selects one entrypoint to run. We can't submit a job without an entrypoint, so let's make one now.

From the top menu, navigate to the Entrypoints page and then click "create". For the name, put "greeting" and select "public" for the group. In the task graph section, enter the following yaml::

   message:
      hello_world:
      greeting: $greeting
      name: $name

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

An experiment is a collection of related entrypoint runs. It is also required to make a job so follow the steps below to create one.

From the top menu, navigate to the Experiments page and then click "create". Enter the following information:

|   **Name**: Demo Experiment
|   **Group**: public
|   **Description** (optional): Just a demo
|   **Entrypoints**: greeting

Then, click "submit experiment".

Create and Run a Job
____________________

Lastly, it's time to create the job so we can run our Hello World example.

Click on the "Demo Experiment" link inside the Experiments table. Next, click "create" to open the job creation form. Use the following information to create a job:

|   **Description**: First run
|   **Queue**: tensorflow_cpu
|   **Entrypoint**: greeting
|   **Timeout**: 24h

Then, click "submit job". This will start the execution of our example.

.. image:: /images/frontend-guide/job-create.png
   :width: 700

Check the output by looking in the container log files by running `docker compose logs | grep tfcpu-01` and look for text like the following:

.. image:: /images/frontend-guide/docker-compose-log.png
   :width: 800
