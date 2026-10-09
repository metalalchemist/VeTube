"""Integration tests for the full update flow."""

from unittest.mock import MagicMock, patch

import pytest

from update.github_client import ReleaseInfo, clear_cache


@pytest.fixture(autouse=True)
def _clear_gh_cache():
    clear_cache()
    yield
    clear_cache()


@pytest.fixture(autouse=True)
def _no_real_windows(monkeypatch):
    for name in ("hide_main_window", "show_main_window", "update_finished"):
        monkeypatch.setattr(f"update.updater.{name}", MagicMock())


def _make_release(tag="v4.0", version="4.0"):
    return ReleaseInfo(
        tag=tag,
        version=version,
        prerelease=False,
        description="New features",
        zip_url="https://example.com/VeTube.zip",
        checksum_url="https://example.com/VeTube.zip.sha256",
        zip_name="VeTube.zip",
    )


class TestInstallUpdateFlow:
    @patch("update.updater.update_finished")
    @patch("update.updater.launch_bootstrap")
    @patch("update.updater.extract")
    @patch("update.updater.create_backup")
    @patch("update.updater.verify")
    @patch("update.updater._fetch_checksum")
    @patch("update.updater.download")
    @patch("update.updater.cleanup_backup")
    def test_successful_update(
        self,
        mock_cleanup,
        mock_download,
        mock_fetch_checksum,
        mock_verify,
        mock_backup,
        mock_extract,
        mock_bootstrap,
        mock_finished,
        tmp_path,
    ):
        from update.updater import _install_update

        release = _make_release()
        mock_download.return_value = str(tmp_path / "VeTube.zip")
        mock_fetch_checksum.return_value = "abc123  VeTube.zip\n"
        mock_verify.return_value = True
        mock_backup.return_value = str(tmp_path / "backup")
        mock_bootstrap.return_value = 0

        _install_update(release)

        mock_download.assert_called_once()
        mock_fetch_checksum.assert_called_once_with(
            "https://example.com/VeTube.zip.sha256"
        )
        mock_verify.assert_called_once()
        mock_backup.assert_called_once()
        mock_extract.assert_called_once()
        mock_bootstrap.assert_called_once()
        mock_cleanup.assert_called_once_with(str(tmp_path / "backup"))
        mock_finished.assert_called_once()

    @patch("update.updater.restore_backup")
    @patch("update.updater.launch_bootstrap")
    @patch("update.updater.extract")
    @patch("update.updater.create_backup")
    @patch("update.updater.verify")
    @patch("update.updater._fetch_checksum")
    @patch("update.updater.download")
    def test_verification_fail_no_backup_to_restore(
        self,
        mock_download,
        mock_fetch_checksum,
        mock_verify,
        mock_backup,
        mock_extract,
        mock_bootstrap,
        mock_restore,
        tmp_path,
    ):
        from update.updater import _install_update

        release = _make_release()
        mock_download.return_value = str(tmp_path / "VeTube.zip")
        mock_fetch_checksum.return_value = "abc123  VeTube.zip\n"
        mock_verify.return_value = False

        _install_update(release)

        mock_backup.assert_not_called()
        mock_extract.assert_not_called()
        mock_bootstrap.assert_not_called()
        mock_restore.assert_not_called()

    @patch("update.updater.restore_backup")
    @patch("update.updater.launch_bootstrap")
    @patch("update.updater.extract")
    @patch("update.updater.create_backup")
    @patch("update.updater.verify")
    @patch("update.updater._fetch_checksum")
    @patch("update.updater.download")
    def test_extraction_fail_triggers_rollback(
        self,
        mock_download,
        mock_fetch_checksum,
        mock_verify,
        mock_backup,
        mock_extract,
        mock_bootstrap,
        mock_restore,
        tmp_path,
    ):
        from update.updater import _install_update

        release = _make_release()
        mock_download.return_value = str(tmp_path / "VeTube.zip")
        mock_fetch_checksum.return_value = "abc123  VeTube.zip\n"
        mock_verify.return_value = True
        mock_backup.return_value = str(tmp_path / "backup")
        mock_extract.side_effect = OSError("extraction failed")

        with patch("update.updater.os.path.isdir", return_value=True):
            _install_update(release)

        mock_bootstrap.assert_not_called()
        mock_restore.assert_called_once()

    @patch("update.updater.restore_backup")
    @patch("update.updater.launch_bootstrap")
    @patch("update.updater.extract")
    @patch("update.updater.create_backup")
    @patch("update.updater.verify")
    @patch("update.updater._fetch_checksum")
    @patch("update.updater.download")
    def test_bootstrap_fail_triggers_rollback(
        self,
        mock_download,
        mock_fetch_checksum,
        mock_verify,
        mock_backup,
        mock_extract,
        mock_bootstrap,
        mock_restore,
        tmp_path,
    ):
        from update.updater import _install_update

        release = _make_release()
        mock_download.return_value = str(tmp_path / "VeTube.zip")
        mock_fetch_checksum.return_value = "abc123  VeTube.zip\n"
        mock_verify.return_value = True
        mock_backup.return_value = str(tmp_path / "backup")
        mock_bootstrap.return_value = 1

        _install_update(release)

        mock_restore.assert_called_once_with(
            str(tmp_path / "backup"), mock_backup.call_args[0][0]
        )


class TestVersionComparison:
    def test_newer_version_is_detected(self):
        from packaging.version import Version

        current = Version("1.0")
        latest = Version("99.0")
        assert latest > current

    def test_same_version_no_update(self):
        from packaging.version import Version

        current = Version("1.0")
        latest = Version("1.0")
        assert latest <= current

    def test_older_version_no_update(self):
        from packaging.version import Version

        current = Version("1.0")
        latest = Version("0.5")
        assert latest <= current


class TestChannelFiltering:
    @patch("update.github_client.httpx.Client")
    def test_stable_filters_prereleases(self, mock_client_cls):
        from update.github_client import get_latest_release

        releases = [
            {
                "tag_name": "v4.0-beta1",
                "prerelease": True,
                "body": "",
                "assets": [
                    {
                        "name": "VeTube.zip",
                        "browser_download_url": "https://example.com/VeTube.zip",
                    },
                    {
                        "name": "VeTube.zip.sha256",
                        "browser_download_url": "https://example.com/VeTube.zip.sha256",
                    },
                ],
            },
            {
                "tag_name": "v3.95",
                "prerelease": False,
                "body": "",
                "assets": [
                    {
                        "name": "VeTube.zip",
                        "browser_download_url": "https://example.com/VeTube.zip",
                    },
                    {
                        "name": "VeTube.zip.sha256",
                        "browser_download_url": "https://example.com/VeTube.zip.sha256",
                    },
                ],
            },
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = releases
        mock_response.headers = {"ETag": "etag"}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = get_latest_release(channel="stable")
        assert result is not None
        assert result.tag == "v3.95"
