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
import pytest


@pytest.fixture
def context():
    return {
        "project_name": "Test Label Studio Deployment",
        "project_slug": "test-label-studio-deployment",
        "project_snakecase": "test_label-studio_deployment",
        "container_slug_prefix": "test-label-studio-deployment",
        "container_registry": "artifacts.example.org:8200",
        "container_namespace": "testname",
        "container_tag": "latest",
        "db_admin_username": "postgres",
        "db_admin_database": "postgres",
        "generate_passwords": "True",
        "nginx_use_https": "True",
        "nginx_server_name": "test-label-studio-server.example.org",
        "nginx_ssl_certificate_stem": "test-label-studio-server",
        "label_studio_http_port": "30080",
        "label_studio_https_port": "30443",
        "label_studio_files_host_dir": "/nfs/label-studio/files",
        "is_firewall_forwarding_ports_80_433": "True",
        "ner_spacy_model_language": "en",
        "ner_spacy_model_flavors": "efficient,accurate",
        "is_podman_deployment": "True",
        "containers": {
            "label_studio": {
                "image": "label-studio",
                "namespace": "testname",
                "tag": "latest",
                "registry": "artifacts.example.org:8200",
            },
            "label_studio_ml_spacy": {
                "image": "label-studio-ml-spacy",
                "namespace": "testname",
                "tag": "latest",
                "registry": "artifacts.example.org:8200",
            },
            "nginx": {
                "image": "nginx",
                "namespace": "testname",
                "tag": "latest",
                "registry": "artifacts.example.org:8200",
            },
            "db": {
                "image": "postgres",
                "namespace": "",
                "tag": "latest",
                "registry": "docker.io",
            },
            "redis": {
                "image": "redis",
                "namespace": "",
                "tag": "latest",
                "registry": "docker.io",
            },
        },
        "ner_flavor_to_model_type": {
            "accurate": "trf",
            "efficient": "sm",
        },
        "_is_pytest": "True",
    }


@pytest.fixture
def result(cookies, context):
    return cookies.bake(extra_context={**context})
