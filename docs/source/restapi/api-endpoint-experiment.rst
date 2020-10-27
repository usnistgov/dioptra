.. _restapi-endpoint-experiment:

Endpoint: Experiment
====================

Data Models
-----------

.. autoclass:: mitre.securingai.restapi.experiment.model.Experiment
   :members:
   :undoc-members:
   :show-inheritance:

Forms
-----

.. autoclass:: mitre.securingai.restapi.experiment.model.ExperimentRegistrationForm
   :members:
   :undoc-members:
   :show-inheritance:

Services
--------

.. autoclass:: mitre.securingai.restapi.experiment.service.ExperimentService
   :members:
   :undoc-members:

Controllers
-----------

.. automodule:: mitre.securingai.restapi.experiment.controller
   :members:
   :undoc-members:
   :show-inheritance:

Error Messages
--------------

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentAlreadyExistsError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentMLFlowTrackingAlreadyExistsError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentDoesNotExistError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentMLFlowTrackingDoesNotExistError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentMLFlowTrackingRegistrationError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentRegistrationError
