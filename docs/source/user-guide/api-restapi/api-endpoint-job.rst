.. _restapi-endpoint-job:

Endpoint: Job
=============

Data Models
-----------

.. autoclass:: mitre.securingai.restapi.job.model.Job
   :members:
   :undoc-members:
   :show-inheritance:

Forms
-----

.. autoclass:: mitre.securingai.restapi.job.model.JobForm
   :members:
   :undoc-members:
   :show-inheritance:

Services
--------

.. autoclass:: mitre.securingai.restapi.job.service.JobService
   :members:
   :undoc-members:

Controllers
-----------

.. automodule:: mitre.securingai.restapi.job.controller
   :members:
   :undoc-members:
   :show-inheritance:

Error Messages
--------------

.. autoexception:: mitre.securingai.restapi.job.errors.JobDoesNotExistError

.. autoexception:: mitre.securingai.restapi.job.errors.JobSubmissionError

.. autoexception:: mitre.securingai.restapi.job.errors.JobWorkflowUploadError
