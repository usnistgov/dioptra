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
"""Read and normalize deployment certificate settings from config/ssl.toml.

An endpoint specification contains source (generated or supplied), dns_sans,
ip_sans and trust_files. Generated endpoints use the local issuer; supplied
endpoints name explicit root files under ssl/ca-certificates/. The public host
and API service identity are always included so generated and supplied workflows
must cover the same required names. Docker port mappings remain Compose settings.
"""

import ipaddress
import json
import re
import tomllib
from pathlib import Path

from . import files

GENERATED_LIMIT = "2030-12-31T23:59:59Z"
SUPPLIED_LIMIT = "2035-12-31T23:59:59Z"
ENDPOINTS = ("restapi", "nginx")


def host(value: object) -> str:
    """Normalize a concrete DNS hostname or IP address.

    Args:
        value: Hostname or IP string without a scheme, port, wildcard or IPv6 brackets.

    Returns:
        Lowercase ASCII IDNA hostname or canonical IP address text.

    Raises:
        ValueError: The value is not a concrete hostname or IP address.
    """
    if not isinstance(value, str) or not value:
        raise ValueError("public.host must be a DNS name or IP literal")
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        normalized = value.encode("idna").decode("ascii").lower()
        parts = normalized.split(".")
        if len(normalized) > 253 or any(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part) is None
            for part in parts
        ):
            raise ValueError(
                f"{value!r}: expected concrete DNS name or IP, without URL, port or wildcard"
            ) from None
        return normalized


def _fields(value: object, allowed: set[str], location: str) -> dict:
    """Require a TOML table and reject unknown fields.

    Args:
        value: Untrusted parsed TOML value.
        allowed: Permitted field names; missing fields are checked by the caller.
        location: Setting name used in validation errors.

    Returns:
        The original dictionary.

    Raises:
        ValueError: The value is not a table or contains an unrecognized field.
    """
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError(f"{location}: unsupported fields; expected {sorted(allowed)}")
    return value


def _strings(value: object, location: str) -> list[str]:
    """Require an array of nonempty strings without coercing its values.

    Args:
        value: Parsed TOML value; an empty list is allowed.
        location: Setting name used in errors.

    Returns:
        The unchanged list. Duplicate removal, where needed, belongs to endpoint().

    Raises:
        ValueError: The value is not a list of nonempty strings.
    """
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(f"{location}: expected array of nonempty strings")
    return value


def trust_path(root: Path, value: str) -> Path:
    """Check that a selected CA file stays inside the public certificate directory.

    Args:
        root: Deployment root containing config/, ssl/ and .ssl-private/.
        value: Relative .crt path beginning with ssl/ca-certificates/.

    Returns:
        The deployment path after checking file safety and mode 0644.

    Raises:
        ValueError: The spelling escapes the directory or the file is unsafe.
        OSError: The file cannot be opened without following symbolic links.
    """
    selected = Path(value)
    if (
        selected.is_absolute()
        or selected.parts[:2] != ("ssl", "ca-certificates")
        or ".." in selected.parts
        or selected.suffix != ".crt"
    ):
        raise ValueError(
            f"{value}: trust files must be .crt files under ssl/ca-certificates"
        )
    path = root / selected
    # Descriptor traversal in read rejects every symlink component, including a
    # root directory link that a lexical containment check alone would accept.
    files.read(path, 0o644)
    return path


def endpoint(root: Path, name: str, value: object, primary: str) -> dict:
    """Normalize one endpoint and include the name clients must verify.

    Args:
        root: Deployment root containing config/, ssl/ and .ssl-private/.
        name: Endpoint label used in errors, normally restapi or nginx.
        value: TOML table with source, dns_sans, ip_sans and trust_files.
        primary: Required API service hostname or public nginx hostname/IP address.

    Returns:
        A dictionary with source and sorted, deduplicated dns_sans, ip_sans and
        trust_files. The required primary identity is included in the appropriate list.

    Raises:
        ValueError: Fields or identities are invalid, generated endpoints specify
            external trust, or supplied endpoints omit their explicit trust files.
        OSError: A selected trust file cannot be read safely.
    """
    spec = _fields(value, {"source", "dns_sans", "ip_sans", "trust_files"}, name)
    if not isinstance(spec.get("source"), str) or spec["source"] not in {
        "generated",
        "supplied",
    }:
        raise ValueError(f"{name}.source must be generated or supplied")
    dns = [
        host(item) for item in _strings(spec.get("dns_sans", []), name + ".dns_sans")
    ]
    ips = [
        str(ipaddress.ip_address(item))
        for item in _strings(spec.get("ip_sans", []), name + ".ip_sans")
    ]
    try:
        ips.insert(0, str(ipaddress.ip_address(primary)))
    except ValueError:
        dns.insert(0, primary)
    trust = _strings(spec.get("trust_files", []), name + ".trust_files")
    if (spec["source"] == "generated" and trust) or (
        spec["source"] == "supplied" and not trust
    ):
        raise ValueError(
            f"{name}: generated endpoints use only the local CA; supplied endpoints require explicit trust_files"
        )
    for path in trust:
        trust_path(root, path)
    return {
        "source": spec["source"],
        "dns_sans": sorted(set(dns)),
        "ip_sans": sorted(set(ips)),
        "trust_files": sorted(set(trust)),
    }


def load(root: Path, api_identity: str) -> dict:
    """Load certificate configuration without making Docker or cryptography calls.

    Args:
        root: Deployment root containing config/, ssl/ and .ssl-private/.
        api_identity: Effective API service name that direct clients must verify.

    Returns:
        A schema-version-1 dictionary with public.host, transport.key_exchange, and
        restapi/nginx endpoint specifications returned by endpoint().

    Raises:
        ValueError: TOML syntax, schema, fields, identities or trust selection is
            invalid.
        OSError: Configuration or selected trust files cannot be read safely.
    """
    # Config is not private, but stable no-follow reads still reject unsafe files.
    content = files.read(root / "config/ssl.toml", None)
    config = _fields(
        tomllib.loads(content.decode()),
        {"schema_version", "public", "transport", *ENDPOINTS},
        "ssl.toml",
    )
    if type(config.get("schema_version")) is not int or config["schema_version"] != 1:
        raise ValueError("ssl.toml: unsupported schema_version")
    public = _fields(config.get("public"), {"host"}, "public")
    public_host = host(public.get("host"))
    transport = _fields(config.get("transport", {}), {"key_exchange"}, "transport")
    exchange = transport.get("key_exchange", "default")
    if not isinstance(exchange, str) or exchange not in {"default", "hybrid-required"}:
        raise ValueError("transport.key_exchange must be default or hybrid-required")
    api_identity = host(api_identity)
    return {
        "schema_version": 1,
        "public": {"host": public_host},
        "transport": {"key_exchange": exchange},
        **{
            name: endpoint(
                root,
                name,
                config.get(name),
                api_identity if name == "restapi" else public_host,
            )
            for name in ENDPOINTS
        },
    }


def digest(config: dict) -> str:
    """Identify normalized configuration independently of TOML formatting.

    Args:
        config: Normalized configuration dictionary, normally from load().

    Returns:
        Lowercase SHA-256 hex digest of sorted-key JSON. No files are changed.
    """
    return files.digest(json.dumps(config, sort_keys=True).encode())


def identities(spec: dict) -> list[str]:
    """Build certificate-tool DNS/IP options from an endpoint specification.

    Args:
        spec: Normalized endpoint dictionary containing dns_sans and ip_sans lists.

    Returns:
        Argument list alternating --dns/--ip options and their individual values.
    """
    return [
        part
        for option, key in (("--dns", "dns_sans"), ("--ip", "ip_sans"))
        for value in spec[key]
        for part in (option, value)
    ]
