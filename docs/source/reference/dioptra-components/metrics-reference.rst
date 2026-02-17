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

.. _reference-metrics:

Metrics
=================


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-metrics-definition:

Metric Definition
---------------------

A **Metric** in Dioptra is a representation of a measurement taken during a job.

.. _reference-metrics-attributes:

Metric Attributes
-----------------

A metric has the following attributes. Note that the ``name`` and ``step`` values together form a primary key for metrics.

* **Name**: (string) The name associated with the metric.
* **Value**: (float or string) The value of the metric. Can be a float, NaN, Infinity, or -Infinity. When sent to the API, the following values will be converted:
   - ``NaN`` will become ``"nan"``
   - ``Infinity`` will become ``"inf"``
   - ``-Infinity`` will become ``"-inf"``

.. _reference-experiments-optional-attributes:

Optional Attributes
~~~~~~~~~~~~~~~~~~~

* **Step**: (integer, optional) an optional value which can be used to track the change of a metric over time (using sequentially increasing integers). Defaults to 0.
* **Timestamp**: (datetime or string, optional) - a timestamp value to associate with the metric. If not provided, defaults to the server time when the metric is logged.


.. _reference-metrics-retrieval-interfaces:

Retrieval Interfaces
--------------------

Metrics can be retrieved using the python client or the RESTAPI. Alternatively, the :ref:`Job Dashboard <how-to-logging-metrics>` page in the UI can 
show an overview of metrics for the job.

.. _reference-metrics-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Retrieve the metrics with the highest step number for the job.**

   .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_metrics_by_id

**Retrieve the full metric history for a job for a given name.**

   .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_metrics_snapshots_by_id

**Retrieve the metrics with the highest step number for all jobs in an experiment**

   .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.get_metrics_by_id


.. _reference-metrics-rest-api:

Using REST API
~~~~~~~~~~~~~~

Metrics can be retrieved directly via the HTTP API.

**Retrieve Latest Metrics for a Job**

See the :http:get:`GET /api/v1/jobs/{int:id}/metrics </api/v1/jobs/{id}/metrics>` endpoint documentation for payload requirements.

**Retrieve Full Metric History for a Job for a given Metric**

See the :http:get:`GET /api/v1/jobs/{int:id}/metrics/{str:name}/snapshots </api/v1/jobs/{id}/metrics/{name}/snapshots>` endpoint documentation for payload requirements.

**Retrieve Latest Metrics for all Jobs in an Experiment**

See the :http:get:`GET /api/v1/experiments/{int:id}/metrics </api/v1/experiments/{id}/metrics>` endpoint documentation for payload requirements.


.. _reference-metrics-registration-interfaces:

Registration Interfaces
-----------------------

Metrics can be logged to a job using either the python client or the REST API.

.. _reference-metrics-registration-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Post metrics for a job.**

   .. automethod:: dioptra.client.jobs.JobsCollectionClient.append_metric_by_id


.. _reference-metrics-registration-rest-api:

Using REST API
~~~~~~~~~~~~~~

Metrics can be logged using the RESTAPI.

**Log Metrics**

See the :http:post:`POST /api/v1/jobs/{int:id}/metrics </api/v1/jobs/{id}/metrics>` endpoint documentation for payload requirements.


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`<how-to-logging-metrics>` 
