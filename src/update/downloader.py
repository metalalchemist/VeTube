"""Streaming file downloader with progress reporting."""

import logging
from collections.abc import Callable

import httpx

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 128 * 1024


def download(
    url: str,
    dest_path: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> str:
    """Download file from URL to dest_path with optional progress reporting.

    Uses httpx streaming to read in 128KB chunks.

    Args:
        url: URL to download from.
        dest_path: Local file path to write to.
        progress_callback: Called with (bytes_downloaded, total_bytes) per chunk.
            total_bytes is 0 if Content-Length is unknown.

    Returns:
        dest_path on success.

    Raises:
        httpx.HTTPStatusError: On HTTP errors.
        OSError: On file write errors.
    """
    logger.info("Downloading '%s' to '%s'", url, dest_path)

    with httpx.Client(follow_redirects=True, timeout=300) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()

            total_bytes = int(response.headers.get("content-length", 0))
            bytes_downloaded = 0

            with open(dest_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=_CHUNK_SIZE):
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_downloaded, total_bytes)

    logger.info("Download complete: %d bytes", bytes_downloaded)
    return dest_path
