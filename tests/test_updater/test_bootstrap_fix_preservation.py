"""Tests for preserving user-owned files during bootstrap updates."""

import os
import shutil
import sys
from unittest.mock import patch

import pytest

from update.bootstrap_fix import (
    EXIT_FAILURE,
    EXIT_SUCCESS,
    LEFTOVERS_MANIFEST,
    _copy_update_files,
    cleanup_leftovers,
    _finalize_bootstrap,
    _launch_executable,
    _stage_bootstrap,
    _wait_for_process_exit,
)


def test_preserves_data_json_and_keymaps(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "data.json").write_text("packaged", encoding="utf-8")
    (destination / "data.json").write_text("user", encoding="utf-8")
    (source / "keymaps").mkdir()
    (source / "keymaps" / "default.json").write_text("packaged", encoding="utf-8")
    (destination / "keymaps").mkdir()
    (destination / "keymaps" / "custom.json").write_text("user", encoding="utf-8")

    _copy_update_files(str(source), str(destination))

    assert (destination / "data.json").read_text(encoding="utf-8") == "user"
    assert not (destination / "keymaps" / "default.json").exists()
    assert (destination / "keymaps" / "custom.json").read_text(encoding="utf-8") == "user"


def test_copies_new_sounds_without_overwriting_existing_files(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "sounds" / "theme").mkdir(parents=True)
    (destination / "sounds" / "theme").mkdir(parents=True)
    (source / "sounds" / "theme" / "existing.wav").write_text("packaged", encoding="utf-8")
    (source / "sounds" / "theme" / "new.wav").write_text("new", encoding="utf-8")
    (destination / "sounds" / "theme" / "existing.wav").write_text("custom", encoding="utf-8")

    _copy_update_files(str(source), str(destination))

    assert (destination / "sounds" / "theme" / "existing.wav").read_text(encoding="utf-8") == "custom"
    assert (destination / "sounds" / "theme" / "new.wav").read_text(encoding="utf-8") == "new"


def test_refreshes_existing_locale_files(tmp_path):
    # locales/ are program files, not user data: updates must refresh them or
    # existing installs keep stale catalogs and show Spanish for new strings
    # (decided by César on 2026-08-22 after a real NVDA repro).
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "locales").mkdir(parents=True)
    (destination / "locales").mkdir(parents=True)
    (source / "locales" / "es.json").write_text("packaged", encoding="utf-8")
    (destination / "locales" / "es.json").write_text("stale", encoding="utf-8")

    _copy_update_files(str(source), str(destination))

    assert (destination / "locales" / "es.json").read_text(encoding="utf-8") == "packaged"


def test_copies_new_locale_files(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "locales").mkdir(parents=True)
    (source / "locales" / "en.json").write_text("new", encoding="utf-8")

    _copy_update_files(str(source), str(destination))

    assert (destination / "locales" / "en.json").read_text(encoding="utf-8") == "new"


def test_replaces_ordinary_files_and_creates_missing_destination(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "missing-destination"
    source.mkdir()
    (source / "application.exe").write_text("updated", encoding="utf-8")

    _copy_update_files(str(source), str(destination))

    assert (destination / "application.exe").read_text(encoding="utf-8") == "updated"


def test_copies_ordinary_directories_recursively(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "bin" / "nested").mkdir(parents=True)
    (source / "bin" / "nested" / "module.pyd").write_bytes(b"updated")

    _copy_update_files(str(source), str(destination))

    assert (destination / "bin" / "nested" / "module.pyd").read_bytes() == b"updated"


def test_missing_source_is_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        _copy_update_files(str(tmp_path / "missing-source"), str(tmp_path / "destination"))


def test_active_bootstrap_is_not_copied_directly(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "bootstrap.exe").write_bytes(b"incoming")
    (destination / "bootstrap.exe").write_bytes(b"active")

    _copy_update_files(str(source), str(destination))

    assert (destination / "bootstrap.exe").read_bytes() == b"active"
    assert not (destination / "bootstrap.next.exe").exists()


def test_stages_incoming_bootstrap(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "bootstrap.exe").write_bytes(b"incoming")

    staged = _stage_bootstrap(str(source), str(destination))

    assert staged == str(destination / "bootstrap.next.exe")
    assert (destination / "bootstrap.next.exe").read_bytes() == b"incoming"
    assert not (destination / "bootstrap.exe").exists()


def test_finalize_waits_replaces_and_launches(tmp_path):
    destination = tmp_path / "destination"
    destination.mkdir()
    active = destination / "bootstrap.exe"
    staged = destination / "bootstrap.next.exe"
    app = destination / "VeTube.exe"
    active.write_bytes(b"old")
    staged.write_bytes(b"new")
    app.write_bytes(b"app")

    with patch("update.bootstrap_fix._wait_for_process_exit", return_value=True) as wait, patch(
        "update.bootstrap_fix._launch_executable", return_value=True
    ) as launch:
        result = _finalize_bootstrap(
            42, str(destination), str(app), str(active), str(staged)
        )

    assert result == EXIT_SUCCESS
    wait.assert_called_once_with(42)
    launch.assert_called_once_with(str(app))
    assert active.read_bytes() == b"new"
    assert not staged.exists()
    assert not (destination / "bootstrap.exe.previous").exists()


def test_finalize_failure_restores_old_bootstrap_and_signals(tmp_path):
    destination = tmp_path / "destination"
    destination.mkdir()
    active = destination / "bootstrap.exe"
    staged = destination / "bootstrap.next.exe"
    active.write_bytes(b"old")
    staged.write_bytes(b"new")

    with patch("update.bootstrap_fix._wait_for_process_exit", return_value=True), patch(
        "update.bootstrap_fix._launch_executable", return_value=False
    ), patch("update.bootstrap_fix._write_rollback_signal") as signal:
        result = _finalize_bootstrap(
            42, str(destination), str(destination / "VeTube.exe"), str(active), str(staged)
        )

    assert result == EXIT_FAILURE
    assert active.read_bytes() == b"old"
    assert not staged.exists()
    signal.assert_called_once_with(str(destination))


def test_existing_dll_is_replaced_and_old_copy_removed(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "vcruntime140.dll").write_bytes(b"new")
    (destination / "vcruntime140.dll").write_bytes(b"old")

    _copy_update_files(str(source), str(destination))

    assert (destination / "vcruntime140.dll").read_bytes() == b"new"
    assert not (destination / "vcruntime140.dll.old").exists()
    assert not (destination / LEFTOVERS_MANIFEST).exists()


def test_failed_copy_undoes_every_replacement(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "a.dll").write_bytes(b"new a")
    (source / "b.dll").write_bytes(b"new b")
    (source / "c.dll").write_bytes(b"new c")
    (destination / "a.dll").write_bytes(b"old a")
    (destination / "b.dll").write_bytes(b"old b")
    real_copy2 = shutil.copy2

    def copy_or_fail(src, dst, *args, **kwargs):
        if src.endswith("c.dll"):
            raise PermissionError("locked")
        return real_copy2(src, dst, *args, **kwargs)

    with patch("update.bootstrap_fix.shutil.copy2", side_effect=copy_or_fail), pytest.raises(
        PermissionError
    ):
        _copy_update_files(str(source), str(destination))

    assert (destination / "a.dll").read_bytes() == b"old a"
    assert (destination / "b.dll").read_bytes() == b"old b"
    assert not (destination / "c.dll").exists()
    assert not list(destination.glob("*.old"))


def test_old_copy_still_in_use_is_recorded_and_cleaned_later(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "python314.dll").write_bytes(b"new")
    (destination / "python314.dll").write_bytes(b"old")
    real_remove = os.remove

    def remove_unless_old(path):
        if str(path).endswith(".old"):
            raise PermissionError("in use")
        return real_remove(path)

    with patch("update.bootstrap_fix.os.remove", side_effect=remove_unless_old):
        _copy_update_files(str(source), str(destination))

    assert (destination / "python314.dll").read_bytes() == b"new"
    assert (destination / "python314.dll.old").read_bytes() == b"old"
    assert (destination / LEFTOVERS_MANIFEST).exists()

    cleanup_leftovers(str(destination))

    assert not (destination / "python314.dll.old").exists()
    assert not (destination / LEFTOVERS_MANIFEST).exists()


def test_cleanup_ignores_entries_that_are_not_old_files_inside_destination(tmp_path):
    destination = tmp_path / "destination"
    destination.mkdir()
    outside = tmp_path / "outside.old"
    outside.write_text("keep", encoding="utf-8")
    not_old = destination / "VeTube.exe"
    not_old.write_text("keep", encoding="utf-8")
    (destination / LEFTOVERS_MANIFEST).write_text(
        f"{outside}\n{not_old}\n", encoding="utf-8"
    )

    cleanup_leftovers(str(destination))

    assert outside.exists()
    assert not_old.exists()


def test_kill_process_also_terminates_children():
    from update import bootstrap_fix

    with patch.object(bootstrap_fix, "_descendant_pids", return_value=[7, 8]), patch.object(
        bootstrap_fix, "_terminate_process"
    ) as terminate:
        bootstrap_fix.kill_process(42)

    assert [call.args[0] for call in terminate.call_args_list] == [42, 7, 8]


def test_staging_failure_cleans_temporary_file(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "bootstrap.exe").write_bytes(b"incoming")

    with patch("update.bootstrap_fix.shutil.copy2", side_effect=OSError("disk full")), pytest.raises(
        OSError, match="disk full"
    ):
        _stage_bootstrap(str(source), str(destination))

    assert not (destination / "bootstrap.next.exe.tmp").exists()


def test_finalize_timeout_preserves_active_bootstrap(tmp_path):
    destination = tmp_path / "destination"
    destination.mkdir()
    active = destination / "bootstrap.exe"
    staged = destination / "bootstrap.next.exe"
    active.write_bytes(b"old")
    staged.write_bytes(b"new")

    with patch("update.bootstrap_fix._wait_for_process_exit", return_value=False), patch(
        "update.bootstrap_fix._write_rollback_signal"
    ) as signal:
        result = _finalize_bootstrap(
            42, str(destination), "app.exe", str(active), str(staged)
        )

    assert result == EXIT_FAILURE
    assert active.read_bytes() == b"old"
    signal.assert_called_once_with(str(destination))


def test_launch_executable_uses_shell_fallback(tmp_path):
    app = tmp_path / "VeTube.exe"
    app.write_bytes(b"app")
    popen = patch("update.bootstrap_fix.subprocess.Popen", side_effect=[OSError("locked"), object()])

    with popen as mocked_popen:
        assert _launch_executable(str(app)) is True

    assert mocked_popen.call_count == 2


def test_launch_executable_reports_missing_and_fallback_failure(tmp_path):
    assert _launch_executable(str(tmp_path / "missing.exe")) is False
    app = tmp_path / "VeTube.exe"
    app.write_bytes(b"app")
    with patch("update.bootstrap_fix.subprocess.Popen", side_effect=OSError("locked")):
        assert _launch_executable(str(app)) is False


def test_finalize_missing_stage_signals_rollback(tmp_path):
    destination = tmp_path / "destination"
    destination.mkdir()
    active = destination / "bootstrap.exe"
    active.write_bytes(b"old")
    with patch("update.bootstrap_fix._wait_for_process_exit", return_value=True), patch(
        "update.bootstrap_fix._write_rollback_signal"
    ) as signal:
        result = _finalize_bootstrap(
            42, str(destination), "app.exe", str(active), str(destination / "missing.exe")
        )

    assert result == EXIT_FAILURE
    assert active.read_bytes() == b"old"
    signal.assert_called_once_with(str(destination))


def test_wait_for_process_exit_times_out(tmp_path):
    kernel32 = type("Kernel32", (), {
        "OpenProcess": staticmethod(lambda *_args: 1),
        "CloseHandle": staticmethod(lambda *_args: None),
    })()
    windll = type("WinDll", (), {"kernel32": kernel32})()
    with patch("update.bootstrap_fix.ctypes.windll", windll), patch(
        "update.bootstrap_fix.time.monotonic", side_effect=[0, 31]
    ), patch("update.bootstrap_fix.time.sleep"):
        assert _wait_for_process_exit(42, timeout=30) is False


def test_kill_process_handles_windows_process_handle():
    kernel32 = type(
        "Kernel32",
        (),
        {
            "OpenProcess": staticmethod(lambda *_args: 1),
            "TerminateProcess": staticmethod(lambda *_args: None),
            "CloseHandle": staticmethod(lambda *_args: None),
        },
    )()
    windll = type("WinDll", (), {"kernel32": kernel32})()
    from update import bootstrap_fix

    with patch.object(bootstrap_fix.ctypes, "windll", windll):
        bootstrap_fix.kill_process(42)


def test_wait_for_process_exit_returns_when_process_is_absent():
    kernel32 = type("Kernel32", (), {"OpenProcess": staticmethod(lambda *_args: 0)})()
    windll = type("WinDll", (), {"kernel32": kernel32})()
    from update import bootstrap_fix

    with patch.object(bootstrap_fix.ctypes, "windll", windll), patch.object(
        bootstrap_fix.time, "monotonic", return_value=0
    ):
        assert bootstrap_fix._wait_for_process_exit(42, timeout=30) is True


def test_main_stages_and_launches_finalizer(tmp_path):
    from update import bootstrap_fix

    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "bootstrap.exe").write_bytes(b"new")
    (destination / "bootstrap.exe").write_bytes(b"old")
    app = destination / "VeTube.exe"
    app.write_bytes(b"app")
    argv = ["bootstrap.exe", "42", str(source), str(destination), str(app)]

    with patch.object(sys, "argv", argv), patch.object(bootstrap_fix, "kill_process"), patch.object(
        bootstrap_fix.time, "sleep"
    ), patch.object(bootstrap_fix.subprocess, "Popen") as popen:
        bootstrap_fix.main()

    assert (destination / "bootstrap.next.exe").exists()
    assert popen.call_args.args[0][1] == "--finalize"
    assert popen.call_args.args[0][2] == str(bootstrap_fix.os.getpid())


def test_main_staging_failure_signals_rollback(tmp_path):
    from update import bootstrap_fix

    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "bootstrap.exe").write_bytes(b"new")
    active = destination / "bootstrap.exe"
    active.write_bytes(b"old")
    argv = ["bootstrap.exe", "42", str(source), str(destination), "app.exe"]

    with patch.object(sys, "argv", argv), patch.object(bootstrap_fix, "kill_process"), patch.object(
        bootstrap_fix.time, "sleep"
    ), patch.object(bootstrap_fix, "_stage_bootstrap", side_effect=OSError("staging failed")), patch.object(
        bootstrap_fix, "_write_rollback_signal"
    ) as signal, pytest.raises(SystemExit) as error:
        bootstrap_fix.main()

    assert error.value.code == EXIT_FAILURE
    assert active.read_bytes() == b"old"
    signal.assert_called_once_with(str(destination))


def test_main_finalize_mode_delegates(tmp_path):
    from update import bootstrap_fix

    argv = [
        "bootstrap.next.exe", "--finalize", "42", str(tmp_path), "app.exe",
        "bootstrap.exe", "bootstrap.next.exe",
    ]
    with patch.object(sys, "argv", argv), patch.object(
        bootstrap_fix, "_finalize_bootstrap", return_value=EXIT_SUCCESS
    ) as finalize, pytest.raises(SystemExit) as error:
        bootstrap_fix.main()

    assert error.value.code == EXIT_SUCCESS
    finalize.assert_called_once_with(
        42, str(tmp_path), "app.exe", "bootstrap.exe", "bootstrap.next.exe"
    )


def test_main_legacy_payload_relaunches_application(tmp_path):
    from update import bootstrap_fix

    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    app = destination / "VeTube.exe"
    app.write_bytes(b"app")
    argv = ["bootstrap.exe", "42", str(source), str(destination), str(app)]

    with patch.object(sys, "argv", argv), patch.object(bootstrap_fix, "kill_process"), patch.object(
        bootstrap_fix.time, "sleep"
    ), patch.object(bootstrap_fix, "_launch_executable", return_value=True) as launch, pytest.raises(
        SystemExit
    ) as error:
        bootstrap_fix.main()

    assert error.value.code == EXIT_SUCCESS
    launch.assert_called_once_with(str(app))


def test_main_rejects_missing_update_source(tmp_path):
    from update import bootstrap_fix

    argv = ["bootstrap.exe", "42", str(tmp_path / "missing"), str(tmp_path), "app.exe"]
    with patch.object(sys, "argv", argv), patch.object(bootstrap_fix, "kill_process"), patch.object(
        bootstrap_fix.time, "sleep"
    ), pytest.raises(SystemExit) as error:
        bootstrap_fix.main()

    assert error.value.code == EXIT_FAILURE
