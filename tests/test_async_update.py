"""Native-update lifecycle tests that do not import wx or voice engines."""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tools.package_native import package
from update import backup, lifecycle
from update.preparation import prepare

ROOT = Path(__file__).resolve().parents[1]


class PreparationTests(unittest.TestCase):
    def test_download_overlaps_backup_and_waits_for_completion(self):
        started = threading.Event()
        release = threading.Event()
        finished = threading.Event()

        def make_backup(downloaded):
            started.set()
            self.assertTrue(release.wait(3))
            self.assertTrue(downloaded.is_set())
            finished.set()
            return "backup"

        def download():
            self.assertTrue(started.wait(3), "backup did not overlap download")

        def waiting():
            self.assertFalse(finished.is_set())
            release.set()

        self.assertEqual(prepare(download, make_backup, waiting), "backup")
        self.assertTrue(finished.is_set())

    def test_failed_download_joins_backup_before_cleanup(self):
        finished = threading.Event()

        def make_backup(downloaded):
            self.assertTrue(downloaded.wait(3))
            finished.set()

        with self.assertRaisesRegex(OSError, "download failed"):
            prepare(
                lambda: (_ for _ in ()).throw(OSError("download failed")),
                make_backup,
                lambda: None,
            )
        self.assertTrue(finished.is_set())

    def test_failed_backup_prevents_installation(self):
        with self.assertRaisesRegex(OSError, "backup failed"):
            prepare(
                lambda: None,
                lambda _: (_ for _ in ()).throw(OSError("backup failed")),
                lambda: None,
            )

    def test_backup_excludes_mutable_data_and_never_reuses_an_old_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "install"
            install.mkdir()
            (install / "VERSION").write_text("old")
            for name in ["logs", "voices", "engines", "sounds", "keymaps"]:
                (install / name).mkdir()
                (install / name / "user.txt").write_text("keep")
            (install / "data.json").write_text("user")
            with patch.object(backup, "check_disk_space", return_value=(True, 0)):
                first = Path(backup.create_backup(str(install), "old"))
                second = Path(backup.create_backup(str(install), "old"))
            self.assertNotEqual(first, second)
            self.assertEqual({p.name for p in first.iterdir()}, {"VERSION"})

    def test_partial_backup_is_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "install"
            install.mkdir()
            (install / "VERSION").write_text("old")
            with (
                patch.object(backup, "check_disk_space", return_value=(True, 0)),
                patch.object(backup.shutil, "copy2", side_effect=OSError("full")),
                self.assertRaises(OSError),
            ):
                backup.create_backup(str(install), "old")
            self.assertEqual(list(root.iterdir()), [install])


class LifecycleTests(unittest.TestCase):
    def test_only_settled_transaction_is_cleaned_on_normal_startup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            transaction = root / "_update_transaction"
            transaction.mkdir()
            (transaction / "journal.txt").write_text("pending")

            def inline_thread(*, target, **kwargs):
                thread = MagicMock()
                thread.start.side_effect = target
                return thread

            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(lifecycle.threading, "Thread", side_effect=inline_thread),
            ):
                lifecycle.startup_ready(root)
                self.assertTrue(transaction.exists())
                (transaction / "settled").write_text("")
                lifecycle.startup_ready(root)
                self.assertFalse(transaction.exists())

    def test_event_handle_is_closed_even_when_signalling_fails(self):
        if os.name != "nt":
            self.skipTest("Win32 event handles")
        kernel = MagicMock()
        kernel.OpenEventW.return_value = 123
        kernel.SetEvent.return_value = False
        with (
            patch.dict(os.environ, {"VETUBE_UPDATE_READY": "Local\\VeTubeReady-test"}),
            patch.object(lifecycle.ctypes, "WinDLL", return_value=kernel),
        ):
            self.assertFalse(lifecycle.signal_ready())
        kernel.CloseHandle.assert_called_once_with(123)

    def test_cleanup_preserves_current_unknown_and_user_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ["obsolete.txt", "current.txt", "unknown.txt", "data.json"]:
                (root / name).write_text("keep")
            (root / lifecycle.MANIFEST).write_text("current.txt\nprogram-files.txt")
            (root / lifecycle.CLEANUP).write_text(
                "obsolete.txt\ncurrent.txt\ndata.json\n../outside"
            )
            lifecycle.cleanup_obsolete(root)
            self.assertFalse((root / "obsolete.txt").exists())
            self.assertTrue((root / "current.txt").exists())
            self.assertTrue((root / "unknown.txt").exists())
            self.assertTrue((root / "data.json").exists())
            self.assertFalse((root / lifecycle.CLEANUP).exists())

    def test_cleanup_keeps_failed_entries_for_next_startup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "locked.txt").write_text("old")
            (root / lifecycle.MANIFEST).write_text("program-files.txt")
            (root / lifecycle.CLEANUP).write_text("locked.txt")
            original = Path.unlink

            def locked(path, *args, **kwargs):
                if path.name == "locked.txt":
                    raise PermissionError("locked")
                return original(path, *args, **kwargs)

            with patch.object(Path, "unlink", locked):
                lifecycle.cleanup_obsolete(root)
            self.assertEqual((root / lifecycle.CLEANUP).read_text(), "locked.txt")
            lifecycle.cleanup_obsolete(root)
            self.assertFalse((root / lifecycle.CLEANUP).exists())

    def test_unconfirmed_startup_does_not_start_cleanup(self):
        with (
            patch.dict(os.environ, {"VETUBE_UPDATE_READY": "Local\\VeTubeReady-test"}),
            patch.object(lifecycle, "signal_ready", return_value=False),
            patch.object(lifecycle.threading, "Thread") as thread,
        ):
            lifecycle.startup_ready(Path("unused"))
        thread.assert_not_called()


class PackagingTests(unittest.TestCase):
    def test_manifest_tracks_only_program_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            native = root / "bootstrap.exe"
            native.write_bytes(b"native fixture")
            build = root / "build"
            (build / "lib").mkdir(parents=True)
            (build / "lib/module.pyd").write_bytes(b"module")
            (build / "data.json").write_text("settings")
            (build / "sounds").mkdir()
            (build / "sounds/custom.wav").write_bytes(b"sound")
            package(build, native)
            paths = set((build / lifecycle.MANIFEST).read_text().splitlines())
            self.assertEqual(
                paths, {"bootstrap.exe", "lib/module.pyd", "program-files.txt"}
            )

    def test_legacy_names_are_generated_only_for_python314(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            native = root / "bootstrap.exe"
            native.write_bytes(b"native fixture")
            build = root / "build"
            (build / "lib").mkdir(parents=True)
            names = ("_bz2", "_ctypes", "_lzma", "_zstd")
            for name in names:
                (build / "lib" / f"{name}.pyd").write_bytes(b"module")
            with (
                patch(
                    "tools.package_native.importlib.machinery.EXTENSION_SUFFIXES",
                    [".cp315-win_amd64.pyd"],
                ),
                self.assertRaisesRegex(ValueError, "3.14"),
            ):
                package(build, native, legacy_pyd=True)
            with patch(
                "tools.package_native.importlib.machinery.EXTENSION_SUFFIXES",
                [".cp314-win_amd64.pyd"],
            ):
                package(build, native, legacy_pyd=True)
            paths = set((build / lifecycle.MANIFEST).read_text().splitlines())
            for name in names:
                self.assertFalse((build / "lib" / f"{name}.pyd").exists())
                self.assertIn(f"lib/{name}.cp314-win_amd64.pyd", paths)


class PublishedBootstrapTransitionTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows migration")
    def test_exact_v396_bootstrap_hands_off_to_native_finalizer(self):
        native = ROOT / "native/bootstrap/target/debug/bootstrap.exe"
        fixture = ROOT / "native/bootstrap/target/debug/startup-fixture.exe"
        if not native.exists() or not fixture.exists():
            self.skipTest("Run cargo test first to build the native fixtures")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "install"
            source = root / "source"
            install.mkdir()
            source.mkdir()
            shutil.copy2(fixture, install / "VeTube.exe")
            (install / "fixture-mode.txt").write_text("old")
            (install / "data.json").write_text("user settings")
            shutil.copy2(fixture, source / "VeTube.exe")
            shutil.copy2(native, source / "bootstrap.exe")
            (source / "fixture-mode.txt").write_text("ready:0")
            (source / "VERSION").write_text("bridge")
            # The old bootstrap file is a placeholder here: the exact released
            # Python source below performs its work in a separate interpreter.
            (install / "bootstrap.exe").write_bytes(b"old placeholder")
            parent = subprocess.Popen([str(install / "VeTube.exe"), "--parent"])
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "tests/fixtures/bootstrap_v3_96.py"),
                        str(parent.pid),
                        str(source),
                        str(install),
                        str(install / "VeTube.exe"),
                    ],
                    env={**os.environ, "TEMP": str(root)},
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                deadline = time.monotonic() + 20
                while not (install / "ready-confirmed.txt").exists():
                    if time.monotonic() > deadline:
                        log = root / "vetube_bootstrap_debug.txt"
                        self.fail(
                            log.read_text() if log.exists() else "No finalizer log"
                        )
                    time.sleep(0.05)
                self.assertEqual(
                    (install / "bootstrap.exe").read_bytes(), native.read_bytes()
                )
                self.assertEqual((install / "data.json").read_text(), "user settings")
                parent.wait(timeout=5)
                time.sleep(0.5)  # fixture releases its mapped executable
            finally:
                if parent.poll() is None:
                    parent.kill()
                    parent.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
