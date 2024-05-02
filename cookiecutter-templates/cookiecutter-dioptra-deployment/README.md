# cookiecutter-dioptra-deployment

A Cookiecutter template that generates the scripts, configuration files, and Docker Compose files needed to run Dioptra on a single machine.

## Prerequisites

-   [Bash v5 or higher](https://tiswww.case.edu/php/chet/bash/bashtop.html)
-   [Python 3.11 or higher](https://www.python.org/)
-   [Cruft 2.15.0 or higher](https://cruft.github.io/cruft/)
-   [Docker Engine 20.10.13 or higher](https://docs.docker.com/engine/install/)
-   [Docker Compose](https://docs.docker.com/compose/install/)
-   Dictionary of words at `/usr/share/dict/words` (`apt-get install wamerican`)
-   [Working builds of the Dioptra container images](https://pages.nist.gov/dioptra/getting-started/building-the-containers.html)

## Usage

Open a terminal and run the following to generate a setup that is appropriate for testing Dioptra on your personal computer or laptop.

```sh
# Move to the base directory where you plan to store your Dioptra
# configuration folder
mkdir -p /path/to/deployments/folder  # Create it if it doesn't exist
cd /path/to/deployments/folder

# Create a virtual environment and install cruft
python -m venv venv-cruft
source venv-cruft/bin/activate
python -m pip install --upgrade pip cruft

# Run cruft and set the template's variables
# (If using a different branch, replace "main" with that branch's name)
cruft create https://github.com/usnistgov/dioptra --checkout main \
  --directory cookiecutter-templates/cookiecutter-dioptra-deployment

# Deactivate the virtual environment
deactivate
```

This will create a Dioptra configuration folder at the path `/path/to/deployments/folder/dioptra-deployment` (`dioptra-deployment` is the default name).
See the README.md in this folder for instructions on how to start and stop Dioptra.

## Template variables

See [Running Dioptra - Applying the template](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html#applying-the-template) for a full list of template variables, their default values, and explanations of what they mean.

## License

[![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

This Software (Dioptra) is being made available as a public service by the [National Institute of Standards and Technology (NIST)](https://www.nist.gov/), an Agency of the United States Department of Commerce.
This software was developed in part by employees of NIST and in part by NIST contractors.
Copyright in portions of this software that were developed by NIST contractors has been licensed or assigned to NIST.
Pursuant to Title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.
However, NIST may hold international copyright in software created by its employees and domestic copyright (or licensing rights) in portions of software that were assigned or licensed to NIST.
To the extent that NIST holds copyright in this software, it is being made available under the [Creative Commons Attribution 4.0 International license (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/).
The disclaimers of the CC BY 4.0 license apply to all parts of the software developed or licensed by NIST.
