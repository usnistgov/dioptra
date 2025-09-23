Guidelines for Documentation
============================

Our documentation uses **reStructuredText (.rst)** with Sphinx. We attempt to organize
content by `Diátaxis <https://diataxis.fr/>`_:
**Tutorials**, **How-to guides**, **Reference**, and **Explanation**.

Documentation goals
-------------------

- **Brevity & placement.** Put content where it belongs; avoid duplication across types.
- **Single purpose per page.** Don’t mix a tutorial with reference or explanation on the same page.
- **Source of truth lives in code dirs.** Bring example code in with ``literalinclude``.
  Eventually a script will hopefully copy code into ``docs/`` folder. 

Style guide for RST documents
-----------------------------

Steps
~~~~~

When documenting steps for a tutorial or how-to guide, use admonitions to make them stand out:

.. tabs::

   .. tab:: Rendered

      .. admonition:: Steps

         1. Open **Plugins**.
         2. Click **Create Plugin**.
         3. Name it and **Save**.

   .. tab:: RST Source

      .. code-block:: rst

         .. admonition:: Steps

            1. Open **Plugins**.
            2. Click **Create Plugin**.
            3. Name it and **Save**.


Notes and warnings
~~~~~~~~~~~~~~~~~~

To caveat steps or reference explanation/reference material elsewhere, use notes and warnings:

.. tabs::

   .. tab:: Rendered

      .. note::
         This tutorial uses the **web UI**; you can do the same via **API** or **TOML**.

      .. warning::
         Make sure the queue is **Public** or jobs won’t start.

   .. tab:: RST Source

      .. code-block:: rst

         .. note::
            This tutorial uses the **web UI**; you can do the same via **API** or **TOML**.

         .. warning::
            Make sure the queue is **Public** or jobs won’t start.


Figures (screenshots)
~~~~~~~~~~~~~~~~~~~~~

Screenshots should be cropped and zoomed for readability. Always include ``:alt:`` text.

.. tabs::

   .. tab:: Rendered

      .. figure:: ../tutorials/tutorial_1/_static/screenshots/login_dioptra.png
         :alt: Dioptra login screen
         :width: 900px
         :figclass: bordered-image

         **Login screen.** Use a tight crop so text remains readable.



   .. tab:: RST Source

      .. code-block:: rst

         .. figure:: ../tutorials/tutorial_1/_static/screenshots/login_dioptra.png
            :alt: Dioptra login screen
            :width: 900px
            :figclass: bordered-image

            **Login screen.** Use a tight crop so text remains readable.


Literal includes
~~~~~~~~~~~~~~~~

Use ``literalinclude`` to pull code from the repo instead of pasting it:

.. tabs::

   .. tab:: Rendered

      .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_1.py
         :language: python
         :linenos:

   
   .. tab:: RST Source

      .. code-block:: rst

         .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_1.py
            :language: python
            :linenos:

.. note::
   Use ``[docs:start]`` and ``[docs:end]`` to only grab sections of code. Needs corresponding tags in code files

Tabs for alternate paths
~~~~~~~~~~~~~~~~~~~~~~~~

Tabs can be used for alternate instructions (e.g. UI vs API):

.. tabs::

   .. tab:: Rendered

      .. tabs::

         .. tab:: UI
            Login using the UI

            .. figure:: ../tutorials/tutorial_1/_static/screenshots/login_dioptra.png
               :alt: Dioptra login screen
               :width: 900px
               :figclass: bordered-image

         .. tab:: API
            Login using the Python client API 

            .. code-block:: python

               LOCAL_PATH = 'http://127.0.0.1'
               from dioptra.client import connect_json_dioptra_client
               client = connect_json_dioptra_client(LOCAL_PATH)
               client.users.create(username=USER_NAME, email=USER_EMAIL, password=USER_PASSWORD)
               client.auth.login(USER_NAME, USER_PASSWORD)


   .. tab:: RST Source

      .. code-block:: rst

         .. tabs::

            .. tab:: UI
               Login using the UI

               .. figure:: ../tutorials/tutorial_1/_static/screenshots/login_dioptra.png
                  :alt: Dioptra login screen
                  :width: 900px
                  :figclass: bordered-image

            .. tab:: API
               Login using the Python client API 

               .. code-block:: python
                  
                  LOCAL_PATH = 'http://127.0.0.1'
                  from dioptra.client import connect_json_dioptra_client
                  client = connect_json_dioptra_client(LOCAL_PATH)
                  client.users.create(username=USER_NAME, email=USER_EMAIL, password=USER_PASSWORD)
                  client.auth.login(USER_NAME, USER_PASSWORD)


Collapsible content
-------------------

Use collapsible admonitions for long sections of code or optional context.  

.. tabs::

   .. tab:: Rendered

      .. admonition:: Python Plugin Code (long)
         :class: dropdown

         .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_3.py
            :language: python
            :linenos:

   .. tab:: RST Source

      .. code-block:: rst

         .. admonition:: Python Plugin Code (long)
            :class: dropdown

            .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_3.py
               :language: python
               :linenos:

Cross-references
----------------

Use explicit references (``.. _label-name:``) together with ``:ref:``.  
This is the most reliable way to link between pages, since it does not  
depend on the document being in a ``.. toctree::``.


   .. code-block:: rst

      .. _getting-started-running-dioptra:

   Once the label exists, you can link to it with ``:ref:``.

.. tabs::

   .. tab:: Rendered

      See more about :ref:`getting-started-running-dioptra`  
      in the dedicated page.

   .. tab:: RST Source

      .. code-block:: rst

         See more about :ref:`getting-started-running-dioptra`  
         in the dedicated page.

.. warning::

   To make a ``:ref:`` work, the target document must define a label
   (``.. _label-name:``). Without a label, ``:link-type: ref`` cannot resolve.

   Place the label near the top of the file you want to link to. For example:

   .. code-block:: rst

      .. _tutorial-1:

      Tutorial 1
      ==========

      Continue with the rest of the document...


Cards, grids, and callouts
--------------------------

`sphinx-design` provides cards and grids for menus or callouts.  


.. tabs::

   .. tab:: Rendered

      .. grid:: 2

         .. grid-item-card:: **Run Dioptra**
            :link: getting-started-running-dioptra
            :link-type: ref

            Step-by-step instructions for running Dioptra.

         .. grid-item-card:: **Installation**
            :link: getting-started-installation
            :link-type: ref

            How to install Dioptra locally.

         .. grid-item-card:: **Build Containers**
            :link: getting-started-building-the-containers
            :link-type: ref

            Instructions for building container images.

         .. grid-item-card:: **Additional Configuration**
            :link: getting-started-additional-configuration
            :link-type: ref

            Optional configuration steps after setup.

   .. tab:: RST Source

      .. code-block:: rst

         .. grid:: 2

            .. grid-item-card:: **Run Dioptra**
               :link: getting-started-running-dioptra
               :link-type: ref

               Step-by-step instructions for running Dioptra.

            .. grid-item-card:: **Installation**
               :link: getting-started-installation
               :link-type: ref

               How to install Dioptra locally.

            .. grid-item-card:: **Build Containers**
               :link: getting-started-building-the-containers
               :link-type: ref

               Instructions for building container images.

            .. grid-item-card:: **Additional Configuration**
               :link: getting-started-additional-configuration
               :link-type: ref

               Optional configuration steps after setup.



Section hierarchy
-----------------

Headings should be nested consistently.

- ``=`` for page title
- ``-`` for H2
- ``~`` for H3
- ``^`` for H4

Diátaxis content types
----------------------

Below is our interpretation of Diátaxis and the principles we are trying to follow in Dioptra docs.

Tutorials (learning by doing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Learn by doing
- Provide early wins for users with small accomplishments
- Tell readers upfront what to expect ("In this tutorial, you will build a plugin that...")
- Give feedback along the way ("You should see...")
- Minimize explanation — link out to other docs instead

How-to guides (solve a task)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Cookbook style
- One outcome per page
- Concise, no digressions

Reference (facts)
~~~~~~~~~~~~~~~~~

- Precise, factual
- No steps or advice
- Covers APIs, schemas, configs

Explanation (concepts & why)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Provide background and rationale
- Cover trade-offs and mental models
- No steps

Author checklist
----------------

- Did you read the Diátaxis guide for your documentation type?
- Does the page belong to **one** Diátaxis type?  
- Are links used instead of duplication of content?  
