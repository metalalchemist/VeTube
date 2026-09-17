"""Update channel management for stable and beta release filtering."""

import logging
import re

from utils.fajustes import guardarConfiguracion, leerConfiguracion

logger = logging.getLogger(__name__)

VALID_CHANNELS = ("stable", "beta")
DEFAULT_CHANNEL = "stable"
_PRERELEASE_PATTERN = re.compile(r"-(beta|rc|alpha|dev|pre)", re.IGNORECASE)


def get_channel() -> str:
    """Read update_channel from data.json.

    Returns:
        'stable' or 'beta'. Defaults to 'stable' if not set.
    """
    configs = leerConfiguracion()
    channel = configs.get("update_channel", DEFAULT_CHANNEL)
    if channel not in VALID_CHANNELS:
        logger.warning(
            "Invalid channel '%s', falling back to '%s'", channel, DEFAULT_CHANNEL
        )
        return DEFAULT_CHANNEL
    return channel


def set_channel(channel: str) -> None:
    """Write update_channel to data.json.

    Args:
        channel: Only accepts 'stable' or 'beta'.

    Raises:
        ValueError: If channel is not a valid value.
    """
    if channel not in VALID_CHANNELS:
        raise ValueError(
            f"Invalid channel '{channel}'. Must be one of {VALID_CHANNELS}"
        )
    configs = leerConfiguracion()
    configs["update_channel"] = channel
    guardarConfiguracion(configs)
    logger.info("Update channel set to '%s'", channel)


def filter_releases(releases: list[dict], channel: str) -> list[dict]:
    """Filter GitHub releases by channel.

    Stable: only releases whose tag matches v* with no prerelease suffix.
    Beta: all releases including prereleases.

    Args:
        releases: List of GitHub API release objects.
        channel: 'stable' or 'beta'.

    Returns:
        Filtered list of release dicts.
    """
    if channel == "beta":
        return releases

    filtered = []
    for release in releases:
        tag = release.get("tag_name", "")
        if _PRERELEASE_PATTERN.search(tag):
            continue
        if release.get("prerelease", False):
            continue
        filtered.append(release)
    return filtered
