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
# The load_private_key and sign_payload functions are adapted from the following source:
#
#     ErikusMaximus (https://stackoverflow.com/users/3508142/erikusmaximus), How to
#         verify a signed file in python, URL (version: 2019-07-02):
#         https://stackoverflow.com/q/51331461

from __future__ import annotations

import base64
from typing import Optional

import click
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.sdk.exceptions import CryptographyDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

from .common import load_payload

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.asymmetric.rsa import (
        RSAPrivateKeyWithSerialization,
    )
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="cryptography",
    )


@require_package("cryptography", exc_type=CryptographyDependencyError)
def load_private_key(filepath: str) -> RSAPrivateKeyWithSerialization:
    """Load the private RSA key from a file"""
    with open(filepath, "rb") as f:
        private_key: RSAPrivateKeyWithSerialization = load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend(),
        )

    return private_key


@require_package("cryptography", exc_type=CryptographyDependencyError)
def sign_payload(
    payload: bytes, private_key: RSAPrivateKeyWithSerialization, filepath: str
) -> bytes:
    """Sign the payload"""
    signature: bytes = base64.b64encode(
        private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    )

    with open(filepath, "wb") as f:
        f.write(signature)

    return signature


@click.command()
@click.option(
    "--private-key-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True
    ),
    required=True,
    show_default=True,
    default="private.key",
    help="File with private key to use for signing",
)
@click.option(
    "--payload-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True
    ),
    required=True,
    help="File with payload to sign",
)
@click.option(
    "--signature-file",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, resolve_path=True, readable=True
    ),
    required=False,
    help=(
        "File with payload to sign. Default is to use payload filename with .sig "
        "appended."
    ),
)
def sign(
    private_key_file: str, payload_file: str, signature_file: Optional[str]
) -> bytes:
    private_key: RSAPrivateKeyWithSerialization = load_private_key(
        filepath=private_key_file
    )
    payload: bytes = load_payload(filepath=payload_file)
    signature: bytes = sign_payload(
        payload=payload,
        private_key=private_key,
        filepath=signature_file or f"{payload_file}.sig",
    )

    return signature


if __name__ == "__main__":
    _ = sign()
