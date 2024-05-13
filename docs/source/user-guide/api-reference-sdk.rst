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

.. _user-guide-api-reference-sdk:

Testbed SDK API Reference
=========================

.. include:: /_glossary_note.rst

.. toctree::
   :hidden:
   :maxdepth: -1

   api-sdk/api-generics
   api-sdk/api-utilities
   api-sdk/api-exceptions
   api-sdk/api-pyplugs

generics
--------

.. currentmodule:: dioptra.sdk.generics

.. autosummary::

   fit_estimator
   estimator_predict

utilities
---------

.. currentmodule:: dioptra.sdk.utilities

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

.. currentmodule:: dioptra.sdk.exceptions

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

.. currentmodule:: dioptra

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
