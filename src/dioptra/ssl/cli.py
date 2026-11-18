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
"""Explicit-path certificate operations independent of deployment configuration."""

import json
import sys
from collections.abc import Callable, Sequence
from functools import wraps
from pathlib import Path
from typing import Any

import click
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm

from . import certificates as certs
from .files import absolute
from .publication import PublicationError, check_outputs, publish


def _report(operation: str, result: dict[str, Any], format: str) -> None:
    """Print one successful command result in the selected output format.

    Include the schema version and operation name in the printed result without changing
    the caller's dictionary. The result must contain only public certificate metadata,
    check results and output paths, not private-key bytes.

    Args:
        operation: Public command name.
        result: JSON-compatible public metadata/checks/output-path dictionary.
        format: json for compact JSON, text for indented readable JSON.

    Returns:
        None.
    """
    result = {"schema_version": 1, "operation": operation, **result}
    click.echo(
        json.dumps(result, sort_keys=True, indent=None if format == "json" else 2)
    )


def _command(function):
    """Wrap a Click callback with one consistent failure diagnostic.

    Args:
        function: Certificate command callback accepting the parsed keyword arguments.

    Returns:
        Callback wrapper that reports relevant file/cryptographic errors and exits
        nonzero, including inspectable publication recovery details.
    """

    @wraps(function)
    def run(**kwargs):
        """Normalize callback failures into the command result format without duplicate diagnostics."""
        try:
            function(**kwargs)
        except (OSError, ValueError, InvalidSignature, UnsupportedAlgorithm) as exc:
            error: dict[str, Any] = {
                "schema_version": 1,
                "operation": function.__name__.replace("_", "-"),
                "error": str(exc),
            }
            if isinstance(exc, PublicationError):
                error["recovery"] = exc.recovery
            click.echo(
                json.dumps(error) if kwargs["format"] == "json" else str(exc), err=True
            )
            raise click.exceptions.Exit(1) from exc

    return run


def _output_options(days: int = 365) -> Callable:
    """Create the shared certificate-output option decorator.

    Args:
        days: Command-specific default lifetime, in days.

    Returns:
        Decorator adding explicit key/certificate paths, key size, lifetime, deadline
        and output format while preserving each command's chosen default.
    """

    def decorate(function):
        """Apply the selected command defaults without mutating decorated Click parameters."""
        return _decorate_outputs(function, days)

    return decorate


def _decorate_outputs(function: Callable, days: int) -> Callable:
    """Attach shared certificate-output Click parameters to a callback.

    Args:
        function: Callback receiving the shared option values.
        days: Default requested lifetime for this command.

    Returns:
        Decorated callback with a separate option definition for each parameter.
    """
    for option in [
        click.option(
            "--format",
            type=click.Choice(["text", "json"]),
            default="text",
            show_default=True,
            help="Output format for results and errors.",
        ),
        click.option(
            "--key-out",
            type=click.Path(path_type=Path),
            required=True,
            help="Unused private-key output path in an existing protected directory.",
        ),
        click.option(
            "--cert-out",
            type=click.Path(path_type=Path),
            required=True,
            help="Unused PEM certificate output path, separate from the key.",
        ),
        click.option(
            "--rsa-bits",
            type=click.IntRange(min=2048),
            default=3072,
            show_default=True,
            help="RSA size for the new key, in bits.",
        ),
        click.option(
            "--valid-days",
            type=click.IntRange(min=1),
            default=days,
            show_default=True,
            help="Requested lifetime; issuer expiry and an explicit deadline can shorten it.",
        ),
        click.option(
            "--not-after-limit",
            help="Optional expiration cap in YYYY-MM-DDTHH:MM:SSZ UTC format.",
        ),
    ]:
        function = option(function)
    return function


class CertificateGroup(click.Group):
    """Report parse failures in the same selected format as operation failures."""

    def main(
        self,
        args: Sequence[str] | None = None,
        prog_name: str | None = None,
        complete_var: str | None = None,
        standalone_mode: bool = True,
        **kwargs: Any,
    ) -> Any:
        """Dispatch Click commands while giving parse errors the selected output format.

        Args:
            args: Argument sequence, or None for sys.argv[1:].
            prog_name: Displayed program name, or None for Click's default.
            complete_var: Optional environment variable controlling shell completion.
            standalone_mode: Exit after dispatch when True; return the callback result
                on success when False.
            kwargs: Additional Click Group.main keyword arguments.

        Returns:
            Callback result only when standalone_mode=False.

        Raises:
            SystemExit: Dispatch completes in standalone mode, or parsing fails. Parse
                failures emit one text/JSON diagnostic and the Click failure status.
        """
        arguments = list(sys.argv[1:] if args is None else args)
        standalone = standalone_mode
        try:
            result = super().main(
                args=arguments,
                prog_name=prog_name,
                complete_var=complete_var,
                standalone_mode=False,
                **kwargs,
            )
        except click.ClickException as exc:
            structured = (
                any(
                    arguments[i : i + 2] == ["--format", "json"]
                    for i in range(len(arguments))
                )
                or "--format=json" in arguments
            )
            message = {
                "schema_version": 1,
                "operation": next(
                    (a for a in arguments if a in {"create-ca", "issue", "validate"}),
                    "parse",
                ),
                "error": exc.format_message(),
            }
            click.echo(
                json.dumps(message) if structured else exc.format_message(), err=True
            )
            raise SystemExit(exc.exit_code) from exc
        if standalone:
            raise SystemExit(result if isinstance(result, int) else 0)
        return result


@click.group(cls=CertificateGroup)
def main() -> None:
    """Create, issue or validate explicitly selected certificate files."""


@main.command("create-ca")
@click.option(
    "--common-name",
    required=True,
    help="Nonblank subject name for the new certificate authority.",
)
@_output_options(1825)
@_command
def create_ca(
    common_name: str,
    key_out: Path,
    cert_out: Path,
    rsa_bits: int,
    valid_days: int,
    not_after_limit: str | None,
    format: str,
) -> None:
    """Create a signing CA at unused output paths; default lifetime is 1825 days.

    \f

    Save the generated key and CA certificate at the requested paths and print their
    public metadata and any warnings. Publication failures can leave a staged pair or
    partial output; the diagnostic identifies retained files for recovery. The command
    wrapper reports file and cryptographic failures in the selected format and exits
    unsuccessfully.

    Args:
        common_name: Nonblank CA subject name.
        key_out: Unused PEM private-key path in an existing protected directory.
        cert_out: Distinct unused PEM CA certificate path.
        rsa_bits: RSA key size, at least 2048; the CLI default is 3072.
        valid_days: Requested CA lifetime; the CLI default is 1825 days.
        not_after_limit: Optional UTC YYYY-MM-DDTHH:MM:SSZ expiration cap.
        format: text for readable output or json for a single structured result.

    Returns:
        None.
    """
    key_out, cert_out = absolute(key_out), absolute(cert_out)
    check_outputs(key_out, cert_out)
    key, cert, warnings = certs.create_ca(
        common_name, rsa_bits, valid_days, certs.parse_date(not_after_limit)
    )
    publication = publish("create-ca", key, cert, key_out, cert_out)
    _report(
        "create-ca",
        {
            "certificate": certs.metadata(cert),
            "checks": ["ca-constraints", "key-match", "current-validity"],
            "warnings": warnings,
            **publication,
        },
        format,
    )


@main.command("issue")
@click.option(
    "--ca-cert",
    type=click.Path(path_type=Path),
    required=True,
    help="PEM certificate of the signing CA.",
)
@click.option(
    "--ca-key",
    type=click.Path(path_type=Path),
    required=True,
    help="Matching protected unencrypted CA private key.",
)
@click.option(
    "--ca-chain",
    type=click.Path(path_type=Path),
    help="Issuer chain to a root when the signing CA is an intermediate.",
)
@click.option(
    "--dns",
    multiple=True,
    help="Concrete server DNS identity; repeat for additional names.",
)
@click.option(
    "--ip",
    multiple=True,
    help="Server IPv4/IPv6 identity without brackets; repeat as needed.",
)
@click.option(
    "--issuance-log",
    type=click.Path(path_type=Path),
    help="Optional protected append-only JSON-lines signing history.",
)
@_output_options()
@_command
def issue(
    ca_cert: Path,
    ca_key: Path,
    ca_chain: Path | None,
    dns: tuple[str, ...],
    ip: tuple[str, ...],
    issuance_log: Path | None,
    key_out: Path,
    cert_out: Path,
    rsa_bits: int,
    valid_days: int,
    not_after_limit: str | None,
    format: str,
) -> None:
    """Issue a separate server key and certificate for concrete DNS/IP identities.

    \f

    Require at least one DNS or IP identity. Validate the issued certificate chain
    before saving the files and any requested signing-history entry. The command wrapper
    reports failures without overwriting existing outputs or discarding a retained
    staged pair.

    Args:
        ca_cert: PEM signing-CA certificate path.
        ca_key: Matching protected unencrypted CA private-key path.
        ca_chain: Optional PEM path from an intermediate issuer to its root; omitted for
            a root issuer.
        dns: Concrete DNS names to include in subject-alternative names.
        ip: IPv4/IPv6 address strings to include in subject-alternative names.
        issuance_log: Optional protected JSON-lines signing-history path.
        key_out: Unused PEM private-key output path.
        cert_out: Distinct unused certificate-chain output path, leaf first.
        rsa_bits: New server RSA key size; CLI default 3072, minimum 2048.
        valid_days: Requested server lifetime; CLI default 365 days.
        not_after_limit: Optional UTC expiration cap; issuer expiration also limits the
            lifetime.
        format: text or json result/diagnostic format.

    Returns:
        None.
    """
    names = certs.identities(dns, ip)
    limit = certs.parse_date(not_after_limit)
    key_out, cert_out = absolute(key_out), absolute(cert_out)
    check_outputs(key_out, cert_out)
    issuer = certs.load_certificates(ca_cert)[0]
    chain = certs.load_certificates(ca_chain) if ca_chain else []
    key, cert, warnings = certs.issue(
        issuer, certs.load_key(ca_key), names, rsa_bits, valid_days, limit
    )
    signed_at = certs.utc_now()
    # The selected library builds the path. A root-signed issuer needs no supplied
    # chain; an intermediate issuer must be accompanied by its path to a root.
    full_chain = [issuer, *chain]
    result = certs.validate_server(
        [cert, *full_chain[:-1]], [full_chain[-1]], names, key=key, maximum=limit
    )
    publication = publish(
        "issue",
        key,
        cert,
        key_out,
        cert_out,
        issuer=issuer,
        chain=full_chain[:-1],
        log=absolute(issuance_log) if issuance_log else None,
        signed_at=signed_at,
    )
    _report("issue", {**result, "warnings": warnings, **publication}, format)


@main.command("validate")
@click.option(
    "--cert",
    type=click.Path(path_type=Path),
    required=True,
    help="PEM server chain (leaf first), or a single CA certificate.",
)
@click.option(
    "--key",
    type=click.Path(path_type=Path),
    help="Optional protected private key to match against the certificate.",
)
@click.option(
    "--trust",
    type=click.Path(path_type=Path),
    multiple=True,
    help="Explicit root CA PEM file for server checks; repeat as needed.",
)
@click.option(
    "--dns",
    multiple=True,
    help="Concrete server DNS identity; repeat for additional names.",
)
@click.option(
    "--ip",
    multiple=True,
    help="Server IPv4/IPv6 identity without brackets; repeat as needed.",
)
@click.option(
    "--kind",
    type=click.Choice(["server", "ca", "outbound-ca"]),
    default="server",
    show_default=True,
    help="Strict server/CA validation, or warning-only outbound CA policy inspection.",
)
@click.option(
    "--max-not-after", help="Reject later expiration; use YYYY-MM-DDTHH:MM:SSZ UTC."
)
@click.option(
    "--warn-ca-not-after",
    help="Warn for later CA expiration; use YYYY-MM-DDTHH:MM:SSZ UTC.",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format for results and errors.",
)
@_command
def validate(
    cert: Path,
    key: Path | None,
    trust: tuple[Path, ...],
    dns: tuple[str, ...],
    ip: tuple[str, ...],
    kind: str,
    max_not_after: str | None,
    warn_ca_not_after: str | None,
    format: str,
) -> None:
    """Validate certificate files read-only using explicit trust and identities.

    \f

    Print public certificate metadata and the checks performed. Server validation
    requires explicit trust roots and at least one identity. Leave certificate files,
    permissions and workstation trust unchanged. The command wrapper reports a nonzero
    exit when validation fails.

    Args:
        cert: PEM server chain or single CA certificate path.
        key: Optional protected private-key path to check for a match.
        trust: Explicit PEM root files for server validation; unused for CA inspection.
        dns: Required DNS identities for server validation.
        ip: Required IP identities for server validation.
        kind: server verifies a trusted chain; ca requires signing suitability;
            outbound-ca reports policy differences for one outbound-only certificate.
        max_not_after: Optional UTC expiration deadline that causes rejection when
            exceeded.
        warn_ca_not_after: Optional UTC CA expiration threshold producing warnings only.
        format: text or json result/diagnostic format.

    Returns:
        None.
    """
    maximum, warning = (
        certs.parse_date(max_not_after),
        certs.parse_date(warn_ca_not_after),
    )
    chain = certs.load_certificates(cert)
    private = certs.load_key(key) if key else None
    if kind == "server":
        names = certs.identities(dns, ip)
        roots = [item for path in trust for item in certs.load_certificates(path)]
        result = certs.validate_server(
            chain, roots, names, key=private, maximum=maximum, warn_ca=warning
        )
    elif kind == "outbound-ca":
        if len(chain) != 1 or key or trust or dns or ip or maximum is not None:
            raise ValueError(
                "outbound-ca requires one certificate and accepts no key, trust, "
                "identity or maximum-expiration options"
            )
        result = certs.inspect_outbound_ca(chain[0], warn_after=warning)
    else:
        result = _validate_ca(chain, private, maximum, warning)
    _report("validate", result, format)


def _validate_ca(chain: list, key: Any, maximum: Any, warning: Any) -> dict[str, Any]:
    """Inspect one CA with optional key matching and caller-selected expiration policy.

    Args:
        chain: Exactly one parsed CA certificate.
        key: Optional RSA/ECDSA private key, or None.
        maximum: Optional aware expiration deadline, or None.
        warning: Optional aware warning-only expiration threshold, or None.

    Returns:
        Certificate metadata, performed check names and warning messages.

    Raises:
        ValueError: Input contains multiple certificates or CA/key/expiration checks
            fail.
    """
    if len(chain) != 1:
        raise ValueError("CA validation requires exactly one certificate")
    certs.validate_ca(chain[0], key)
    if maximum is not None and chain[0].not_valid_after_utc > maximum:
        raise ValueError(f"CA expiration exceeds caller limit {maximum.isoformat()}")
    warnings = []
    if warning is not None and chain[0].not_valid_after_utc > warning:
        warnings.append(
            f"CA expires {chain[0].not_valid_after_utc.isoformat()} after {warning.isoformat()}"
        )
    return {
        "certificate": certs.metadata(chain[0]),
        "checks": ["ca-suitability", "current-validity", "supported-key"]
        + (["self-issued-root"] if chain[0].subject == chain[0].issuer else [])
        + (["key-match"] if key else []),
        "warnings": warnings,
    }


if __name__ == "__main__":
    main()
