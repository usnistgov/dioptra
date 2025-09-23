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

We provide **custom CSS and JavaScript** for images.

To get our custom styling, use one or more of the following figure classes with ``:figclass:``:  

- ``border-image`` → Adds a light border, shadow, and background  
- ``clickable-image`` → Makes the image interactive with cursor + modal support  
- ``big-image`` → Allows images to grow wider than the text column (fragile; hacky CSS that may break with sidebar/layout changes — use sparingly)  

.. note::
   These assets are loaded via ``conf.py`` using ``html_css_files`` and ``html_js_files`` to point to CSS and JS code in our ``_static`` directory. 
   Modals are included by adding a ``div`` element in the ``layout.html`` footer.

**A screenshot using all three CSS classes**

On click, JavaScript shows the modal ``div`` element. 

.. figure:: ../tutorials/tutorial_1/_static/screenshots/login_dioptra.png
   :alt: Dioptra login screen
   :figclass: border-image clickable-image big-image

   **Login screen.** Use a tight crop so text remains readable.  
   Click to enlarge.


**RST Source code**

.. code-block:: rst

   .. figure:: ../tutorials/tutorial_1/_static/screenshots/login_dioptra.png
      :alt: Dioptra login screen
      :figclass: border-image clickable-image big-image

      **Login screen.** Use a tight crop so text remains readable.  
      Click to enlarge.

.. note::
   Making images larger than the text column with ``big-image`` is potentially **fragile** and relies on CSS workarounds.
   It may look odd with different sidebar widths or screen sizes. Prefer standard-sized images unless
   the extra width is necessary for readability.


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
   Use ``# [docs:start]`` and ``# [docs:end]`` in Python files
   (or the appropriate comment style for other languages)
   to only grab sections of code. These tags must be present in the code files.

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
               :figclass: border-image

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
                  :figclass: border-image

            .. tab:: API
               Login using the Python client API 

               .. code-block:: python
                  
                  LOCAL_PATH = 'http://127.0.0.1'
                  from dioptra.client import connect_json_dioptra_client
                  client = connect_json_dioptra_client(LOCAL_PATH)
                  client.users.create(username=USER_NAME, email=USER_EMAIL, password=USER_PASSWORD)
                  client.auth.login(USER_NAME, USER_PASSWORD)


Collapsible content
~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~

Use explicit references (``.. _label-name:``) together with ``:ref:``.  
This is the most reliable way to link between pages, since it does not  
depend on the document being in a ``.. toctree::``.



.. tabs::

   .. tab:: Rendered

      See more about :ref:`getting-started-running-dioptra`  
      in the dedicated page.

   .. tab:: RST Source

      .. code-block:: rst

         See more about :ref:`getting-started-running-dioptra`  
         in the dedicated page.

.. note::

   To make a ``:ref:`` work, the target document must define a label
   (``.. _label-name:``). Without a label, ``:link-type: ref`` cannot resolve.

   Place the label near the top of the file you want to link to. For example:

   .. code-block:: rst

      .. _tutorial-1:

      Tutorial 1
      ==========

      Continue with the rest of the document...


Cards, grids, and callouts
~~~~~~~~~~~~~~~~

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
