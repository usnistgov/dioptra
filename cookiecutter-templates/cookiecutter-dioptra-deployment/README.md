# cookiecutter-dioptra-deployment

A [Cookiecutter](https://cookiecutter.readthedocs.io/) template that generates the scripts, configuration files, and Docker Compose files needed to run Dioptra on a single machine.

## Prerequisites

- [Python 3.11 or higher](https://www.python.org/)
- [Cruft](https://cruft.github.io/cruft/) (`pip install cruft`)
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed and running
- [Dioptra container images](https://pages.nist.gov/dioptra/how-to/setup-dioptra/get-container-images/index.html) (downloaded or built locally)
- [Bash v5 or higher](https://tiswww.case.edu/php/chet/bash/bashtop.html)
- A word dictionary at `/usr/share/dict/words` (install with `apt-get install wamerican` on Debian/Ubuntu)

## Usage

Install cruft and run it to generate the deployment folder.

```sh
# Install cookiecutter (in a virtual environment or globally)
pip install cruft

# Generate the deployment folder
# (Replace "main" with the branch that matches your container images if different)
cruft create https://github.com/usnistgov/dioptra --checkout main \
  --directory cookiecutter-templates/cookiecutter-dioptra-deployment
```

This creates a deployment folder (default name: `dioptra-deployment`).
See the README.md inside the generated folder for quick start instructions.

## Template variables

See the [Deployment Template Reference](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/deployment-template-reference.html) for a full list of template variables, their default values, and descriptions.

## License

[![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

This Software (Dioptra) is being made available as a public service by the [National Institute of Standards and Technology (NIST)](https://www.nist.gov/), an Agency of the United States Department of Commerce.
This software was developed in part by employees of NIST and in part by NIST contractors.
Copyright in portions of this software that were developed by NIST contractors has been licensed or assigned to NIST.
Pursuant to Title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.
However, NIST may hold international copyright in software created by its employees and domestic copyright (or licensing rights) in portions of software that were assigned or licensed to NIST.
To the extent that NIST holds copyright in this software, it is being made available under the [Creative Commons Attribution 4.0 International license (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/).
The disclaimers of the CC BY 4.0 license apply to all parts of the software developed or licensed by NIST.
