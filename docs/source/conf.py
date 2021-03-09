# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../../task-plugins"))
sys.path.insert(0, os.path.abspath("../../src"))


# -- Project information -----------------------------------------------------

project = "Securing AI Testbed"
release = "0.0.0"
version = ".".join(release.split(".")[:2])


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "recommonmark",
    "sphinx_copybutton",
    "sphinx_panels",
    "sphinx_togglebutton",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

add_module_names = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
on_rtd = os.environ.get("READTHEDOCS") == "True"
html_theme = "sphinx_book_theme"
# if on_rtd:
#     html_theme = "default"

# else:
#     html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# html_context = {
#     "css_files": ["_static/theme_overrides.css"]  # override wide tables in RTD theme
# }

html_theme_options = {
    "repository_url": "https://gitlab.mitre.org/secure-ai/securing-ai-lab-components",
    "repository_branch": "master",
    "use_repository_button": True,
    "home_page_in_toc": True,
    "path_to_docs": "docs/source",
}

# -- Extension configuration -------------------------------------------------

# -- Options for autodoc extension -------------------------------------------

autoclass_content = "class"
autodoc_mock_imports = [
    "alembic",
    "botocore",
    "boto3",
    "entrypoints",
    "flask_injector",
    "flask_migrate",
    "injector",
    "mlflow",
    "numpy",
    "pandas",
    "redis",
    "rq",
    "scipy",
    "sklearn",
    "structlog",
    "tensorflow",
]
autodoc_inherit_docstrings = True
autodoc_member_order = "bysource"
autodoc_typehints = "signature"

# -- Options for napoleon extension ------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

# -- Options for panels extension --------------------------------------------

panels_add_bootstrap_css = False
