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


.. _contributing-documentation-guide:

Guidelines for Documentation
============================

Our documentation uses **reStructuredText (.rst)** with Sphinx.

We attempt to organize content by `Diátaxis <https://diataxis.fr/>`_:

- **Tutorials**
- **How-to guides**
- **Reference**
- **Explanation**.

Documentation goals
-------------------

- **Brevity & placement.** Put content where it belongs; avoid duplication across types.
- **Single purpose per page.** Don’t mix a tutorial with reference or explanation on the same page.
- **Source of truth lives in code dirs.** Bring example code in with ``literalinclude``.
  Eventually a script will hopefully copy code into ``docs/`` folder. 


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


Notes, warnings, and important
~~~~~~~~~~~~~~~~~~

To caveat steps or reference explanation/reference material elsewhere, use notes, warnings, and the important flag:

.. tabs::

   .. tab:: Rendered

      .. note::
         This tutorial uses the **web UI**; you can do the same via **API** or **TOML**.

      .. warning::
         Make sure the queue is **Public** or jobs won’t start.

      .. important::
         In YAML, null is interpreted as the null value. Therefore, it does not name the null type!

   .. tab:: RST Source

      .. code-block:: rst

         .. note::
            This tutorial uses the **web UI**; you can do the same via **API** or **TOML**.

         .. warning::
            Make sure the queue is **Public** or jobs won’t start.

         .. important::
            In YAML, null is interpreted as the null value. Therefore, it does not name the null type!


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

      **Plugin 1: **

      .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_1.py
         :language: python
         :linenos:

   
   .. tab:: RST Source

      .. code-block:: rst

         **Plugin 1: **

         .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_1.py
            :language: python
            :linenos:


Custom Code Block Styling
~~~~~~~~~~~~~~~~

We provide custom CSS classes to style code blocks for improved visual separation and language-specific branding. You apply these classes using the standard Sphinx admonition directive.

**Available Classes**

Use the following classes with an `.. admonition::` block:

- ``code-panel``: The base class. This applies the custom box, rounded corners, shadow, and reduced font size.
- ``python``: Applies the custom dark blue title bar, yellow border, and the >>> prompt prefix.
- ``yaml``: Applies the custom dark brown title bar, dark border, and the >> prompt prefix.
- ``console``: Applies custom dark theme and the $ prompt prefix.

.. tabs::

   .. tab:: Rendered

      .. admonition:: <My Python LiteralInclude>
         :class: code-panel python
         
            .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_1.py
               :language: python
               :linenos:

      .. admonition:: <My YAML LiteralInclude>
         :class: code-panel yaml

         .. literalinclude:: ../../../examples/tutorials/tutorial_1/entrypoint_1_task_graph.yaml
            :language: yaml

      .. admonition:: <My Console Input/Output>
         :class: code-panel console

         .. code-block:: console

            Plugin 1 was successfully completed. Output value was .7432 with parameter "random".

   
   .. tab:: RST Source

      .. code-block:: rst

         .. admonition:: <My Python LiteralInclude>
            :class: code-panel python

            .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_1.py
               :language: python
               :linenos:

         .. admonition:: <My YAML LiteralInclude>
            :class: code-panel yaml

            .. literalinclude:: ../../../examples/tutorials/tutorial_1/entrypoint_1_task_graph.yaml
               :language: yaml

         .. admonition:: <My Console Input/Output>
            :class: code-panel console

            .. code-block:: console
               
               Plugin 1 was successfully completed. Output value was .7432 with parameter "random".
               
.. note::
   Use unique comments, such as ``# [docs:start]`` and ``# [docs:end]``, in Python files
   (or the appropriate comment style for other languages)
   to only grab sections of code. These tags must be present in the code files.

   In literalincludes, use the following syntax:

   :code-block: rst

      .. literalinclude:: python_file.py
         :language: python
         :start-after: # my-start-comment
         :end-before: # my-end-comment

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

Note - should we do this? It hides important content and is not super intuitive to me without a preview... I default to no unless the content is very skippable. 

.. tabs::

   .. tab:: Rendered

      .. admonition:: Python Plugin Code (long)
         :class: dropdown code-panel python

         .. literalinclude:: ../../../examples/tutorials/tutorial_1/plugin_3.py
            :language: python
            :linenos:

   .. tab:: RST Source

      .. code-block:: rst

         .. admonition:: Python Plugin Code (long)
            :class: dropdown code-panel python

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
   (``.. _label-name:``) in the .rst file. Without a label, ``:link-type: ref`` cannot resolve.

   Place the label near the top of the file you want to link to. For example:

   .. code-block:: rst

      .. _tutorial-1:

      Tutorial 1
      ==========

      Continue with the rest of the document...

   Notice that the reference does not include the leading underscore. You are also able to link to specific section headers and figures.

Sphinx Page Options
~~~~~~~~~~~~~~~~

1. **Remove the page specific table of contents** on the right-hand side:

   - Place ``:html_theme.sidebar_secondary.remove:`` in the .rst file, ideally at the top.


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
~~~~~~~~~~~~~~~~

Headings should be nested consistently.

- ``=`` for page title
- ``-`` for H2
- ``~`` for H3
- ``^`` for H4


Standardized Dioptra Terminology
----------------

Be specific and consistent when referring to Dioptra concepts and components. 

**Plugins**:

- ``Plugin Task``: A single Python function within a Plugin file, used in Entrypoints
- ``Plugin Task Input``: An input into a Plugin Task (i.e. a Python argument)
- ``Plugin Task Output``: The output of a Plugin Task. Can be fed in as a Plugin Task Input via the Entrypoint Task Graph 
- ``Plugin``: A collection of Python files which contain Plugin Tasks and/or Artifact Plugin Tasks 
- ``Plugin Parameter Type``: Either a built-in or user-defined type, used for Entrypoint validation 


**Artifacts**:

- ``Artifact Plugin``: (?) A subtype of a ``Plugin`` that specifically contains Artifact Plugin Tasks. 
- ``Artifact``: The output of a Plugin Task that has been saved to disk 
- ``Artifact Type``: A subclass of ArtifactTaskInterface, defining serialization / deserialization logic 
- ``Artifact Task``: The serialize method for an Artifact Type, used in the Artifact Output Graph 
- ``Artifact Task Input``: An input into the serialization method of an Artifact Type / Artifact Task. Can be a parameter, an artifact, or Plugin Task Output
- ``Artifact Task Output Parameter``: *TBD* (?)

**Entrypoints**:

- ``Entrypoint``: Define parameterizable workflows 
- ``Entrypoint Parameter``: An input used for the Entrypoint Task Graph and the Artifact Output Graph that can be customized during a Job run 
- ``Entrypoint Artifact Parameter``: A kind of Entrypoint Parameter that is assigned to a snapshot of an Artifact
- ``Entrypoint Task Graph``: The sequence of Plugin Tasks an Entrypoint executes, written in YAML
- ``Entrypoint Task Graph Step``: A single step in the Entrypoint Task Graph, which must have a name
- ``Entrypoint Artifact Output Graph``: The logic dictating which Plugin Task outputs are saved to Artifacts and how

**Experiments/Jobs**:

- ``Experiment``: A container that holds Entrypoints and Jobs 
- ``Job``: A parameterized run of an Entrypoint 

**Other**:

- ``Metric``: *TBD*
- ``Snapshot`` (Artifact, Plugin, Entrypoint?): A specific version of an item in time 
- ``Queue``: *TBD* 
- ``Worker``: *TBD* 
- ``User``: *TBD* 
- ``Groups``: *TBD* 
- ``Models``: *TBD* 
- ``Tags``: *TBD* 


.. note:: 
   These terms should (shouldn't?) be capitalized.


Author checklist
----------------

- Did you read the Diátaxis guide for your documentation type?
- Does the page belong to **one** Diátaxis type?  
- Are links used instead of duplication of content?  
