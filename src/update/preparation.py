"""Download and backup concurrently, joining both before installation."""

import threading
from concurrent.futures import ThreadPoolExecutor


def prepare(download_task, backup_task, waiting_for_backup):
    """A failure waits for the other task before callers clean its files."""
    downloaded = threading.Event()
    if backup_task is None:
        download_task()
        return None
    with ThreadPoolExecutor(
        max_workers=1, thread_name_prefix="update-backup"
    ) as executor:
        backup = executor.submit(backup_task, downloaded)
        try:
            download_task()
        finally:
            downloaded.set()
        if not backup.done():
            waiting_for_backup()
        return backup.result()
