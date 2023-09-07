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
import urllib.parse
from typing import Optional


def s3_uri_to_bucket_prefix(s3_uri: str) -> tuple[Optional[str], str]:
    """
    Given an S3 URI in the form:

        s3://<bucket>/<key_prefix>

    extract the bucket and key prefix parts, and return them.

    Args:
        s3_uri: An S3 URI

    Returns:
        A bucket, prefix 2-tuple.
    """
    uri_parts = urllib.parse.urlparse(s3_uri)
    bucket = uri_parts.hostname
    prefix = uri_parts.path.lstrip("/")

    return bucket, prefix
