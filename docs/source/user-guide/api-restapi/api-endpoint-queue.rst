.. _restapi-endpoint-queue:

Endpoint: Queue
===============

Data Models
-----------

.. autoclass:: mitre.securingai.restapi.queue.model.Queue
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: mitre.securingai.restapi.queue.model.QueueLock
   :members:
   :undoc-members:
   :show-inheritance:

Forms
-----

.. autoclass:: mitre.securingai.restapi.queue.model.QueueRegistrationForm
   :members:
   :undoc-members:
   :show-inheritance:

Services
--------

.. autoclass:: mitre.securingai.restapi.queue.service.QueueService
   :members:
   :undoc-members:

Controllers
-----------

.. automodule:: mitre.securingai.restapi.queue.controller
   :members:
   :undoc-members:
   :show-inheritance:

Error Messages
--------------

.. autoexception:: mitre.securingai.restapi.queue.errors.QueueAlreadyExistsError

.. autoexception:: mitre.securingai.restapi.queue.errors.QueueDoesNotExistError

.. autoexception:: mitre.securingai.restapi.queue.errors.QueueRegistrationError
