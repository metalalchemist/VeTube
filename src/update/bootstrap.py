"""Bootstrap process launcher with UAC elevation for file replacement."""

import logging
import subprocess
import time

logger = logging.getLogger(__name__)

_EXIT_SUCCESS = 0
_EXIT_FAILURE = 1
_EXIT_CANCELLED = 2
_EXIT_TIMEOUT = -1
_WAIT_TIMEOUT_SECONDS = 30


def _build_args(pid: int, source_dir: str, dest_dir: str, exe_path: str) -> str:
    """Build the command-line argument string for bootstrap.exe."""
    return f'"{pid}" "{source_dir}" "{dest_dir}" "{exe_path}"'


def _is_process_running(name: str) -> bool:
    """Check if a process with the given name is currently running."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return name.lower() in result.stdout.lower()
    except (subprocess.SubprocessError, OSError):
        logger.debug("Failed to check process '%s'", name, exc_info=True)
        return False


def launch_bootstrap(
    bootstrap_exe: str,
    pid: int,
    source_dir: str,
    dest_dir: str,
    exe_path: str,
) -> int:
    """Launch bootstrap.exe to replace files and relaunch the app.

    Requests UAC elevation via ShellExecute with 'runas' verb, then waits
    for the process to complete.

    Args:
        bootstrap_exe: Path to bootstrap.exe.
        pid: PID of the current application process to terminate.
        source_dir: Directory containing the new version files.
        dest_dir: Target installation directory.
        exe_path: Path to the application executable to relaunch.

    Returns:
        Exit code: 0=success, 1=failure, 2=cancelled by user, -1=timeout.
    """
    import win32api
    import win32con

    args = _build_args(pid, source_dir, dest_dir, exe_path)
    logger.info("Launching bootstrap: '%s' %s", bootstrap_exe, args)

    try:
        result = win32api.ShellExecute(
            0,
            "runas",
            bootstrap_exe,
            args,
            None,
            win32con.SW_SHOW,
        )
    except Exception:
        logger.exception("Failed to launch bootstrap (UAC may have been denied)")
        return _EXIT_CANCELLED

    if isinstance(result, int) and result <= 32:
        logger.error("ShellExecute failed with code: %s", result)
        return _EXIT_FAILURE

    logger.info(
        "Bootstrap launched, waiting for completion (timeout=%ds)",
        _WAIT_TIMEOUT_SECONDS,
    )

    deadline = time.monotonic() + _WAIT_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if not (
            _is_process_running("bootstrap.exe")
            or _is_process_running("bootstrap.next.exe")
        ):
            logger.info("Bootstrap process completed")
            return _EXIT_SUCCESS
        time.sleep(0.5)

    logger.error("Bootstrap did not complete within %d seconds", _WAIT_TIMEOUT_SECONDS)
    return _EXIT_TIMEOUT
