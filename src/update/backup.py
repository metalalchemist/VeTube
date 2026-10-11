"""Backup and restore support for safe update rollback."""

import logging
import os
import shutil
import tempfile
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


def create_backup(install_dir: str, version: str, progress_callback=None) -> str:
    """Create a fresh backup of immutable program files.

    Checks disk space first (needs 2x install size). Creates a
    unique ``_backup_v{version}-*/`` directory in the parent of install_dir.

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

    # Program files are immutable while VeTube runs; mutable user data and logs
    # must not race the parallel backup or be restored over newer user changes.
    ignored = {
        "logs",
        "voices",
        "engines",
        "keymaps",
        "sounds",
        "data.json",
        "favoritos.json",
        "mensajes_destacados.json",
        "keys.txt",
        "_update_transaction",
        "_update_cleanup.txt",
        "_update_leftovers.txt",
    }

    def ignore(directory, names):
        excluded = (
            {name for name in names if name.lower() in ignored}
            if Path(directory).resolve() == Path(install_dir).resolve()
            else set()
        )
        for name in names:
            if name in excluded:
                continue
            candidate = Path(directory) / name
            if (
                candidate.is_symlink()
                or getattr(candidate, "is_junction", lambda: False)()
            ):
                raise OSError("Backup contains a linked path")
        return excluded

    total = 0
    for directory, subdirs, names in os.walk(install_dir):
        excluded = ignore(directory, subdirs + names)
        subdirs[:] = [name for name in subdirs if name not in excluded]
        total += sum(name not in excluded for name in names)
    # Allocate only after scanning succeeds, so a bad path leaves no partial dir.
    backup_path = tempfile.mkdtemp(
        prefix=f"_backup_v{version}-", dir=Path(install_dir).resolve().parent
    )
    logger.info("Creating backup at '%s'", backup_path)
    copiados = 0

    def _copiar(src, dst, *, follow_symlinks=True):
        nonlocal copiados
        if Path(src).is_symlink():
            raise OSError("Backup contains a symbolic link")
        shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
        copiados += 1
        if progress_callback:
            progress_callback(copiados, total)

    try:
        shutil.copytree(
            install_dir,
            backup_path,
            dirs_exist_ok=True,
            copy_function=_copiar,
            ignore=ignore,
        )
        if total == 0 and progress_callback:
            progress_callback(0, 0)
    except BaseException:
        shutil.rmtree(backup_path, ignore_errors=True)
        raise
    logger.info("Backup created successfully")

    return backup_path


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
