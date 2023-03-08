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

.. _user-guide-task-plugins-collection:

Task Plugins Collection
=======================

.. include:: /_glossary_note.rst

.. toctree::
   :hidden:
   :maxdepth: -1

   api-task-plugins/api-builtins-artifacts
   api-task-plugins/api-builtins-attacks
   api-task-plugins/api-builtins-backend_configs
   api-task-plugins/api-builtins-data
   api-task-plugins/api-builtins-estimators
   api-task-plugins/api-builtins-metrics
   api-task-plugins/api-builtins-random
   api-task-plugins/api-builtins-registry
   api-task-plugins/api-builtins-tracking

Artifacts
---------

.. currentmodule:: dioptra_builtins.artifacts

.. autosummary::

   mlflow.download_all_artifacts_in_run
   mlflow.upload_data_frame_artifact
   mlflow.upload_directory_as_tarball_artifact
   mlflow.upload_file_as_artifact
   utils.extract_tarfile
   utils.make_directories

Exceptions
^^^^^^^^^^

.. autosummary::

   exceptions.UnsupportedDataFrameFileFormatError

Attacks
-------

.. currentmodule:: dioptra_builtins.attacks

.. autosummary::

   fgm.create_adversarial_fgm_dataset

Backend Configuration
---------------------

.. currentmodule:: dioptra_builtins.backend_configs

.. autosummary::

   tensorflow.init_tensorflow

Data
----

.. currentmodule:: dioptra_builtins.data

.. autosummary::

   tensorflow.create_image_dataset
   tensorflow.get_n_classes_from_directory_iterator

Estimators
----------

.. currentmodule:: dioptra_builtins.estimators

.. autosummary::

   keras_classifiers.init_classifier
   methods.fit
   methods.predict

Available Estimators
^^^^^^^^^^^^^^^^^^^^

.. autosummary::

   keras_classifiers.shallow_net
   keras_classifiers.le_net
   keras_classifiers.alex_net

Metrics
-------

.. currentmodule:: dioptra_builtins.metrics

.. autosummary::

   distance.get_distance_metric_list
   distance.get_distance_metric
   performance.get_performance_metric_list
   performance.get_performance_metric

Available Metrics
^^^^^^^^^^^^^^^^^

.. autosummary::

   distance.l_inf_norm
   distance.l_1_norm
   distance.l_2_norm
   distance.paired_cosine_similarities
   distance.paired_euclidean_distances
   distance.paired_manhattan_distances
   distance.paired_wasserstein_distances
   performance.accuracy
   performance.roc_auc
   performance.categorical_accuracy
   performance.mcc
   performance.f1
   performance.precision
   performance.recall

Exceptions
^^^^^^^^^^

.. autosummary::

   exceptions.UnknownDistanceMetricError
   exceptions.UnknownPerformanceMetricError

Random
------

.. currentmodule:: dioptra_builtins.random

.. autosummary::

   rng.init_rng
   sample.draw_random_integer
   sample.draw_random_integers

Registry
--------

.. currentmodule:: dioptra_builtins.registry

.. autosummary::

   art.load_wrapped_tensorflow_keras_classifier
   mlflow.add_model_to_registry
   mlflow.get_experiment_name
   mlflow.load_tensorflow_keras_classifier

Tracking
--------

.. currentmodule:: dioptra_builtins.tracking

.. autosummary::

   mlflow.log_metrics
   mlflow.log_parameters
   mlflow.log_tensorflow_keras_estimator

.. Substitutions

.. |ART| replace:: `Adversarial Robustness Toolbox <https://adversarial-robustness-toolbox.readthedocs.io/en/latest/>`__
.. |directory_iterator| replace:: :py:class:`~tensorflow.keras.preprocessing.image.DirectoryIterator`
.. |Linf| replace:: L\ :sub:`∞`
.. |L1| replace:: L\ :sub:`1`
.. |L2| replace:: L\ :sub:`2`
