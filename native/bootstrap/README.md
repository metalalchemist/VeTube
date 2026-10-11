# Native VeTube update installer

VeTube prepares and verifies the download while backing up immutable program
files in another thread. The native Windows installer closes VeTube and its
descendants, waits for their exit, replaces the installation, and supervises the
new application's startup. It does not load Python DLLs or `.pyd` modules.

## Build and verify

Run from the repository root on Windows with Rust/MSVC installed:

```powershell
cargo fmt --manifest-path native/bootstrap/Cargo.toml --check
cargo clippy --manifest-path native/bootstrap/Cargo.toml --locked --all-targets -- -D warnings
cargo test --manifest-path native/bootstrap/Cargo.toml --locked -- --test-threads=1
python -m unittest tests.test_async_logging tests.test_async_update -v
./native/bootstrap/build.ps1
```

The last command writes `bootstrap.exe` at the repository root. The MSVC C
runtime is linked statically via `.cargo/config.toml`. Keep Cargo.toml, Cargo.lock,
the Rust source and the executable together when distributing this change.
Local packaging and GitHub releases copy the prebuilt `bootstrap.exe` from the
repository root into the ZIP and MSI without rebuilding Rust. Commit this binary
alongside its source changes. Rebuild it explicitly with the command above when
the installer changes. The separate `bootstrap.yml` workflow checks Rust and
its tests; it does not replace the binary used for releases.

`uv run poe build` prepares the portable directory and `uv run poe msi` prepares
the MSI. Both generate `program-files.txt` after freezing; the portable build
also applies the Python 3.14 `.pyd` compatibility names. Do not zip an unprepared
`cxfreeze build` directory: its manifest would be missing or stale.

## Startup contract

| Result | Action |
| --- | --- |
| VeTube signals its unique Win32 event | Commit the installation; delete the transaction and optional backup. |
| VeTube exits before signalling, or cannot be launched | Restore the changed files and remove introduced files; relaunch the previous app once. |
| VeTube remains alive without signalling for 180 seconds | Leave the application running and retain the transaction and backup. |
| File replacement fails | Restore the changed files before relaunching the previous application. |

Rust passes the unique event name in `VETUBE_UPDATE_READY`. The GUI signals it
after the main window and essential components initialize and the event loop
starts servicing callbacks. Optional voice-engine downloads happen afterward.
Closing the application before this point counts as an unconfirmed startup.

Original files remain in `_update_transaction/files/` until confirmation. The
durable `journal.txt` records replacements and introduced paths. This supplies
precise rollback even when the optional full backup is disabled. User settings,
voices, engines, keymaps and custom sounds are preserved.

A pending transaction prevents another update. After inspecting
`%TEMP%/vetube_bootstrap_debug.txt`, it can be recovered explicitly with the
native executable (run with the permissions needed for the installation):

```text
bootstrap.exe --recover VETUBE_PID INSTALL_DIR APP_EXE [BACKUP_DIR]
```

This stops the specified VeTube process tree, restores its pending journal and
relaunches the previous app. It retains the full backup for inspection. Do not
manually delete `_update_transaction` to dismiss an unconfirmed update.

## Transition from 3.96 and 3.97-rc1

A `settled` marker distinguishes an interrupted deletion after commit/rollback
from a pending installation. Such completed transaction folders are cleaned on
a later normal startup; they are never used for partial rollback.

Both released versions run their installed Python bootstrap. That old process
copies the new package, stages Rust as `bootstrap.next.exe`, and calls:

```text
bootstrap.next.exe --finalize OLD_BOOTSTRAP_PID INSTALL_DIR APP_EXE ACTIVE_EXE STAGED_EXE
```

Rust accepts that protocol, relocates itself to a temporary directory, waits for
the old process to exit, installs the native bootstrap and supervises startup.
The released Python source is retained only as the compatibility test fixture
`tests/fixtures/bootstrap_v3_96.py`; it is identical in the RC1 tag. Production no
longer freezes or imports the Python installer.

Keep Python 3.14 and the portable ZIP's `.cp314-win_amd64.pyd` renaming during
this transition: the first copy still runs under the old installed Python
bootstrap. New versions execute Rust directly from the downloaded package.

The old protocol does not pass a backup path or a pre-copy journal. The first
transition therefore cannot provide automatic restoration of the entire old
installation after a startup failure. It records failure and retains existing
backups rather than guessing which directory to restore. New-to-new native
updates have the full rollback contract above. A legacy caller that does supply
the optional backup argument can use snapshot restoration only when that backup
has an authoritative program manifest; unknown user files are never restored
over newer ones.

## Cleanup and validation limits

Only files owned by the previous `program-files.txt` and absent from the new
manifest are obsolete. Unknown files and user data are retained. Obsolete
runtime/code files are moved aside before launch, preventing stale imports.
Other obsolete files are listed in `_update_cleanup.txt`; VeTube removes them
in a background thread after readiness. Failed deletions remain for retry.
An old installation without a manifest is preserved conservatively.

Native tests cover mid-copy failure, startup crash, a real 60-second startup,
the real 180-second pending timeout, legacy finalization, file ownership and
interrupted-journal recovery. Python tests execute the released 3.96 installer
against native fixture applications in temporary directories. This is a
protocol rehearsal, not a full installation test using released ZIP binaries.
An isolated Windows VM rehearsal of the frozen application and UAC remains a
release validation step.

The Win32 soak test checks handle counts and private-memory growth after warmup
across thousands of event/process operations, including failure paths. Handles
use RAII and are closed on all return paths. GitHub also runs the portable file
transaction tests under Miri on Linux; Win32 FFI is outside that Miri check.
These checks detect regressions, not a proof that every possible execution is
free of leaks.

## Review and rollback boundaries

Local verification on Windows (Python 3.12): `python -m pytest tests -q`
passed 190 tests (two dependency deprecation warnings). The complete
`cargo test --manifest-path native/bootstrap/Cargo.toml --locked -- --test-threads=1`
run passed five library and nine integration tests, including the real 60/180
second waits. Clippy with `--all-targets -- -D warnings` and formatting passed.
The final Win32 soak measured 57 handles before/after and 720896 private bytes
before/after warmup. The release binary was rebuilt after these changes.
Python 3.14 frozen-package/UAC validation and the CI Miri run remain pending.

Review the native file transaction and process supervision first, then the
Python startup/preparation integration, then packaging and compatibility tests.
They are separate work units even though they must ship together. Reverting
the native installer requires reverting its Python lifecycle, packaging and
manifest changes together and restoring the previous Python installer/tests.
Do not revert only the binary or remove compatibility renaming independently.
