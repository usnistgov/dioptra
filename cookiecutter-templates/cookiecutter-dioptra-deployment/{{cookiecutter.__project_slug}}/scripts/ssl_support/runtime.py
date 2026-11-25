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
"""Direct Docker operations used by the certificate manager.

Helpers receive named volumes and explicit argument arrays. They receive neither
host write mounts nor the Docker socket. Only private construction helpers receive
issuer certificates or private keys. Effective Compose configuration selects images and volume names.
"""

import json
import os
import re
import secrets
import shlex
import subprocess
from contextlib import contextmanager
from pathlib import Path

from . import config, files, probe

# Fixed service listeners shared with the deployment template's nginx and API setup.
API_INTERNAL_PORT = 5000
NGINX_HTTP_PORT = 30080
NGINX_HTTPS_PORT = 30443
# Compose wildcard binds must be reached through a concrete address by host probes.
IPV4_WILDCARD = "0.0.0.0"
IPV6_WILDCARD = "::"


def run(
    arguments: list[str],
    *,
    root: Path,
    input: bytes | None = None,
    env: dict[str, str] | None = None,
) -> bytes:
    """Run one command with a 180-second deadline and capture its diagnostics.

    Args:
        arguments: Executable and separate argument strings; no shell interpretation
            occurs.
        root: Deployment root containing config/, ssl/ and .ssl-private/.
        input: Optional stdin bytes.
        env: Complete child environment, or None to inherit the current environment.

    Returns:
        Captured stdout bytes.

    Raises:
        ValueError: The command times out or exits nonzero; stderr is included.
        OSError: The executable cannot be started.
    """
    try:
        result = subprocess.run(
            arguments,
            cwd=root,
            env=env,
            input=input,
            capture_output=True,
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"command {arguments!r} timed out after 180 seconds") from exc
    if result.returncode:
        raise ValueError(
            f"command {arguments!r} failed ({result.returncode}): {result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def engine_command(compose: list[str]) -> list[str]:
    """Resolve the Docker engine command used by a configured Compose invocation.

    Args:
        compose: Split docker [global options] compose command, or standalone
            docker-compose.

    Returns:
        Docker executable and global engine options, excluding the compose subcommand.

    Raises:
        ValueError: A wrapper or unsupported flag makes engine selection ambiguous.
    """
    executable = Path(compose[0]).name
    if executable in {"docker-compose", "docker-compose.exe"}:
        engine_options = {
            "--context",
            "--host",
            "-H",
            "--config",
            "--tls",
            "--tlsverify",
            "--tlscert",
            "--tlskey",
            "--tlscacert",
        }
        if any(
            token.split("=", 1)[0] in engine_options or token.startswith("-H")
            for token in compose[1:]
        ):
            raise ValueError(
                "standalone Compose engine flags are ambiguous; use Docker global engine flags before the compose subcommand or standard Docker environment inputs"
            )
        return ["docker"]
    if executable not in {"docker", "docker.exe"}:
        raise ValueError(
            "cannot resolve the Docker engine for configured Compose command; use docker [global options] compose or standalone docker-compose with standard Docker environment inputs"
        )
    index = 1
    values = {
        "--context",
        "--host",
        "-H",
        "--config",
        "--log-level",
        "--tlscacert",
        "--tlscert",
        "--tlskey",
    }
    flags = {"--tls", "--tlsverify", "--debug", "-D"}
    while index < len(compose):
        token = compose[index]
        if token == "compose":
            return compose[:index]
        index += _engine_option_width(token, values, flags)
    raise ValueError("configured Docker command must select the compose subcommand")


def _engine_option_width(token: str, values: set[str], flags: set[str]) -> int:
    """Recognize Docker global options before resolving the Compose subcommand."""
    if token in values:
        return 2
    if token in flags or token.split("=", 1)[0] in values or token.startswith("-H"):
        return 1
    raise ValueError(
        f"unsupported Docker global option {token!r}; cannot safely determine the helper engine"
    )


def require_offline(root: Path, compose: list[str], *, absent: bool = False) -> None:
    """Reject runtime containers that violate an offline initialization prerequisite.

    Read the project and service names without requiring populated service environment
    files. During fresh setup, placeholder credential values are used only to resolve
    Compose configuration. This check changes no files or containers. If the offline
    prerequisite is not met, the error explains which teardown command is needed.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        compose: Split Compose executable/options for the selected deployment.
        absent: Require containers removed, including stopped ones, for full setup.
            False permits stopped containers for certificate-only initialization.

    Returns:
        None.

    Raises:
        ValueError: Required services are still present or running, or Docker
            configuration cannot be inspected.
    """
    environment = None
    if absent and not (root / ".env").exists():
        # These required runtime credentials do not exist before first setup.
        # Public placeholders are used only to resolve Compose coordinates. No
        # container is created from this configuration and no file is written.
        environment = dict(os.environ)
        for name in (
            "RUSTFS_ACCESS_KEY",
            "RUSTFS_SECRET_KEY",
            "RUSTFS_KMS_STATIC_SECRET_KEY",
        ):
            environment.setdefault(name, "initialization-preflight")
    configuration = json.loads(
        run(
            [*compose, "config", "--no-env-resolution", "--format", "json"],
            root=root,
            env=environment,
        )
    )
    arguments = [*engine_command(compose), "ps"]
    if absent:
        arguments.append("--all")
    arguments.extend(
        [
            "--filter",
            "label=com.docker.compose.project=" + configuration["name"],
            "--format",
            '{{ '{{.Label "com.docker.compose.service"}}' }}',
        ]
    )
    services = set(run(arguments, root=root).decode().splitlines())
    retained = sorted(services.intersection(configuration["services"]))
    if retained:
        prerequisite = "removed" if absent else "stopped"
        raise ValueError(
            f"normal deployment services must be {prerequisite} before initialization: "
            f"{', '.join(retained)}. Run {shlex.join(compose)} down without --volumes "
            "to retain deployment data, then retry."
        )


class Runtime:
    """Resolve one effective Compose project for certificate installation.

    Read the effective Compose configuration once so certificate commands use the same
    project, Docker engine, images and volumes as the deployment. The configuration must
    identify API and nginx services, one public HTTP port, one public HTTPS port and an
    API network. Temporary helper containers use these selections without host write
    mounts or access to the Docker socket.

    Args:
        root: Deployment directory containing SSL configuration and certificate files.
        compose: Split Compose command including any selected files and engine options.
    """

    def __init__(self, root: Path, compose: list[str]):
        """Load the deployment services, images, published ports, network and volumes.

        Resolve the service configuration used by later certificate commands.
        Construction does not start or stop application services.

        Args:
            root: Deployment directory containing SSL configuration and certificate
                files.
            compose: Split Compose command; --project-directory is added for root.

        Returns:
            None.

        Raises:
            ValueError: Compose cannot be resolved or a selected value is invalid.
            KeyError: A required service or configuration field is missing.
            StopIteration: A required published port or API network cannot be selected.
        """
        self.root = root
        self.docker = engine_command(compose)
        self.compose = [*compose, "--project-directory", str(root)]
        self.config = json.loads(
            run([*self.compose, "config", "--format", "json"], root=root)
        )
        self.project = self.config["name"]
        self.services = self.config["services"]
        self.volumes = self.config.get("volumes", {})
        self.api = next(name for name in self.services if name.endswith("-restapi"))
        self.nginx = next(name for name in self.services if name.endswith("-nginx"))
        self.image = self.services[self.api]["image"]
        self.public_connect()
        self.published_port(NGINX_HTTP_PORT)
        networks = self.services[self.api].get("networks", {})
        if not networks:
            raise ValueError(
                "API requires an effective Compose network for verified live checks"
            )
        self.network = self.config["networks"][next(iter(networks))]["name"]

    def volume(self, logical: str) -> str:
        """Resolve a logical Compose volume key to its effective Docker name.

        Args:
            logical: Volume key in the effective Compose volumes table.

        Returns:
            Valid Docker volume name, including any externally supplied name.

        Raises:
            KeyError: The logical volume is not configured.
            ValueError: Its effective name has invalid syntax.
        """
        name = self.volumes[logical]["name"]
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", name) is None
        ):
            raise ValueError(f"{logical}: invalid effective volume name")
        return name

    def affected(self, targets: list[str]) -> list[str]:
        """Select serving services and direct API consumers for an endpoint change.

        Args:
            targets: Selected endpoint names, restapi and/or nginx.

        Returns:
            Sorted service names. An API change includes nginx and configured workers;
            an nginx-only change does not restart unrelated API consumers.
        """
        selected = {self.api if name == "restapi" else self.nginx for name in targets}
        if "restapi" in targets:
            selected.add(self.nginx)
            selected.update(
                name
                for name in self.services
                if any(
                    kind in name
                    for kind in ("-tfcpu-", "-tfgpu-", "-pytorchcpu-", "-pytorchgpu-")
                )
            )
        return sorted(selected)

    def stop(self, services: list[str]) -> None:
        """Stop selected normal services without removing their persistent volumes.

        Wait for Compose to stop the selected services. Their containers and persistent
        volumes remain available for the subsequent installation or restart.

        Args:
            services: Service names in this deployment to stop with Compose.

        Returns:
            None.

        Raises:
            ValueError: The Compose stop command fails.
        """
        run([*self.compose, "stop", *services], root=self.root)

    def start(self, services: list[str]) -> None:
        """Start selected services with the API first and no implicit dependencies.

        Use up -d --no-deps for the API and then the remaining consumers. This method
        does not wait for live HTTPS; the caller verifies readiness before reporting
        success.

        Args:
            services: Effective service names whose backend prerequisites the caller
                has supplied.

        Returns:
            None.

        Raises:
            ValueError: A Compose command fails.
        """
        if self.api in services:
            run([*self.compose, "up", "-d", "--no-deps", self.api], root=self.root)
        remaining = [service for service in services if service != self.api]
        if remaining:
            run([*self.compose, "up", "-d", "--no-deps", *remaining], root=self.root)

    def public_port(self) -> int:
        """Resolve nginx's required public HTTPS port.

        Returns:
            The sole published TCP port mapped to nginx container port 30443.

        Raises:
            ValueError: The mapping is missing, ambiguous or invalid.
        """
        return self.published_port(NGINX_HTTPS_PORT)

    def published_port(self, target: int) -> int:
        """Resolve exactly one nginx TCP port mapping.

        Args:
            target: Container-side nginx port, normally 30080 or 30443.

        Returns:
            Published numeric port in the range 1 through 65535.

        Raises:
            ValueError: There is no unique numeric valid mapping for the target.
        """
        ports = [
            port
            for port in self.services[self.nginx].get("ports", [])
            if port["target"] == target and port.get("protocol", "tcp") == "tcp"
        ]
        if len(ports) != 1 or not str(ports[0].get("published", "")).isdigit():
            raise ValueError(
                f"nginx requires one unambiguous published mapping for container port {target} in effective Compose configuration"
            )
        published = int(ports[0]["published"])
        if not 1 <= published <= 65535:
            raise ValueError(
                f"nginx published port for {target} must be between 1 and 65535"
            )
        return published

    def public_connect(self) -> str:
        """Choose the manager's TCP destination for nginx verification.

        Use x-dioptra.nginx-connect-host from the effective Compose configuration when
        nonempty. Otherwise use the published bind address, translating wildcard binds
        to the corresponding loopback address. The override changes neither the
        published port nor the identity verified by TLS and sent in the Host header.

        Returns:
            Concrete connection hostname or IP address.

        Raises:
            ValueError: The HTTPS mapping, bind address or connection override is invalid.
        """
        self.public_port()
        options = self.config.get("x-dioptra", {})
        if not isinstance(options, dict):
            raise ValueError("x-dioptra must be a mapping")
        address = options.get("nginx-connect-host", "")
        if not isinstance(address, str):
            raise ValueError("x-dioptra.nginx-connect-host must be a string")
        if address:
            try:
                address = config.host(address)
            except ValueError as exc:
                raise ValueError(f"x-dioptra.nginx-connect-host: {exc}") from exc
            if address in (IPV4_WILDCARD, IPV6_WILDCARD):
                raise ValueError("nginx-connect-host requires a concrete destination")
            return address
        ports = [
            p
            for p in self.services[self.nginx].get("ports", [])
            if p["target"] == NGINX_HTTPS_PORT and p.get("protocol", "tcp") == "tcp"
        ]
        address = ports[0].get("host_ip", IPV4_WILDCARD)
        if not isinstance(address, str):
            raise ValueError("invalid published bind address")
        return {
            IPV4_WILDCARD: probe.IPV4_LOOPBACK,
            IPV6_WILDCARD: probe.IPV6_LOOPBACK,
        }.get(address, address)

    def create_operation_volume(self, name: str, operation: str) -> None:
        """Create or reuse storage belonging to exactly one recorded operation.

        Label a newly created volume with the supplied operation ID. Reuse is allowed
        only when an existing volume has that same label, preventing one operation from
        taking over another's files. The caller retains the volume for recovery and is
        responsible for any later removal.

        Args:
            name: Docker volume name reserved for this operation.
            operation: Operation ID required in the org.dioptra.ssl.operation label.

        Returns:
            None.

        Raises:
            ValueError: Docker fails or an existing volume has a missing or conflicting
                operation label.
        """
        result = subprocess.run(
            [*self.docker, "volume", "inspect", name],
            cwd=self.root,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            labels = json.loads(result.stdout)[0].get("Labels") or {}
            if labels.get("org.dioptra.ssl.operation") != operation:
                raise ValueError(
                    f"{name}: unknown initialization volume; expected operation {operation}"
                )
            return
        run(
            [
                *self.docker,
                "volume",
                "create",
                "--label",
                f"org.dioptra.ssl.operation={operation}",
                name,
            ],
            root=self.root,
        )

    @contextmanager
    def helper(
        self, image: str, mounts: list[tuple[str, str, bool]], *, network: str = "none"
    ):
        """Run certificate tools in a temporary root container.

        Start a temporary container for certificate tools and file inspection, then
        remove it on leaving the context. Named volumes are retained. If removal fails
        while another exception is already being handled, attach the cleanup error to
        that exception so both failures remain visible.

        Args:
            image: Container image providing the required certificate or filesystem
                tools.
            mounts: Tuples of Docker volume name, absolute container mount path and
                read-only flag.
            network: Docker network name, or none to disable networking.

        Yields:
            A Container interface for the started helper.

        Raises:
            ValueError: Docker creation, startup, operations or removal fails.
        """
        name = f"{self.project}-ssl-{secrets.token_hex(12)}"
        args = [
            *self.docker,
            "create",
            "--name",
            name,
            "--user",
            "0:0",
            "--network",
            network,
        ]
        for volume, destination, readonly in mounts:
            args.extend(
                [
                    "--mount",
                    f"type=volume,source={volume},target={destination}"
                    + (",readonly" if readonly else ""),
                ]
            )
        args.extend(["--entrypoint", "sleep", image, "infinity"])
        run(args, root=self.root)
        try:
            run([*self.docker, "start", name], root=self.root)
            yield Container(self.root, name, self.docker)
        except BaseException as primary:
            try:
                run([*self.docker, "rm", "--force", name], root=self.root)
            except (OSError, ValueError) as cleanup:
                primary.add_note(
                    f"temporary helper {name} removal also failed: {cleanup}"
                )
            raise
        else:
            run([*self.docker, "rm", "--force", name], root=self.root)


class Container:
    """Execute commands and transfer checked files through one existing Docker container.

    Runtime.helper creates and removes the container; this object provides access to it
    while it is running. File transfers set destination ownership explicitly. Copying a
    file out of the container never applies container user or group ownership to the
    host file.

    Args:
        root: Working directory used by Docker commands.
        name: Existing helper container name.
        docker: Docker executable and engine-selection arguments.
    """

    def __init__(self, root: Path, name: str, docker: list[str]):
        """Retain the coordinates of an already running helper.

        Args:
            root: Docker command working directory.
            name: Existing helper container name.
            docker: Docker executable and global engine options.

        Returns:
            None.
        """
        self.root, self.name, self.docker = root, name, docker

    def exec(self, *arguments: str) -> bytes:
        """Run a command inside this helper without shell interpolation.

        Args:
            arguments: Executable and separate command arguments inside the container.

        Returns:
            Captured stdout bytes.

        Raises:
            ValueError: Docker or the container command fails or times out.
        """
        return run([*self.docker, "exec", self.name, *arguments], root=self.root)

    def put(
        self, source: Path, destination: str, mode: int, owner: str = "0:0"
    ) -> None:
        """Publish one checked host file inside a container with explicit permissions.

        Copy through a temporary name, verify the contents and metadata, then rename the
        file into place and verify it again. Use the requested container ownership
        rather than the host file's owner. Destination parent directories must already
        exist and must not be symbolic links.

        Args:
            source: Caller-owned host file with mode 0600.
            destination: Absolute container file path with existing directory parents.
            mode: Required permissions on the installed container file.
            owner: Numeric uid:gid for the installed file; defaults to root.

        Returns:
            None.

        Raises:
            ValueError: The destination is unsafe, file verification fails or a Docker
                command fails.
        """
        expected = files.digest(files.read(source, 0o600))
        self.safe_destination(destination)
        staging = destination + "." + secrets.token_hex(16)
        run([*self.docker, "cp", str(source), f"{self.name}:{staging}"], root=self.root)
        self.exec("chown", owner, staging)
        self.exec("chmod", f"{mode:04o}", staging)
        self.check(staging, expected, mode, owner)
        self.exec("mv", "-T", staging, destination)
        self.check(destination, expected, mode, owner)

    def safe_destination(self, destination: str) -> None:
        """Reject symbolic links and unexpected objects before writing a container file.

        Check the parent directories and any existing destination before a file
        transfer. An existing destination must be a regular file with one hard link.
        This check creates or changes nothing.

        Args:
            destination: Absolute container path. Its parents must be directories; the
                final file may be absent.

        Returns:
            None.

        Raises:
            ValueError: The path is unsafe or cannot be inspected.
        """
        path = Path(destination)
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError(
                f"{destination}: requires an absolute contained container path"
            )
        for parent in reversed(path.parents):
            info = self.exec("stat", "-c", "%F", str(parent)).decode().strip()
            if info != "directory":
                raise ValueError(
                    f"{parent}: expected real container directory, got {info}"
                )
        result = subprocess.run(
            [*self.docker, "exec", self.name, "stat", "-c", "%F:%h", destination],
            cwd=self.root,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip() != b"regular file:1":
            raise ValueError(
                f"{destination}: refuses unsafe existing destination {result.stdout!r}"
            )
        if result.returncode and b"No such file" not in result.stderr:
            raise ValueError(
                f"{destination}: cannot inspect destination: {result.stderr!r}"
            )

    def private_directory(self, destination: str) -> None:
        """Create and protect each directory in a helper's private volume.

        Create missing directories below the helper's private mount and protect them
        with mode 0700. Existing components must be real directories owned by root.

        Args:
            destination: Absolute path below /private with no parent traversal.

        Returns:
            None.

        Raises:
            ValueError: A component is unsafe or a container command fails.
        """
        path = Path(destination)
        if (
            not path.is_absolute()
            or path.parts[:2] != ("/", "private")
            or ".." in path.parts
        ):
            raise ValueError("construction directories must stay under /private")
        for current in [*reversed(path.parents), path]:
            if str(current) == "/":
                continue
            self.exec("mkdir", "-p", "-m", "0700", str(current))
            observed = self.exec("stat", "-c", "%F:%u", str(current)).decode().strip()
            if observed != "directory:0":
                raise ValueError(f"{current}: unsafe construction directory {observed}")
            self.exec("chmod", "0700", str(current))

    def check(
        self, destination: str, expected: str, mode: int, owner: str = "0:0"
    ) -> None:
        """Check a container file against its recorded bytes and metadata.

        Inspect file type, hard-link count, permissions and ownership before comparing
        the SHA-256 digest. A mismatch is reported without repairing metadata or
        rewriting the file.

        Args:
            destination: Absolute path to a regular file with one hard link.
            expected: Expected lowercase SHA-256 hex digest.
            mode: Exact POSIX permissions.
            owner: Expected numeric uid:gid, defaulting to root.

        Returns:
            None.

        Raises:
            ValueError: The file metadata or digest differs, or a Docker command fails.
        """
        info = self.exec("stat", "-c", "%F:%h:%a:%u:%g", destination).decode().strip()
        required = f"regular file:1:{mode:o}:{owner}"
        if info != required:
            raise ValueError(
                f"{self.name}:{destination}: observed {info!r}, expected {required!r}"
            )
        actual = self.exec("sha256sum", destination).decode().split()[0]
        if actual != expected:
            raise ValueError(
                f"{self.name}:{destination}: digest differs from selected candidate"
            )

    def get(self, source: str, destination: Path, mode: int = 0o600) -> None:
        """Export a container file without applying its ownership on the host.

        Check the container file type, link count and digest before publishing bytes
        through the protected host writer. Preserve an identical existing host file.

        Args:
            source: Container file path to read and hash.
            destination: Host snapshot path; an identical existing file is preserved.
            mode: Required host mode, defaulting to 0600.

        Returns:
            None.

        Raises:
            ValueError: The source is unsafe or changes during export, an existing
                host file differs, or a Docker command fails.
            OSError: A host file cannot be read or published.
        """
        info = self.exec("stat", "-c", "%F:%h", source).decode().strip()
        if info != "regular file:1":
            raise ValueError(
                f"{self.name}:{source}: expected single-link regular export file, got {info}"
            )
        expected = self.exec("sha256sum", source).decode().split()[0]
        # cat uses an explicit executable array, not command interpretation. Python
        # creates the host file, so container UID/GID never controls host ownership.
        content = self.exec("cat", source)
        if files.digest(content) != expected:
            raise ValueError(f"{source}: changed during container export")
        try:
            existing = files.read(destination, mode)
        except FileNotFoundError:
            files.write(destination, content, mode)
        else:
            if existing != content:
                raise ValueError(
                    f"{destination}: retained export differs; refusing overwrite"
                )

    def exists(self, path: str) -> bool:
        """Check container path existence without accepting its type or ownership.

        This answers only whether test -e succeeds. Before reading or replacing an
        existing path, callers must also check its file type, ownership and permissions.

        Args:
            path: Container path supplied to test -e.

        Returns:
            True when test -e succeeds, False when it reports absence.

        Raises:
            ValueError: Docker or the existence check is unavailable.
        """
        result = subprocess.run(
            [*self.docker, "exec", self.name, "test", "-e", path],
            cwd=self.root,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode not in {0, 1}:
            raise ValueError(f"{self.name}:{path}: existence check unavailable")
        return result.returncode == 0
