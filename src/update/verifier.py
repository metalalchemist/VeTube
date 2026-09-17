"""SHA256 verification for downloaded update archives."""

import hashlib
import logging

logger = logging.getLogger(__name__)

_HASH_BUFFER_SIZE = 65536


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Lowercase hex digest string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(_HASH_BUFFER_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest().lower()


def parse_checksum_file(content: str) -> dict[str, str]:
    """Parse sha256sum format: '{hash}  {filename}' per line.

    Handles both two-space and single-space separators.
    Blank lines and lines without a valid format are skipped.

    Args:
        content: Raw text content of a .sha256 checksum file.

    Returns:
        Dict mapping filename -> hash (lowercase).
    """
    result: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            logger.debug("Skipping malformed checksum line: '%s'", line)
            continue
        hash_value, filename = parts
        result[filename.strip()] = hash_value.strip().lower()
    return result


def verify(zip_path: str, checksum_content: str, expected_name: str) -> bool:
    """Verify zip file integrity against checksum content.

    Args:
        zip_path: Path to the downloaded zip file.
        checksum_content: Raw text of the .sha256 checksum file.
        expected_name: Filename to look up in the checksum file.

    Returns:
        True if the computed hash matches the expected hash, False otherwise.
    """
    checksums = parse_checksum_file(checksum_content)
    expected_hash = checksums.get(expected_name)

    if expected_hash is None:
        logger.error("Filename '%s' not found in checksum file", expected_name)
        return False

    actual_hash = compute_sha256(zip_path)
    match = actual_hash == expected_hash.lower()

    if match:
        logger.info("Verification passed for '%s'", expected_name)
    else:
        logger.error(
            "Verification FAILED for '%s': expected=%s, actual=%s",
            expected_name,
            expected_hash,
            actual_hash,
        )

    return match
