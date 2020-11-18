#!/usr/bin/env python
# type: ignore

import os
import shutil
from pathlib import Path

import setuptools


class Clean(setuptools.Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for subdir in (NAME, "app"):
            for root, dirs, files in os.walk(
                os.path.join(os.path.dirname(__file__), subdir)
            ):
                for dir_ in dirs:
                    if dir_ == "__pycache__":
                        shutil.rmtree(os.path.join(root, dir_))


def _discover_packages(packages, setup_dirname):
    modules = []

    for package in packages:
        for root, _, files in os.walk(Path(setup_dirname) / package):
            pdir = os.path.relpath(root, setup_dirname)
            modname = pdir.replace(os.sep, ".")
            modules.append(modname)

    return modules


def _extract_version(release):
    return ".".join(release.split(".")[:2])


NAME = "mitre-securing-ai"
MAINTAINER = "James Glasbrenner"
MAINTAINER_EMAIL = "jglasbrenner@mitre.org"
DESCRIPTION = "Source code powering the Securing AI Lab architecture."
URL = "https://gitlab.mitre.org/secure-ai/securing-ai-lab-components"
PROJECT_URLS = {
    "Changelog": "https://gitlab.mitre.org/secure-ai/securing-ai-lab-components/blob/master/CHANGELOG.md",
    "Issue Tracker": "https://gitlab.mitre.org/secure-ai/securing-ai-lab-components/issues",
}
RELEASE = "0.0.0"
VERSION = _extract_version(RELEASE)
CLASSIFIERS = [
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.7",
]

PYTHON_REQUIRES = ">=3.7"
INCLUDE_PACKAGE_DATA = True
ZIP_SAFE = True
DEPENDENCIES = [
    "boto3>=1.16.0",
    "Click>=7.1.0",
    "Flask>=1.1.0",
    "injector>=0.18.0",
    "mlflow>=1.11.0",
    "numpy>=1.19.0",
    "pandas>=1.1.0",
    "pyarrow>=2.0.0",
    "pyzmq>=18.1.0",
    "redis>=3.5.0",
    "rq>=1.5.0",
    "scipy==1.4.1",
    "structlog>=20.1.0",
    "typing-extensions>=3.7.4.0",
    "werkzeug>=1.0.0",
]
PACKAGE_DIR = {"": "src"}
PACKAGES = [
    Path("mitre") / "securingai" / "restapi",
    Path("mitre") / "securingai" / "plugins" / "mlflow_plugins",
]
PY_MODULES = [
    pypath.stem for pypath in (Path("src") / "mitre" / "securingai").glob("*.py")
]
ENTRY_POINTS = {
    "mlflow.project_backend": (
        "securingai=mitre.securingai.plugins.mlflow_plugins.securingai_backend"
        ":SecuringAIProjectBackend"
    )
}

CMDCLASS = {"clean": Clean}
COMMAND_OPTIONS = {}
EXTRAS_DEPENDENCIES = {
    "restapi": [
        "flask-accepts>=0.17.0",
        "Flask-Injector>=0.12.0",
        "Flask-SQLAlchemy>=2.4.0",
        "flask-restx>=0.2.0",
        "marshmallow>=3.9.0",
        "psycopg2>=2.8.0",
        "sqlalchemy<=1.3.13",
    ],
    "docs": [
        "markdown",
        "plantuml-markdown",
        "pymdown-extensions",
        "recommonmark",
        "sphinx",
        "sphinx-rtd-theme",
        "sphinx-book-theme",
    ],
    "dev": [
        "autopep8",
        "black",
        "commitizen",
        "coverage",
        "docker-py",
        "entrypoints",
        "flake8-bugbear",
        "flake8",
        "freezegun",
        "ghp-import",
        "ipython",
        "mypy",
        "pre-commit",
        "pycodestyle",
        "pydocstyle",
        "pytest",
        "pytest-cov",
        "pytest-datadir",
        "pytoml",
        "seed-isort-config",
        "setuptools-scm",
        "testinfra",
        "twine",
        "tox",
    ],
}

SETUP_DIRNAME = Path(__file__).parent / "src"

if not SETUP_DIRNAME:
    SETUP_DIRNAME = os.getcwd()

setuptools.setup(
    name=NAME,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    version=RELEASE,
    url=URL,
    project_urls=PROJECT_URLS,
    description=DESCRIPTION,
    entry_points=ENTRY_POINTS,
    packages=_discover_packages(PACKAGES, SETUP_DIRNAME),
    package_dir=PACKAGE_DIR,
    py_modules=PY_MODULES,
    include_package_data=INCLUDE_PACKAGE_DATA,
    setup_requires=DEPENDENCIES,
    zip_safe=ZIP_SAFE,
    install_requires=DEPENDENCIES,
    extras_require=EXTRAS_DEPENDENCIES,
    cmdclass=CMDCLASS,
    command_options=COMMAND_OPTIONS,
    python_requires=PYTHON_REQUIRES,
    classifiers=CLASSIFIERS,
)
