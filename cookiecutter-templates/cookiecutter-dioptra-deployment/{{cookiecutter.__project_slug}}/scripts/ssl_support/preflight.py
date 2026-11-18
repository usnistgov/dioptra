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
"""Check the full initializer's teardown prerequisite before it creates files.

This private helper is invoked by init-deployment.sh with the deployment root.
It shares the manager's configured Compose command without embedding Python in Bash.
"""

import shlex
import sys
from pathlib import Path

from manage_ssl import COMPOSE_COMMAND

from .runtime import require_offline


def main() -> int:
    """Check that the deployment passed on the command line has no runtime containers.

    Returns:
        Zero when initialization may proceed, or one after reporting a failed
        teardown check to stderr. No deployment files or services are changed.
    """
    try:
        require_offline(Path(sys.argv[1]), shlex.split(COMPOSE_COMMAND), absent=True)
    except (OSError, ValueError, KeyError, IndexError) as exc:
        print(f"Initialization preflight failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
