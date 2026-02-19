# custom-dioptra-worker

A [Cookiecutter](https://cookiecutter.readthedocs.io/) template that generates the files needed to build a custom Dioptra worker container image.
Use this when you need a worker with Python packages or other software that is not available in the standard Dioptra worker images.

## Prerequisites

- [Python 3.11 or higher](https://www.python.org/)
- [Cookiecutter](https://cookiecutter.readthedocs.io/) (`pip install cookiecutter`)
- [Docker](https://docs.docker.com/get-docker/) installed and running

## Usage

Install cookiecutter and run it to generate the project folder.

```sh
# Install cookiecutter (in a virtual environment or globally)
pip install cookiecutter

# Generate the project folder
# (Replace "main" with the branch that matches your deployment if different)
cookiecutter https://github.com/usnistgov/dioptra --checkout main \
  --directory cookiecutter-templates/custom-dioptra-worker
```

You will be prompted for a project name, which is used to create the project folder.
See the README.md inside the generated folder for quick start instructions.

## Template variables

See the [Custom Worker Template Reference](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/custom-worker-template-reference.html) for a full list of template variables, their default values, and descriptions.

## License

[![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

This Software (Dioptra) is being made available as a public service by the [National Institute of Standards and Technology (NIST)](https://www.nist.gov/), an Agency of the United States Department of Commerce.
This software was developed in part by employees of NIST and in part by NIST contractors.
Copyright in portions of this software that were developed by NIST contractors has been licensed or assigned to NIST.
Pursuant to Title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.
However, NIST may hold international copyright in software created by its employees and domestic copyright (or licensing rights) in portions of software that were assigned or licensed to NIST.
To the extent that NIST holds copyright in this software, it is being made available under the [Creative Commons Attribution 4.0 International license (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/).
The disclaimers of the CC BY 4.0 license apply to all parts of the software developed or licensed by NIST.
