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


class TaskEngineSubmission(Schema):
    queue = fields.String(
        required=True,
        metadata={"description": "The name of an active queue"},
    )

    experimentName = fields.String(
        required=True,
        metadata={"description": "The name of a registered experiment."},
    )

    experimentDescription = fields.Dict(
        keys=fields.String(),
        required=True,
        metadata={"description": "A declarative experiment description."},
    )

    globalParameters = fields.Dict(
        keys=fields.String(),
        metadata={"description": "Global parameters for this task engine job."},
    )

    timeout = fields.String(
        metadata={
            "description": "The maximum alloted time for a job before it times"
            " out and is stopped. If omitted, the job timeout"
            " will default to 24 hours.",
        },
    )

    dependsOn = fields.String(
        metadata={
            "description": "A job UUID to set as a dependency for this new job."
            " The new job will not run until this job completes"
            " successfully. If omitted, then the new job will"
            " start as soon as computing resources are"
            " available.",
        },
    )
