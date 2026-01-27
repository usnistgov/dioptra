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

.. _how-to-set-up-the-python-client:

Set Up the Python Client
========================

This how-to explains how to initialize the Dioptra Python Client in a Jupyter notebook and login. 


Prerequisites
-------------

* :ref:`how-to-prepare-deployment` -  A deployment of Dioptra is required.

.. _setup_python_client_recipe:

Client Setup Workflow
------------------------


.. rst-class:: header-on-a-card header-steps

Step 1: Configure the Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set environment variables with the proper values for *host*, *port*, *user*, and *password*.

.. code-block:: bash

    DIOPTRA_REST_API_ADDRESS = "<host>:<port>"
    DIOPTRA_REST_API_USER = "<user>"
    DIOPTRA_REST_API_PASS = "<password>"

.. rst-class:: header-on-a-card header-steps

Step 2: Initialize Client
~~~~~~~~~~~~~~~~~~~~~~~~~

There are two Dioptra clients to choose from: the JSON client with returns dictionaries and will raise an exception if a non-200 response is recived, and the Response client which returns Response objects and does not raise exceptions.

Choose your preferred client, then in your python interpreter, run the following code: 

.. tabs::

   .. group-tab:: JSON Client

        .. admonition:: Initialize Client
            :class: code-panel python

                from dioptra.client import connect_json_dioptra_client

                client = connect_json_dioptra_client(DIOPTRA_REST_API_ADDRESS)

   .. group-tab:: Response Client

        .. admonition:: Initialize Client
            :class: code-panel python

                from dioptra.client import connect_response_dioptra_client

                client = connect_response_dioptra_client(DIOPTRA_REST_API_ADDRESS)



Step 3: Register User
~~~~~~~~~~~~~~~~~~~~~

In your python interpreter, run the following code: 
        
.. tabs::

    .. group-tab:: JSON Client
        .. admonition:: Register User
            :class: code-panel python

                client.users.create(DIOPTRA_REST_API_USER, email=f"{DIOPTRA_REST_API_USER}@localhost", password=DIOPTRA_REST_API_PASS)

        You should see a successful response similar to the below:

        .. code-block:: bash

            { "json": 1 }

    .. group-tab:: Response Client

        todo


Step 4: Log In
~~~~~~~~~~~~~~

In your python interpreter, run the following code: 
        
.. code-block:: python3

    client.auth.login(DIOPTRA_REST_API_USER, DIOPTRA_REST_API_PASS)
