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
"""Tests for core.uninstaller - plan generation."""
from contextlib import ExitStack
from unittest.mock import patch

from dioptra.cli.core import uninstaller


class TestPlanUninstall:
    """Tests for uninstaller.plan_uninstall()."""

    def _mock_dependencies(
        self,
        record=None,
        manifest_resources=None,
        refs=None,
    ):
        """Return a stack of patches for the deployment/docker dependencies."""
        record = record or {"path": "/tmp/foo", "docker_compose_path": None}
        manifest_resources = manifest_resources or {
            "images": {"internal": [], "external": []},
            "volumes": [],
            "networks": [],
        }
        refs = refs or {"images": {}, "volumes": {}, "networks": {}}

        return [
            patch(
                "dioptra.cli.core.deployments.get_deployment_record",
                return_value=record,
            ),
            patch(
                "dioptra.cli.core.deployments.read_manifest",
                return_value={"resources": manifest_resources},
            ),
            patch(
                "dioptra.cli.core.deployments.get_resource_references",
                return_value=refs,
            ),
        ]

    def _call(self, **kwargs) -> dict:
        """Call plan_uninstall with defaults, asserting non-None result."""
        plan = uninstaller.plan_uninstall(
            name=kwargs.pop("name", "foo"),
            remove_images=kwargs.pop("remove_images", False),
            include_external=kwargs.pop("include_external", False),
            verbose=kwargs.pop("verbose", False),
        )
        assert plan is not None, "plan_uninstall unexpectedly returned None"
        return plan

    def test_deployment_not_found_returns_none(self):
        with patch(
            "dioptra.cli.core.deployments.get_deployment_record",
            side_effect=ValueError("not found"),
        ):
            plan = uninstaller.plan_uninstall(
                name="foo",
                remove_images=False,
                include_external=False,
            )
            assert plan is None

    def test_basic_plan_structure(self):
        patches = self._mock_dependencies()
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            plan = self._call()

        assert plan["name"] == "foo"
        assert "remove_images" in plan
        assert "remove_volumes" in plan
        assert "remove_networks" in plan
        assert "skip_images" in plan
        assert "skip_volumes" in plan
        assert "skip_networks" in plan

    def test_images_not_removed_unless_requested(self):
        patches = self._mock_dependencies(
            manifest_resources={
                "images": {
                    "internal": ["ghcr.io/usnistgov/dioptra/nginx:1.1.0"],
                    "external": ["postgres:17"],
                },
                "volumes": [],
                "networks": [],
            },
        )
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            plan = self._call(remove_images=False)

        assert plan["remove_images"] == []

    def test_internal_images_removed_when_requested(self):
        patches = self._mock_dependencies(
            manifest_resources={
                "images": {
                    "internal": ["ghcr.io/usnistgov/dioptra/nginx:1.1.0"],
                    "external": ["postgres:17"],
                },
                "volumes": [],
                "networks": [],
            },
        )
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            plan = self._call(remove_images=True, include_external=False)

        assert plan["remove_images"] == [
            "ghcr.io/usnistgov/dioptra/nginx:1.1.0",
        ]

    def test_external_images_included_when_requested(self):
        patches = self._mock_dependencies(
            manifest_resources={
                "images": {
                    "internal": ["ghcr.io/usnistgov/dioptra/nginx:1.1.0"],
                    "external": ["postgres:17"],
                },
                "volumes": [],
                "networks": [],
            },
        )
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            plan = self._call(remove_images=True, include_external=True)

        assert set(plan["remove_images"]) == {
            "ghcr.io/usnistgov/dioptra/nginx:1.1.0",
            "postgres:17",
        }

    def test_shared_images_skipped(self):
        patches = self._mock_dependencies(
            manifest_resources={
                "images": {
                    "internal": ["ghcr.io/usnistgov/dioptra/nginx:1.1.0"],
                    "external": [],
                },
                "volumes": [],
                "networks": [],
            },
            refs={
                "images": {
                    "ghcr.io/usnistgov/dioptra/nginx:1.1.0": {"other-deployment"},
                },
                "volumes": {},
                "networks": {},
            },
        )
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            plan = self._call(remove_images=True)

        assert plan["remove_images"] == []
        assert plan["skip_images"] == [
            "ghcr.io/usnistgov/dioptra/nginx:1.1.0",
        ]

    def test_volumes_always_removed(self):
        patches = self._mock_dependencies(
            manifest_resources={
                "images": {"internal": [], "external": []},
                "volumes": ["foo-data", "foo-config"],
                "networks": [],
            },
        )
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            plan = self._call()

        assert set(plan["remove_volumes"]) == {"foo-data", "foo-config"}

    def test_networks_included(self):
        patches = self._mock_dependencies(
            manifest_resources={
                "images": {"internal": [], "external": []},
                "volumes": [],
                "networks": ["foo-net"],
            },
        )
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            plan = self._call()

        assert plan["remove_networks"] == ["foo-net"]
