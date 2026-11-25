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
import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-v1", action="store_true", default=False, help="run v1 tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "v1: mark test as v1")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-v1"):
        # --run-v1 given in cli: do not skip v1 tests
        return
    skip_v1 = pytest.mark.skip(reason="need --run-v1 option to run")
    for item in items:
        if "v1_test" in item.keywords:
            item.add_marker(skip_v1)


@pytest.fixture
def tls_certificates(tmp_path):
    """Issue a localhost certificate/key pair and CA trust file for TLS tests."""
    if os.name == "nt":
        pytest.skip("Certificate file protections require POSIX")
    from dioptra.ssl import certificates, publication

    ca_key, ca, _ = certificates.create_ca("Transport test CA", 2048, 2, None)
    key, cert, _ = certificates.issue(
        ca, ca_key, certificates.identities(("localhost",), ()), 2048, 1, None
    )
    cert_path, key_path, ca_path = (
        tmp_path / name for name in ("server.crt", "server.key", "ca.crt")
    )
    publication.publish("create-ca", ca_key, ca, tmp_path / "ca.key", ca_path)
    publication.publish("issue", key, cert, key_path, cert_path)
    return cert_path, key_path, ca_path
