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
from update.backup import (
    InsufficientSpaceError,
    backup_dir_for,
    cleanup_backup,
    create_backup,
)
from update.bootstrap import launch_bootstrap
from update.channel import get_channel
from update.downloader import download
from update.extractor import extract
from update.release_notes_dialog import show_release_notes_dialog
from update.update import donation
from update.verifier import verify
from update.wxUpdater import (
    aviso_descargada,
    backup_progress_callback,
    dentro_de_update,
    iniciar_descarga,
    mostrar_ventanas,
    progress_callback,
    rollback_notification,
)

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
                    # Quien tiene desactivado el diálogo de donaciones al
                    # inicio no lo ve nunca: aprovechamos que va a actualizar.
                    # Aquí, en el hilo de la interfaz y ANTES de empezar: si
                    # se lanzara con CallAfter durante la descarga, se abriría
                    # con la ventana principal ya escondida (su dueña) y
                    # desaparecería sin respuesta.
                    if not config.get("donations", True):
                        donation()
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


def _en_interfaz(funcion, esperar: bool = False) -> None:
    """Ejecuta ``funcion`` en el hilo de la interfaz desde el hilo de descarga.

    Con ``esperar`` el hilo de descarga se queda parado hasta que la función
    termina (un diálogo modal, por ejemplo).

    Nunca se ejecuta dentro de un ProgressDialog.Update() en curso (que
    procesa los CallAfter pendientes antes de volver): si toca ahí, se vuelve
    a intentar con un temporizador, que ese bucle no atiende. Véase
    wxUpdater._actualizar_barra.
    """
    listo = threading.Event()

    def _correr() -> None:
        if dentro_de_update():
            wx.CallLater(50, _correr)
            return
        try:
            funcion()
        finally:
            listo.set()

    wx.CallAfter(_correr)
    if esperar:
        listo.wait()


def _avisar_fallo(motivo: str) -> None:
    """Devuelve las ventanas y, ya con ellas delante, avisa del fallo (en ese orden)."""
    _en_interfaz(mostrar_ventanas)
    _en_interfaz(lambda: rollback_notification(motivo))


def _motivo(error: Exception) -> str:
    """El motivo de un fallo, traducido cuando el usuario puede hacer algo con él."""
    if isinstance(error, InsufficientSpaceError):
        return _(
            "no hay espacio suficiente en el disco: hacen falta %d MB libres "
            "para la copia de seguridad"
        ) % getattr(error, "required_mb", 0)
    return str(error)


def _anunciar(texto: str) -> None:
    """Dice en voz alta el cambio de fase (descarga, copia de seguridad, extracción).

    El lector de pantalla no lee los cambios de texto de la barra de progreso:
    solo oye el porcentaje, que cae de 99 a 0 al cambiar de fase, y nada
    durante la extracción. Sale por leer_interfaz, como el resto de la
    interfaz (con «Usar voz sapi» marcada, el lector de pantalla): actualizar
    es cosa del programa, no del chat, y con la barra quieta no hay foco
    siguiente que corte la frase. Import perezoso: setup arranca los motores.
    """
    try:
        from setup import reader

        reader.leer_interfaz(texto)
    except Exception:
        logger.debug("No se pudo anunciar «%s»", texto, exc_info=True)


def _bootstrap_del_paquete(extract_path: str) -> str:
    """El bootstrap que instala la actualización: el del paquete descargado.

    El bootstrap de la instalación se traba a sí mismo: mientras corre tiene
    abiertos python3.dll, python314.dll y varios .pyd de lib/ (_bz2, _ctypes,
    _lzma, _zstd), y solo los .dll bloqueados se toleran, así que la copia
    reventaba en lib/_bz2.pyd con VERSION ya sobrescrito (reproducido con el
    bootstrap.exe de la 3.96 sobre el zip de la 3.97-rc1). El bootstrap del
    paquete corre con su propia lib/ desde la carpeta temporal: en la carpeta
    de destino no queda nada abierto una vez cerrado VeTube. Si el paquete no
    trae bootstrap, se usa el instalado.
    """
    candidato = os.path.join(extract_path, BOOTSTRAP_EXE.name)
    if os.path.isfile(candidato):
        return candidato
    logger.warning("El paquete no trae %s; se usa el instalado", BOOTSTRAP_EXE.name)
    return str(BOOTSTRAP_EXE)


def _install_update(release: github_client.ReleaseInfo) -> None:
    """Download, verify, backup, extract, notify, and launch bootstrap.

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

    try:
        logger.info("Starting update to v%s", release.version)

        # Solo queda a la vista la barra de progreso; las ventanas vuelven si
        # la actualización falla (si sale bien, el bootstrap cierra VeTube).
        _en_interfaz(iniciar_descarga)
        _anunciar(_("Descargando la actualización"))
        download(release.zip_url, zip_path, progress_callback=progress_callback)

        checksum_content = _fetch_checksum(release.checksum_url)
        if checksum_content is None:
            raise RuntimeError("Failed to fetch checksum file")

        if not verify(zip_path, checksum_content, release.zip_name):
            raise RuntimeError(
                _("el archivo descargado no supera la comprobación de integridad")
            )

        # Create backup if enabled
        if create_backup_flag:
            _anunciar(_("Creando la copia de seguridad..."))
            backup_path = create_backup(
                install_dir, VERSION, progress_callback=backup_progress_callback
            )
            logger.info("Backup created at %s", backup_path)
        else:
            logger.info("Backup disabled by user configuration")

        _anunciar(_("Extrayendo la actualización..."))
        extract(zip_path, extract_path)

        # Todo descargado y extraído: el usuario decide cuándo se instala.
        _en_interfaz(aviso_descargada, esperar=True)

        exe_path = (
            sys.executable
            if getattr(sys, "frozen", False)
            else str(BASE_DIR / "run_main_window.py")
        )

        # Hasta aquí no se ha tocado nada de la instalación: si el bootstrap
        # falla a medias, es ÉL quien vuelve a la copia de seguridad (VeTube ya
        # está cerrado); si la copia sale bien, él borra la copia de seguridad.
        exit_code = launch_bootstrap(
            bootstrap_exe=_bootstrap_del_paquete(extract_path),
            pid=os.getpid(),
            source_dir=extract_path,
            dest_dir=install_dir,
            exe_path=exe_path,
            backup_dir=backup_path,
        )

        if exit_code == 0:
            # En Windows no se llega aquí: el bootstrap cierra VeTube en
            # cuanto arranca. Si aun así seguimos vivos (modo de desarrollo,
            # pruebas, un bootstrap que murió antes de matarnos), la interfaz
            # tiene que volver: si no, el programa queda invisible.
            if backup_path:
                cleanup_backup(backup_path)
            logger.info("Update installed successfully")
            _en_interfaz(mostrar_ventanas)
        elif exit_code == 2:
            # UAC rechazado: el bootstrap no llegó a correr, nada que deshacer.
            # Se dice: quien acaba de oír «VeTube se cerrará» y ve volver la
            # ventana sin una palabra no sabe si se instaló o no.
            logger.warning("Bootstrap cancelled by the user; nothing was installed")
            if backup_path:
                cleanup_backup(backup_path)
            _avisar_fallo(_("Windows no dio permiso para instalar"))
        elif exit_code == 1:
            logger.error("Bootstrap could not start")
            if backup_path:
                cleanup_backup(backup_path)
            _avisar_fallo(_("el instalador no pudo arrancar (código %d)") % exit_code)
        else:
            # -1: sigue corriendo tras 30 s (VeTube debería estar cerrado ya).
            # Se le deja la copia de seguridad, puede estar copiando todavía,
            # y no se promete nada: no sabemos cómo acabará.
            logger.error("Bootstrap still running after the timeout")
            _avisar_fallo(_("el instalador sigue en marcha tras 30 segundos"))

    except Exception as error:
        # Todo lo que puede fallar aquí (descarga, verificación, copia de
        # seguridad, extracción) pasa ANTES de tocar la instalación: no hay
        # nada que restaurar, y restaurar con VeTube abierto borraría archivos
        # de una instalación que sigue en uso.
        logger.exception("Update failed")
        # backup_path sigue en None si create_backup falló a medias: la
        # carpeta a medio copiar se borra igual.
        if create_backup_flag:
            cleanup_backup(backup_path or backup_dir_for(install_dir, VERSION))
        _avisar_fallo(_motivo(error))


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
