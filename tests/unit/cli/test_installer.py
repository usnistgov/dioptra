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
"""Tests for core.installer - install selection and version validation."""

from unittest.mock import patch

import pytest

from dioptra.cli.core import installer
from dioptra.cli.core.installer import InstallSelection


class TestNormalizeReleaseVersion:
    """Tests for installer.normalize_release_version()"""

    def test_plain_version(self):
        assert installer.normalize_release_version("1.1.0") == "1.1.0"

    def test_strips_whitespace(self):
        assert installer.normalize_release_version("  1.1.0  ") == "1.1.0"

    def test_empty_rejected(self):
        with pytest.raises(RuntimeError, match="empty"):
            installer.normalize_release_version("")

    def test_whitespace_only_rejected(self):
        with pytest.raises(RuntimeError, match="empty"):
            installer.normalize_release_version("   ")

    def test_leading_v_rejected(self):
        with pytest.raises(RuntimeError, match="without a leading 'v'"):
            installer.normalize_release_version("v1.1.0")

    def test_build_suffix_rejected(self):
        with pytest.raises(RuntimeError, match="--image-tag"):
            installer.normalize_release_version("1.1.0-1")


class TestResolveInstallSelection:
    """Tests for installer.resolve_install_selection()."""

    @pytest.fixture(autouse=True)
    def mock_get_version(self):
        """Patch get_version for all tests in this class.

        Individual tests can override by patching within their body if
        they need a specific pkg version behavior.
        """
        with patch(
            "dioptra.cli.core.installer.get_version",
            return_value="1.1.0",
        ):
            yield

    def _resolve(self, **overrides) -> InstallSelection:
        defaults = {
            "template_ref" : None,
            "validation_ref": None,
            "init_ref" : None,
            "version" : None,
            "image_tag" : None,
        }
        defaults.update(overrides)
        return installer.resolve_install_selection(**defaults)

    def test_defaults_use_pkg_version_when_release(self):
        # default to the the fixture's "1.1.0"
        sel = self._resolve()
        assert sel.image_tag == "1.1.0"
        assert sel.version is None

    def test_defaults_fall_back_to_dev_for_dev_pkg(self):
        with patch(
            "dioptra.cli.core.installer.get_version",
            return_value="1.2.0.dev0",
        ):
            sel = self._resolve()
        assert sel.image_tag == "dev"

    def test_image_tag_wins_over_version(self):
        sel = self._resolve(version="1.1.0", image_tag="custom-build")
        assert sel.image_tag == "custom-build"
        assert sel.version == "1.1.0"

    def test_version_used_when_no_image_tag(self):
        sel = self._resolve(version="1.1.0")
        assert sel.image_tag == "1.1.0"
        assert sel.version == "1.1.0"

    def test_image_tag_strips_whitespace(self):
        sel = self._resolve(image_tag="  1.1.0  ")
        assert sel.image_tag == "1.1.0"

    def test_template_ref_defaults_to_none(self):
        sel = self._resolve()
        assert sel.template_ref is None

    def test_template_ref_passed_through(self):
        sel = self._resolve(template_ref="feature-branch")
        assert sel.template_ref == "feature-branch"

    def test_validation_ref_defaults_to_main(self):
        sel = self._resolve()
        assert sel.validation_ref == "main"

    def test_init_ref_defaults_to_main(self):
        sel = self._resolve()
        assert sel.init_ref == "main"

    def test_refs_passed_through(self):
        sel = self._resolve(
            template_ref="ref-a",
            validation_ref="ref-b",
            init_ref="ref-c",
        )
        assert sel.template_ref == "ref-a"
        assert sel.validation_ref == "ref-b"
        assert sel.init_ref == "ref-c"

    def test_empty_pkg_version_raises(self):
        with patch(
            "dioptra.cli.core.installer.get_version",
            return_value="",
        ):
            with pytest.raises(RuntimeError, match="Could not determine"):
                self._resolve()
