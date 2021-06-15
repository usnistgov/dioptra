# Dioptra

The project documentation is available at https://pages.nist.gov/dioptra/.

To build the documentation locally, they are in the `docs` folder and compiled using Sphinx, make sure you have Docker installed and try to pull the builder images:

    make pull-latest-ci

If you do not have access to the project's Docker registry, then you can build and tag them manually:

    make build-ci tag-latest-ci

The documentation can then be built with,

    make docs

When the build is done, open `docs/build/index.html` in your web browser.

## License

[![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

This Software (Dioptra) is being made available as a public service by the [National Institute of Standards and Technology (NIST)](https://www.nist.gov/), an Agency of the United States Department of Commerce.
This software was developed in part by employees of NIST and in part by NIST contractors.
Copyright in portions of this software that were developed by NIST contractors has been licensed or assigned to NIST.
Pursuant to Title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.
However, NIST may hold international copyright in software created by its employees and domestic copyright (or licensing rights) in portions of software that were assigned or licensed to NIST.
To the extent that NIST holds copyright in this software, it is being made available under the [Creative Commons Attribution 4.0 International license (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/). The disclaimers of the CC BY 4.0 license apply to all parts of the software developed or licensed by NIST.
