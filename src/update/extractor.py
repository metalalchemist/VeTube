"""Zip archive extraction with progress reporting and error recovery."""

import logging
import os
import shutil
import zipfile
from collections.abc import Callable

logger = logging.getLogger(__name__)


def extract(
    zip_path: str,
    dest_dir: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """Extract a zip file to dest_dir.

    Iterates members for granular progress reporting. On failure, deletes
    the partial extraction directory to avoid leaving corrupted state.

    Args:
        zip_path: Path to the .zip archive.
        dest_dir: Directory to extract into.
        progress_callback: Called with (extracted_count, total_count) per member.

    Raises:
        zipfile.BadZipFile: If the archive is corrupt or invalid.
        PermissionError: If a file is locked or write-protected.
        OSError: On other I/O errors during extraction.
    """
    logger.info("Extracting '%s' to '%s'", zip_path, dest_dir)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.infolist()
            total = len(members)

            for index, member in enumerate(members, start=1):
                zf.extract(member, dest_dir)
                if progress_callback:
                    progress_callback(index, total)

    except (zipfile.BadZipFile, PermissionError, OSError) as exc:
        logger.error("Extraction failed: %s", exc)
        if os.path.isdir(dest_dir):
            logger.info("Cleaning up partial extraction at '%s'", dest_dir)
            shutil.rmtree(dest_dir, ignore_errors=True)
        raise

    logger.info("Extraction complete: %d members", total)
