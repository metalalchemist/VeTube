"""Verify UAC launcher ownership, timeout and native exit-code reporting."""

from unittest.mock import MagicMock, patch

import pytest

from update.bootstrap import _build_args, launch_bootstrap


def test_arguments_quote_paths_and_trailing_slashes():
    assert (
        _build_args(12, "source folder", "dest", "app", "backup folder")
        == '12 "source folder" dest app "backup folder"'
    )


@pytest.mark.parametrize(
    "wait,code,expected", [(0, 0, 0), (0, 1, 1), (258, 259, -1), (0xFFFFFFFF, 0, 1)]
)
def test_actual_process_is_tracked_and_handle_is_always_closed(wait, code, expected):
    handle = MagicMock()
    with (
        patch("win32com.shell.shell.ShellExecuteEx", return_value={"hProcess": handle}),
        patch("win32event.WaitForSingleObject", return_value=wait),
        patch("win32process.GetExitCodeProcess", return_value=code),
    ):
        assert (
            launch_bootstrap("bootstrap.exe", 12, "source", "dest", "app") == expected
        )
    handle.Close.assert_called_once()


def test_uac_denial_is_distinct_from_launch_failure():
    error = OSError("cancelled")
    error.winerror = 1223
    with patch("win32com.shell.shell.ShellExecuteEx", side_effect=error):
        assert launch_bootstrap("bootstrap.exe", 12, "source", "dest", "app") == 2
    with patch("win32com.shell.shell.ShellExecuteEx", side_effect=OSError("missing")):
        assert launch_bootstrap("bootstrap.exe", 12, "source", "dest", "app") == 1


def test_wait_failure_still_closes_handle():
    handle = MagicMock()
    with (
        patch("win32com.shell.shell.ShellExecuteEx", return_value={"hProcess": handle}),
        patch("win32event.WaitForSingleObject", side_effect=OSError("wait failed")),
        pytest.raises(OSError),
    ):
        launch_bootstrap("bootstrap.exe", 12, "source", "dest", "app")
    handle.Close.assert_called_once()
