# The bootstrap must report failures and keep running on partially initialized
# Windows environments, so its broad exception handling is intentional.
# ruff: noqa: BLE001, S110

import ctypes
import logging
import os
import shutil
import subprocess
import sys
import time
import traceback

logger = logging.getLogger(__name__)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_CANCELLED = 2

LOG_FILE = os.path.join(
    os.environ.get("TEMP", os.path.expanduser("~")), "vetube_bootstrap_debug.txt"
)
ROLLBACK_SIGNAL = "_rollback_needed"
APP_EXECUTABLE = "VeTube.exe"
BOOTSTRAP_NAME = "bootstrap.exe"
STAGED_BOOTSTRAP_NAME = "bootstrap.next.exe"
FINALIZE_MODE = "--finalize"


def _copy_file(source_path: str, dest_path: str) -> None:
    """Copy a file, retaining an existing locked runtime DLL for finalization."""
    try:
        shutil.copy2(source_path, dest_path)
    except PermissionError:
        if not dest_path.lower().endswith(".dll") or not os.path.exists(dest_path):
            raise
        log(f"Keeping locked runtime dependency: {dest_path}")


def _copy_tree(source_path: str, dest_path: str) -> None:
    """Copy a directory while applying the locked-DLL policy recursively."""
    for root, dirs, files in os.walk(source_path):
        dirs.sort()
        files.sort()
        relative_root = os.path.relpath(root, source_path)
        destination_root = (
            dest_path if relative_root == "." else os.path.join(dest_path, relative_root)
        )
        os.makedirs(destination_root, exist_ok=True)
        for filename in files:
            _copy_file(
                os.path.join(root, filename), os.path.join(destination_root, filename)
            )


def _copy_update_files(source: str, dest: str) -> None:
    """Copy update files while preserving user-owned installation data."""
    if not os.path.isdir(source):
        raise FileNotFoundError(f"Update source directory does not exist: {source}")

    os.makedirs(dest, exist_ok=True)

    for name in sorted(os.listdir(source)):
        source_path = os.path.join(source, name)
        dest_path = os.path.join(dest, name)

        # The running bootstrap cannot replace itself on Windows.  The new
        # bootstrap is staged separately by _stage_bootstrap().
        if name in {"data.json", "keymaps", BOOTSTRAP_NAME, STAGED_BOOTSTRAP_NAME}:
            continue

        # locales/ son archivos del programa: se copian SIEMPRE (decisión de
        # César, 22-08), si no los usuarios existentes se quedan con catálogos
        # viejos y ven en español toda cadena nueva.  sounds/ sí se preserva:
        # ahí viven los packs personalizados del usuario.
        if name == "sounds":
            if not os.path.isdir(source_path):
                continue
            for root, dirs, files in os.walk(source_path):
                dirs.sort()
                files.sort()
                relative_root = os.path.relpath(root, source_path)
                destination_root = (
                    dest_path
                    if relative_root == "."
                    else os.path.join(dest_path, relative_root)
                )
                os.makedirs(destination_root, exist_ok=True)
                for filename in files:
                    destination_file = os.path.join(destination_root, filename)
                    if not os.path.exists(destination_file):
                        _copy_file(os.path.join(root, filename), destination_file)
            continue

        if os.path.isdir(source_path):
            _copy_tree(source_path, dest_path)
        else:
            _copy_file(source_path, dest_path)


def _stage_bootstrap(source: str, dest: str) -> str:
    """Stage the incoming bootstrap without touching the active executable."""
    source_path = os.path.join(source, BOOTSTRAP_NAME)
    staged_path = os.path.join(dest, STAGED_BOOTSTRAP_NAME)
    temporary_path = staged_path + ".tmp"

    if not os.path.isfile(source_path):
        raise FileNotFoundError(f"Incoming bootstrap does not exist: {source_path}")

    try:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
        shutil.copy2(source_path, temporary_path)
        os.replace(temporary_path, staged_path)
        if not os.path.isfile(staged_path):
            raise OSError(f"Bootstrap staging did not create: {staged_path}")
    except Exception:
        try:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass
        raise

    log(f"Incoming bootstrap staged at: {staged_path}")
    return staged_path


def log(msg: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def kill_process(pid: int) -> None:
    log(f"Intentando matar proceso PID: {pid}")
    try:
        PROCESS_TERMINATE = 1
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if handle:
            ctypes.windll.kernel32.TerminateProcess(handle, -1)
            ctypes.windll.kernel32.CloseHandle(handle)
            log("Proceso terminado exitosamente.")
        else:
            log("No se pudo obtener handle del proceso (¿ya estaba cerrado?).")
    except Exception as e:
        log(f"Error matando proceso: {e}")


def _wait_for_process_exit(pid: int, timeout: float = 30.0) -> bool:
    """Wait for a process to exit, using the Windows API when available."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x100000, False, pid)
            if not handle:
                return True
            try:
                # OpenProcess also succeeds on a TERMINATED process while any
                # other handle to it survives (an antivirus is enough), which
                # used to read as "still running" until the timeout and end in
                # a needless rollback.  Ask for the real termination signal.
                if ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == 0:
                    return True
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            # A missing process is the desired state; continue briefly when
            # the platform/API is unavailable so tests and non-Windows runs
            # remain deterministic.
            try:
                os.kill(pid, 0)
            except OSError:
                return True
        time.sleep(0.1)
    return False


def _resolve_app_executable(dest: str, exe_path: str) -> str:
    """Prefer the packaged app executable over an outdated requested one.

    Las 3.94 y anteriores (PyInstaller) piden relanzar run_main_window.exe, que
    sigue existiendo en el disco porque la actualización nunca borra nada:
    relanzarlo devolvería al usuario a la versión VIEJA con la actualización ya
    copiada al lado.  Si el paquete nuevo trae su ejecutable canónico
    (VeTube.exe) en el destino, ese es el que hay que relanzar.
    """
    if os.path.basename(os.path.normpath(exe_path)).lower() == APP_EXECUTABLE.lower():
        return exe_path
    candidate = os.path.join(dest, APP_EXECUTABLE)
    if os.path.isfile(candidate):
        log(f"Exe pedido obsoleto ({exe_path}); relanzando la app nueva: {candidate}")
        return candidate
    return exe_path


def _launch_executable(exe_path: str) -> bool:
    """Launch an executable detached from the bootstrap process."""
    if not os.path.isfile(exe_path):
        return False
    working_dir = os.path.dirname(os.path.abspath(exe_path))
    try:
        subprocess.Popen(
            [exe_path],
            creationflags=subprocess.DETACHED_PROCESS,
            cwd=working_dir,
            close_fds=False,
            shell=False,
        )
        return True
    except Exception as first_error:
        log(f"Fallo intento 1: {first_error}")
        try:
            subprocess.Popen(f'"{exe_path}"', shell=True, cwd=working_dir)
            return True
        except Exception as second_error:
            log(f"Fallo intento 2: {second_error}")
            return False


def _finalize_bootstrap(pid: int, dest: str, exe_path: str, active_path: str, staged_path: str) -> int:
    """Replace the old bootstrap after phase one has exited, then relaunch."""
    backup_path = active_path + ".previous"
    try:
        if not _wait_for_process_exit(pid):
            raise TimeoutError(f"Phase-one bootstrap did not exit: {pid}")
        if not os.path.isfile(staged_path):
            raise FileNotFoundError(f"Staged bootstrap does not exist: {staged_path}")

        had_active = os.path.exists(active_path)
        if had_active:
            os.replace(active_path, backup_path)
        try:
            os.replace(staged_path, active_path)
        except Exception:
            if had_active and os.path.exists(backup_path):
                os.replace(backup_path, active_path)
            raise

        exe_path = _resolve_app_executable(dest, exe_path)
        if not _launch_executable(exe_path):
            raise OSError(f"Failed to relaunch application: {exe_path}")

        if os.path.exists(backup_path):
            os.remove(backup_path)
        return EXIT_SUCCESS
    except Exception as error:
        log(f"Bootstrap finalization failed: {error}")
        try:
            if os.path.exists(backup_path):
                if os.path.exists(active_path):
                    os.remove(active_path)
                os.replace(backup_path, active_path)
        except OSError as restore_error:
            log(f"Failed to restore old bootstrap: {restore_error}")
        try:
            if os.path.exists(staged_path):
                os.remove(staged_path)
        except OSError:
            pass
        _write_rollback_signal(dest)
        return EXIT_FAILURE


def _write_rollback_signal(dest: str) -> None:
    signal_path = os.path.join(dest, ROLLBACK_SIGNAL)
    try:
        with open(signal_path, "w") as f:
            f.write(str(int(time.time())))
        log(f"Rollback signal written: {signal_path}")
    except Exception as e:
        log(f"Failed to write rollback signal: {e}")


def main() -> None:
    log("=== INICIO BOOTSTRAP ===")
    log(f"Argumentos recibidos: {sys.argv}")

    if len(sys.argv) >= 2 and sys.argv[1] == FINALIZE_MODE:
        if len(sys.argv) != 7:
            log("ERROR: Argumentos de finalización inválidos.")
            sys.exit(EXIT_FAILURE)
        try:
            result = _finalize_bootstrap(
                int(sys.argv[2]),
                sys.argv[3],
                sys.argv[4],
                sys.argv[5],
                sys.argv[6],
            )
        except Exception:
            log(traceback.format_exc())
            result = EXIT_FAILURE
        log(f"=== FIN BOOTSTRAP FINALIZER (exit={result}) ===")
        sys.exit(result)

    if len(sys.argv) < 5:
        log("ERROR: No hay suficientes argumentos.")
        sys.exit(EXIT_FAILURE)

    exit_code = EXIT_FAILURE

    try:
        pid = int(sys.argv[1])
        source = sys.argv[2]
        dest = sys.argv[3]
        exe_path = sys.argv[4]

        log(f"Config inicial -> Source: {source} | Dest: {dest} | Exe: {exe_path}")

        if os.path.basename(os.path.normpath(dest)) == "_internal":
            log("Detectado destino '_internal'. Corrigiendo a directorio padre.")
            dest = os.path.dirname(os.path.normpath(dest))
            log(f"Nuevo Destino: {dest}")

        time.sleep(1)
        kill_process(pid)
        time.sleep(2)

        if os.path.isdir(source):
            log("Iniciando copia de archivos...")
            try:
                _copy_update_files(source, dest)
                log("Copia finalizada correctamente.")
            except PermissionError as e:
                log(f"ERROR copiando archivos (permiso deniado): {e}")
                log(traceback.format_exc())
                _write_rollback_signal(dest)
                sys.exit(EXIT_CANCELLED)
            except Exception as e:
                log(f"ERROR copiando archivos: {e}")
                log(traceback.format_exc())
                _write_rollback_signal(dest)
                sys.exit(EXIT_FAILURE)
        else:
            log("ERROR: La carpeta source o dest no existen.")
            sys.exit(EXIT_FAILURE)

        incoming_bootstrap = os.path.join(source, BOOTSTRAP_NAME)
        if os.path.isfile(incoming_bootstrap):
            try:
                staged_path = _stage_bootstrap(source, dest)
                active_path = os.path.join(dest, BOOTSTRAP_NAME)
                subprocess.Popen(
                    [
                        staged_path,
                        FINALIZE_MODE,
                        str(os.getpid()),
                        dest,
                        exe_path,
                        active_path,
                        staged_path,
                    ],
                    creationflags=subprocess.DETACHED_PROCESS,
                    cwd=dest,
                    close_fds=False,
                    shell=False,
                )
                log("Finalizer launched successfully.")
                exit_code = EXIT_SUCCESS
                return
            except Exception as e:
                log(f"ERROR preparando finalización de bootstrap: {e}")
                log(traceback.format_exc())
                _write_rollback_signal(dest)
                try:
                    if os.path.exists(os.path.join(dest, STAGED_BOOTSTRAP_NAME)):
                        os.remove(os.path.join(dest, STAGED_BOOTSTRAP_NAME))
                except OSError:
                    pass
                sys.exit(EXIT_FAILURE)

        log("Incoming bootstrap absent; using legacy relaunch path.")
        log("Intentando relanzar aplicación...")

        exe_path = os.path.normpath(exe_path)
        log(f"Ruta exe original: {exe_path}")
        exe_path = _resolve_app_executable(dest, exe_path)

        final_exe_path = exe_path
        if not os.path.exists(final_exe_path):
            log("El exe no existe en la ruta original. Buscando alternativas...")
            candidate = os.path.join(dest, os.path.basename(exe_path))
            if os.path.exists(candidate):
                final_exe_path = candidate
                log(f"Encontrado en raíz destino: {final_exe_path}")
            else:
                clean_path = exe_path.replace("_internal\\", "").replace(
                    "_internal/", ""
                )
                if os.path.exists(clean_path):
                    final_exe_path = clean_path
                    log(f"Encontrado limpiando ruta: {final_exe_path}")

        if os.path.exists(final_exe_path):
            working_dir = os.path.dirname(os.path.abspath(final_exe_path))
            log(f"Lanzando: {final_exe_path}")
            log(f"Directorio de trabajo (CWD): {working_dir}")

            os.chdir(working_dir)

            try:
                if not _launch_executable(final_exe_path):
                    raise OSError("application launch failed")
                log("subprocess.Popen llamado con éxito (DETACHED).")
                exit_code = EXIT_SUCCESS
            except Exception as e:
                log(f"Fallo intento 1: {e}")
                exit_code = EXIT_FAILURE
        else:
            log(
                f"ERROR CRÍTICO: No se encontró el ejecutable en ninguna ruta probada. Última intentada: {final_exe_path}"
            )
            exit_code = EXIT_FAILURE

    except Exception as e:
        log(f"ERROR GLOBAL NO CONTROLADO: {e}")
        log(traceback.format_exc())
        exit_code = EXIT_FAILURE

    log(f"=== FIN BOOTSTRAP (exit={exit_code}) ===")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
