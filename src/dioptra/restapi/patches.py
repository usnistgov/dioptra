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
import hashlib
import inspect
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

EXPECTED_SERIALIZE_OPERATION_SHA256_HASH = "57241f0a33ed5e1771e5032d1e6f6994685185ed526b9ca2c70f4f27684d1f92"  # noqa: B950; fmt: skip
PATCHED_SERIALIZE_OPERATION_SHA256_HASH = "8a51bc04c8dcb81820548d9de53a9606faf0681ffc3684102744c69fbd076437"  # noqa: B950; fmt: skip

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def monkey_patch_flask_restx() -> None:
    """
    Monkey patch flask_restx.Swagger.serialize_operation to force Swagger docs to use
    the multipart/form-data content type for multi-file uploads instead of the
    application/x-www-form-urlencoded content type.

    This monkey-patch applies the proposed change in this PR
    https://github.com/python-restx/flask-restx/pull/542.
    """
    import flask_restx
    from flask_restx.utils import not_none

    serialize_operation_sha256_hash = get_source_code_hash(
        flask_restx.Swagger.serialize_operation
    )

    if serialize_operation_sha256_hash == PATCHED_SERIALIZE_OPERATION_SHA256_HASH:
        LOGGER.debug(
            "flask_restx.Swagger.serialize_operation already patched",
            sha256_hash=serialize_operation_sha256_hash,
        )
        return None

    if serialize_operation_sha256_hash != EXPECTED_SERIALIZE_OPERATION_SHA256_HASH:
        LOGGER.error(
            "Source code hash changed",
            reason="hash of flask_restx.Swagger.serialize_operation did not match",
            expected_hash=EXPECTED_SERIALIZE_OPERATION_SHA256_HASH,
            sha256_hash=serialize_operation_sha256_hash,
        )
        raise RuntimeError(
            "Source code hash changed (reason: hash of "
            "flask_restx.Swagger.serialize_operation did not match "
            f"{EXPECTED_SERIALIZE_OPERATION_SHA256_HASH}): "
            f"{serialize_operation_sha256_hash}"
        )

    def serialize_operation_patched(self, doc, method):
        operation = {
            "responses": self.responses_for(doc, method) or None,
            "summary": doc[method]["docstring"]["summary"],
            "description": self.description_for(doc, method) or None,
            "operationId": self.operation_id_for(doc, method),
            "parameters": self.parameters_for(doc[method]) or None,
            "security": self.security_for(doc, method),
        }
        # Handle 'produces' mimetypes documentation
        if "produces" in doc[method]:
            operation["produces"] = doc[method]["produces"]
        # Handle deprecated annotation
        if doc.get("deprecated") or doc[method].get("deprecated"):
            operation["deprecated"] = True
        # Handle form exceptions:
        doc_params = list(doc.get("params", {}).values())
        all_params = doc_params + (operation["parameters"] or [])
        if all_params and any(p["in"] == "formData" for p in all_params):
            if any(p["type"] == "file" for p in all_params):
                operation["consumes"] = ["multipart/form-data"]
            elif any(
                p["type"] == "array" and p["collectionFormat"] == "multi"
                for p in all_params
                if "collectionFormat" in p
            ):
                operation["consumes"] = ["multipart/form-data"]
            else:
                operation["consumes"] = [
                    "application/x-www-form-urlencoded",
                    "multipart/form-data",
                ]
        operation.update(self.vendor_fields(doc, method))
        return not_none(operation)

    flask_restx.Swagger.serialize_operation = serialize_operation_patched
    LOGGER.info("flask_restx.Swagger.serialize_operation patched successfully")


def get_source_code_hash(obj: Any) -> str:
    """Generate a hash of the underlying source code of a Python object.

    Args:
        obj: The Python object for which to generate a source code hash.

    Returns:
        The hash of the source code of the Python object.
    """

    hash_sha256 = hashlib.sha256()
    source_lines, _ = inspect.getsourcelines(obj)
    source_lines = [line.rstrip() for line in source_lines]

    for line in source_lines:
        hash_sha256.update(line.encode("utf-8"))

    return hash_sha256.hexdigest()
