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
"""Tests for core.updater - .env parsing/writing, version helpers, and upgrade
behavior."""

from unittest.mock import patch

import pytest

from dioptra.cli.core import updater


class TestReadContainerTag:
    """Tests for updater._read_container_tag()"""

    def test_reads_simple_value(self, tmp_path):
        (tmp_path / ".env").write_text("CONTAINER_TAG=1.1.0\n")
        assert updater._read_container_tag(tmp_path) == "1.1.0"

    def test_no_env_file_returns_none(self, tmp_path):
        assert updater._read_container_tag(tmp_path) is None

    def test_no_container_tag_key_returns_none(self, tmp_path):
        (tmp_path / ".env").write_text("OTHER_VAR=value\n")
        assert updater._read_container_tag(tmp_path) is None

    def test_ignores_comments(self, tmp_path):
        (tmp_path / ".env").write_text(
            "# CONTAINER_TAG=commented\nCONTAINER_TAG=real\n"
        )
        assert updater._read_container_tag(tmp_path) == "real"

    def test_strips_double_quotes(self, tmp_path):
        (tmp_path / ".env").write_text('CONTAINER_TAG="1.1.0"\n')
        assert updater._read_container_tag(tmp_path) == "1.1.0"

    def test_strips_single_quotes(self, tmp_path):
        (tmp_path / ".env").write_text("CONTAINER_TAG='1.1.0'\n")
        assert updater._read_container_tag(tmp_path) == "1.1.0"

    def test_ignores_whitespace_around_equals(self, tmp_path):
        (tmp_path / ".env").write_text("CONTAINER_TAG = 1.1.0\n")
        assert updater._read_container_tag(tmp_path) == "1.1.0"

    def test_reads_amid_other_vars(self, tmp_path):
        (tmp_path / ".env").write_text(
            "MINIO_ROOT_PASSWORD=secret\nCONTAINER_TAG=1.1.0-3\nOTHER=thing\n"
        )
        assert updater._read_container_tag(tmp_path) == "1.1.0-3"

    def test_ignores_blank_lines(self, tmp_path):
        (tmp_path / ".env").write_text("\nCONTAINER_TAG=1.1.0\n\n")
        assert updater._read_container_tag(tmp_path) == "1.1.0"


class TestWriteContainerTag:
    """Tests for updater._write_container_tag()."""

    def test_writes_new_tag_preserving_other_lines(self, tmp_path):
        (tmp_path / ".env").write_text(
            "OTHER=value\nCONTAINER_TAG=1.1.0\nANOTHER=thing\n"
        )
        updater._write_container_tag(tmp_path, "1.1.0-3")

        content = (tmp_path / ".env").read_text()
        assert "CONTAINER_TAG=1.1.0-3" in content
        assert "OTHER=value" in content
        assert "ANOTHER=thing" in content
        # check old tag is gone
        assert "CONTAINER_TAG=1.1.0\n" not in content

    def test_missing_env_file_raises(self, tmp_path):
        with pytest.raises(RuntimeError, match=".env not found"):
            updater._write_container_tag(tmp_path, "1.1.0")

    def test_missing_container_tag_key_raises(self, tmp_path):
        (tmp_path / ".env").write_text("OTHER=value\n")
        with pytest.raises(RuntimeError, match="CONTAINER_TAG not found"):
            updater._write_container_tag(tmp_path, "1.1.0")

    def test_preserves_trailing_newline(self, tmp_path):
        (tmp_path / ".env").write_text("CONTAINER_TAG=old\n")
        updater._write_container_tag(tmp_path, "new")
        assert (tmp_path / ".env").read_text().endswith("\n")

    def test_atomic_write_leaves_no_temp(self, tmp_path):
        (tmp_path / ".env").write_text("CONTAINER_TAG=old\n")
        updater._write_container_tag(tmp_path, "new")
        # check no leftover temp files
        assert not (tmp_path / ".env.tmp").exists()


class TestApplyUpdateRollback:
    """Tests that verify apply_update rolls back state on failure."""

    def _write_env(self, path, container_tag):
        """Write a minimal .env with the given CONTAINER_TAG."""
        (path / ".env").write_text(f"CONTAINER_TAG={container_tag}\n")

    def _mock_check_update(self, current, latest):
        """Return a check_update patch that reports the given tags."""
        return patch(
            "dioptra.cli.core.updater.check_update",
            return_value={
                "name": "foo",
                "supported": True,
                "current_container": current,
                "latest_container": latest,
                "current_python": "1.1.0",
                "latest_python": "1.1.0",
                "container_update_available": True,
                "python_update_available": False,
            },
        )

    def _mock_get_record(self, tmp_path):
        """Return a get_deployment_record patch with a minimal record."""
        return patch(
            "dioptra.cli.core.deployments.get_deployment_record",
            return_value={
                "path": str(tmp_path),
                "docker_compose_path": None,
            },
        )

    def test_env_rolled_back_when_pull_fails(self, tmp_path):
        self._write_env(tmp_path, "1.0.0")

        with (
            self._mock_check_update("1.0.0", "1.1.0"),
            self._mock_get_record(tmp_path),
            patch(
                "dioptra.cli.core.docker.compose_pull",
                side_effect=RuntimeError("simulated pull failure"),
            ),
        ):
            with pytest.raises(RuntimeError, match="simulated pull failure"):
                updater.apply_update("foo")

        # .env should be back to the original value
        content = (tmp_path / ".env").read_text()
        assert "CONTAINER_TAG=1.0.0" in content
        assert "CONTAINER_TAG=1.1.0" not in content

    def test_env_rolled_back_when_compose_up_fails(self, tmp_path):
        self._write_env(tmp_path, "1.0.0")

        with (
            self._mock_check_update("1.0.0", "1.1.0"),
            self._mock_get_record(tmp_path),
            patch("dioptra.cli.core.docker.compose_pull"),
            patch(
                "dioptra.cli.core.docker.get_status",
                return_value="running",
            ),
            patch(
                "dioptra.cli.core.docker.compose_up",
                side_effect=RuntimeError("simulated up failure"),
            ),
        ):
            with pytest.raises(RuntimeError, match="simulated up failure"):
                updater.apply_update("foo")

        content = (tmp_path / ".env").read_text()
        assert "CONTAINER_TAG=1.0.0" in content

    def test_no_update_no_side_effects(self, tmp_path):
        self._write_env(tmp_path, "1.1.0")

        # check_update reports no container update available
        with patch(
            "dioptra.cli.core.updater.check_update",
            return_value={
                "name": "foo",
                "supported": True,
                "current_container": "1.1.0",
                "latest_container": "1.1.0",
                "current_python": "1.1.0",
                "latest_python": "1.1.0",
                "container_update_available": False,
                "python_update_available": False,
            },
        ):
            result = updater.apply_update("foo")

        # .env untouched
        assert (tmp_path / ".env").read_text() == "CONTAINER_TAG=1.1.0\n"
        # Returns the status dict unchanged
        assert result["current_container"] == "1.1.0"

    def test_unsupported_deployment_raises_before_side_effects(self, tmp_path):
        self._write_env(tmp_path, "1.0.0")

        with patch(
            "dioptra.cli.core.updater.check_update",
            return_value={
                "name": "foo",
                "supported": False,
                "supported_reason": "no .env container tag",
            },
        ):
            with pytest.raises(RuntimeError, match="no .env container tag"):
                updater.apply_update("foo")

        # .env untouched
        assert (tmp_path / ".env").read_text() == "CONTAINER_TAG=1.0.0\n"
