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
#
# The load_public_key, load_signature, and verify_payload functions are adapted from the
# following source:
#
#     ErikusMaximus (https://stackoverflow.com/users/3508142/erikusmaximus), How to
#         verify a signed file in python, URL (version: 2019-07-02):
#         https://stackoverflow.com/q/51331461

from __future__ import annotations

import base64

import click
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.sdk.exceptions import CryptographyDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

from .common import load_payload

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="cryptography",
    )


@require_package("cryptography", exc_type=CryptographyDependencyError)
def load_public_key(filepath: str) -> RSAPublicKey:
    """Load the public RSA key from a file"""
    with open(filepath, "rb") as f:
        public_key: RSAPublicKey = load_pem_public_key(f.read(), default_backend())

    return public_key


def load_signature(filepath: str) -> bytes:
    """Load the signature"""
    with open(filepath, "rb") as f:
        signature: bytes = base64.b64decode(f.read())

    return signature


@require_package("cryptography", exc_type=CryptographyDependencyError)
def verify_payload(payload: bytes, signature: bytes, public_key: RSAPublicKey) -> bool:
    """Verify the payload signature"""
    try:
        public_key.verify(
            signature,
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

    except InvalidSignature:
        raise InvalidSignature("Payload and/or signature files failed verification")

    return True


@click.command()
@click.option(
    "--public-key-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True
    ),
    required=True,
    help="File with public key to use for signing",
)
@click.option(
    "--payload-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True
    ),
    required=True,
    help="Payload to verify with signature file",
)
@click.option(
    "--signature-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True
    ),
    required=True,
    help="File with the payload signature",
)
def verify(public_key_file: str, payload_file: str, signature_file: str) -> bool:
    public_key: RSAPublicKey = load_public_key(filepath=public_key_file)
    payload: bytes = load_payload(filepath=payload_file)
    signature: bytes = load_signature(filepath=signature_file)

    try:
        verification: bool = verify_payload(
            payload=payload, signature=signature, public_key=public_key
        )
        click.echo("OK")

    except InvalidSignature:
        click.echo("ERROR - Payload and/or signature files failed verification")
        verification = False

    return verification


if __name__ == "__main__":
    _ = verify()
