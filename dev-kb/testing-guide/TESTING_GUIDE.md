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
python -m tox run -e py311-pytest-cov
```

This will give you a code coverage report and run the test to determine if it is successful. The progress report will look similar to the following:

```sh
=============================================== test session starts ===============================================
platform darwin -- Python 3.11.10, pytest-8.3.5, pluggy-1.5.0
cachedir: .tox/py311-pytest-cov/.pytest_cache
rootdir: /Users/dac4/di2run/dio-src
configfile: pyproject.toml
testpaths: tests/unit
plugins: cov-6.0.0, datadir-1.6.1, anyio-4.9.0, Faker-37.0.2, time-machine-2.16.0
collected 637 items                                                                                               

tests/unit/client/test_utils.py ..........................                                                  [  4%]
tests/unit/pyplugs/test_plugins.py ..............................                                           [  8%]
tests/unit/restapi/test_app.py ..                                                                           [  9%]
tests/unit/restapi/test_db_models.py ................sssssss                                                [ 12%]
tests/unit/restapi/test_depth_limited_repr.py .....................                                         [ 16%]
tests/unit/restapi/test_signature_analysis.py .................                                             [ 18%]
tests/unit/restapi/test_utils.py .                                                                          [ 18%]
tests/unit/restapi/v1/test_artifact.py .........                                                            [ 20%]
tests/unit/restapi/v1/test_entrypoint.py ...........................                                        [ 24%]
tests/unit/restapi/v1/test_experiment.py ............sss.........                                           [ 28%]
tests/unit/restapi/v1/test_group.py s..ss                                                                   [ 29%]
tests/unit/restapi/v1/test_io_file_service.py ......ssss.                                                   [ 30%]
tests/unit/restapi/v1/test_job.py ................                                                          [ 33%]
tests/unit/restapi/v1/test_model.py ...................                                                     [ 36%]
tests/unit/restapi/v1/test_plugin.py ...................................................................... [ 47%]
                                                                                                            [ 47%]
tests/unit/restapi/v1/test_plugin_parameter_type.py .................                                       [ 49%]
tests/unit/restapi/v1/test_queue.py ...............                                                         [ 52%]
tests/unit/restapi/v1/test_tag.py .........                                                                 [ 53%]
tests/unit/restapi/v1/test_user.py ...........                                                              [ 55%]
tests/unit/restapi/v1/workflows/test_resource_import.py .....                                               [ 56%]
tests/unit/restapi/v1/workflows/test_signature_analysis.py .                                                [ 56%]
tests/unit/sdk/utilities/paths/test_clear_directory.py .                                                    [ 56%]
tests/unit/sdk/utilities/paths/test_set_path_ext.py ..................                                      [ 59%]
tests/unit/task_engine/test_task_engine.py ......................                                           [ 62%]
tests/unit/task_engine/test_type_registry.py .................                                              [ 65%]
tests/unit/task_engine/test_type_validation.py ..................................................           [ 73%]
tests/unit/task_engine/test_types.py ...............................                                        [ 78%]
tests/unit/task_engine/test_validation.py ................................................................. [ 88%]
```

 In the compact progress report `.` means passed test, `s` indicates skipped tests, and `F` indicates failed tests. The whole test suite can take from 4 to 8 minutes of running time, depending on your workstation OS, resource availability, and hardware available for tox to use for virtual environments.