"""Focused branch tests for updater support modules."""

import io
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

from update import (
    bootstrap_fix,
    release_notes_dialog,
    update,
    updater,
    utils,
    wxUpdater,
)
from update.github_client import ReleaseInfo


def test_convert_bytes_boundaries():
    assert utils.convert_bytes(0) == "0"
    assert utils.convert_bytes(1024) == "1.00Kb"
    assert utils.convert_bytes(1 << 20) == "1.00Mb"
    assert utils.convert_bytes(1 << 30) == "1.00Gb"
    assert utils.convert_bytes(1 << 40) == "1.00Tb"
    # The legacy helper formats petabytes using its existing implementation.
    assert utils.convert_bytes(1 << 50) == "1024.00Pb"


def test_dir_size_ignores_unreadable_files():
    with (
        patch("update.backup.os.walk", return_value=[("dir", [], ["file"])]),
        patch("update.backup.os.path.getsize", side_effect=OSError),
    ):
        from update.backup import _dir_size

        assert _dir_size("dir") == 0


def test_fetch_releases_sends_etag_and_handles_not_modified():
    from update import github_client

    github_client._cache.etag = "etag"
    response = MagicMock(status_code=304)
    client = MagicMock()
    client.get.return_value = response
    assert github_client._fetch_releases(client) == ([], None, True)
    assert client.get.call_args.kwargs["headers"]["If-None-Match"] == "etag"


def test_github_client_cache_hit_and_unexpected_error():
    from update import github_client

    info = ReleaseInfo("v1", "1", False, "", "zip", "sum", "a.zip")
    github_client._cache.store(info, "etag", channel="stable")
    with patch("update.github_client.httpx.Client") as client:
        assert github_client.get_latest_release("stable") is info
        client.assert_not_called()
    github_client.clear_cache()
    with patch("update.github_client.httpx.Client", side_effect=RuntimeError("bad")):
        assert github_client.get_latest_release("stable") is None


def test_read_version_uses_metadata_and_fallback():
    base_dir = MagicMock()
    base_dir.__truediv__.return_value.exists.return_value = False
    with (
        patch.object(updater, "BASE_DIR", base_dir),
        patch("importlib.metadata.version", return_value="7.0"),
    ):
        assert updater._read_version() == "7.0"
    with (
        patch.object(updater, "BASE_DIR", base_dir),
        patch("importlib.metadata.version", side_effect=Exception),
        patch("builtins.open", side_effect=OSError),
    ):
        assert updater._read_version() == "0.0.0"


def test_read_version_uses_pyproject_when_metadata_is_unavailable():
    base_dir = MagicMock()
    base_dir.__truediv__.return_value.exists.return_value = False
    with (
        patch.object(updater, "BASE_DIR", base_dir),
        patch("importlib.metadata.version", side_effect=Exception),
        patch(
            "builtins.open",
            return_value=io.BytesIO(b'[project]\nversion = "8.0"\n'),
        ),
    ):
        assert updater._read_version() == "8.0"


def _run_thread_immediately(target, args=(), daemon=True):
    target(*args)


def test_do_update_manual_no_release_and_latest(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(updater, "_", lambda text: text, raising=False)

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(updater.threading, "Thread", side_effect=run_thread),
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            return_value=updater.github_client.ReleaseLookupResult(
                updater.github_client.ReleaseLookupStatus.NO_COMPATIBLE_RELEASE
            ),
        ),
        patch.object(updater.wx, "MessageBox") as message_box,
        patch.object(
            updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)
        ) as call_after,
    ):
        updater.do_update(is_manual=True)
        assert call_after.called
        assert "no hay una versión compatible" in message_box.call_args.args[0].lower()
    release = SimpleNamespace(version=updater.VERSION, description="notes")
    with (
        patch.object(updater.threading, "Thread", side_effect=run_thread),
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            return_value=updater.github_client.ReleaseLookupResult(
                updater.github_client.ReleaseLookupStatus.SUCCESS, release
            ),
        ),
        patch.object(updater.wx, "MessageBox") as message_box,
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
    ):
        updater.do_update(is_manual=True)
        assert message_box.call_args.args[0] == (
            "Al parecer tienes la última versión del programa"
        )


def test_do_update_starts_install_for_new_release(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(updater, "_", lambda text: text, raising=False)
    release = SimpleNamespace(version="99.0", description="notes")

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            return_value=updater.github_client.ReleaseLookupResult(
                updater.github_client.ReleaseLookupStatus.SUCCESS, release
            ),
        ),
        patch("update.updater.show_release_notes_dialog", return_value=True),
        patch("update.updater._install_update") as install,
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
        patch.object(updater.threading, "Thread", side_effect=run_thread),
    ):
        updater.do_update()
    install.assert_called_once_with(release)


def test_do_update_reports_check_exception(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(updater, "_", lambda text: text, raising=False)

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(updater.threading, "Thread", side_effect=run_thread),
        patch.object(
            updater.github_client,
            "get_latest_release_result",
            side_effect=RuntimeError("offline"),
        ),
        patch.object(updater.wx, "MessageBox"),
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
    ):
        updater.do_update(is_manual=True)


def test_do_update_beta_current_prerelease_reports_latest(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(updater, "VERSION", "3.95rc4")
    monkeypatch.setattr(updater, "_", lambda text: text, raising=False)
    release = SimpleNamespace(version="3.95rc4", description="notes")
    result = updater.github_client.ReleaseLookupResult(
        updater.github_client.ReleaseLookupStatus.SUCCESS, release
    )

    def run_thread(*, target, args=(), daemon=True):
        return SimpleNamespace(start=lambda: target(*args))

    with (
        patch.object(updater, "get_channel", return_value="beta"),
        patch.object(updater.github_client, "get_latest_release_result", return_value=result),
        patch("update.updater.show_release_notes_dialog", return_value=False),
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
        patch.object(updater.threading, "Thread", side_effect=run_thread),
        patch.object(updater.wx, "MessageBox") as message_box,
    ):
        updater.do_update(is_manual=True)

    message_box.assert_called_once()
    assert message_box.call_args.args[0] == (
        "Al parecer tienes la última versión del programa"
    )


def test_github_client_skips_invalid_candidate_version():
    from update import github_client

    invalid = SimpleNamespace(version="not-a-version")
    with patch.object(github_client, "_parse_release", return_value=invalid):
        assert github_client._select_highest_release([{}]) is None


def test_install_update_handles_checksum_and_disabled_backup(tmp_path):
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(updater, "config", {"create_backup_before_update": False}),
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value=None),
        patch("update.updater.verify") as verify,
        patch("update.updater.extract") as extract,
    ):
        updater._install_update(release)
    verify.assert_not_called()
    extract.assert_not_called()


def test_install_update_success_cleans_backup_and_notifies(monkeypatch):
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(updater, "config", {"create_backup_before_update": True}),
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.create_backup", return_value="backup"),
        patch("update.updater.extract"),
        patch("update.updater.launch_bootstrap", return_value=0),
        patch("update.updater.cleanup_backup") as cleanup,
        patch("update.updater.update_finished") as finished,
    ):
        updater._install_update(release)
    cleanup.assert_called_once_with("backup")
    finished.assert_called_once_with()


def test_install_update_restores_when_bootstrap_fails():
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(updater, "config", {"create_backup_before_update": True}),
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.create_backup", return_value="backup"),
        patch("update.updater.extract"),
        patch("update.updater.launch_bootstrap", return_value=1),
        patch("update.updater.restore_backup") as restore,
    ):
        updater._install_update(release)
    restore.assert_called_once()


def test_fetch_checksum_success_and_http_failure():
    response = MagicMock(text="hash  file.zip")
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    with patch("update.updater.httpx.Client", return_value=client):
        assert updater._fetch_checksum("url") == "hash  file.zip"
    client.get.side_effect = httpx.ConnectError("offline")
    with patch("update.updater.httpx.Client", return_value=client):
        assert updater._fetch_checksum("url") is None


def test_donation_dialog_accept_opens_browser(monkeypatch):
    monkeypatch.setattr(update, "_", lambda text: text, raising=False)
    dialog = MagicMock(ShowModal=MagicMock(return_value=update.wx.ID_YES))
    with (
        patch.object(update.wx, "MessageDialog", return_value=dialog),
        patch.object(update.wx, "LaunchDefaultBrowser") as launch,
    ):
        update.donation()
    launch.assert_called_once()


def test_donation_dialog_decline_does_not_open_browser(monkeypatch):
    monkeypatch.setattr(update, "_", lambda text: text, raising=False)
    dialog = MagicMock(ShowModal=MagicMock(return_value=update.wx.ID_NO))
    with (
        patch.object(update.wx, "MessageDialog", return_value=dialog),
        patch.object(update.wx, "LaunchDefaultBrowser") as launch,
    ):
        update.donation()
    launch.assert_not_called()


def test_install_update_shows_donation_dialog_when_disabled():
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(
            updater,
            "config",
            {"create_backup_before_update": True, "donations": False},
        ),
        patch.object(updater.wx, "CallAfter", side_effect=lambda fn, *a: fn(*a)),
        patch("update.updater.donation") as donation,
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.create_backup", return_value="backup"),
        patch("update.updater.extract"),
        patch("update.updater.launch_bootstrap", return_value=0),
        patch("update.updater.cleanup_backup"),
        patch("update.updater.update_finished"),
    ):
        updater._install_update(release)
    donation.assert_called_once()


def test_install_update_skips_donation_dialog_when_enabled():
    release = SimpleNamespace(
        version="4.0", zip_name="update.zip", zip_url="zip", checksum_url="sum"
    )
    with (
        patch.object(
            updater,
            "config",
            {"create_backup_before_update": True, "donations": True},
        ),
        patch.object(updater.wx, "CallAfter") as call_after,
        patch("update.updater.download"),
        patch("update.updater._fetch_checksum", return_value="hash"),
        patch("update.updater.verify", return_value=True),
        patch("update.updater.create_backup", return_value="backup"),
        patch("update.updater.extract"),
        patch("update.updater.launch_bootstrap", return_value=0),
        patch("update.updater.cleanup_backup"),
        patch("update.updater.update_finished"),
    ):
        updater._install_update(release)
    call_after.assert_not_called()


def test_wx_updater_progress_and_notifications(monkeypatch):
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    wxUpdater.progress_dialog = None
    dialog = MagicMock()
    with (
        patch.object(wxUpdater.wx, "CallAfter", side_effect=lambda fn: fn()),
        patch.object(wxUpdater, "create_progress_dialog", return_value=dialog),
    ):
        wxUpdater.progress_callback(10, 100)
        wxUpdater.progress_callback(100, 100)
    dialog.Update.assert_called_once()
    assert wxUpdater.progress_dialog is None
    wxUpdater.backup_dialog = None
    backup = MagicMock()
    with (
        patch.object(wxUpdater.wx, "CallAfter", side_effect=lambda fn: fn()),
        patch.object(wxUpdater.wx, "ProgressDialog", return_value=backup),
    ):
        wxUpdater.backup_progress_callback(1, 2)
        wxUpdater.backup_progress_callback(2, 2)
    backup.Destroy.assert_called_once()
    with (
        patch.object(wxUpdater.wx, "CallAfter", side_effect=lambda fn: fn()),
        patch.object(wxUpdater.wx, "MessageDialog", return_value=MagicMock()),
    ):
        wxUpdater.rollback_notification("checksum")
        wxUpdater.no_updates_dialog("1.0")
        wxUpdater.update_finished()


def test_wx_updater_dialog_choices(monkeypatch):
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    dialog = MagicMock(ShowModal=MagicMock(return_value=wxUpdater.wx.ID_YES))
    with (
        patch.object(wxUpdater.wx, "MessageDialog", return_value=dialog),
        patch.object(wxUpdater, "get_channel", return_value="beta"),
    ):
        assert wxUpdater.available_update_dialog("2.0", "notes") is True
    dialog.ShowModal.return_value = wxUpdater.wx.ID_NO
    with patch.object(wxUpdater.wx, "MessageDialog", return_value=dialog):
        assert wxUpdater.available_update_dialog("2.0", "notes") is False


def test_wx_updater_creates_check_and_download_dialogs(monkeypatch):
    monkeypatch.setattr(wxUpdater, "_", lambda text: text, raising=False)
    dialog = MagicMock()
    with patch.object(wxUpdater.wx, "ProgressDialog", return_value=dialog):
        assert wxUpdater.checking_updates_dialog() is dialog
        assert wxUpdater.create_progress_dialog() is dialog
    dialog.Pulse.assert_called_once()
    dialog.Show.assert_called_once()


def test_release_notes_helpers_and_navigation(monkeypatch):
    monkeypatch.setattr(release_notes_dialog, "_", lambda text: text, raising=False)
    html = release_notes_dialog._markdown_to_html(
        "# Title\n\n**bold** *italic*\n\n- item\n\n[x](https://example.com)"
    )
    assert "<h1>Title</h1>" in html and "<strong>bold</strong>" in html
    assert '<a href="https://example.com">x</a>' in html
    assert "<html>" in release_notes_dialog._get_styled_html("Title", html)
    dialog = release_notes_dialog.ReleaseNotesDialog.__new__(
        release_notes_dialog.ReleaseNotesDialog
    )
    dialog.version = "2.0"
    dialog.release_notes = "notes"
    dialog.webview = MagicMock()
    dialog._load_content()
    assert dialog.webview.SetPage.called
    event = MagicMock()
    event.GetURL.return_value = "https://example.com"
    with patch.object(release_notes_dialog.wx, "LaunchDefaultBrowser"):
        dialog._on_webview_navigating(event)
    event.Veto.assert_called_once()
    dialog._on_webview_navigating(SimpleNamespace(GetURL=lambda: "about:blank"))


def test_release_notes_dialog_callbacks_and_fallback(monkeypatch):
    monkeypatch.setattr(release_notes_dialog, "_", lambda text: text, raising=False)
    dialog = release_notes_dialog.ReleaseNotesDialog.__new__(
        release_notes_dialog.ReleaseNotesDialog
    )
    dialog.version = "2.0"
    dialog.release_notes = "raw notes"
    dialog.webview = MagicMock()
    dialog.webview.SetPage.side_effect = [RuntimeError("webview unavailable"), None]
    with patch.object(release_notes_dialog.logger, "exception"):
        dialog._load_content()
    assert "raw notes" in dialog.webview.SetPage.call_args.args[0]
    dialog.user_accepted = False
    dialog.EndModal = MagicMock()
    dialog._on_update(None)
    assert dialog.get_user_choice() is True
    dialog._on_cancel(None)
    assert dialog.get_user_choice() is False
    for url in ("", "data:text/plain,ok", "ftp://example.com"):
        event = SimpleNamespace(GetURL=lambda url=url: url)
        dialog._on_webview_navigating(event)


def test_show_release_notes_dialog_returns_modal_and_choice(monkeypatch):
    monkeypatch.setattr(release_notes_dialog, "_", lambda text: text, raising=False)
    dialog = MagicMock()
    dialog.ShowModal.return_value = release_notes_dialog.wx.ID_OK
    dialog.get_user_choice.return_value = True
    with patch.object(release_notes_dialog, "ReleaseNotesDialog", return_value=dialog):
        assert release_notes_dialog.show_release_notes_dialog(None, "1.0", "notes")
    dialog.Destroy.assert_called_once_with()


def test_bootstrap_fix_helpers_and_main_success(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap_fix, "LOG_FILE", str(tmp_path / "log.txt"))
    bootstrap_fix.log("message")
    assert "message" in (tmp_path / "log.txt").read_text()
    bootstrap_fix._write_rollback_signal(str(tmp_path))
    assert (tmp_path / bootstrap_fix.ROLLBACK_SIGNAL).exists()
    with patch.object(bootstrap_fix.ctypes, "windll", create=True) as windll:
        windll.kernel32.OpenProcess.return_value = 0
        bootstrap_fix.kill_process(123)
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    exe = dest / "app.exe"
    exe.write_text("exe")
    monkeypatch.setattr(
        sys, "argv", ["bootstrap.py", "1", str(source), str(dest), str(exe)]
    )
    with (
        patch.object(bootstrap_fix.time, "sleep"),
        patch.object(bootstrap_fix, "kill_process"),
        patch.object(bootstrap_fix.shutil, "copytree"),
        patch.object(bootstrap_fix.subprocess, "Popen"),
        pytest.raises(SystemExit) as result,
    ):
        bootstrap_fix.main()
    assert result.value.code == bootstrap_fix.EXIT_SUCCESS


def test_bootstrap_fix_rejects_missing_arguments(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["bootstrap.py"])
    with patch.object(bootstrap_fix, "log"), pytest.raises(SystemExit) as result:
        bootstrap_fix.main()
    assert result.value.code == bootstrap_fix.EXIT_FAILURE


@pytest.mark.parametrize(
    ("error", "exit_code"),
    [(PermissionError("denied"), bootstrap_fix.EXIT_CANCELLED),
     (OSError("copy failed"), bootstrap_fix.EXIT_FAILURE)],
)
def test_bootstrap_fix_copy_errors_write_rollback(tmp_path, monkeypatch, error, exit_code):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    monkeypatch.setattr(
        sys, "argv", ["bootstrap.py", "1", str(source), str(dest), "missing.exe"]
    )
    with (
        patch.object(bootstrap_fix.time, "sleep"),
        patch.object(bootstrap_fix, "kill_process"),
        patch.object(bootstrap_fix, "_copy_update_files", side_effect=error),
        patch.object(bootstrap_fix, "_write_rollback_signal") as rollback,
        pytest.raises(SystemExit) as result,
    ):
        bootstrap_fix.main()
    assert result.value.code == exit_code
    rollback.assert_called_once_with(str(dest))


def test_bootstrap_fix_uses_fallback_executable_launch(tmp_path, monkeypatch):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    exe = dest / "app.exe"
    exe.write_text("exe")
    original = tmp_path / "_internal" / "app.exe"
    monkeypatch.setattr(
        sys, "argv", ["bootstrap.py", "1", str(source), str(dest), str(original)]
    )
    with (
        patch.object(bootstrap_fix.time, "sleep"),
        patch.object(bootstrap_fix, "kill_process"),
        patch.object(bootstrap_fix, "_copy_update_files"),
        patch.object(bootstrap_fix.subprocess, "Popen", side_effect=[OSError("first"), MagicMock()]),
        pytest.raises(SystemExit) as result,
    ):
        bootstrap_fix.main()
    assert result.value.code == bootstrap_fix.EXIT_SUCCESS
