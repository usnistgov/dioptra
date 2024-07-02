# Dioptra: Test Software for the Characterization of AI Technologies

Dioptra is a software test bed for assessing the trustworthy characteristics of artificial intelligence (AI).
Trustworthy AI is: valid and reliable, safe, fair and bias is managed, secure and resilient, accountable and transparent, explainable and interpretable, and privacy-enhanced. [1](https:// [1](https:/st.gov/system/files/documents/2022/08/18/AI_RMF_2nd_draft.pdf)
Dioptra supports the Measure function of the [NIST AI Risk Management Framework](https:/https:/st.gov/itl/ai-risk-management-framework/) by providing functionality to assess, analyze, and track identified AI risks.

Dioptra provides a REST API, which can be controlled via an intuitive web interface or python client, for designing, managing, executing, and tracking experiments.
Details are available in the project documentation available at https://pages.nist.gov/dioptra/.

## Use Cases
We envision the following primary use cases for Dioptra:
- Model Testing
    - 1st party - Assess AI models throughout the development lifecycle
    - 2nd party - Assess AI models during acquisition or in an evaluation lab environment
    - 3rd party - Assess AI models during auditing or compliance activities
- Research - Aid trustworthy AI researchers in tracking experiments
- Evaluations and Challenges - Provide a common platform and resources for participants
- Red-Teaming - Expose models and resources to a red team in a controlled environment

## Key Properties
Dioptra strives for the following key properties:
- Reproducible - Dioptra automatically creates snapshots of resources so experiments and be reproduced and validated
- Traceable - The full history of experiments and their inputs are tracked
- Extensible - Support for expanding functionality and importing existing Python packages via a plugin system
- Interoperable - A type system promotes interoperability between plugins
- Modular - New experiments can be composed from modular components in a simple yaml file
- Secure - Dioptra provides user authentication with access controls coming soon
- Interactive - Users can interact with Dioptra via an intuitive web interface or the python client
- Shareable and Reusable - Dioptra provides a multi-tenant environment so users can share and reuse components


## Instructions

<!-- markdownlint-disable MD007 MD030 -->
- [User setup](#user-setup)
    - [Build the containers](#build-the-containers)
    - [Runn Dioptra](#run-dioptra)
- [User quickstart](#user-quickstart)
- [Developer quickstart](#developer-quickstart)
    - [Setting up the Python virtual environment](#setting-up-the-python-virtual-environment)
    - [Frontend development setup](#frontend-development-setup)
    - [Building the documentation](#building-the-documentation)
    - [Reformatting code with black and isort](#reformatting-code-with-black-and-isort)
    - [Checking your code with flake8 and mypy](#checking-your-code-with-flake8-and-mypy)
    - [Checking your commit message with gitlint](#checking-your-commit-message-with-gitlint)
    - [Running unit tests with pytest](#running-unit-tests-with-pytest)
    - [Cleanup](#cleanup)
- [License](#license)
<!-- markdownlint-enable MD007 MD030 -->

### User setup

If you are have been provided with an existing Dioptra deployment, skip ahead to the [User quickstart](#user-quickstart) section.

#### Build the Containers

The first step in setting up Dioptra is to clone the repository and build the docker containers for the various services that are part of a deployment.
See the [Building the Containers](https://pages.nist.gov/dioptra/getting-started/building-the-containers.html) section of the documentation for instructions.

#### Run Dioptra

Once the containers have been built, the next step is to configure the deployment with cruft and run Dioptra.
See the [Running Dioptra](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html) section of the documentation for instructions

Additionally, you may want to add datasets and configure some of the provided examples in your deployment. See...


### User quickstart


Read through the user guide starting with [the basics](https://pages.nist.gov/dioptra/user-guide/the-basics.html) to become familiar with the core concepts of Dioptra.

Register a user account with your Dioptra instance via either the web interface or python client.

Consider exploring the example
https://github.com/usnistgov/dioptra/tree/main/examples


### Developer quickstart

#### Setting up the Python virtual environment

Developers must use Python 3.11 and create a virtual environment using one of the requirements.txt files in the `requirements/` directory in order to make contributions to this project.
Ensure that you have Python 3.11 installed and that it is available in your PATH, and then identify the requirements file that you want to use:

| Filename | OS | Architecture | Tensorflow | PyTorch |
| :--- | :---: | :---: | :--- | :--- |
| linux-amd64-py3.11-requirements-dev.txt | Linux | x86-64 | ❌ | ❌ |
| linux-amd64-py3.11-requirements-dev-tensorflow.txt | Linux | x86-64 | ✅ | ❌ |
| linux-amd64-py3.11-requirements-dev-pytorch.txt | Linux | x86-64 | ❌ | ✅ |
| linux-arm64-py3.11-requirements-dev.txt | Linux | arm64 | ❌ | ❌ |
| linux-arm64-py3.11-requirements-dev-tensorflow.txt | Linux | arm64 | ✅ | ❌ |
| linux-arm64-py3.11-requirements-dev-pytorch.txt | Linux | arm64 | ❌ | ✅ |
| macos-amd64-py3.11-requirements-dev.txt | MacOS | x86-64 | ❌ | ❌ |
| macos-amd64-py3.11-requirements-dev-tensorflow.txt | MacOS | x86-64 | ✅ | ❌ |
| macos-amd64-py3.11-requirements-dev-pytorch.txt | MacOS | x86-64 | ❌ | ✅ |
| macos-arm64-py3.11-requirements-dev.txt | MacOS | arm64 | ❌ | ❌ |
| macos-arm64-py3.11-requirements-dev-tensorflow.txt | MacOS | arm64 | ✅ | ❌ |
| macos-arm64-py3.11-requirements-dev-pytorch.txt | MacOS | arm64 | ❌ | ✅ |
| win-amd64-py3.11-requirements-dev.txt | Windows | x86-64 | ❌ | ❌ |
| win-amd64-py3.11-requirements-dev-tensorflow.txt | Windows | x86-64 | ✅ | ❌ |
| win-amd64-py3.11-requirements-dev-pytorch.txt | Windows | x86-64 | ❌ | ✅ |

Next, use the `venv` module to create a new virtual environment:

```sh
python -m venv .venv
```

Activate the virtual environment after creating it.
To activate it on MacOS/Linux:

```sh
source .venv/bin/activate
```

To activate it on Windows:

```powershell
.venv\Scripts\activate
```

Next, upgrade `pip` and install `pip-tools`:

```sh
python -m pip install --upgrade pip pip-tools
```

Finally, use `pip-sync` to install the dependencies in your chosen requirements file and install `dioptra` in development mode.
On MacOS/Linux:

```sh
# Replace "linux-amd64-py3.11-requirements-dev.txt" with your chosen file
pip-sync requirements/linux-amd64-py3.11-requirements-dev.txt
```

On Windows:

```powershell
# Replace "win-amd64-py3.11-requirements-dev.txt" with your chosen file
pip-sync requirements\win-amd64-py3.11-requirements-dev.txt
```

If the requirements file you used is updated, or if you want to switch to another requirements file (you need access to the Tensorflow library, for example), just run `pip-sync` again using the appropriate filename.
It will install, upgrade, and uninstall all packages accordingly and ensure that you have a consistent environment.

#### Frontend development setup

For instructions on how to prepare the frontend development environment, [see the src/frontend/README.md file](src/frontend/README.md)

#### Building the documentation

This project uses Sphinx to generate the documentation published at <https://pages.nist.gov/dioptra>.
To build the documentation locally, activate your virtual environment if you haven't already and run:

```sh
python -m tox run -e web-compile,docs
```

Alternatively, you can also use `make` to do this:

```sh
make docs
```

#### Reformatting code with black and isort

This project uses `black` and `isort` to automatically format Python code:
Developers are expected to run `black` and `isort` over their contributions before opening a Pull Request.
To do this, activate your virtual environment if you haven't already and run:

```sh
# Run black to reformat code
python -m tox run -e black -- src/dioptra task-plugins/dioptra_builtins tests

# Run isort to reformat import statements
python -m tox run -e isort -- src/dioptra task-plugins/dioptra_builtins tests
```

Alternatively, you can also use `make` to do this:

```sh
make beautify
```

#### Checking your code with flake8 and mypy

This project uses `flake8` as a code linter and `mypy` to perform static type checking.
Developers are expected to run `flake8` and `mypy` and resolve all issues before opening a Pull Request.
To do this, activate your virtual environment if you haven't already and run:

```sh
# Lint the code
python -m tox run -e flake8

# Perform static type checking
python -m tox run -e mypy
```

Alternatively, you can also use `make` to do this:

```sh
make code-check
```

#### Checking your commit message with gitlint

This project has a [commit style guide](./COMMIT_STYLE_GUIDE.md) that is enforced using the `gitlint` tool.
Developers are expected to run `gitlint` and validate their commit message before opening a Pull Request.
After commiting your contribution, activate your virtual environment if you haven't already and run:

```sh
python -m tox run -e gitlint
```

Alternatively, you can also use `make` to do this:

```sh
make commit-check
```

#### Running unit tests with pytest

This project stores its unit tests in the `tests/` folder and runs them using pytest.
Developers are expected to create new unit tests to validate any new features or behavior that they contribute and to verify that all unit tests pass before opening a Pull Request.
To run the unit tests, activate your virtual environment if you haven't already and run:

```sh
python -m tox run -e py39-pytest -- tests/unit
python -m tox run -e py39-cookiecutter
```

Alternatively, you can also use `make` to do this:

```sh
make tests-unit
```

#### Cleanup

Run the following to clear away the project's temporary files, which includes the sentinel dotfiles that are created in `build/` when using `make`:

```sh
make clean
```

### License

[![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

This Software (Dioptra) is being made available as a public service by the [National Institute of Standards and Technology (NIST)](https://www.nist.gov/), an Agency of the United States Department of Commerce.
This software was developed in part by employees of NIST and in part by NIST contractors.
Copyright in portions of this software that were developed by NIST contractors has been licensed or assigned to NIST.
Pursuant to Title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.
However, NIST may hold international copyright in software created by its employees and domestic copyright (or licensing rights) in portions of software that were assigned or licensed to NIST.
To the extent that NIST holds copyright in this software, it is being made available under the [Creative Commons Attribution 4.0 International license (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/).
The disclaimers of the CC BY 4.0 license apply to all parts of the software developed or licensed by NIST.
