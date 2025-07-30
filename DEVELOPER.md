# Developer Guide

If you have not already, please review [CONTRIBUTING.md](CONTRIBUTING.md) for more complete information on expectations for contributions.

## Developer Set-up
See the [Local Developer Set-up](dev-kb/local-setup/README.md) knowledge base article for
instructions.

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
python -m tox run -e py311-extra
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
