#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[cfg(windows)]
mod app {
    use std::env;
    use std::ffi::OsString;
    use std::fs::{self, OpenOptions};
    use std::io::{self, Write};
    use std::os::windows::process::CommandExt;
    use std::path::{Path, PathBuf};
    use std::process::{Child, Command};
    use std::time::{SystemTime, UNIX_EPOCH};
    use vetube_bootstrap::files::{self, Transaction};
    use vetube_bootstrap::windows::{self, ReadyEvent, Startup};

    fn log(message: &str) {
        if let Ok(mut file) = OpenOptions::new()
            .append(true)
            .create(true)
            .open(env::temp_dir().join("vetube_bootstrap_debug.txt"))
        {
            let _ = writeln!(file, "{message}");
        }
    }

    fn unique() -> String {
        format!(
            "{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_nanos()
        )
    }

    fn launch(exe: &Path, event: Option<&str>) -> io::Result<Child> {
        let mut command = Command::new(exe);
        command
            .current_dir(exe.parent().unwrap())
            .creation_flags(0x00000008); // DETACHED_PROCESS
        command.env_remove("VETUBE_UPDATE_READY");
        if let Some(event) = event {
            command.env("VETUBE_UPDATE_READY", event);
        }
        command.spawn()
    }

    fn resolve(dest: &Path, requested: &Path) -> PathBuf {
        let canonical = dest.join("VeTube.exe");
        if canonical.is_file() {
            canonical
        } else {
            requested.into()
        }
    }

    fn watch(
        dest: &Path,
        requested: &Path,
        backup: Option<&Path>,
        transaction: Option<&mut Transaction>,
    ) -> io::Result<()> {
        let event_name = format!("Local\\VeTubeReady-{}", unique());
        let event = ReadyEvent::create(&event_name)?;
        let exe = resolve(dest, requested);
        let mut transaction = transaction;
        let started = launch(&exe, Some(&event_name));
        let mut failed_pid = None;
        let outcome = match &started {
            Ok(child) => {
                // The Child owns its process handle; dropping it does not stop
                // VeTube, but does release the supervisor's handle.
                let outcome = event.wait(child, 180_000)?;
                if outcome == Startup::Exited {
                    failed_pid = Some(child.id());
                }
                outcome
            }
            Err(error) => {
                log(&format!("Launch failed: {error}"));
                Startup::Exited
            }
        };
        match outcome {
            Startup::Ready => {
                log("Startup confirmed; committing update");
                if let Some(tx) = transaction.as_mut() {
                    tx.finish()?;
                }
                if let Some(backup) = backup {
                    fs::remove_dir_all(backup)?;
                }
                let _ = fs::remove_file(dest.join("_rollback_needed"));
                Ok(())
            }
            Startup::Pending => {
                log(
                    "Startup still unconfirmed after 180 seconds; retaining backup and transaction",
                );
                // The running app is never overwritten on a timeout.
                Ok(())
            }
            Startup::Exited => {
                log("Application exited before readiness; restoring previous files");
                // Snapshot still identifies surviving children by their parent
                // PID even after the application exits.
                if let Some(pid) = failed_pid {
                    windows::stop_tree(pid)?;
                }
                if let Some(tx) = transaction.as_mut() {
                    tx.rollback()?;
                    fs::write(dest.join("_rollback_needed"), "startup failed")?;
                    let _previous_app = launch(&resolve(dest, requested), None)?;
                } else if let Some(backup) = backup {
                    files::restore_snapshot(backup, dest)?;
                    fs::write(dest.join("_rollback_needed"), "legacy startup failed")?;
                    let _previous_app = launch(&resolve(dest, requested), None)?;
                } else {
                    // Legacy finalization has no journal. Its old bootstrap did
                    // not pass a backup path, so never pretend rollback occurred.
                    fs::write(
                        dest.join("_rollback_needed"),
                        "legacy startup failed; backup retained",
                    )?;
                }
                Err(io::Error::other("application failed before readiness"))
            }
        }
    }

    pub fn run() -> io::Result<()> {
        let mut args: Vec<OsString> = env::args_os().skip(1).collect();
        let worker = args.first().is_some_and(|a| a == "--worker");
        if worker {
            let relocating_pid: u32 = args
                .get(1)
                .and_then(|arg| arg.to_str())
                .and_then(|pid| pid.parse().ok())
                .ok_or_else(|| io::Error::other("invalid relocation PID"))?;
            args.drain(..2);
            // The staged Rust executable must also be unloaded before deletion.
            windows::wait_for_exit(relocating_pid, 30_000)?;
        }
        let legacy = args.first().is_some_and(|a| a == "--finalize");
        let recover = args.first().is_some_and(|a| a == "--recover");
        if (legacy && !(args.len() == 6 || args.len() == 7))
            || (!legacy && !(args.len() == 4 || args.len() == 5))
        {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "No hay suficientes argumentos / invalid arguments",
            ));
        }
        let offset = usize::from(legacy || recover);
        let pid: u32 = args[offset]
            .to_str()
            .and_then(|s| s.parse().ok())
            .ok_or_else(|| io::Error::other("invalid PID"))?;
        let mut dest = PathBuf::from(&args[2]);
        if dest.file_name().is_some_and(|name| name == "_internal") {
            dest.pop();
        }
        let dest = fs::canonicalize(dest)?;
        let requested = PathBuf::from(&args[3]);
        let backup = args
            .get(if legacy { 6 } else { 4 })
            .filter(|a| !a.is_empty())
            .map(PathBuf::from);
        if let Some(backup) = &backup {
            let canonical = fs::canonicalize(backup)?;
            if canonical.starts_with(&dest) || dest.starts_with(&canonical) {
                return Err(io::Error::other("backup overlaps installation"));
            }
        }
        let current = fs::canonicalize(env::current_exe()?)?;
        if !worker && current.starts_with(&dest) {
            // Legacy bootstrap.next.exe runs inside the destination. Relocate
            // before replacing it, so even our own executable is never locked.
            let temp = env::temp_dir().join(format!("vetube-bootstrap-{}", unique()));
            fs::create_dir(&temp)?;
            let helper = temp.join("bootstrap.exe");
            fs::copy(current, &helper)?;
            let _helper = Command::new(helper)
                .arg("--worker")
                .arg(std::process::id().to_string())
                .args(args)
                .creation_flags(0x08000000)
                .spawn()?;
            return Ok(());
        }
        if recover {
            windows::stop_tree(pid)?;
            let mut tx = Transaction::recover(&dest)?;
            tx.rollback()?;
            fs::write(dest.join("_rollback_needed"), "manual recovery")?;
            let _previous_app = launch(&resolve(&dest, &requested), None)?;
            return Ok(());
        }
        if legacy {
            windows::wait_for_exit(pid, 30_000)?;
            let active = fs::canonicalize(PathBuf::from(&args[4]))?;
            let staged = fs::canonicalize(PathBuf::from(&args[5]))?;
            if active != dest.join("bootstrap.exe") || staged != dest.join("bootstrap.next.exe") {
                return Err(io::Error::other("invalid legacy finalizer paths"));
            }
            fs::copy(&staged, &active)?;
            fs::remove_file(staged)?;
            log("Legacy Python -> Rust finalization completed");
            return watch(&dest, &requested, backup.as_deref(), None);
        }
        let source = fs::canonicalize(PathBuf::from(&args[1]))?;
        if source.starts_with(&dest) || dest.starts_with(&source) {
            return Err(io::Error::other("source overlaps installation"));
        }
        if files::manifest(&source)?.is_empty() {
            return Err(io::Error::other("package has no program manifest"));
        }
        if dest.join(files::TRANSACTION).exists() {
            return Err(io::Error::other(
                "an earlier update is unconfirmed; recovery is required",
            ));
        }
        windows::stop_tree(pid)?;
        let mut tx = Transaction::begin(&dest)?;
        if let Err(error) = tx.install(&source) {
            log(&format!("Copy failed: {error}; restoring journal"));
            tx.rollback()?;
            fs::write(dest.join("_rollback_needed"), "copy failed")?;
            let _previous_app = launch(&resolve(&dest, &requested), None)?;
            return Err(error);
        }
        watch(&dest, &requested, backup.as_deref(), Some(&mut tx))
    }

    pub fn main() {
        if let Err(error) = run() {
            log(&format!("ERROR: {error}"));
            std::process::exit(1);
        }
    }
}

#[cfg(windows)]
fn main() {
    app::main();
}

#[cfg(not(windows))]
fn main() {
    eprintln!("The VeTube bootstrap requires Windows");
    std::process::exit(1);
}
