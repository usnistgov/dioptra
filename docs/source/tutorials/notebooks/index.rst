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

.. _tutorial-advanced-tutorials:

Advanced Tutorials
==================

The following tutorials are captured in Jupyter notebooks and are distributed as part of the dioptra git repository in the `examples folder <https://github.com/usnistgov/dioptra/tree/main/examples>`__. 
These tutorials use the Python client and can be run interactively from the provided notebook files. 


.. toctree::
  :hidden:

  mnist_demo 

.. Symlink created for notebook:  cd dioptra/docs/source/tutorials/notebooks/
..  ln -s ../../../../examples/mnist_demo.ipynb mnist_demo.ipynb
.. Note that building notebook pages with nbsphinx requires installation of pandoc

View the Tutorials
------------------
Click any of the links below to view the Jupyter notebook tutorials rendered in HTML. 

.. list-table::
  :widths: 25 75
  :header-rows: 1

  * - Name
    - Description
  * - :ref:`Adversarial ML with OPTIC </tutorials/notebooks/mnist_demo.ipynb>`
    - This tutorial demonstrates how the OPTIC (Open Perturbation Testing for Image Classifers) plugin can be used to
      evaluate adversarial attacks and defenses on a model trained to recognize handwritten digits.



Run the Tutorials in a Local Deployment 
---------------------------------------------

To run the tutorials in a local deployment, you'll need to do the following:

- :ref:`Install Dioptra <how-to-install-dioptra>`: Ensure you have access to a Dioptra deployment
- :ref:`Setup the Python Client <how-to-set-up-the-python-client>`: Set up the Python Client 

After doing this, open any of the Jupyter Notebook tutorials locally (they are located at `dioptra/examples <https://github.com/usnistgov/dioptra/tree/main/examples>`__). 
Select the Python environment that was created during installation. Download any datasets as needed in the instructions and then execute the code cells. 