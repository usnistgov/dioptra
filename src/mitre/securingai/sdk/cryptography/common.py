# The load_payload function is adapted from the following source:
#
#     ErikusMaximus (https://stackoverflow.com/users/3508142/erikusmaximus), How to
#         verify a signed file in python, URL (version: 2019-07-02):
#         https://stackoverflow.com/q/51331461

from __future__ import annotations


def load_payload(filepath: str) -> bytes:
    """Load the payload contents"""
    with open(filepath, "rb") as f:
        payload: bytes = f.read()

    return payload
