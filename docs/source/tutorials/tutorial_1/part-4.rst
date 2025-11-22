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
:html_theme.sidebar_secondary.remove:

.. _tutorial-1-part-4:

Utilizing Metric Logging
==============================

Overview
--------

In the last tutorial, you built a multi-step workflow that transformed a numpy array multiple times.
After each step, you printed summary stats and then viewed those in the logs. 

Instead of printing values in the logs, we will record them using 'metrics'. This will produce nice time-series visualizations for us. 
This can be useful if you are trying to keep track of a metric across various steps, both within and across plugins. 
Metrics are stored at the job level. 

All we'll do in this step is replace our prior ``print_stats`` plugin task with a new ``log_metrics`` task instead.

.. Warning:: 

    This part of the tutorial will not work properly until new changes from DIOPTRA-OPTIC branch are merged in for metric logging

.. _tutorial-1-part-4-modify-plugin-3:

Add metrics task to plugin 3
-------------

Let's create the new plugin task that using Dioptra's metric logging. 

.. admonition:: Steps

   1. Go to the **Plugins** tab and open up the **plugin 3** from last step  
   2. Navigate to the Python file you created 
   3. Copy in the following new plugin task to the bottom of the file

 
**Plugin task: Using Metrics**

`Paste this below your existing Python code in Plugin 3`

.. admonition:: Plugin 3
    :class: code-panel python

    .. literalinclude:: ../../../../examples/tutorials/tutorial_1/plugin_3_w_metrics.py
       :language: python
       :start-after: # [new-plugin-definition]

.. admonition:: Steps (continued)

   4. Click "Import Tasks" again to import the new plugin task. 

.. Note:: 

    Metrics are appended to a job. They are identified by the metric name, and they also require a value and a step name.


Now let's edit entrypoint 3 to use this new Plugin task.

Modify Entrypoint 3
-------------------

Change the entrypoint graph to utilize ``log_metrics`` instead of ``print_stats``

.. admonition:: Steps

   1. Open up entrypoint 3
   2. In the entrypoint task graph window, change every reference of ``print_stats`` to ``log_metrics`` (should be 3 references)
   

Now let's re-run this entrypoint and see if our metrics get logged. 

Re-run Entrypoint 3 
-------------------


.. admonition:: Steps

   1. Go to the last experiment you made (e.g. ``experiment_3``).  
   2. Create a new job with entrypoint 3 and click run


Inspect Metrics
---------

Let's view our results

.. admonition:: Steps

   1. Go to the job page for the job you just ran
   2. Click the `metrics` tabs - you should see some graphs


Conclusion
----------

You now know how to log metrics within a plugin task!

Next, we will save outputs from plugin tasks as **artifacts**.