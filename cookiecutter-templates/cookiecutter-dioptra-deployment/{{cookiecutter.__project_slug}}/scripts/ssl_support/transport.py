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
"""Prepare, publish and inspect public transport policy independently of certificates."""

import copy
import json
import tempfile
from pathlib import Path

from . import files, probe
from . import install as installation
from .runtime import API_INTERNAL_PORT, NGINX_HTTP_PORT, run

ENVIRONMENT = "envs/tls.env"
DERIVED = (
    "DIOPTRA_TLS_ALLOWED_AUTHORITIES",
    "DIOPTRA_TLS_KEY_EXCHANGE",
    "DIOPTRA_PUBLIC_HOST",
    "DIOPTRA_PUBLIC_HTTPS_PORT",
)

NGINX = "/etc/nginx/conf.d/https_restapi.conf"


def authority(host: str, port: int) -> str:
    """Format a hostname/IP and optional HTTPS port for URLs and Host headers.

    Args:
        host: Concrete DNS hostname or unbracketed IP address.
        port: TCP port; 443 is omitted from the formatted result.

    Returns:
        Host text with IPv6 brackets and a nondefault port suffix when required.
    """
    name = f"[{host}]" if ":" in host else host
    return name if port == probe.DEFAULT_HTTPS_PORT else f"{name}:{port}"


def intent(configuration: dict) -> dict:
    """Remove derived fields and the local probe address before comparing deployments.

    The manager's nginx connection address does not change service configuration or
    certificates. Ignore only that connection setting; preserve other extension fields
    so unrelated runtime changes still affect the comparison.

    Args:
        configuration: Effective Compose configuration dictionary.

    Returns:
        A deep copy without DERIVED service environment fields or the manager's local
        connection override. The input dictionary is unchanged.
    """
    selected = copy.deepcopy(configuration)
    options = selected.get("x-dioptra")
    if isinstance(options, dict):
        options.pop("nginx-connect-host", None)
        if not options:
            selected.pop("x-dioptra")
    for service in selected["services"].values():
        environment = service.get("environment", {})
        for name in DERIVED:
            environment.pop(name, None)
    return selected


def prepare(root: Path, runtime, selected: dict) -> dict:
    """Derive approved hosts, public ports and nginx policy from deployment inputs.

    Read the selected configuration and nginx template without changing active files
    or services.

    Args:
        root: Deployment root containing config/, ssl/ and .ssl-private/.
        runtime: Effective Compose project configuration, images and volumes.
        selected: Normalized certificate and transport settings from config.load.

    Returns:
        Dictionary with environment values, rendered nginx configuration, published
        HTTP port and normalized runtime_intent.

    Raises:
        ValueError: A required published mapping is missing or ambiguous.
        OSError: The nginx source template cannot be read.
    """
    host = selected["public"]["host"]
    public = authority(host, runtime.public_port())
    http = runtime.published_port(NGINX_HTTP_PORT)
    exchange = selected["transport"]["key_exchange"]
    environment = {
        "DIOPTRA_TLS_ALLOWED_AUTHORITIES": json.dumps(
            [authority(runtime.api, API_INTERNAL_PORT), public]
        ),
        "DIOPTRA_TLS_KEY_EXCHANGE": exchange,
        "DIOPTRA_PUBLIC_HOST": host,
        "DIOPTRA_PUBLIC_HTTPS_PORT": str(runtime.public_port()),
    }
    nginx = (root / "scripts/templates/restapi.conf.template").read_text()
    replacements = {
        "PUBLIC_HOST": authority(host, probe.DEFAULT_HTTPS_PORT),
        "PUBLIC_AUTHORITY": public,
        "LISTENER_GROUPS": "ssl_ecdh_curve X25519MLKEM768;"
        if exchange == "hybrid-required"
        else "",
        "UPSTREAM_GROUPS": "proxy_ssl_conf_command Groups X25519MLKEM768;"
        if exchange == "hybrid-required"
        else "",
    }
    for name, value in replacements.items():
        nginx = nginx.replace("__DIOPTRA_" + name + "__", value)
    return {
        "environment": environment,
        "nginx": nginx,
        "public_http_port": http,
        "runtime_intent": intent(runtime.config),
    }


def environment_bytes(policy: dict) -> bytes:
    """Encode derived public policy as a Compose environment file.

    Args:
        policy: Transport policy from prepare(), containing environment, nginx text and
            effective runtime intent.

    Returns:
        UTF-8 environment assignments in stable DERIVED field order, with quoting
        suitable for Compose env-file parsing. The result must not be shell-evaluated.
    """
    return "".join(
        f"{key}='{policy['environment'][key]}'\n" for key in DERIVED
    ).encode()


def check_effective(runtime, policy: dict) -> None:
    """Check that the active Compose configuration actually supplies the recorded policy.

    Resolve the active Compose configuration and compare it with the recorded TLS
    settings using check_resolved. This catches an override that would give a service
    different settings from the ones prepared for installation.

    Args:
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        policy: TLS settings from prepare(), including environment values, nginx text
            and expected Compose configuration.

    Returns:
        None.

    Raises:
        ValueError: The effective Compose configuration differs from the recorded
            service mapping or TLS environment.
    """
    actual = json.loads(
        run([*runtime.compose, "config", "--format", "json"], root=runtime.root)
    )
    check_resolved(actual, runtime, policy)


def preflight(root: Path, runtime, policy: dict, snapshot: Path) -> None:
    """Resolve candidate policy under Compose overrides before publishing it.

    Resolve Compose using a temporary copy of the proposed TLS environment before
    replacing the active file. This detects conflicting overrides while the current
    configuration is still intact. Temporary files are removed on exit; application
    services are not changed.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        policy: TLS settings from prepare(), including environment values, nginx text
            and expected Compose configuration.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.

    Returns:
        None.

    Raises:
        ValueError: Compose overrides conflict with the proposed TLS configuration.
    """
    raw = json.loads(
        run(
            [*runtime.compose, "config", "--format", "json", "--no-env-resolution"],
            root=root,
        )
    )
    with tempfile.TemporaryDirectory(
        prefix="transport-preflight-", dir=snapshot
    ) as temporary:
        directory = Path(temporary)
        environment = directory / "candidate.env"
        files.write(environment, environment_bytes(policy))
        for name in runtime.affected(["restapi"]):
            service = raw["services"][name]
            service.setdefault("env_file", []).append(
                {"path": str(environment), "required": True}
            )
        configuration = directory / "compose.json"
        files.write(configuration, files.json_bytes(raw))
        command = [
            *runtime.docker,
            "compose",
            "--project-directory",
            str(root),
            "-f",
            str(configuration),
        ]
        actual = json.loads(run([*command, "config", "--format", "json"], root=root))
        check_resolved(actual, runtime, policy)


def check_resolved(actual: dict, runtime, policy: dict) -> None:
    """Require resolved Compose mapping and API-consumer environment to match policy.

    Compare both the service configuration and the derived TLS environment values. A
    Compose override must not silently change either after the certificate installation
    has been prepared. This function only compares the supplied configuration.

    Args:
        actual: Resolved Compose dictionary for the active or staged configuration.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        policy: TLS settings from prepare(), including environment values, nginx text
            and expected Compose configuration.

    Returns:
        None.

    Raises:
        ValueError: The service configuration or a derived environment value differs
            from the prepared policy.
    """
    if intent(actual) != policy["runtime_intent"]:
        raise ValueError(
            "effective Compose configuration differs from recorded transport policy"
        )
    for name in runtime.affected(["restapi"]):
        environment = actual["services"][name].get("environment", {})
        if any(
            environment.get(key) != value
            for key, value in policy["environment"].items()
        ):
            raise ValueError(
                f"{name}: effective Compose environment overrides derived TLS policy; "
                "reconcile envs/tls.env and service overrides"
            )


def curl_handshake(
    container, identity: str, port: int = probe.HYBRID_PROBE_PORT
) -> None:
    """Check that a container's curl can verify hybrid HTTPS and receive a 2xx status.

    Connect to the local test server using /curl-ca.crt and the X25519MLKEM768 group.
    Require successful certificate verification and an HTTP 2xx response without
    following redirects.

    Args:
        container: Running helper container used to inspect or install certificate
            files.
        identity: Certificate DNS/IP identity for the loopback test peer.
        port: Loopback peer port, defaulting to 18443.

    Returns:
        None.

    Raises:
        ValueError: Verification fails, curl output is invalid, or the response is a
            redirect or another non-2xx status.
    """
    name = f"[{identity}]" if ":" in identity else identity
    try:
        result = container.exec(
            "curl",
            "--disable",
            "--fail",
            "--silent",
            "--show-error",
            "--noproxy",
            "*",
            "--tlsv1.3",
            "--curves",
            "X25519MLKEM768",
            "--cacert",
            "/curl-ca.crt",
            "--connect-to",
            f"::{probe.IPV4_LOOPBACK}:{port}",
            "--max-time",
            "5",
            "--retry",
            "3",
            "--retry-connrefused",
            "--retry-delay",
            "1",
            "--output",
            "/dev/null",
            "--write-out",
            "%{http_code}",
            f"https://{name}:{port}/",
        )
        status = result.strip()
        if len(status) != 3 or not status.isdigit() or not 200 <= int(status) < 300:
            raise ValueError(f"unexpected HTTP status {result!r}")
    except (OSError, ValueError) as exc:
        raise ValueError(
            f"healthcheck curl cannot complete verified hybrid HTTPS for {identity}: {exc}"
        ) from exc


def curl_trust(container, snapshot: Path, selected: dict, endpoint: str) -> None:
    """Copy an endpoint's explicit public validation roots into the curl helper.

    Build a temporary PEM bundle from the selected endpoint's public roots and copy it
    into the helper as /curl-ca.crt. The copied bundle is public; the signing CA's
    private key is not transferred.

    Args:
        container: Running helper container used to inspect or install certificate
            files.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.
        selected: Certificate and TLS settings loaded by config.load.
        endpoint: restapi or nginx, selecting one endpoint configuration.

    Returns:
        None.
    """
    trust = snapshot / ("curl-trust-" + endpoint + ".crt")
    files.write(
        trust, installation.trust_bundle(snapshot, selected[endpoint]), replace=True
    )
    container.put(trust, "/curl-ca.crt", 0o644)


def reconcile(root: Path, runtime, operation: dict, candidate: dict) -> None:
    """Reject unrecorded active transport bytes before continuing interrupted installation.

    Before resuming installation, require the active environment and nginx configuration
    to match the operation's recorded original files, previous policy or proposed
    policy. An empty nginx volume is allowed for first installation. Older operation
    records may also contain the original nginx_input copy. This check reads
    configuration without changing files or services.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        operation: Saved operation record with its ID, progress phase, configuration and
            recovery data.
        candidate: Prepared installation record identifying the new generation and its
            files.

    Returns:
        None.

    Raises:
        ValueError: Active configuration differs from every permitted recorded version.
    """
    policies = [candidate["transport_policy"]]
    if operation.get("candidate"):
        policies.append(operation["candidate"]["transport_policy"])
    if (operation.get("previous") or {}).get("transport_policy"):
        policies.append(operation["previous"]["transport_policy"])
    allowed_environment = {
        operation["transport_input"].encode(),
        *(environment_bytes(policy) for policy in policies),
    }
    if files.read(root / ENVIRONMENT, 0o640) not in allowed_environment:
        raise ValueError(
            "derived TLS environment differs from recorded input/candidate; recovery refused"
        )
    allowed_nginx = {
        *(policy["nginx"].encode() for policy in policies),
    }
    if operation.get("nginx_input") is not None:
        allowed_nginx.add(operation["nginx_input"].encode())
    mounts = [(runtime.volume("nginx-conf-d"), "/etc/nginx/conf.d", True)]
    with runtime.helper(runtime.services[runtime.nginx]["image"], mounts) as container:
        container.safe_destination(NGINX)
        if (
            container.exists(NGINX)
            and container.exec("cat", NGINX) not in allowed_nginx
        ):
            raise ValueError(
                "nginx transport policy differs from recorded prior/candidate; recovery refused"
            )


def publish(root: Path, runtime, policy: dict, snapshot: Path) -> None:
    """Install public environment and nginx policy while affected services are stopped.

    Replace envs/tls.env, verify the resulting effective Compose configuration, then
    copy the prepared nginx configuration into its volume with the service account's
    ownership. The caller keeps affected services stopped during publication. If a write
    or Docker command fails, the saved operation remains available for recovery.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        policy: TLS settings from prepare(), including environment values, nginx text
            and expected Compose configuration.
        snapshot: Private copy of certificate files, using paths relative to the
            deployment directory.

    Returns:
        None.
    """
    files.write(root / ENVIRONMENT, environment_bytes(policy), 0o640, replace=True)
    check_effective(runtime, policy)
    rendered = snapshot / "nginx-transport.conf"
    files.write(rendered, policy["nginx"].encode(), replace=True)
    mounts = [(runtime.volume("nginx-conf-d"), "/etc/nginx/conf.d", False)]
    with runtime.helper(runtime.services[runtime.nginx]["image"], mounts) as container:
        container.put(
            rendered,
            NGINX,
            0o644,
            installation._owner(runtime, runtime.nginx, container),
        )


def inspect(root: Path, runtime, installed: dict, selected: dict) -> None:
    """Require active host, Compose and nginx policy to match the installed record.

    Compare host settings, resolved Compose values and nginx's installed configuration
    with the recorded installation. Read volume contents through temporary helpers. This
    is inspection only: it does not repair configuration or change application service
    state.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        runtime: Deployment configuration and Docker access for the selected Compose
            project.
        installed: Installation record describing files on the host and in Docker
            volumes.
        selected: Certificate and TLS settings loaded by config.load.

    Returns:
        None.

    Raises:
        ValueError: Settings, overrides, derived environment values or nginx
            configuration differ from the installation record.
    """
    policy = installed.get("transport_policy")
    if policy != prepare(root, runtime, selected):
        raise ValueError(
            "runtime transport policy is stale; run init to requalify derived "
            "authorities without replacing certificates"
        )
    if files.read(root / ENVIRONMENT, 0o640) != environment_bytes(policy):
        raise ValueError(
            "derived TLS environment differs from recorded policy; run init to reconcile"
        )
    check_effective(runtime, policy)
    mounts = [(runtime.volume("nginx-conf-d"), "/etc/nginx/conf.d", True)]
    with runtime.helper(runtime.services[runtime.nginx]["image"], mounts) as container:
        container.safe_destination(NGINX)
        if container.exec("cat", NGINX) != policy["nginx"].encode():
            raise ValueError(
                "nginx transport configuration differs from recorded policy; run init to reconcile"
            )
