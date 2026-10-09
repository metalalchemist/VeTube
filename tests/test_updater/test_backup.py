"""Tests for update.backup module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from update.backup import (
    InsufficientSpaceError,
    _dir_size,
    check_disk_space,
    cleanup_backup,
    create_backup,
    restore_backup,
)


class TestDirSize:
    def test_empty_dir(self, tmp_path):
        assert _dir_size(str(tmp_path)) == 0

    def test_with_files(self, tmp_path):
        (tmp_path / "a.txt").write_bytes(b"x" * 100)
        (tmp_path / "b.txt").write_bytes(b"y" * 200)
        assert _dir_size(str(tmp_path)) == 300

    def test_nested_dirs(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "c.txt").write_bytes(b"z" * 50)
        assert _dir_size(str(tmp_path)) == 50


class TestCheckDiskSpace:
    @patch("update.backup.shutil.disk_usage")
    @patch("update.backup._dir_size")
    def test_sufficient_space(self, mock_dir_size, mock_disk_usage):
        mock_dir_size.return_value = 100 * 1024 * 1024
        mock_disk_usage.return_value = MagicMock(free=500 * 1024 * 1024)
        ok, required_mb = check_disk_space("/fake/install")
        assert ok is True
        assert required_mb == 200

    @patch("update.backup.shutil.disk_usage")
    @patch("update.backup._dir_size")
    def test_insufficient_space(self, mock_dir_size, mock_disk_usage):
        mock_dir_size.return_value = 100 * 1024 * 1024
        mock_disk_usage.return_value = MagicMock(free=50 * 1024 * 1024)
        ok, required_mb = check_disk_space("/fake/install")
        assert ok is False
        assert required_mb == 200


class TestCreateBackup:
    @patch("update.backup.shutil.copytree")
    @patch("update.backup.check_disk_space")
    def test_creates_correct_path(self, mock_check, mock_copytree):
        mock_check.return_value = (True, 200)
        result = create_backup("/opt/VeTube", "3.95")
        assert result.endswith("_backup_v3.95")
        mock_copytree.assert_called_once_with("/opt/VeTube", result, dirs_exist_ok=True)

    @patch("update.backup.check_disk_space")
    def test_raises_insufficient_space(self, mock_check):
        mock_check.return_value = (False, 500)
        with pytest.raises(InsufficientSpaceError, match="500 MB"):
            create_backup("/opt/VeTube", "3.95")

    @patch("update.backup.shutil.copytree")
    @patch("update.backup.check_disk_space")
    def test_returns_backup_path(self, mock_check, mock_copytree, tmp_path):
        mock_check.return_value = (True, 0)
        install_dir = str(tmp_path / "install")
        os.makedirs(install_dir)
        result = create_backup(install_dir, "1.0")
        assert "_backup_v1.0" in result


class TestRestoreBackup:
    def test_raises_if_backup_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Backup not found"):
            restore_backup(str(tmp_path / "nonexistent"), str(tmp_path / "install"))

    @patch("update.backup.shutil.copytree")
    @patch("update.backup.shutil.rmtree")
    def test_restores_files(self, mock_rmtree, mock_copytree, tmp_path):
        backup = tmp_path / "backup"
        backup.mkdir()
        install = tmp_path / "install"
        install.mkdir()
        restore_backup(str(backup), str(install))
        mock_rmtree.assert_called_once_with(str(install))
        mock_copytree.assert_called_once_with(str(backup), str(install))

    @patch("update.backup.shutil.copytree")
    def test_restores_when_install_missing(self, mock_copytree, tmp_path):
        backup = tmp_path / "backup"
        backup.mkdir()
        install = str(tmp_path / "nonexistent_install")
        restore_backup(str(backup), install)
        mock_copytree.assert_called_once()


class TestCleanupBackup:
    @patch("update.backup.shutil.rmtree")
    def test_deletes_existing_backup(self, mock_rmtree, tmp_path):
        backup = tmp_path / "backup"
        backup.mkdir()
        cleanup_backup(str(backup))
        mock_rmtree.assert_called_once_with(str(backup), ignore_errors=True)

    def test_silent_if_missing(self, tmp_path):
        cleanup_backup(str(tmp_path / "nonexistent"))


class TestBackupProgress:
    @patch("update.backup.check_disk_space", return_value=(True, 0))
    def test_reports_every_file_and_the_total(self, mock_check, tmp_path):
        install = tmp_path / "install"
        (install / "lib").mkdir(parents=True)
        (install / "VeTube.exe").write_bytes(b"app")
        (install / "lib" / "a.pyd").write_bytes(b"a")
        (install / "lib" / "b.pyd").write_bytes(b"b")
        avisos = []

        result = create_backup(
            str(install), "1.0", progress_callback=lambda c, t: avisos.append((c, t))
        )

        assert avisos == [(1, 3), (2, 3), (3, 3)]
        assert (tmp_path / "_backup_v1.0" / "lib" / "b.pyd").read_bytes() == b"b"
        assert result == str(tmp_path / "_backup_v1.0")

    @patch("update.backup.check_disk_space", return_value=(True, 0))
    def test_empty_install_still_closes_the_dialog(self, mock_check, tmp_path):
        install = tmp_path / "install"
        install.mkdir()
        avisos = []
        create_backup(str(install), "1.0", progress_callback=lambda c, t: avisos.append((c, t)))
        assert avisos == [(0, 0)]
