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
"""Wrapper around cruft and cookiecutter for rendering deployment templates.

Dioptra uses two related tools depending on installation mode:

* In a development checkout, cruft (which wraps cookiecutter) is used so
  template versions can be tracked via git refs and updated in place.
* In a pip-installed package, the templates ship as bundled data and are
  rendered with cookiecutter directly - there's no git history to track.
"""

import json

from dioptra.cli.core import process, templates


def create(
    output_dir, context, cruft_bin, cookiecutter_bin, branch=None, verbose=False
) -> None:
    """Render the Dioptra deployment template into output_dir.

    In a dev checkout, uses cruft to check out `branch` (or the current HEAD)
    and render the template from there. cruft does `git checkout <ref>` before reading
    the template, so uncommitted template changes are NOT seen. Commit template edits
    before installing.

    In a packaged install, uses cookiecutter to render the bundled template directly;
    `branch` must be None in this mode. The bundled template ships as package data
    (no git history), so cruft's git-based rendering can't be used. --template-ref is
    not supported in this mode.
    """
    if templates.is_dev_checkout():
        _create_from_dev_checkout(output_dir, context, cruft_bin, branch, verbose)
    else:
        if branch is not None:
            raise RuntimeError(
                "--template-ref is only supported when running from a "
                "development checkout of dioptra-platform. The current "
                "installation uses the bundled template."
            )
        _create_from_package(output_dir, context, cookiecutter_bin, verbose)


def _create_from_dev_checkout(output_dir, context, cruft_bin, branch, verbose) -> None:
    """Render the template from the local git checkout with the given ref.

    Validates the template existence at the ref before invoking cruft,
    so we can give clear error instead of a cruft failure when template changes
    haven't been committed or we have a ref that lacks the expected layout.
    """
    repo_root = templates.get_repo_root()
    template_subdir = templates.get_template_subdir()
    ref = branch or templates.get_current_git_ref()

    try:
        process.run(
            ["git", "cat-file", "-e", f"{ref}:{template_subdir}/cookiecutter.json"],
            cwd=repo_root,
            suppress_output=True,
        )
    except RuntimeError as e:
        raise RuntimeError(
            f"Template not found at '{template_subdir}/cookiecutter.json' "
            f"at ref '{ref}'. Make sure your template changes are committed "
            f"to the ref you're installing from (--template-ref={ref})."
        ) from e

    cmd = [
        str(cruft_bin),
        "create",
        str(repo_root),
        "--directory",
        template_subdir,
        "--output-dir",
        str(output_dir),
        "--checkout",
        ref,
        "--no-input",
        "--extra-context",
        json.dumps(context),
    ]
    process.run(cmd, verbose=verbose)


def _create_from_package(output_dir, context, cookiecutter_bin, verbose) -> None:
    """Render the bundled template using cookiecutter directly.

    cookiecutter doesn't require git like cruft does, which is necessary
    here since the package isn't a git repo. Extra context is passed as
    positional key=value args (required by cookiecutter).
    """
    with templates.get_packaged_template_path() as template_path:
        cmd = [
            str(cookiecutter_bin),
            str(template_path),
            "--output-dir",
            str(output_dir),
            "--no-input",
        ]
        for key, value in context.items():
            cmd.append(f"{key}={value}")
        process.run(cmd, verbose=verbose)
