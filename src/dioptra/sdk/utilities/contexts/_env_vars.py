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
