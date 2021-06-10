# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
#
# The generate_rsa_key_pair, save_private_key, and save_public_key functions are
# adapted from the following source:
#
#     ErikusMaximus (https://stackoverflow.com/users/3508142/erikusmaximus), How to
#         verify a signed file in python, URL (version: 2019-07-02):
#         https://stackoverflow.com/q/51331461

from __future__ import annotations

from typing import Tuple

import click
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.sdk.exceptions import CryptographyDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric.rsa import (
        RSAPrivateKeyWithSerialization,
        RSAPublicKey,
        generate_private_key,
    )
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        PublicFormat,
    )

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="cryptography",
    )


@require_package("cryptography", exc_type=CryptographyDependencyError)
def generate_rsa_key_pair(
    public_exponent: int = 65537, key_size: int = 4096
) -> Tuple[RSAPrivateKeyWithSerialization, RSAPublicKey]:
    """Generate a public/private key pair using the RSA algorithm"""
    private_key: RSAPrivateKeyWithSerialization = generate_private_key(
        public_exponent=public_exponent,
        key_size=key_size,
        backend=default_backend(),
    )
    public_key: RSAPublicKey = private_key.public_key()

    return private_key, public_key


@require_package("cryptography", exc_type=CryptographyDependencyError)
def save_private_key(private_key: RSAPrivateKeyWithSerialization, filepath: str):
    """Save the private RSA key to a file"""
    private_key_bytes: bytes = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption(),
    )

    with open(filepath, "wb") as f:
        f.write(private_key_bytes)


@require_package("cryptography", exc_type=CryptographyDependencyError)
def save_public_key(public_key: RSAPublicKey, filepath: str):
    """Save the public RSA key to a file"""
    public_key_bytes: bytes = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )

    with open(filepath, "wb") as f:
        f.write(public_key_bytes)


def _coerce_to_int(ctx, param, value):
    return int(value)


@click.command()
@click.option(
    "--private-key-file",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, resolve_path=True, readable=True
    ),
    required=True,
    show_default=True,
    default="private.key",
    help="Output path for the generated private key",
)
@click.option(
    "--public-key-file",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, resolve_path=True, readable=True
    ),
    required=True,
    show_default=True,
    default="public.pem",
    help="Output path for the generated public key",
)
@click.option(
    "--public-exponent",
    type=click.Choice(["65537", "3"]),
    required=True,
    show_default=True,
    default="65537",
    callback=_coerce_to_int,
    help=(
        "The public exponent of the new key. Either 65537 or 3 (for legacy purposes). "
        "Almost everyone should use 65537."
    ),
)
@click.option(
    "--key-size",
    type=click.IntRange(min=512, max=None),
    required=True,
    show_default=True,
    default=4096,
    help=(
        "The length of the modulus in bits. It is strongly recommended to be at least "
        "2048 or higher."
    ),
)
def keygen(
    private_key_file: str, public_key_file: str, public_exponent: int, key_size: int
) -> Tuple[RSAPrivateKeyWithSerialization, RSAPublicKey]:
    """Generate a public/private key pair using the RSA algorithm"""
    private_key, public_key = generate_rsa_key_pair(
        public_exponent=public_exponent, key_size=key_size
    )
    save_private_key(private_key=private_key, filepath=private_key_file)
    save_public_key(public_key=public_key, filepath=public_key_file)

    return private_key, public_key


if __name__ == "__main__":
    _ = keygen()
