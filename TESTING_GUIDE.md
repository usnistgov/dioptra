# Testing Guide

Prior to finalizing a submission, tests need to be written to cover new code. What follows is a process outlining test creation.

## User Stories

The first step is to define a user story for the feature in question. We follow a simplified user story model:

    Scenario: (FEATURE)
        Given (Pre-conditions),
        I need to be able to (perform a user action)
        in order to (perform an internal action), (optional: specify variables).

Example:

    Scenario: Registering an Experiment
        Given I am an authorized user,
        I need to be able to submit a register request,
        in order to register an experiment with a provided name.

Once the user story has been created you can use it as a framework to create your tests.

## Creating the Test

Tests are organized in the [tests](./tests) directory based on their scope (unit, integration, etc.) and what they are testing (restapi, task_engine, etc.).

### Unit Tests

Create a file in the subdirectory of [unit](./tests/unit) which matches your test's conditions with the name "test_(feature).py". This will be the main file where you implement your test.

### Integration Tests

Create a folder in [integration](./tests/integration). This will encapsulate the integration test and will be where the "test_(feature).py" files, conftest.py, and other relevant files are stored.

### Test Files

Test files are organized into 3 main sections: actions, assertions, and tests.

The actions section encompasses functions which directly perform the action they are testing (i.e. the second line in our user story). Using restapi tests as an example, these functions would directly interact with the api by performing a POST, PUT or DELETE.

The assertions section encompasses functions which perform assert statements and check retrieved values against expected ones (this checks the third line in our user story). Again using restapi tests as an example, these functions would perform a GET to retrieve an object and then check it against an expected value within an assert.

The tests section encompasses functions which act as the main test for each feature. They call functions within the actions and assertions sections to fully test the feature. For readability and clarity, include the user story and describe the specific actions being performed within the test in the function docstring. Any feature-specific variables should be defined here. The expected output from the test is defined here and passed to the assertion function.

For a detailed example on how to implement a test file, refer to [test_experiment.py](./tests/unit/restapi/test_experiment.py)

### Conftest.py

PyTest allows for the creation of fixtures to address any pre-conditions or variables that are required for tests to function (i.e. the first line in our user story). They are placed within a [conftest.py](./tests/unit/restapi/conftest.py) file. For unit tests you can add on to the conftest in the relevant subdirectory. Integrations tests will require a new conftest to be defined in their folder. Refer to one of the conftests for help with implementation.

## Running the Test

Tests can be using the following command:

```sh
python -m tox run -e py39-pytest-cov
```

This will give you a code coverage report and run the test to determine if it is successful.
