# Dioptra: Test Software for the Characterization of AI Technologies

The code is currently in a _pre-release_ status.
There is enough functionality to demonstrate the direction of the project, but the software is currently missing functionality that would provide a robust security model for deployment within an enterprise.

The project documentation is available at https://pages.nist.gov/dioptra/.

## User setup

For instructions on how to build and run a fresh instance of Dioptra, see [cookiecutter-templates/README.md](cookiecutter-templates/README.md) and the [Building the containers](https://pages.nist.gov/dioptra/getting-started/building-the-containers.html) and [Running Dioptra](https://pages.nist.gov/dioptra/getting-started/running-dioptra.html) sections of the published documentation.

## Developer setup

### Python virtual environment

Ensure a Python interpreter version 3.9 or higher is in your PATH, and then run the following,

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,sdk]"
```

### Frontend development setup

For instructions on how to prepare the frontend development environment, [see the src/frontend/README.md file](src/frontend/README.md)

## License

[![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

This Software (Dioptra) is being made available as a public service by the [National Institute of Standards and Technology (NIST)](https://www.nist.gov/), an Agency of the United States Department of Commerce.
This software was developed in part by employees of NIST and in part by NIST contractors.
Copyright in portions of this software that were developed by NIST contractors has been licensed or assigned to NIST.
Pursuant to Title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.
However, NIST may hold international copyright in software created by its employees and domestic copyright (or licensing rights) in portions of software that were assigned or licensed to NIST.
To the extent that NIST holds copyright in this software, it is being made available under the [Creative Commons Attribution 4.0 International license (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/).
The disclaimers of the CC BY 4.0 license apply to all parts of the software developed or licensed by NIST.
