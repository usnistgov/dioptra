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
"""Install command support for the Dioptra CLI."""

import click

from dioptra.cli.core import installer


def _validate_version(ctx, param, value):
    if value is None:
        return None
    if not value.strip():
        raise click.BadParameter("Version cannot be empty.")
    return value


@click.command()
@click.argument("name", required=False)
@click.option(
    "--dir",
    "directory",
    type=click.Path(),
    help="Parent directory for the deployment. "
    "Defaults to the standard deployments directory.",
)
@click.option(
    "--docker-compose-path",
    help="Override the docker compose command (e.g., 'docker-compose'). "
    "Auto-detected if not specified.",
)
@click.option(
    "--version",
    default=None,
    callback=_validate_version,
    help="Dioptra release version to install (e.g., '1.1.0'). "
    "Defaults to the version of dioptra-platform you have installed.",
)
@click.option(
    "--image-tag",
    default=None,
    help="Docker tag to pull for Dioptra images. Overrides --version. Defaults "
    "to the installed dioptra-platform version, or 'dev' for dev installs.",
)
@click.option(
    "--skip-image-validation",
    is_flag=True,
    help="Skip cosign verification of Dioptra images. Use only when you "
    "trust the registry and need to install without network access "
    "to GitHub.",
)
@click.option(
    "--datasets-dir",
    type=click.Path(),
    help="Host path to mount read-only into worker containers at /dioptra/data.",
)
@click.option(
    "--cert",
    type=click.Path(exists=True),
    help="Path to a CA certificate (PEM, single cert) to add to the trust "
    "stores of Dioptra services. Use this when services need to trust "
    "internal HTTPS endpoints signed by a private CA.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Print detailed output including subprocess commands.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite an existing deployment with the same name, deleting "
    "its data volumes for a fresh start. To preserve data across "
    "a container update, use `dioptra-platform upgrade` instead.",
)
@click.option(
    "--yes",
    is_flag=True,
    help="Skip the confirmation prompt when overwriting an existing deployment.",
)
# --- Hidden developer options ---
# These are are not shown in --help output.
# They control which git refs are used for distinct install stages:
#   --template-ref:   what cruft checks out locally (accepts SHAs, branches, tags)
#   --validation-ref: ref for fetching verify.json from GitHub raw
#   --init-ref:       ref passed to init-deployment.sh (branches/tags only)
@click.option("--template-ref", default=None, hidden=True)
@click.option("--validation-ref", default=None, hidden=True)
@click.option("--init-ref", default=None, hidden=True)
@click.pass_context
def install(
    context,
    name,
    directory,
    docker_compose_path,
    version,
    image_tag,
    skip_image_validation,
    datasets_dir,
    cert,
    verbose,
    force,
    yes,
    template_ref,
    validation_ref,
    init_ref,
):
    """Install a new Dioptra deployment.

    Pulls and verifies Dioptra images, generates a deployment configuration,
    and initializes it for use.

    If NAME is omitted and no deployments exist, the new deployment is named
    'default'. If a single deployment already exists and --force is set, that
    deployment is overwritten.

    \b
    Examples:
      Install the latest version:
        dioptra-platform install my-deployment

      Install a specific release:
        dioptra-platform install my-deployment --version 1.1.0

      Install with a local datasets directory mounted:
        dioptra-platform install my-deployment --datasets-dir ~/data
    """

    if name and ("/" in name or "\\" in name):
        raise click.BadParameter("Deployment name cannot contain path separators.")

    if force and not yes:
        click.echo(
            "--force will delete any existing deployment's data volumes "
            "(database, artifacts, etc)."
        )
        if not click.confirm("Continue?", default=False):
            click.echo("Install aborted.")
            return

    click.echo(
        f"Beginning install for Dioptra deployment '{name}'"
        if name
        else "Beginning Dioptra install"
    )

    try:
        resolved_name = installer.install(
            name=name,
            directory=directory,
            template_ref=template_ref,
            validation_ref=validation_ref,
            init_ref=init_ref,
            version=version,
            image_tag=image_tag,
            skip_image_validation=skip_image_validation,
            docker_compose_path=docker_compose_path,
            datasets_dir=datasets_dir,
            cert=cert,
            verbose=verbose or context.obj["VERBOSE"],
            force=force or context.obj["FORCE"],
        )
    except Exception as e:
        raise click.ClickException(str(e)) from None

    click.echo("\nInstallation Successful!")
    click.echo(f"Start the deployment with `dioptra-platform start {resolved_name}`")
