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

.. _user-guide-generics-plugin-system:

Generics Plugin System
======================

.. include:: /_glossary_note.rst

What are generics?
------------------

The generic functions (*generics* for short) in :py:mod:`dioptra.sdk.generics` provide standardized interfaces for sets of related methods.
As an example, the :py:func:`.fit_estimator` generic can be called to train an estimator without needing to specify the name of the underlying library (scikit-learn, Tensorflow, PyTorch).
This is possible since the generics all use multiple argument dispatch, which is an approach to polymorphism that selects the underlying implementation to use based on the types of the objects passed to the function arguments.

The flow chart below illustrates how method dispatching works when using a generic that has three different implementations,

.. code-block::  none

                               if Arg1     +------------------+
                               is type A   |                  |
                              +----------->| Implementation 1 |
                              |            |                  |
                              |            +------------------+
                              |
             +--------------+ |if Arg1     +------------------+
   object -->|Arg1 generic  | |is type B   |                  |
   type B    |     function +-+----------->| Implementation 2 |
             +--------------+ |            |   (dispatched)   |
                              |            +------------------+
                              |
                              |if Arg1     +------------------+
                              |is type C   |                  |
                              +----------->| Implementation 3 |
                                           |                  |
                                           +------------------+

In the schematic, an object of type `B` is passed to the first argument of a generic function.
Since type `B` objects have a corresponding implementation, the object is dispatched (along with any other arguments passed to the generic function) to implementation 2 for processing.
On the other hand, if an object of type `D` is passed to the generic function instead, then there is no corresponding implementation available.
When this happens, the generic function will either raise an exception immediately or attempt to process the object using a default implementation (if one is defined).

The implementations are registered using a plugin system where each generic advertises a plugin entry point that it scans for methods at runtime.
This system means that **all** the underlying generic implementations, even the ones that come bundled with the Testbed, are plugins that are independent of the core :py:mod:`dioptra.sdk` package and users are free to create custom implementations and share them as Python packages.

Available plugin entry points
-----------------------------

=============================  =======================================
          generic                   advertised plugin entry point
=============================  =======================================
:py:func:`.fit_estimator`      `dioptra.generics.fit_estimator`
:py:func:`.estimator_predict`  `dioptra.generics.estimator_predict`
=============================  =======================================

Registering generic dispatch methods
------------------------------------

Creating a new dispatch method for a generic is done by writing a Python function and adding a function decorator.
Each generic exposes a `.register` attribute that is a decorator for registering new dispatch methods, and is applied to functions that implement a new dispatch method.
These functions do not have to have the same number of arguments as the associated generic, but all arguments that are used should be in the same order and assigned the same names, with extra arguments not found in the generic coming at the end.
None of these arguments are allowed to have default values.
The expected types for the arguments are then declared using type annotations, which is how the different dispatch methods available to generics are distinguished from one another.

Consider the following example for the :py:func:`~dioptra.sdk.generics.fit_estimator` generic, which has the following signature:

.. code-block:: python

   def fit_estimator(estimator: Any, x: Any, y: Any, **kwargs):
      ...

The code below registers two new implementations to this generic:

.. code-block:: python

   # tf_keras_model.py
   from typing import Any

   from dioptra.sdk.generics import fit_estimator
   from tensorflow.keras import Model
   
   @fit_estimator.register
   def _(estimator: Model, x: Any, **kwargs):
       return fit_keras_model(estimator=estimator, x=x, **kwargs)
   
   
   @fit_estimator.register
   def _(estimator: Model, x: Any, y: Any, **kwargs):
       return fit_keras_model(estimator=estimator, x=x, y=y, **kwargs)
   
   
   def fit_keras_model(
       estimator, x, y = None, batch_size = None, nb_epochs = 1, **kwargs
   ):
       fit_kwargs = dict(y=y, batch_size=batch_size, epochs=nb_epochs, **kwargs)
       return estimator.fit(
           x=x, **{k: v for k, v in fit_kwargs.items() if v is not None}
       )

There are a few things to note about the above code,

#. The first of the two implementations omits the `y` argument, which allows :py:func:`~dioptra.sdk.generics.fit_estimator` to be called without having to specify `y`.
#. Both implementations call the helper function :py:func:`fit_keras_model`, which allows additional arguments with default values to be included in an implementation.
#. The functions, which do not need to have unique names, are registered simply by topping them with the `@fit_estimator.register` decorator.

More complicated function signatures can be used.
For example, if you wanted to handle a :py:class:`~pandas.DataFrame` passed to the `x` argument differently from other data types, you could register the following implementation:

.. code-block:: python

   import pandas as pd

   @fit_estimator.register
   def _(estimator: Model, x: pd.DataFrame, **kwargs):
       ...

Then, in the implementation, you could process the :py:class:`~pandas.DataFrame` so that it was compatible with the :py:meth:`estimator.fit` method used in the :py:func:`fit_keras_model` helper function.
In this way you can incrementally add new implementations to handle many different combinations of estimator and data types!

Packaging a generic plugin
--------------------------

A generic plugin is a Python package that registers an implementation to the generic's plugin entry point.
The Python package itself should be structured in the usual way, with a minimal plugin package containing the following files:

.. code-block:: none

   fit-estimator-tf-keras
   ├── pyproject.toml
   ├── README.md
   ├── setup.cfg
   ├── setup.py
   └── src
       └── fit_estimator_tf_keras
           ├── __init__.py
           └── tf_keras_model.py

In the file layout shown above, the implementation from the previous section is saved to the file ``src/fit_estimator_tf_keras/tf_keras_model.py``.
Knowing this, we add the following to our `setup.cfg` file to register the implementation to the advertised plugin entry point for the :py:class:`~dioptra.sdk.generics.fit_estimator` generic:

.. code-block:: ini

   [options.entry_points]
   dioptra.generics.fit_estimator = tf_keras_model=fit_estimator_tf_keras.tf_keras_model

As usual, the name of the advertised plugin entry point goes on the left of the first ``=`` and the import path to the module (:py:mod:`fit_estimator_tf_keras.tf_keras_model` in this case) containing the implementation goes to the right, which is passed as the `value` of a `key=value` pair.
The name of the `key`, on the other hand, is not used by the plugin system, so it can be whatever you want and it doesn't have to match the name of the module.

Once you have this configured for your package, all you need to do is ``pip install`` it and the new implementation will be available to the :py:class:`~dioptra.sdk.generics.fit_estimator` generic for dispatching the next time you use it.

.. tip::

   For guidance on how to prepare a Python package, including what else needs to be included in `setup.cfg` and the rest of the files, see the `Packaging Python Projects`_ tutorial.
   Readers are also encouraged to examine the source files of the Dioptra repository itself.

.. _Packaging Python Projects: https://packaging.python.org/tutorials/packaging-projects/
