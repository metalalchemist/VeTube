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


def _count_files(path: str) -> int:
    """Count the files of a directory tree (for backup progress)."""
    return sum(len(filenames) for _, _, filenames in os.walk(path))


def backup_dir_for(install_dir: str, version: str) -> str:
    """Where create_backup() puts the copy: ``_backup_v{version}/`` next to install_dir."""
    return str(Path(install_dir).parent / f"_backup_v{version}")


def create_backup(install_dir: str, version: str, progress_callback=None) -> str:
    """Create a backup of the installation directory.

    Checks disk space first (needs 2x install size). Creates a
    ``_backup_v{version}/`` directory in the parent of install_dir.

    Args:
        install_dir: Path to the application installation directory.
        version: Version string for the backup directory name.
        progress_callback: Optional ``callback(current, total)`` called after
            each copied file (and once with ``(total, total)`` if there was
            nothing to copy). Without it the backup is silent.

    Returns:
        Path to the created backup directory.

    Raises:
        InsufficientSpaceError: If not enough disk space is available.
    """
    ok, required_mb = check_disk_space(install_dir)
    if not ok:
        error = InsufficientSpaceError(
            f"Need {required_mb} MB free for backup, insufficient disk space"
        )
        error.required_mb = required_mb  # para el aviso traducido al usuario
        raise error

    backup_path = backup_dir_for(install_dir, version)

    logger.info("Creating backup at '%s'", backup_path)
    if progress_callback is None:
        shutil.copytree(install_dir, backup_path, dirs_exist_ok=True)
    else:
        total = _count_files(install_dir)
        copiados = 0

        def _copiar(src, dst, *, follow_symlinks=True):
            nonlocal copiados
            shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
            copiados += 1
            progress_callback(copiados, total)

        shutil.copytree(
            install_dir, backup_path, dirs_exist_ok=True, copy_function=_copiar
        )
        if total == 0:
            progress_callback(0, 0)
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
