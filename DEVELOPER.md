# Developer Guide

If you have not already, please review [CONTRIBUTING.md](CONTRIBUTING.md) for more complete information on expectations for contributions.

## Developer quickstart

### Setting up the Python virtual environment

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

### Frontend development setup

For instructions on how to prepare the frontend development environment, [see the src/frontend/README.md file](src/frontend/README.md)

### Building the documentation

This project uses Sphinx to generate the documentation published at <https://pages.nist.gov/dioptra>.
To build the documentation locally, activate your virtual environment if you haven't already and run:

```sh
python -m tox run -e web-compile,docs
```

Alternatively, you can also use `make` to do this:

```sh
make docs
```

### Reformatting code with black and isort

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

### Checking your code with flake8 and mypy

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

### Checking your commit message with gitlint

This project has a [commit style guide](./COMMIT_STYLE_GUIDE.md) that is enforced using the `gitlint` tool.
Developers are expected to run `gitlint` and validate their commit message before opening a Pull Request.
After committing your contribution, activate your virtual environment if you haven't already and run:

```sh
python -m tox run -e gitlint
```

Alternatively, you can also use `make` to do this:

```sh
make commit-check
```

### Running unit tests with pytest

This project stores its unit tests in the `tests/` folder and runs them using pytest.
Developers are expected to create new unit tests to validate any new features or behavior that they contribute and to verify that all unit tests pass before opening a Pull Request.
To run the unit tests, activate your virtual environment if you haven't already and run:

```sh
python -m tox run -e py311-pytest -- tests/unit
python -m tox run -e py311-cookiecutter
```

Alternatively, you can also use `make` to do this:

```sh
make tests-unit
```

### Cleanup

Run the following to clear away the project's temporary files, which includes the sentinel dotfiles that are created in `build/` when using `make`:

```sh
make clean
```
