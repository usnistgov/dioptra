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

..  .. tabs::
..  
..     .. tab:: Rendered
..  
..        .. admonition:: Steps
..  
..           1. Open **Plugins**.
..           2. Click **Create Plugin**.
..           3. Name it and **Save**.
..  
..     .. tab:: RST Source
..  
..        .. code-block:: rst
..  
..           .. admonition:: Steps
..  
..              1. Open **Plugins**.
..              2. Click **Create Plugin**.
..              3. Name it and **Save**.

Rendered:

.. admonition:: Steps

   1. Open **Plugins**.
   2. Click **Create Plugin**.
   3. Name it and **Save**.

RST Source:

.. code-block:: rst

   .. admonition:: Steps

      1. Open **Plugins**.
      2. Click **Create Plugin**.
      3. Name it and **Save**

Notes and warnings
~~~~~~~~~~~~~~~~~~

To caveat steps or reference explanation/reference material elsewhere, use notes and warnings:

..  .. tabs::
..  
..     .. tab:: Rendered
..  
..        .. note::
..           This tutorial uses the **web UI**; you can do the same via **API** or **TOML**.
..  
..        .. warning::
..           Make sure the queue is **Public** or jobs won’t start.
..  
..     .. tab:: RST Source
..  
..        .. code-block:: rst
..  
..           .. note::
..              This tutorial uses the **web UI**; you can do the same via **API** or **TOML**.
..  
..           .. warning::
..              Make sure the queue is **Public** or jobs won’t start.

Rendered:

.. note::
   This tutorial uses the **web UI**; you can do the same via **API** or **TOML**.

.. warning::
   Make sure the queue is **Public** or jobs won’t start.

RST Source:

.. code-block:: rst

   .. note::
      This tutorial uses the **web UI**; you can do the same via **API** or **TOML**.

   .. warning::
      Make sure the queue is **Public** or jobs won’t start.

Figures (screenshots)
~~~~~~~~~~~~~~~~~~~~~

Screenshots should be cropped and zoomed for readability. Always include ``:alt:`` text.

..  .. tabs::
..  
..     .. tab:: Rendered
..  
..        .. figure:: _static/screenshots/login.png
..           :alt: Dioptra login screen
..           :width: 900px
..           :figclass: bordered-image
..  
..           **Login screen.** Use a tight crop so text remains readable.
..  
..     .. tab:: RST Source
..  
..        .. code-block:: rst
..  
..           .. figure:: _static/screenshots/login.png
..              :alt: Dioptra login screen
..              :width: 900px
..              :figclass: bordered-image
..  
..              **Login screen.** Use a tight crop so text remains readable.

**Example**: (todo - replace with tabs once we install sphinx-tabs)

Rendered:

.. figure:: ../tutorials/tutorial_1/_static/screenshots/login_dioptra.png
   :alt: Dioptra login screen
   :width: 900px
   :figclass: bordered-image

   **Login screen.** Use a tight crop so text remains readable.

RST Source:

.. code-block:: rst

   .. figure:: ../../tutorials/tutorial_1/_static/screenshots/login_dioptra.png
      :alt: Dioptra login screen
      :width: 900px
      :figclass: bordered-image

      **Login screen.** Use a tight crop so text remains readable.

Literal includes
~~~~~~~~~~~~~~~~

Use ``literalinclude`` to pull code from the repo instead of pasting it:

..  .. tabs::
..  
..     .. tab:: Rendered
..  
..        .. literalinclude:: ../../../../../examples/tutorials/tutorial_1/plugin_1.py
..           :language: python
..           :linenos:
..           :start-after: [docs:start]
..           :end-before: [docs:end]
..  
..     .. tab:: RST Source
..  
..        .. code-block:: rst
..  
..           .. literalinclude:: ../../examples/tutorials/plugin_1.py
..              :language: python
..              :linenos:
..              :start-after: [docs:start]
..              :end-before: [docs:end]

**Example**: (todo - replace with tabs once we install sphinx-tabs)

Rendered:

.. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_1.py 
   :language: python
   :linenos:

RST Source:

.. code-block:: rst

   .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_1.py 
      :language: python
      :linenos:
      # :start-after: [docs:start]
      # :end-before: [docs:end]

Tabs for alternate paths
~~~~~~~~~~~~~~~~~~~~~~~~

Tabs can be used for alternate instructions (e.g. UI vs API):

..  .. tabs::
..  
..     .. tab:: Rendered
..  
..        .. tabs::
..  
..           .. tab:: UI
..              Steps for the web UI…
..  
..           .. tab:: API
..              Steps for the Python client…
..  
..     .. tab:: RST Source
..  
..        .. code-block:: rst
..  
..           .. tabs::
..  
..              .. tab:: UI
..                 Steps for the web UI…
..  
..              .. tab:: API
..                 Steps for the Python client…

**Example**: (todo - replace with tabs once we install sphinx-tabs)

Rendered:

[ERROR: can’t display tabs without sphinx-tabs module]

RST Source:

.. code-block:: rst

   .. tabs::

      .. tab:: UI
         Steps for the web UI…

      .. tab:: API
         Steps for the Python client…

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
