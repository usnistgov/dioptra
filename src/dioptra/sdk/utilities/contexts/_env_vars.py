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
import os
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def env_vars(env_updates: dict[str, str]) -> Iterator[None]:
    """Create a context for temporarily updating environment variables.

    Args:
        env_updates: A dictionary that maps the environment variables (keys) to a new
            value. Both the keys and values must be strings.

    Examples:
        The example below shows how to use env_vars to set/update the value of the
        environment variable __A within a context block. First, import the os module
        and check the current value of __A (we provide a a default value because this
        environment variable should not exist).

        >>> import os
        >>> print(os.getenv("__A", "default value of __A"))
        default value of __A

        Next, set up a with statement using env_vars to set a new value for __A confirm
        that the update worked.

        >>> with env_vars({"__A": "new value of __A"}):
        ...     print(os.getenv("__A", "default value of A"))
        new value of __A

        Finally, confirm that __A has been restored to its default value after exiting
        the with statement.

        >>> print(os.getenv("__A", "default value of __A"))
        default value of __A

    Note:
        This code is adapted from https://stackoverflow.com/a/34333710.
    """
    original_env = os.environ.copy()
    os.environ.update(env_updates)

    try:
        yield

    finally:
        os.environ.clear()
        os.environ.update(original_env)
