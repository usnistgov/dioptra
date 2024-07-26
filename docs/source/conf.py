# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
#
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

sys.path.insert(0, os.path.abspath("../../task-plugins"))
sys.path.insert(0, os.path.abspath("../../src"))


# -- Project information -----------------------------------------------------

project = "Dioptra"
release = "1.0.0"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "recommonmark",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_togglebutton",
    "sphinxcontrib.httpdomain",
    "sphinxcontrib.openapi",
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
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "dev-guide", "getting-started/installation.rst"]

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

html_css_files = ["dioptra.css"]

html_js_files = [
    "jquery.visible.js",
    "jquery.leaveNotice-nist.js",
    "applyLeaveNotice.js",
    "smoothNavScroll.js",
]

html_theme_options = {
    "repository_url": "https://github.com/usnistgov/dioptra",
    "repository_branch": "main",
    "use_repository_button": True,
    "home_page_in_toc": True,
    "path_to_docs": "docs/source",
}

# -- Extension configuration -------------------------------------------------

# -- Options for autodoc extension -------------------------------------------

autoclass_content = "class"
autodoc_mock_imports = [
    "alembic",
    "art",
    "botocore",
    "boto3",
    "entrypoints",
    "flask_injector",
    "flask_migrate",
    "flask_sqlalchemy",
    "injector",
    "mlflow",
    "numpy",
    "pandas",
    "passlib",
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

# -- Options for intersphinx extension ---------------------------------------

intersphinx_mapping = {
    "alembic": ("https://alembic.sqlalchemy.org/en/latest/", None),
    "art": (
        "https://adversarial-robustness-toolbox.readthedocs.io/en/latest/",
        None,
    ),
    "boto3": ("https://boto3.amazonaws.com/v1/documentation/api/latest/", None),
    "click": ("https://click.palletsprojects.com/en/8.1.x/", None),
    "flask": ("https://flask.palletsprojects.com/en/2.1.x/", None),
    "flask_migrate": ("https://flask-migrate.readthedocs.io/en/latest/", None),
    "flask_restx": ("https://flask-restx.readthedocs.io/en/latest/", None),
    "flask_sqlalchemy": ("https://flask-sqlalchemy.palletsprojects.com/en/2.x/", None),
    "injector": ("https://injector.readthedocs.io/en/latest/", None),
    "marshmallow": ("https://marshmallow.readthedocs.io/en/stable/", None),
    "mlflow": ("https://mlflow.org/docs/latest/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "python": ("https://docs.python.org/3/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/14/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "sklearn": ("https://scikit-learn.org/1.0/", None),
    "structlog": ("https://www.structlog.org/en/stable/", None),
}

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
