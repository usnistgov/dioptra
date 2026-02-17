# Dioptra: Test Software for the Characterization of AI Technologies

Dioptra is a software test platform for assessing the trustworthy characteristics of artificial intelligence (AI).
Trustworthy AI is: valid and reliable, safe, secure and resilient, accountable and transparent, explainable and interpretable, privacy-enhanced, and fair - with harmful bias managed[^1].
Dioptra supports the Measure function of the [NIST AI Risk Management Framework](https://nist.gov/itl/ai-risk-management-framework/) by providing functionality to assess, analyze, and track identified AI potential benefits and negative consequences.

Dioptra provides a REST API, which can be controlled via an intuitive web interface, a Python client, or any REST client library of the user's choice for designing, managing, executing, and tracking experiments.
Details are available in the project documentation available at <https://pages.nist.gov/dioptra/>.

[^1]: <https://doi.org/10.6028/NIST.AI.100-1>

<!-- markdownlint-disable MD007 MD030 -->
- [Current Release Status](#current-release-status)
- [Use Cases](#use-cases)
- [Key Properties](#key-properties)
- [Usage Instructions](#usage-instructions)
- [Develop Dioptra](#develop-dioptra)
- [License](#license)
- [How to Cite](#how-to-cite)
<!-- markdownlint-enable MD007 MD030 -->

## Current Release Status

Release 1.1.0-dev -- with on-going improvements and development

## Use Cases

We envision the following primary use cases for Dioptra:

-   Model Testing:
    -   1st party - Assess AI models throughout the development lifecycle
    -   2nd party - Assess AI models during acquisition or in an evaluation lab environment
    -   3rd party - Assess AI models during auditing or compliance activities
-   Research: Aid trustworthy AI researchers in tracking experiments
-   Evaluations and Challenges: Provide a common platform and resources for participants
-   Red-Teaming: Expose models and resources to a red team in a controlled environment

## Key Properties

Dioptra strives for the following key properties:

-   Reproducible: Dioptra automatically creates snapshots of resources so experiments can be reproduced and validated
-   Traceable: The full history of experiments and their inputs are tracked
-   Extensible: Support for expanding functionality and importing existing Python packages via a plugin system
-   Interoperable: A type system promotes interoperability between plugins
-   Modular: New experiments can be composed from modular components in a simple yaml file
-   Secure: Dioptra provides user authentication with access controls coming soon
-   Interactive: Users can interact with Dioptra via an intuitive web interface
-   Shareable and Reusable: Dioptra can be deployed in a multi-tenant environment so users can share and reuse components

## Usage Instructions

### Install Dioptra

See the [Install Dioptra](https://pages.nist.gov/dioptra/getting-started/install-dioptra-explanation.html) section of the documentation for more detailed instructions.

1. Pull the Dioptra docker images:
```sh
# pull the core dioptra images:
docker pull ghcr.io/usnistgov/dioptra/nginx:1.1.0
docker pull ghcr.io/usnistgov/dioptra/mlflow-tracking:1.1.0
docker pull ghcr.io/usnistgov/dioptra/restapi:1.1.0

# pull the worker images:
docker pull ghcr.io/usnistgov/dioptra/pytorch-cpu:1.1.0
docker pull ghcr.io/usnistgov/dioptra/tensorflow2-cpu:1.1.0

# optionally pull the GPU worker images:
docker pull ghcr.io/usnistgov/dioptra/pytorch-gpu:1.1.0
docker pull ghcr.io/usnistgov/dioptra/tensorflow2-gpu:1.1.0
```

2. Prepare your Dioptra deployment:
```sh
cruft create https://github.com/usnistgov/dioptra --checkout main \
  --directory cookiecutter-templates/cookiecutter-dioptra-deployment
```

3. Initialize your Dioptra deployment:
```sh
cd dioptra-deployment  # Or your deployment folder name
./init-deployment.sh --branch main
```

4. Run Dioptra
```
docker compose up -d
```

Your Dioptra deployment is now accessible at `http://localhost`. We recommend getting started with the [Hello World Tutorial](https://pages.nist.gov/dioptra/tutorials/hello_world/index.html)

## Develop Dioptra

If you are interested in contributing to Dioptra, please see the [Developer Guide](DEVELOPER.md)

## License

[![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

This Software (Dioptra) is being made available as a public service by the [National Institute of Standards and Technology (NIST)](https://www.nist.gov/), an Agency of the United States Department of Commerce.
This software was developed in part by employees of NIST and in part by NIST contractors.
Copyright in portions of this software that were developed by NIST contractors has been licensed or assigned to NIST.
Pursuant to Title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States.
However, NIST may hold international copyright in software created by its employees and domestic copyright (or licensing rights) in portions of software that were assigned or licensed to NIST.
To the extent that NIST holds copyright in this software, it is being made available under the [Creative Commons Attribution 4.0 International license (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/).
The disclaimers of the CC BY 4.0 license apply to all parts of the software developed or licensed by NIST.

## How to Cite

Glasbrenner, James, Booth, Harold, Manville, Keith, Sexton, Julian, Chisholm, Michael Andy, Choy, Henry, Hand, Andrew, Hodges, Bronwyn, Scemama, Paul, Cousin, Dmitry, Trapnell, Eric, Trapnell, Mark, Huang, Howard, Rowe, Paul, Byrne, Alex (2024), Dioptra Test Platform, National Institute of Standards and Technology, https://doi.org/10.18434/mds2-3398 (Accessed 'Today's Date')

N.B.: Replace 'Today's Date' with today's date
