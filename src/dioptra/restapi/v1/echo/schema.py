# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
from marshmallow import Schema, fields

from dioptra.restapi.custom_schema_fields import FileUpload, MultiFileUpload


class TestFilesInfoSchema(Schema):
    filename = fields.String(
        attribute="filename",
        metadata=dict(
            description="The name of the file.",
        ),
    )
    size = fields.Integer(
        attribute="size",
        metadata=dict(
            description="The size of the file in bytes.",
        ),
    )


class EchoSchema(Schema):
    testFilesInfo = fields.List(
        fields.Nested(TestFilesInfoSchema),
        attribute="test_files_info",
        metadata=dict(
            description="Information about the uploaded test files.",
        ),
        dump_only=True,
    )
    testFiles = MultiFileUpload(
        attribute="test_files",
        metadata=dict(
            description="One or more files.",
        ),
        load_only=True,
    )
    testString = fields.String(
        attribute="test_string",
        metadata=dict(
            description="An arbitrary string.",
        ),
        load_default="A simple test.",
    )


class EchoSingleFileSchema(Schema):
    testFileInfo = fields.Nested(
        TestFilesInfoSchema,
        attribute="test_file_info",
        metadata=dict(
            description="Information about the uploaded test file.",
        ),
        dump_only=True,
    )
    testFile = FileUpload(
        attribute="test_file",
        metadata=dict(
            description="One file.",
        ),
        load_only=True,
    )
    testString = fields.String(
        attribute="test_string",
        metadata=dict(
            description="An arbitrary string.",
        ),
        load_default="A simple test.",
    )
