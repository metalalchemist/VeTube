"""Legacy update module — simplified for backward compatibility.

The main update flow is now in updater.py. This module keeps async_check_update()
and perform_update() for backward compatibility with existing callers.
"""

import json
import logging
import os
import tempfile

import wx
from packaging.version import Version

from globals.paths import DATA_FILE
from update import github_client
from update.channel import get_channel
from update.downloader import download
from update.extractor import extract

logger = logging.getLogger(__name__)


async def async_check_update(
    endpoint: str = "", current_version: str = ""
) -> dict | Exception | None:
    """Check for updates using GitHub Releases API.

    Args:
        endpoint: Ignored (kept for backward compatibility).
        current_version: Ignored (reads from updater.VERSION).

    Returns:
        Dict with update info, None if no update, or Exception on error.
    """
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE) as file:
                resultado = json.load(file)
            donations = resultado.get("donations", True)
        else:
            donations = True

        channel = get_channel()
        release = github_client.get_latest_release(channel)

        if release is None:
            logger.debug("No release found for channel '%s'", channel)
            return None

        from update.updater import VERSION

        current = Version(VERSION)
        latest = Version(release.version)

        if latest <= current:
            logger.debug(
                "No update available (current=%s, latest=%s)", VERSION, release.version
            )
            return None

        return {
            "update_url": release.zip_url,
            "available_version": release.version,
            "available_description": release.description,
            "donations": donations,
        }

    except Exception as e:
        logger.exception("Error checking for updates")
        return e


def perform_update(
    update_url: str,
    donations: bool = True,
    password: str | None = None,
    progress_callback=None,
    update_complete_callback=None,
) -> None:
    """Download and extract update (simplified flow without verification/backup).

    Args:
        update_url: URL to download the update from.
        donations: Whether to show donation dialog.
        password: Password for zip extraction (unused, kept for compatibility).
        progress_callback: Called with (bytes_downloaded, total_bytes).
        update_complete_callback: Called when extraction is complete.
    """
    try:
        base_path = tempfile.mkdtemp()
        download_path = os.path.join(base_path, "update.zip")
        update_path = os.path.join(base_path, "update")

        logger.info("Starting simplified update from %s", update_url)

        if not donations:
            wx.CallAfter(donation)

        download(update_url, download_path, progress_callback=progress_callback)
        extract(download_path, update_path)

        if callable(update_complete_callback):
            update_complete_callback()

        logger.info("Simplified update complete")

    except Exception:
        logger.exception("Failed to download or extract update")


def donation() -> None:
    """Show donation dialog."""
    dlg = wx.MessageDialog(
        None,
        _(
            "Con tu apoyo contribuyes a que este programa siga siendo gratuito. ¿Te unes a nuestra causa?"
        ),
        _("Atención:"),
        wx.YES_NO | wx.ICON_ASTERISK,
    )
    dlg.SetYesNoLabels(_("&Aceptar"), _("&Cancelar"))
    if dlg.ShowModal() == wx.ID_YES:
        wx.LaunchDefaultBrowser(
            "https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U"
        )
