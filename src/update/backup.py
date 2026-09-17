"""Backup and restore support for safe update rollback."""

import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class InsufficientSpaceError(OSError):
    """Raised when there is not enough disk space for a backup."""


def _dir_size(path: str) -> int:
    """Calculate total size of a directory tree in bytes."""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def check_disk_space(install_dir: str) -> tuple[bool, int]:
    """Check if there is enough disk space for a backup.

    Requires free space >= 2x the install directory size (one copy for the
    backup, one for the extraction target).

    Args:
        install_dir: Path to the application installation directory.

    Returns:
        Tuple of (ok, required_mb). ``ok`` is True when enough space is
        available. ``required_mb`` is the estimated space needed in megabytes.
    """
    install_size = _dir_size(install_dir)
    required_bytes = install_size * 2
    required_mb = required_bytes // (1024 * 1024)

    usage = shutil.disk_usage(os.path.dirname(os.path.abspath(install_dir)))
    ok = usage.free >= required_bytes

    if not ok:
        logger.warning(
            "Insufficient disk space: need %d MB, have %d MB",
            required_mb,
            usage.free // (1024 * 1024),
        )

    return ok, required_mb


def create_backup(install_dir: str, version: str) -> str:
    """Create a backup of the installation directory.

    Checks disk space first (needs 2x install size). Creates a
    ``_backup_v{version}/`` directory in the parent of install_dir.

    Args:
        install_dir: Path to the application installation directory.
        version: Version string for the backup directory name.

    Returns:
        Path to the created backup directory.

    Raises:
        InsufficientSpaceError: If not enough disk space is available.
    """
    ok, required_mb = check_disk_space(install_dir)
    if not ok:
        raise InsufficientSpaceError(
            f"Need {required_mb} MB free for backup, insufficient disk space"
        )

    parent = Path(install_dir).parent
    backup_path = str(parent / f"_backup_v{version}")

    logger.info("Creating backup at '%s'", backup_path)
    shutil.copytree(install_dir, backup_path, dirs_exist_ok=True)
    logger.info("Backup created successfully")

    return backup_path


def restore_backup(backup_path: str, install_dir: str) -> None:
    """Restore a backup to the installation directory.

    Deletes the current install_dir contents and copies the backup back.

    Args:
        backup_path: Path to the backup directory.
        install_dir: Path to the application installation directory.

    Raises:
        FileNotFoundError: If backup_path does not exist.
    """
    if not os.path.isdir(backup_path):
        raise FileNotFoundError(f"Backup not found: '{backup_path}'")

    logger.info("Restoring backup from '%s' to '%s'", backup_path, install_dir)

    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)

    shutil.copytree(backup_path, install_dir)
    logger.info("Backup restored successfully")


def cleanup_backup(backup_path: str) -> None:
    """Delete a backup directory. Silent if it doesn't exist.

    Args:
        backup_path: Path to the backup directory to remove.
    """
    if not os.path.isdir(backup_path):
        logger.debug("Backup '%s' does not exist, nothing to clean up", backup_path)
        return

    logger.info("Cleaning up backup at '%s'", backup_path)
    shutil.rmtree(backup_path, ignore_errors=True)
