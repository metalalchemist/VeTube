"""Launch the native installer with UAC and track its actual process handle."""

import logging
import subprocess

logger = logging.getLogger(__name__)
_WAIT_TIMEOUT_SECONDS = 30


def _build_args(pid, source_dir, dest_dir, exe_path, backup_dir=None):
    args = [str(pid), str(source_dir), str(dest_dir), str(exe_path)]
    if backup_dir:
        args.append(str(backup_dir))
    return subprocess.list2cmdline(args)


def launch_bootstrap(
    bootstrap_exe, pid, source_dir, dest_dir, exe_path, backup_dir=None
):
    """Return 0=completed, 1=failed, 2=UAC cancelled, -1=still running.

    Normally the installer terminates this process before this call returns.
    Only Rust can confirm the replacement application's startup.
    """
    import win32event
    import win32process
    from win32com.shell import shell

    args = _build_args(pid, source_dir, dest_dir, exe_path, backup_dir)
    try:
        result = shell.ShellExecuteEx(
            fMask=0x40,
            lpVerb="runas",
            lpFile=str(bootstrap_exe),
            lpParameters=args,
            nShow=0,  # SEE_MASK_NOCLOSEPROCESS; hidden helper
        )
    except Exception as error:
        logger.exception("Could not launch native installer")
        return 2 if getattr(error, "winerror", None) == 1223 else 1
    process = result.get("hProcess")
    if process is None:
        return 1
    try:
        result = win32event.WaitForSingleObject(process, _WAIT_TIMEOUT_SECONDS * 1000)
        if result == win32event.WAIT_TIMEOUT:
            return -1
        if result != win32event.WAIT_OBJECT_0:
            return 1
        code = win32process.GetExitCodeProcess(process)
        return 0 if code == 0 else 1
    finally:
        process.Close()
