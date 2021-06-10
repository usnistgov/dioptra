.. NOTICE
..
.. This software (or technical data) was produced for the U. S. Government under
.. contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
.. 52.227-14, Alt. IV (DEC 2007)
..
.. © 2021 The MITRE Corporation.

.. _user-guide-api-reference-sdk:

Testbed SDK API Reference
=========================

.. toctree::
   :hidden:
   :maxdepth: -1

   api-sdk/api-generics
   api-sdk/api-utilities
   api-sdk/api-exceptions
   api-sdk/api-pyplugs
   api-sdk/api-rq
   api-sdk/api-cryptography

generics
--------

.. currentmodule:: mitre.securingai.sdk.generics

.. autosummary::

   fit_estimator
   estimator_predict

utilities
---------

.. currentmodule:: mitre.securingai.sdk.utilities

.. autosummary::

   contexts.plugin_dirs
   decorators.require_package
   logging.attach_stdout_stream_handler
   logging.clear_logger_handlers
   logging.configure_structlog
   logging.set_logging_level
   logging.StderrLogStream
   logging.StdoutLogStream
   paths.set_path_ext

exceptions
----------

.. currentmodule:: mitre.securingai.sdk.exceptions

.. autosummary::

   ARTDependencyError
   CryptographyDependencyError
   EstimatorPredictGenericPredTypeError
   PrefectDependencyError
   TensorflowDependencyError
   UnknownPackageError
   UnknownPluginError
   UnknownPluginFunctionError

pyplugs
-------

.. currentmodule:: mitre.securingai

.. autosummary::

   pyplugs.register
   pyplugs.task_nout
   pyplugs.names
   pyplugs.funcs
   pyplugs.info
   pyplugs.exists
   pyplugs.get
   pyplugs.call
   pyplugs.get_task
   pyplugs.call_task
   pyplugs.names_factory
   pyplugs.funcs_factory
   pyplugs.info_factory
   pyplugs.exists_factory
   pyplugs.get_factory
   pyplugs.call_factory
   pyplugs.get_task_factory
   pyplugs.call_task_factory

rq
--

.. currentmodule:: mitre.securingai.rq

.. autosummary::

   tasks.run_mlflow_task

cryptography
------------

.. currentmodule:: mitre.securingai.sdk.cryptography

.. autosummary::

   common.load_payload
   keygen.generate_rsa_key_pair
   keygen.save_private_key
   keygen.save_public_key
   sign.load_private_key
   sign.sign_payload
   verify.load_public_key
   verify.load_signature
   verify.verify_payload
