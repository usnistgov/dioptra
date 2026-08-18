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
"""Tests for core.deployments - slug and name utilities."""

from unittest.mock import patch

import pytest

from dioptra.cli.core import deployments


class TestNormalizeDeploymentSlug:
    """Tests for deployments.normalize_deployment_slug()."""

    def test_plain_name_unchanged(self):
        assert deployments.normalize_deployment_slug("foo") == "foo"

    def test_strips_leading_trailing_whitespace(self):
        assert deployments.normalize_deployment_slug("  foo  ") == "foo"

    def test_collapses_internal_whitespace_to_hyphen(self):
        assert deployments.normalize_deployment_slug("my deployment") == "my-deployment"

    def test_collapses_multiple_spaces(self):
        assert deployments.normalize_deployment_slug("a   b") == "a-b"

    def test_collapses_tabs(self):
        assert deployments.normalize_deployment_slug("a\tb") == "a-b"

    def test_mixed_whitespace(self):
        assert deployments.normalize_deployment_slug("a \t b") == "a-b"


class TestDeploymentSlugExists:
    """Tests for deployments.deployment_slug_exists()."""

    def _mock_registry(self, records):
        return patch(
            "dioptra.cli.core.deployments._read_registry",
            return_value={"deployments": records},
        )

    def test_no_deployments(self):
        with self._mock_registry({}):
            assert not deployments.deployment_slug_exists("foo")

    def test_matches_by_path_basename(self):
        with self._mock_registry(
            {
                "some-name": {"path": "/tmp/deployments/foo"},
            }
        ):
            assert deployments.deployment_slug_exists("foo")

    def test_no_match(self):
        with self._mock_registry(
            {
                "some-name": {"path": "/tmp/deployments/foo"},
            }
        ):
            assert not deployments.deployment_slug_exists("bar")

    def test_deployment_without_path_ignored(self):
        with self._mock_registry(
            {
                "malformed": {},
            }
        ):
            assert not deployments.deployment_slug_exists("anything")


class TestResolveNewDeploymentName:
    """Tests for deployments.resolve_new_deployment_name()."""

    def _mock_registry(self, records):
        return patch(
            "dioptra.cli.core.deployments._read_registry",
            return_value={"deployments": records},
        )

    def test_name_returned_stripped(self):
        with self._mock_registry({}):
            assert (
                deployments.resolve_new_deployment_name(
                    "  foo  ",
                    force=False,
                )
                == "foo"
            )

    def test_no_name_no_deployments_returns_default(self):
        with self._mock_registry({}):
            assert (
                deployments.resolve_new_deployment_name(
                    None,
                    force=False,
                )
                == "default"
            )

    def test_no_name_single_deployment_with_force(self):
        with self._mock_registry({"only": {"path": "/x"}}):
            assert (
                deployments.resolve_new_deployment_name(
                    None,
                    force=True,
                )
                == "only"
            )

    def test_no_name_single_deployment_without_force_raises(self):
        with self._mock_registry({"only": {"path": "/x"}}):
            with pytest.raises(ValueError, match="already exists"):
                deployments.resolve_new_deployment_name(None, force=False)

    def test_no_name_multiple_deployments_with_force_raises(self):
        with self._mock_registry(
            {
                "a": {"path": "/a"},
                "b": {"path": "/b"},
            }
        ):
            with pytest.raises(ValueError, match="already exists"):
                deployments.resolve_new_deployment_name(None, force=True)


class TestResolveExistingDeploymentName:
    """Tests for deployments.resolve_existing_deployment_name()."""

    def _mock_registry(self, records):
        return patch(
            "dioptra.cli.core.deployments._read_registry",
            return_value={"deployments": records},
        )

    def test_explicit_name_returned(self):
        with self._mock_registry({"foo": {"path": "/x"}}):
            assert deployments.resolve_existing_deployment_name("foo") == "foo"

    def test_no_name_no_deployments_raises(self):
        with self._mock_registry({}):
            with pytest.raises(ValueError, match="No deployments"):
                deployments.resolve_existing_deployment_name(None)

    def test_no_name_single_deployment(self):
        with self._mock_registry({"only": {"path": "/x"}}):
            assert deployments.resolve_existing_deployment_name(None) == "only"

    def test_no_name_multiple_deployments_raises(self):
        with self._mock_registry(
            {
                "a": {"path": "/a"},
                "b": {"path": "/b"},
            }
        ):
            with pytest.raises(ValueError, match="Multiple deployments"):
                deployments.resolve_existing_deployment_name(None)
