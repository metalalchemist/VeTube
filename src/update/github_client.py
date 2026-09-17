"""GitHub Releases API client with in-memory caching and ETag support."""

import logging
import time
from dataclasses import dataclass
from enum import Enum

import httpx
from packaging.version import InvalidVersion, Version

from update.channel import filter_releases, get_channel

logger = logging.getLogger(__name__)

RELEASES_URL = "https://api.github.com/repos/metalalchemist/VeTube/releases"
CACHE_TTL_SECONDS = 300
_USER_AGENT = "VeTube-Updater/1.0"


@dataclass
class ReleaseInfo:
    """Parsed release information from GitHub API."""

    tag: str
    version: str
    prerelease: bool
    description: str
    zip_url: str
    checksum_url: str
    zip_name: str


class ReleaseLookupStatus(Enum):
    """Outcome of querying GitHub for a compatible release."""

    SUCCESS = "success"
    NO_COMPATIBLE_RELEASE = "no_compatible_release"
    FAILURE = "failure"


@dataclass
class ReleaseLookupResult:
    """Release lookup outcome, including an explicit non-release status."""

    status: ReleaseLookupStatus
    release: ReleaseInfo | None = None


class _ReleaseCache:
    """In-memory cache with TTL and ETag support."""

    def __init__(self) -> None:
        self.data: ReleaseInfo | None = None
        self.timestamp: float = 0
        self.etag: str | None = None
        self._data_by_channel: dict[str, ReleaseInfo | None] = {}
        self._timestamps_by_channel: dict[str, float] = {}
        self.releases: list[dict] | None = None

    def is_fresh(self, channel: str | None = None) -> bool:
        if channel is None:
            return (
                self.data is not None
                and (time.time() - self.timestamp) < CACHE_TTL_SECONDS
            )
        timestamp = self._timestamps_by_channel.get(channel)
        return timestamp is not None and (time.time() - timestamp) < CACHE_TTL_SECONDS

    def store(
        self,
        release: ReleaseInfo | None,
        etag: str | None,
        channel: str | None = None,
        releases: list[dict] | None = None,
    ) -> None:
        self.data = release
        self.timestamp = time.time()
        if channel is not None:
            self._data_by_channel[channel] = release
            self._timestamps_by_channel[channel] = self.timestamp
        if releases is not None:
            self.releases = releases
        if etag:
            self.etag = etag

    def get(self, channel: str) -> ReleaseInfo | None:
        return self._data_by_channel.get(channel)


_cache = _ReleaseCache()


def _parse_release(release: dict) -> ReleaseInfo | None:
    """Extract ReleaseInfo from a GitHub release dict.

    Returns None if required assets (zip + checksum) are missing.
    """
    tag = release.get("tag_name", "")
    if not tag:
        return None

    assets = release.get("assets", [])
    zip_url = ""
    zip_name = ""
    checksum_url = ""

    zip_assets = {
        asset.get("name", ""): asset
        for asset in assets
        if asset.get("name", "").endswith(".zip")
    }
    checksum_assets = {
        asset.get("name", ""): asset
        for asset in assets
        if asset.get("name", "").endswith(".sha256")
    }

    for name, asset in zip_assets.items():
        checksum = checksum_assets.get(f"{name}.sha256")
        if checksum is None:
            continue
        zip_url = asset.get("browser_download_url", "")
        zip_name = name
        checksum_url = checksum.get("browser_download_url", "")
        if zip_url and checksum_url:
            break

    # Keep the pairing exact: a checksum for another ZIP is invalid.
    if not zip_url or not checksum_url:
        logger.debug("Release '%s' missing matching zip/checksum assets, skipping", tag)
        return None

    version = tag[1:] if tag[:1].lower() == "v" else tag
    try:
        Version(version)
    except (InvalidVersion, TypeError):
        logger.debug("Release '%s' has an invalid semantic version, skipping", tag)
        return None

    return ReleaseInfo(
        tag=tag,
        version=version,
        prerelease=release.get("prerelease", False),
        description=release.get("body", ""),
        zip_url=zip_url,
        checksum_url=checksum_url,
        zip_name=zip_name,
    )


def _fetch_releases(client: httpx.Client) -> tuple[list[dict], str | None, bool]:
    """Fetch releases from GitHub API.

    Returns:
        Tuple of (releases_list, etag, not_modified).
        If not_modified is True, releases_list is empty.
    """
    headers: dict[str, str] = {"User-Agent": _USER_AGENT}
    if _cache.etag:
        headers["If-None-Match"] = _cache.etag

    response = client.get(RELEASES_URL, headers=headers, timeout=30)

    if response.status_code == 304:
        return [], None, True

    response.raise_for_status()
    etag = response.headers.get("ETag")
    return response.json(), etag, False


def get_latest_release(channel: str | None = None) -> ReleaseInfo | None:
    """Fetch latest release from GitHub API.

    Uses in-memory cache with 5-min TTL and ETag for conditional requests.

    Args:
        channel: 'stable' or 'beta'. Defaults to user preference.

    Returns:
        ReleaseInfo for the latest matching release, or None if no update
        available or on error.
    """
    return get_latest_release_result(channel).release


def get_latest_release_result(channel: str | None = None) -> ReleaseLookupResult:
    """Fetch the latest compatible release and preserve the lookup outcome.

    The legacy :func:`get_latest_release` API intentionally remains a nullable
    release accessor. Callers that need to distinguish an empty result from a
    failed request should use this function.
    """
    if channel is None:
        channel = get_channel()

    if _cache.is_fresh(channel):
        logger.debug("Returning cached release info")
        release = _cache.get(channel)
        return ReleaseLookupResult(
            ReleaseLookupStatus.SUCCESS
            if release is not None
            else ReleaseLookupStatus.NO_COMPATIBLE_RELEASE,
            release,
        )

    try:
        with httpx.Client() as client:
            releases, etag, not_modified = _fetch_releases(client)

            if not_modified:
                filtered = filter_releases(_cache.releases or [], channel)
                release_info = _select_highest_release(filtered)
                _cache.store(release_info, None, channel=channel)
                return ReleaseLookupResult(
                    ReleaseLookupStatus.SUCCESS
                    if release_info is not None
                    else ReleaseLookupStatus.NO_COMPATIBLE_RELEASE,
                    release_info,
                )

            filtered = filter_releases(releases, channel)
            if not filtered:
                logger.info("No releases found for channel '%s'", channel)
                _cache.store(None, etag, channel=channel, releases=releases)
                return ReleaseLookupResult(ReleaseLookupStatus.NO_COMPATIBLE_RELEASE)

            release_info = _select_highest_release(filtered)

            _cache.store(release_info, etag, channel=channel, releases=releases)
            return ReleaseLookupResult(
                ReleaseLookupStatus.SUCCESS
                if release_info is not None
                else ReleaseLookupStatus.NO_COMPATIBLE_RELEASE,
                release_info,
            )

    except httpx.HTTPError:
        logger.exception("Failed to fetch releases from GitHub")
        return ReleaseLookupResult(ReleaseLookupStatus.FAILURE)
    except Exception:
        logger.exception("Unexpected error fetching releases")
        return ReleaseLookupResult(ReleaseLookupStatus.FAILURE)


def clear_cache() -> None:
    """Clear the release cache. Useful for forcing a fresh check."""
    _cache.data = None
    _cache.timestamp = 0
    _cache.etag = None
    _cache._data_by_channel.clear()
    _cache._timestamps_by_channel.clear()
    _cache.releases = None


def _select_highest_release(releases: list[dict]) -> ReleaseInfo | None:
    """Return the highest valid release, independent of API ordering."""
    candidates: list[tuple[Version, ReleaseInfo]] = []
    for release in releases:
        info = _parse_release(release)
        if info is None:
            continue
        try:
            candidates.append((Version(info.version), info))
        except (InvalidVersion, TypeError):
            continue
    return (
        max(candidates, key=lambda candidate: candidate[0])[1] if candidates else None
    )
