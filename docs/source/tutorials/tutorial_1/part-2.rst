Adding Inputs and Outputs
==========

Short description of the step.

.. contents::
   :local:

Prerequisites
-------------

.. note::
   If you see missing dependencies, install them and rebuild the docs.

Code (Python, YAML, TOML)
-------------------------

.. tab-set-code::

   .. literalinclude:: ../../../tutorials_src/my-tutorial/code/step_02_train_model.py
      :language: python
      :linenos:
      :caption: step_02_train_model.py
      :start-after: [docs:start-train]
      :end-before:  [docs:end-train]

   .. code-block:: yaml
      :caption: params.yml

      training:
        epochs: 5
        batch_size: 32

   .. code-block:: toml
      :caption: config.toml

      [model]
      name = "baseline-cnn"
      lr = 0.001

Screenshot
----------

.. figure:: _static/screenshots/training_metrics.png
   :alt: Training metrics chart with loss and accuracy
   :width: 700px

   Metrics after 5 epochs.

Next Steps
----------

- :doc:`part-2`
- :ref:`Some cross-reference label if needed`
