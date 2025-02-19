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
import structlog
from dioptra import pyplugs

LOGGER = structlog.get_logger()


@pyplugs.register
def hello(name: str) -> str:
    message = f"Hello, {name}"
    LOGGER.info(message)
    return message


@pyplugs.register
def greet(greeting: str, name: str) -> str:
    message = f"{greeting}, {name}"
    LOGGER.info(message)
    return message


@pyplugs.register
def shout(greeting: str) -> str:
    loud_greeting = greeting.upper()
    LOGGER.info(loud_greeting)
    return loud_greeting
