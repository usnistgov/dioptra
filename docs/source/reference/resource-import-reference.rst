===========================
 Resource Import Reference
===========================

This document describes the contract for importing resources into a Dioptra instance.

.. contents::

Overview
========

Dioptra provides functionality for importing Plugins, Entrypoints, and
PluginParameterTypes. This allows users to easily publish and share
resources across Dioptra instances. It is also the mechanism used to
distribute core plugins and examples developed by the Dioptra maintainers.

Resources are described via a combination of a TOML configuration file,
Python source code (for plugins), and YAML task graphs (for entrypoints).
The TOML file is the central configuration that references required sources
and includes metadata for fully registering the resources in Dioptra (such
as plugin task specifications, and entrypoint parameters).

Collections of resources can be distributed via git repositories or by sharing
files manually. The resourceImport workflow can import from a repository or
archive file. See the API Reference for details.

TOML Configuration Format
=========================

The TOML format consists of three arrays of tables, one for each of the
importable resource types: Plugins, PluginParameterTypes, and Entrypoints.
This allows for importing of zero or more of each of these resources.

Example
-------

The following example illustrates how to configure a collection of resources
including a Plugin, PluginParameterType, and Entrypoint.

.. code:: TOML

    # Plugins point to a python package and include metadata for registering them in Dioptra
    [[plugins]]
    # the path to the Python plugin relative to the root directory
    path = "plugins/hello_world"
    # an optional description
    description = "A simple plugin used for testing and demonstration purposes."

    # an array of plugin task definitions
      [[plugins.tasks]]
      # the name of the file relative to the root plugin directory
      filename = "tasks.py"
      # the name must match the name of the function
      name = "hello"
      # input parameter names must match the Python function definition
      # types are plugin parameter types and are matched by name
      input_params = [ { name = "name", type = "string", required = true} ]
      output_params = [ { name = "message", type = "message" } ]

      [[plugins.tasks]]
      filename = "tasks.py"
      name = "greet"
      input_params = [
        { name = "greeting", type = "string", required = true },
        { name = "name", type = "string", required = true },
      ]
      output_params = [ { name = "message", type = "message" } ]

      [[plugins.tasks]]
      filename = "tasks.py"
      name = "shout"
      input_params = [ { name = "message", type = "message", required = true} ]
      output_params = [ { name = "message", type = "message" } ]

    # PluginParameterTypes are fully described in the TOML
    [[plugin_param_types]]
    name = "message"
    description = "A message produced by a plugin task"

    # Entrypoints point to a task graph yaml and include metadata for registering them in Dioptra
    [[entrypoints]]
    # path to the task graph yaml
    path = "examples/hello-world.yaml"
    # the name to register the entrypoint under (the task graph filename is use if not provided)
    name = "Hello World"
    # an optional description
    description = "A simple example using the hello_world plugin."
    # entrypoint parameters to register that should match the task graph
    # here, type is an entrypoint parameter type, NOT a plugin parameter type
    params = [
      { name = "name", type = "string", default_value = "World" }
    ]
    # plugins to register with the entrypoint (matched by name)
    plugins = [ "hello_world" ]


JSON Schema
-----------

The following JSON schema fully describes the Dioptra resource TOML.
It is used to validate Dioptra TOML files in the resource import workflow.

.. code:: JSON

    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/usnistgov/dioptra",
        "title": "Dioptra Resource Schema",
        "description": "A schema defining objects that can be imported into a Dioptra instance.",
        "type": "object",
        "properties": {
            "plugins": {
                "type": "array",
                "description": "An array of Dioptra plugins",
                "items": {
                    "type": "object",
                    "description": "A Dioptra plugin",
                    "properties": {
                        "path": { "type": "string" },
                        "description": { "type": "string" },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "filename": { "type": "string" },
                                    "name": { "type": "string" },
                                    "input_params": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": { "type": "string" },
                                                "type": { "type": "string" },
                                                "required": { "type": "boolean" }
                                            },
                                            "required": [ "name", "type" ],
                                            "additionalProperties": false
                                        }
                                    },
                                    "output_params": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": { "type": "string" },
                                                "type": { "type": "string" }
                                            },
                                            "required": [ "name", "type" ],
                                            "additionalProperties": false
                                        }
                                    }
                                },
                                "required": [ "filename", "name", "input_params", "output_params" ],
                                "additionalProperties": false
                            }
                        }
                    },
                    "required": [ "path" ],
                    "additionalProperties": false
                }
            },
            "plugin_param_types": {
                "type": "array",
                "description": "An array of Dioptra plugin parameter types",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": { "type": "string" },
                        "description": { "type": "string" },
                        "structure": { "type": "object" }
                    },
                    "required": [ "name" ],
                    "additionalProperties": false
                }
            },
            "entrypoints": {
                "type": "array",
                "description": "An array of Dioptra entrypoints",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": { "type": "string" },
                        "name": { "type": "string" },
                        "description": { "type": "string" },
                        "params": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": { "type": "string" },
                                    "type": { "type": "string" },
                                    "default_value": { "type": [ "string", "number", "boolean", "null" ] }
                                },
                                "required": [ "name", "type" ],
                                "additionalProperties": false
                            }
                        },
                        "plugins": {
                            "type": "array",
                            "items": { "type": "string" }
                        }
                    },
                    "required": [ "path" ],
                    "additionalProperties": false
                }
            }
        }
    }
