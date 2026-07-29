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
"""Image and certificate validation for Dioptra installs.

Two concerns live here:

* Image verification via cosign. Fetches verify.json from GitHub raw to see which
  public key was used to sign Dioptra's images, downloads that key, then runs
  `cosign verify` against each image.

* CA certificate staging for the deployment. Validates user-provided PEM
  files and copies them into the deployment's ssl/ca-certificates/
  directory, where container-side scripts pick them up and install them into
  service trust stores.

Network operations are wrapped in a retry helper. Transient errors are detected
by string-matching against known network failure messages; non-transient
errors propagate immediately.
"""

import shutil
import tempfile
from pathlib import Path

from dioptra.cli.core import http, process

CERT_DEST_SUBPATH = Path("ssl") / "ca-certificates"


# --- Cosign image verification --------------------------------------------


def is_cosign_available() -> bool:
    """Return True if the cosign binary is on PATH."""
    return shutil.which("cosign") is not None


def validate_internal_images(
    images: list[str],
    branch: str,
    verbose: bool = False,
) -> None:
    """Verify each image's signature with cosign.

    Fetches the cosign key for the given branch, then runs `cosign verify`
    on each image. The key is removed afterward regardless of outcome.

    Raises RuntimeError if any image fails verification, such as "tag doesn't
    exist in the registry" (often a typo in --version).
    """
    if not images:
        return

    if not is_cosign_available():
        raise RuntimeError("cosign not found; cannot verify Dioptra internal images")

    key_path = get_cosign_key(branch, verbose)
    try:
        for image in images:
            try:
                # run verify image for each image, wrapped in the retry helper
                http.retry(
                    lambda img=image: verify_image(img, key_path, verbose=verbose),
                    verbose=verbose,
                )
            except RuntimeError as e:
                msg = str(e).lower()
                if "manifest_unknown" in msg or "manifest unknown" in msg:
                    raise RuntimeError(
                        f"Image '{image}' was not found in the registry.\n"
                        "Check that --version or --image-tag matches a "
                        "published Dioptra release."
                    ) from e
                raise RuntimeError(
                    f"Image verification failed for '{image}': {e}"
                ) from e
            if verbose:
                print(f"Verified: {image}")
    finally:
        key_path.unlink(missing_ok=True)


def verify_image(image: str, key_path: Path, verbose: bool = False) -> None:
    """Run cosign verify on a single image against the given key.

    Captures output so callers can inspect failures (manifest-unknown,
    signature-mismatch, etc.) from the raised exception.
    """
    process.run(
        ["cosign", "verify", "--key", str(key_path), image],
        verbose=verbose,
        capture_output=True,
    )


def get_cosign_key(branch: str, verbose: bool = False) -> Path:
    """Download Dioptra's cosign public key for the given branch.

    Reads verify.json from the branch on GitHub to learn the key's path,
    then downloads the key to a temp file and returns the path.

    The caller is responsible for cleaning up the returned temp file with
    Path.unlink(missing_ok=True) when done.
    """
    verify = http.fetch_json(branch, "verify.json", verbose=verbose)

    try:
        key_path_str = verify["key_path"]
    except KeyError as e:
        raise RuntimeError(
            "verify.json does not contain required field 'key_path'"
        ) from e

    if not key_path_str:
        raise RuntimeError("verify.json did not contain a valid key path.")

    key_file = tempfile.NamedTemporaryFile(
        mode="w+b",
        prefix="dioptra-cosign",
        suffix=".pub",
        delete=False,
    )
    key_path_local = Path(key_file.name)
    key_file.close()

    try:
        http.fetch_to_file(branch, key_path_str, key_path_local, verbose=verbose)
    except RuntimeError:
        key_path_local.unlink(missing_ok=True)
        raise

    if key_path_local.stat().st_size == 0:
        key_path_local.unlink(missing_ok=True)
        raise RuntimeError(
            f"Fetched cosign public key from branch '{branch}', but the file was empty."
        )

    return key_path_local


# --- Certificate handling -------------------------------------------------


def validate_cert(cert_path: str) -> Path:
    """Validate that a cert file looks like a usable PEM and return its path.

    Performs structural checks only - doesn't verify the cert is
    valid or trusted. Single-cert PEM only; rejects concatenated certs because
    install_cert expects one file per cert.

    Returns the resolved (expanduser'd) path of the source file.
    """
    cert_src = Path(cert_path).expanduser()

    if not cert_src.is_file():
        raise RuntimeError(f"Certificate file not found: {cert_src}")

    content = cert_src.read_text()
    if "BEGIN CERTIFICATE" not in content:
        raise RuntimeError(f"File does not appear to be a PEM certificate: {cert_src}")
    if content.count("BEGIN CERTIFICATE") > 1:
        raise RuntimeError(
            "Concatenated PEM files not supported. Split into individual "
            f"certificate files: {cert_src}"
        )

    return cert_src


def install_cert(cert_src: Path, deployment_path: Path) -> Path:
    """Stage a validated CA certificate for installation into Dioptra services.

    Copies the cert into the deployment's ssl/ca-certificates/ directory to be
    later used by init-deployment.sh's `init_extra_ca_certificates` step.

    Note that the cert must be staged before init-deployment.sh runs.
    """
    dest_dir = deployment_path / CERT_DEST_SUBPATH
    if not dest_dir.exists():
        raise RuntimeError(
            f"Expected cert directory not found at {dest_dir}. The deployment "
            "template may have changed; cert installation cannot proceed."
        )

    dest = dest_dir / cert_src.name
    shutil.copy(cert_src, dest)
    return dest
