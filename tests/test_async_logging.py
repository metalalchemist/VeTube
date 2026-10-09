"""Exercise logging in subprocesses to isolate root handlers and exit hooks."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class AsyncLoggingTest(unittest.TestCase):
    def run_script(self, script):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=directory,
                env={
                    **os.environ,
                    "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
                },
                capture_output=True,
                text=True,
                timeout=15,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Exception ignored in atexit callback", result.stderr)
        return result

    def test_slow_output_does_not_block_and_close_drains_queue(self):
        self.run_script('''
import logging
import threading
from utils import logging_setup as logs
logs.configurar_logs()
entered = threading.Event()
release = threading.Event()
produced = threading.Event()
handler = logs._escucha.handlers[-1]
def slow_emit(record):
    entered.set()
    release.wait(5)
handler.emit = slow_emit
logger = logging.getLogger("vetube.test")
logger.info("first")
worker = None
try:
    assert entered.wait(2), "listener did not receive message"
    def produce():
        logger.info("second")
        produced.set()
    worker = threading.Thread(target=produce)
    worker.start()
    assert produced.wait(2), "logging waited for output"
finally:
    release.set()
    logs.cerrar_logs()
    if worker is not None:
        worker.join()
with open("logs/vetube.log", encoding="utf-8") as stream:
    assert "second" in stream.read(), "close lost queued message"
logs.cerrar_logs()
''')

    def test_exit_drains_queue_preserving_levels_and_traceback(self):
        self.run_script('''
import atexit
import logging
from utils import logging_setup as logs
def verify():
    with open("logs/vetube.log", encoding="utf-8") as stream:
        content = stream.read()
    assert "debug-message" in content
    assert "noisy-debug" not in content
    assert "ValueError: example" in content
    assert content.count("last-message") == 1
atexit.register(verify)
logs.configurar_logs()
listener = logs._escucha
logs.configurar_logs()
assert logs._escucha is listener
logger = logging.getLogger("vetube.test")
logger.debug("debug-message")
logging.getLogger("httpx").debug("noisy-debug")
try:
    raise ValueError("example")
except ValueError:
    logger.exception("failure")
logger.info("last-message")
''')

    def test_file_failure_does_not_prevent_startup(self):
        self.run_script('''
import logging
import sys
from unittest.mock import patch
from utils import logging_setup as logs
sys.frozen = True
with patch.object(logs.os, "makedirs", side_effect=PermissionError):
    logs.configurar_logs()
logging.getLogger("vetube").info("still running")
logs.cerrar_logs()
''')


if __name__ == "__main__":
    unittest.main()
