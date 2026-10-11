"""Startup confirmation and deferred cleanup for the native bootstrap."""

import ctypes
import logging
import os
import shutil
import threading
from ctypes import wintypes
from pathlib import Path

logger = logging.getLogger(__name__)
ROLLBACK_SIGNAL = "_rollback_needed"
MANIFEST = "program-files.txt"
CLEANUP = "_update_cleanup.txt"
LEGACY_LEFTOVERS = "_update_leftovers.txt"
_PROTECTED = {
    "data.json",
    "keymaps",
    "sounds",
    "voices",
    "engines",
    "logs",
    "favoritos.json",
    "mensajes_destacados.json",
    "keys.txt",
    "_update_transaction",
    "_rollback_needed",
}


def signal_ready():
    """Signal once, closing the event handle even when SetEvent fails."""
    name = os.environ.pop("VETUBE_UPDATE_READY", None)
    if not name:
        return False
    if os.name != "nt" or not name.startswith("Local\\VeTubeReady-"):
        return False
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.OpenEventW.restype = wintypes.HANDLE
    kernel.SetEvent.argtypes = [wintypes.HANDLE]
    kernel.SetEvent.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenEventW(0x0002, False, name)  # EVENT_MODIFY_STATE
    if not handle:
        logger.warning(
            "No se pudo abrir el evento de actualización: %s", ctypes.get_last_error()
        )
        return False
    try:
        if not kernel.SetEvent(handle):
            logger.warning(
                "No se pudo confirmar el arranque: %s", ctypes.get_last_error()
            )
            return False
        return True
    finally:
        kernel.CloseHandle(handle)


def _safe_relative(root, name):
    path = Path(name.replace("\\", "/"))
    if (
        not name
        or not path.parts
        or path.is_absolute()
        or ":" in name
        or any(part in {"..", "."} for part in path.parts)
        or path.parts[0].lower() in _PROTECTED
    ):
        raise ValueError("Ruta de limpieza inválida")
    target = root / path
    # resolve detects symlinks/junctions leading outside the installation.
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Ruta fuera de la instalación")
    for candidate in [target, *target.parents]:
        if candidate == root:
            break
        if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
            raise ValueError("Ruta enlazada")
    return target


def cleanup_obsolete(root):
    """Remove only explicitly scheduled program files; retain failed entries."""
    root = Path(root)
    manifest = root / MANIFEST
    try:
        current = {
            line.replace("\\", "/").casefold()
            for line in manifest.read_text(encoding="utf-8").splitlines()
        }
    except OSError:
        return  # an old installation has no authority to delete unknown files
    pending = root / CLEANUP
    if pending.is_symlink() or getattr(pending, "is_junction", lambda: False)():
        return
    try:
        names = pending.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    remaining = []
    for name in names:
        try:
            target = _safe_relative(root, name)
            if name.replace("\\", "/").casefold() in current:
                continue
            if target.is_file():
                target.unlink()
        except ValueError:
            logger.warning("Se ignora una ruta de limpieza inválida: %r", name)
        except OSError:
            remaining.append(name)
    try:
        if remaining:
            temporary = pending.with_suffix(".tmp")
            temporary.write_text("\n".join(remaining), encoding="utf-8")
            temporary.replace(pending)
        else:
            pending.unlink()
    except OSError:
        logger.debug("La limpieza se reintentará en el próximo arranque", exc_info=True)


def cleanup_leftovers(root):
    """Bridge cleanup: only .old paths recorded by the previous installer."""
    root = Path(root)
    pending = root / LEGACY_LEFTOVERS
    if pending.is_symlink():
        return
    try:
        names = pending.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    remaining = []
    for name in names:
        try:
            path = Path(name)
            relative = path.relative_to(root) if path.is_absolute() else path
            target = _safe_relative(root, str(relative))
            if not name.endswith(".old"):
                continue
            target.unlink(missing_ok=True)
        except ValueError:
            continue
        except OSError:
            remaining.append(name)
    try:
        if remaining:
            pending.write_text("\n".join(remaining), encoding="utf-8")
        else:
            pending.unlink()
    except OSError:
        logger.debug("Quedan restos de la actualización anterior", exc_info=True)


def startup_ready(root):
    """Called by the GUI event loop after essential initialization succeeds."""
    root = Path(root)
    supervised = "VETUBE_UPDATE_READY" in os.environ
    confirmed = signal_ready()
    # Never delete potential rollback material before readiness is accepted.
    if supervised and not confirmed:
        return

    def clean():
        # On later startups only, retry deletion of an already settled journal.
        # Pending journals are rollback material and must remain untouched.
        if not supervised:
            try:
                transaction = root / "_update_transaction"
                settled = transaction / "settled"
                safe = (
                    not transaction.is_symlink()
                    and not getattr(transaction, "is_junction", lambda: False)()
                    and settled.is_file()
                    and not settled.is_symlink()
                )
                if safe:
                    shutil.rmtree(transaction)
            except OSError:
                logger.debug(
                    "La limpieza de la transacción se reintentará", exc_info=True
                )
        cleanup_obsolete(root)
        cleanup_leftovers(root)

    threading.Thread(target=clean, name="update-cleanup", daemon=True).start()
