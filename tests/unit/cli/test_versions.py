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
"""Tests for core.versions - Dioptra version parsing and comparison."""

import pytest
from packaging.version import Version

from dioptra.cli.core import versions
from dioptra.cli.core.versions import InvalidDioptraVersion


class TestParse:
    """Tests for versions.parse()."""

    def test_base_version_only(self):
        base, build = versions.parse("1.1.0")
        assert base == Version("1.1.0")
        assert build == 0

    def test_dev_release(self):
        base, build = versions.parse("1.1.0dev0")
        assert base == Version("1.1.0.dev0")
        assert build == 0

    def test_with_build_suffix(self):
        base, build = versions.parse("1.1.0-3")
        assert base == Version("1.1.0")
        assert build == 3

    def test_dev_with_build_suffix(self):
        base, build = versions.parse("1.1.0dev0-2")
        assert base == Version("1.1.0.dev0")
        assert build == 2

    def test_post_release(self):
        base, build = versions.parse("1.1.0.post1")
        assert base == Version("1.1.0.post1")
        assert build == 0

    def test_empty_string_rejected(self):
        with pytest.raises(InvalidDioptraVersion, match="empty"):
            versions.parse("")

    def test_invalid_base_rejected(self):
        with pytest.raises(InvalidDioptraVersion, match="Invalid base version"):
            versions.parse("not-a-version")

    def test_non_numeric_build_rejected(self):
        with pytest.raises(InvalidDioptraVersion, match="positive integer"):
            versions.parse("1.1.0-abc")

    def test_zero_build_rejected(self):
        with pytest.raises(InvalidDioptraVersion, match=">= 1"):
            versions.parse("1.1.0-0")


class TestIsNewer:
    """Tests for versions.is_newer()."""

    # oldest to newest
    ORDERED_SEQUENCE = [
        "1.1.0dev0",
        "1.1.0dev0-1",
        "1.1.0dev0-2",
        "1.1.0",
        "1.2.0dev0",
        "1.2.0-1",
    ]

    @pytest.mark.parametrize(
        "older,newer", list(zip(ORDERED_SEQUENCE, ORDERED_SEQUENCE[1:]))
    )
    def test_adjacent_pairs_ordered_correctly(self, older, newer):
        assert versions.is_newer(older, newer), f"{newer} should be newer than {older}"
        assert not versions.is_newer(newer, older), (
            f"{older} should not be newer than {newer}"
        )

    def test_same_version_not_newer(self):
        assert not versions.is_newer("1.1.0", "1.1.0")
        assert not versions.is_newer("1.1.0-3", "1.1.0-3")

    def test_older_base_beats_newer_build(self):
        # Base version wins over build number
        assert not versions.is_newer("1.1.0", "1.0.0-99")
        assert versions.is_newer("1.0.0-99", "1.1.0")

    def test_unparseable_current_not_newer(self):
        # dev tag or similar unparseable strings should never trigger updates
        assert not versions.is_newer("dev", "1.1.0")

    def test_unparseable_candidate_not_newer(self):
        assert not versions.is_newer("1.1.0", "dev")

    def test_both_unparseable_not_newer(self):
        assert not versions.is_newer("dev", "latest")
