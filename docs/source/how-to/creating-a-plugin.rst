
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


.. _how_to_create_a_plugin:

How-To: Creating New Plugins
============================

In Dioptra, the core of experiments are plugins, which are effectively collections
of annotated python files. This guide assumes that Dioptra is already installed and 
is accessible through the web browser, and that the user is logged in.

Adding Annotations to Your Functions
------------------------------------
This guide assumes you have files containing functions you want to import into Dioptra.
Here is an example function.

.. code-block:: python

    def sample_function(a: np.ndarray, b: str) -> str:
        return f"{b}: {a}"


To the top of each file, you should add the following import.

.. code-block:: python

    from dioptra import pyplugs

Annotate each function that should be made available as a plugin task in Dioptra with:

.. code-block:: python

    @pyplugs.register

The file containing our original function would now look like this.

.. code-block:: python

    from dioptra import pyplugs

    @pyplugs.register
    def sample_function(a: np.ndarray, b: str) -> str:
        return f"{b}: {a}"


Creating Types For Plugin Task Parameters
-----------------------------------------

Input and output parameters types for functions should be registered in Dioptra. By default,
Dioptra provides the following pre-registered types: ``any``, ``string``, ``integer``, ``number``,
``boolean``, and ``null``.

If your function uses a type not captured by one of the built-in types, you can register new ones.

1. Click the **Plugin Parameters** tab. 

    .. figure:: /images/plugin-param.png

2. Click **Create**.
3. Enter a name, select the group that should have access to the type, and enter a description.
4. If your type is a structure consisting of mappings, lists, and you would like to represent that, 
   you can do that in the structure field using the type specific. Below is an example of a structure.

    .. code-block:: yaml
        tuple: [integer, string]

    .. figure:: /images/plugin-param-create.png

5. Click **Confirm** when finished.

Create a Plugin
---------------

1. Navigate to the **Plugins** tab.

    .. figure:: /images/plugin.png

2. Click **Create**.
3. Enter a name, select the group that should have access to the plugin, and enter a description.

    .. figure:: /images/plugin-create.png

4. Click **Confirm**.
5. If successful, you should see the newly created plugin in the list.

    .. figure:: /images/plugin-created.png


Create a Plugin File
--------------------

    .. figure:: /images/plugin-manage-files.png

1. On the **Plugins** page, click the **Manage Plugin Files** button next to the plugin you would 
   like to add functions to.

    .. figure:: /images/plugin-files.png

2. On the **Plugin Files** page, click **Create**.
3. On the **Create File** page, you can choose to upload a python file by clicking **Upload Python File**,
   or just use the code box to type python code manually. Ensure that your functions are annotated
   as described above.
4. Enter a filename, and description in the appropriate fields.


    .. figure:: /images/plugin-file-create.png


Create Tasks for each Function in the File
******************************************

1. For each plugin task in the file, use the Task Form on the right to enter the definition of that
   task.
2. For every input parameter to the task, enter the name of the parameter, select the parameter type,
   indicate whether it's required, and click the **Add Input Param** button when finished to add that parameter.
3. For every output parameter to the task, enter the name of the parameter, select the parameter type, and
   click the **Add Output Param** button when finished to add that parameter.

    .. figure:: /images/plugin-task-params.png

4. Ensure that the task name matches the function name in the code. 
5. Indicate whether the function is a function or an artifact task.
   
    .. figure:: /images/plugin-task-create.png

6. Click **Add Task**.
7. If successful, it should appear in the **Plugin Function Tasks** section.

    .. figure:: /images/plugin-task-created.png

8. After adding all the tasks from the file, click **Save File**. Repeat this process for all plugin files in your plugin.

    .. figure:: /images/plugin-file-created.png
