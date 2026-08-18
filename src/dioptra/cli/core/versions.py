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

"""Version parsing and comparison for Dioptra's versioning scheme.

Dioptra versions follow the format: <base>[-<build>]

Where <base> is a PEP 440 version (e.g., '1.1.0', '1.1.0dev0') and
<build> is an optional positive integer container build number that
iterates on top of the same base when only the container changes
(security rebuilds, OS updates) without a Python package change.

Examples in sort order:
    1.1.0dev0        - base 1.1.0.dev0, no build
    1.1.0dev0-1      - base 1.1.0.dev0, build 1
    1.1.0dev0-2      - base 1.1.0.dev0, build 2
    1.1.0            - base 1.1.0, no build  (newer than any 1.1.0dev0*)
    1.2.0dev0        - base 1.2.0.dev0, no build
    1.2.0-1          - base 1.2.0, build 1

Python package versions are guaranteed never to include a build suffix
(those only apply to container images). '-' will only ever appear as the
build-number separator.
"""

from packaging.version import InvalidVersion, Version


class InvalidDioptraVersion(ValueError):
    """Raised when a version string doesn't match Dioptra's format."""


def parse(version: str) -> tuple[Version, int]:
    """Parse a Dioptra version string into (base, build_number).

    The build number defaults to 0 when no -<build> suffix is present;
    this makes 'X.Y.Z' sort before 'X.Y.Z-1'.

    Raises InvalidDioptraVersion for malformed inputs.
    """
    if not version:
        raise InvalidDioptraVersion("Version cannot be empty.")

    base_str, sep, build_str = version.partition("-")

    try:
        base = Version(base_str)
    except InvalidVersion as e:
        raise InvalidDioptraVersion(
            f"Invalid base version '{base_str}' in '{version}': {e}"
        ) from e

    if not sep:
        return base, 0

    if not build_str.isdigit():
        raise InvalidDioptraVersion(
            f"Build number must be a positive integer; got '{build_str}' "
            f"in '{version}'."
        )

    build = int(build_str)
    if build < 1:
        raise InvalidDioptraVersion(
            f"Build number must be >= 1 when present; got {build} in '{version}'."
        )

    return base, build


def is_newer(current: str, candidate: str) -> bool:
    """Return True if candidate is a newer version than current.

    Unparseable versions (e.g., 'dev' or 'latest' tags) compare as
    not-newer, so dev installs don't get false update flags.
    """
    try:
        cur = parse(current)
        cand = parse(candidate)
    except InvalidDioptraVersion:
        return False
    return cand > cur
