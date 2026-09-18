"""Update orchestrator — wires foundation modules into the update flow."""

import logging
import os
import sys
import tempfile
import threading
from pathlib import Path

import httpx
import wx
from packaging.version import Version

from globals.data_store import config
from globals.paths import BASE_DIR, BOOTSTRAP_EXE
from update import github_client
from update.backup import cleanup_backup, create_backup, restore_backup
from update.bootstrap import launch_bootstrap
from update.channel import get_channel
from update.downloader import download
from update.extractor import extract
from update.release_notes_dialog import show_release_notes_dialog
from update.update import donation
from update.verifier import verify
from update.wxUpdater import progress_callback, update_finished

logger = logging.getLogger(__name__)


def _read_version() -> str:
    """Read version using multiple fallback strategies.

    Strategy 1: VERSION file (works in both development and cx_Freeze builds)
    Strategy 2: importlib.metadata (works for installed packages)
    Strategy 3: pyproject.toml (works in development)
    Strategy 4: Return "0.0.0" (should never happen)
    """
    # Strategy 1: Try VERSION file (most reliable for cx_Freeze builds)
    try:
        version_file = BASE_DIR / "VERSION"
        if version_file.exists():
            # Use utf-8-sig to automatically strip BOM if present
            version = version_file.read_text(encoding="utf-8-sig").strip()
            if version:
                return version
    except Exception as e:
        logger.debug(f"VERSION file read failed: {e}")

    # Strategy 2: Try importlib.metadata (standard for installed packages)
    try:
        from importlib.metadata import version

        return version("vetube")
    except Exception as e:
        logger.debug(f"importlib.metadata failed: {e}")

    # Strategy 3: Try pyproject.toml (development mode)
    try:
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except Exception as e:
        logger.debug(f"pyproject.toml read failed: {e}")

    # Strategy 4: Fallback (should never reach here)
    logger.error("Could not determine version from any source")
    return "0.0.0"


VERSION: str = _read_version()

buscando: bool = False


def do_update(is_manual: bool = False) -> None:
    """Check for updates and install if available.

    Args:
        is_manual: True when triggered by the user (shows errors),
            False for auto-check (silent on failure).
    """
    # Don't allow updates in development mode
    if not getattr(sys, "frozen", False):
        if is_manual:
            wx.CallAfter(
                wx.MessageBox,
                _(
                    "Las actualizaciones no están disponibles al ejecutar desde el código fuente.\n\n"
                    "Usa la versión compilada (.exe) para buscar actualizaciones."
                ),
                _("Modo de desarrollo"),
                wx.ICON_INFORMATION,
            )
        return

    global buscando
    if buscando:
        return
    buscando = True

    def _check_and_notify() -> None:
        global buscando
        try:
            channel = get_channel()
            lookup = github_client.get_latest_release_result(channel)

            if lookup.status == github_client.ReleaseLookupStatus.NO_COMPATIBLE_RELEASE:
                if is_manual:
                    wx.CallAfter(
                        wx.MessageBox,
                        _(
                            "No hay una versión compatible disponible para el canal %s. "
                            "El canal Stable puede no tener "
                            "una versión compatible; el canal Beta también puede incluir "
                            "versiones preliminares."
                        )
                        % channel.capitalize(),
                        _("Información"),
                        wx.ICON_INFORMATION,
                    )
                return

            if lookup.status == github_client.ReleaseLookupStatus.FAILURE:
                if is_manual:
                    wx.CallAfter(
                        wx.MessageBox,
                        _("No se pudo comprobar actualizaciones. Verifica tu conexión."),
                        _("Error"),
                        wx.ICON_ERROR,
                    )
                return

            release = lookup.release
            if release is None:
                raise RuntimeError("Successful release lookup returned no release")

            current = Version(VERSION)
            latest = Version(release.version)

            if latest <= current:
                if is_manual:
                    wx.CallAfter(
                        wx.MessageBox,
                        _("Al parecer tienes la última versión del programa"),
                        _("Información"),
                        wx.ICON_INFORMATION,
                    )
                return

            def _on_user_choice() -> None:
                if show_release_notes_dialog(
                    None, release.version, release.description
                ):
                    threading.Thread(
                        target=_install_update,
                        args=(release,),
                        daemon=True,
                    ).start()

            wx.CallAfter(_on_user_choice)

        except Exception:
            logger.exception("Error during update check")
            if is_manual:
                wx.CallAfter(
                    wx.MessageBox,
                    _("Error al comprobar actualizaciones."),
                    _("Error"),
                    wx.ICON_ERROR,
                )
        finally:
            buscando = False

    threading.Thread(target=_check_and_notify, daemon=True).start()


def _install_update(release: github_client.ReleaseInfo) -> None:
    """Download, verify, backup, extract, and launch bootstrap.

    Args:
        release: ReleaseInfo from github_client.
    """
    base_path = tempfile.mkdtemp()
    zip_path = os.path.join(base_path, release.zip_name)
    extract_path = os.path.join(base_path, "update")
    install_dir = str(BASE_DIR)
    backup_path: str | None = None

    # Check if backup should be created
    create_backup_flag = config.get("create_backup_before_update", True)

    # Quien tiene desactivado el diálogo de donaciones al inicio no lo ve
    # nunca: aprovechamos que ya está actualizando para darle esa oportunidad.
    if not config.get("donations", True):
        wx.CallAfter(donation)

    try:
        logger.info("Starting update to v%s", release.version)

        download(release.zip_url, zip_path, progress_callback=progress_callback)

        checksum_content = _fetch_checksum(release.checksum_url)
        if checksum_content is None:
            raise RuntimeError("Failed to fetch checksum file")

        if not verify(zip_path, checksum_content, release.zip_name):
            raise RuntimeError("SHA256 verification failed")

        # Create backup if enabled
        if create_backup_flag:
            backup_path = create_backup(install_dir, VERSION)
            logger.info("Backup created at %s", backup_path)
        else:
            logger.info("Backup disabled by user configuration")

        extract(zip_path, extract_path)

        exe_path = (
            sys.executable
            if getattr(sys, "frozen", False)
            else str(BASE_DIR / "run_main_window.py")
        )
        bootstrap_exe = str(BOOTSTRAP_EXE)

        exit_code = launch_bootstrap(
            bootstrap_exe=bootstrap_exe,
            pid=os.getpid(),
            source_dir=extract_path,
            dest_dir=install_dir,
            exe_path=exe_path,
        )

        if exit_code == 0:
            if backup_path:
                cleanup_backup(backup_path)
            update_finished()
            logger.info("Update installed successfully")
        else:
            logger.error("Bootstrap exited with code %d, restoring backup", exit_code)
            restore_backup(backup_path, install_dir)

    except Exception:
        logger.exception("Update failed")
        if backup_path and os.path.isdir(backup_path):
            try:
                restore_backup(backup_path, install_dir)
            except Exception:
                logger.exception("Failed to restore backup")


def _fetch_checksum(checksum_url: str) -> str | None:
    """Download the .sha256 checksum file content.

    Args:
        checksum_url: URL to the checksum file.

    Returns:
        Raw text content, or None on failure.
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            response = client.get(checksum_url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError:
        logger.exception("Failed to fetch checksum from '%s'", checksum_url)
        return None
