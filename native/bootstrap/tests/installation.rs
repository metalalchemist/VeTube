#![cfg(windows)]

use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use vetube_bootstrap::files::{CLEANUP, MANIFEST, TRANSACTION, Transaction, restore_snapshot};

struct Sandbox(PathBuf);
impl Sandbox {
    fn new() -> Self {
        let name = format!(
            "vetube-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        );
        let root = std::env::temp_dir().join(name);
        fs::create_dir(&root).unwrap();
        Self(root)
    }
    fn directory(&self, name: &str) -> PathBuf {
        let path = self.0.join(name);
        fs::create_dir_all(&path).unwrap();
        path
    }
}
impl Drop for Sandbox {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn write(root: &Path, name: &str, content: &str) {
    let path = root.join(name);
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(path, content).unwrap();
}

fn package(root: &Path, mode: &str) {
    fs::copy(
        env!("CARGO_BIN_EXE_startup-fixture"),
        root.join("VeTube.exe"),
    )
    .unwrap();
    fs::copy(env!("CARGO_BIN_EXE_bootstrap"), root.join("bootstrap.exe")).unwrap();
    write(root, "fixture-mode.txt", mode);
    write(root, "VERSION", "new");
    write(
        root,
        MANIFEST,
        "VeTube.exe\nbootstrap.exe\nVERSION\nfixture-mode.txt\nprogram-files.txt",
    );
}

struct Running(Child);
impl Drop for Running {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

fn run_update(source: &Path, dest: &Path, backup: &Path) -> Running {
    let parent = Running(
        Command::new(dest.join("VeTube.exe"))
            .arg("--parent")
            .spawn()
            .unwrap(),
    );
    let bootstrap = Command::new(source.join("bootstrap.exe"))
        .arg(parent.0.id().to_string())
        .arg(source)
        .arg(dest)
        .arg(dest.join("VeTube.exe"))
        .arg(backup)
        .spawn()
        .unwrap();
    // Keep the parent alive until the bootstrap has actually stopped it.
    let mut parent = parent;
    let deadline = Instant::now() + Duration::from_secs(10);
    while parent.0.try_wait().unwrap().is_none() {
        assert!(Instant::now() < deadline, "bootstrap did not stop parent");
        thread::sleep(Duration::from_millis(20));
    }
    Running(bootstrap)
}

fn wait(process: &mut Running, seconds: u64) -> std::process::ExitStatus {
    let deadline = Instant::now() + Duration::from_secs(seconds);
    loop {
        if let Some(status) = process.0.try_wait().unwrap() {
            return status;
        }
        assert!(Instant::now() < deadline, "bootstrap did not finish");
        thread::sleep(Duration::from_millis(20));
    }
}

#[test]
fn copy_failure_restores_originals_and_removes_new_files() {
    let sandbox = Sandbox::new();
    let source = sandbox.directory("source");
    let dest = sandbox.directory("dest");
    write(&dest, "a.txt", "original");
    write(&dest, "data.json", "user");
    write(&source, "a.txt", "new");
    write(&source, "b.txt", "introduced");
    write(&source, "z.txt", "file");
    fs::create_dir(dest.join("z.txt")).unwrap(); // deterministic mid-copy failure
    write(&source, MANIFEST, "a.txt\nb.txt\nz.txt\nprogram-files.txt");
    let mut tx = Transaction::begin(&dest).unwrap();
    assert!(tx.install(&source).is_err());
    tx.rollback().unwrap();
    assert_eq!(fs::read_to_string(dest.join("a.txt")).unwrap(), "original");
    assert_eq!(fs::read_to_string(dest.join("data.json")).unwrap(), "user");
    assert!(!dest.join("b.txt").exists());
    assert!(!dest.join(TRANSACTION).exists());
}

#[test]
fn stops_parent_and_voice_engine_before_copying() {
    let sandbox = Sandbox::new();
    let dest = sandbox.directory("installation with spaces");
    fs::copy(
        env!("CARGO_BIN_EXE_startup-fixture"),
        dest.join("VeTube.exe"),
    )
    .unwrap();
    let parent = Command::new(dest.join("VeTube.exe"))
        .arg("--parent-tree")
        .spawn()
        .unwrap();
    let mut parent = Running(parent);
    let deadline = Instant::now() + Duration::from_secs(5);
    while !dest.join("voice-child-pid.txt").exists() {
        assert!(Instant::now() < deadline);
        thread::sleep(Duration::from_millis(20));
    }
    let child: u32 = fs::read_to_string(dest.join("voice-child-pid.txt"))
        .unwrap()
        .parse()
        .unwrap();
    vetube_bootstrap::windows::stop_tree(parent.0.id()).unwrap();
    assert!(parent.0.try_wait().unwrap().is_some());
    vetube_bootstrap::windows::wait_for_exit(child, 1000).unwrap();
}

#[test]
fn obsolete_runtime_is_removed_before_launch_and_user_data_is_preserved() {
    let sandbox = Sandbox::new();
    let source = sandbox.directory("source");
    let dest = sandbox.directory("dest");
    write(
        &dest,
        MANIFEST,
        "lib/old.pyd\ndoc/old.txt\nvoices/custom.onnx",
    );
    write(&dest, "lib/old.pyd", "old runtime");
    write(&dest, "doc/old.txt", "old documentation");
    write(&dest, "voices/custom.onnx", "user voice");
    write(&dest, "sounds/custom.wav", "user sound");
    write(&source, MANIFEST, "VERSION\nprogram-files.txt");
    write(&source, "VERSION", "new");
    write(&source, "sounds/custom.wav", "bundled sound");
    let mut tx = Transaction::begin(&dest).unwrap();
    tx.install(&source).unwrap();
    assert!(!dest.join("lib/old.pyd").exists());
    assert!(dest.join("doc/old.txt").exists());
    assert!(
        fs::read_to_string(dest.join(CLEANUP))
            .unwrap()
            .contains("old.txt")
    );
    assert_eq!(
        fs::read_to_string(dest.join("sounds/custom.wav")).unwrap(),
        "user sound"
    );
    tx.rollback().unwrap();
    assert!(dest.join("lib/old.pyd").exists());
    assert!(dest.join("voices/custom.onnx").exists());
}

#[test]
fn successful_startup_commits_and_deletes_backup() {
    successful_startup(0, 15);
}

#[test]
fn legacy_snapshot_restores_program_files_without_overwriting_user_data() {
    let sandbox = Sandbox::new();
    let backup = sandbox.directory("backup");
    let dest = sandbox.directory("dest");
    write(&backup, "VERSION", "previous");
    write(&backup, "data.json", "older settings");
    write(&backup, "personal-notes.txt", "older notes");
    write(&backup, MANIFEST, "VERSION\nprogram-files.txt");
    write(&dest, "VERSION", "new");
    write(&dest, "data.json", "current settings");
    write(&dest, "personal-notes.txt", "current notes");
    write(&dest, "lib/introduced.pyd", "introduced");
    write(
        &dest,
        MANIFEST,
        "VERSION\nprogram-files.txt\nlib/introduced.pyd",
    );
    restore_snapshot(&backup, &dest).unwrap();
    assert_eq!(
        fs::read_to_string(dest.join("VERSION")).unwrap(),
        "previous"
    );
    assert_eq!(
        fs::read_to_string(dest.join("data.json")).unwrap(),
        "current settings"
    );
    assert!(!dest.join("lib/introduced.pyd").exists());
    assert_eq!(
        fs::read_to_string(dest.join("personal-notes.txt")).unwrap(),
        "current notes"
    );
}

#[test]
fn one_minute_startup_is_accepted() {
    successful_startup(60_000, 80);
}

fn successful_startup(delay: u64, deadline: u64) {
    let sandbox = Sandbox::new();
    let source = sandbox.directory("source");
    let dest = sandbox.directory("dest");
    let backup = sandbox.directory("backup");
    package(&dest, "old");
    package(&source, &format!("ready:{delay}"));
    let mut bootstrap = run_update(&source, &dest, &backup);
    assert!(wait(&mut bootstrap, deadline).success());
    assert!(!backup.exists());
    assert!(!dest.join(TRANSACTION).exists());
    assert_eq!(fs::read_to_string(dest.join("VERSION")).unwrap(), "new");
    thread::sleep(Duration::from_millis(250)); // fixture releases its executable
}

#[test]
fn startup_crash_rolls_back_and_relaunches_once() {
    let sandbox = Sandbox::new();
    let source = sandbox.directory("source");
    let dest = sandbox.directory("dest");
    let backup = sandbox.directory("backup");
    package(&dest, "old");
    write(&dest, "VERSION", "previous");
    package(&source, "exit");
    let mut bootstrap = run_update(&source, &dest, &backup);
    assert!(!wait(&mut bootstrap, 15).success());
    assert!(backup.exists());
    assert_eq!(
        fs::read_to_string(dest.join("VERSION")).unwrap(),
        "previous"
    );
    let deadline = Instant::now() + Duration::from_secs(5);
    while !dest.join("restored.txt").exists() {
        assert!(Instant::now() < deadline);
        thread::sleep(Duration::from_millis(20));
    }
    assert!(dest.join("_rollback_needed").exists());
}

#[test]
fn timeout_keeps_the_running_app_backup_and_journal() {
    let sandbox = Sandbox::new();
    let source = sandbox.directory("source");
    let dest = sandbox.directory("dest");
    let backup = sandbox.directory("backup");
    package(&dest, "old");
    package(&source, "pending");
    let mut bootstrap = run_update(&source, &dest, &backup);
    assert!(wait(&mut bootstrap, 200).success());
    assert!(backup.exists());
    assert!(dest.join(TRANSACTION).exists());
    let pid = fs::read_to_string(dest.join("fixture-pid.txt"))
        .unwrap()
        .parse()
        .unwrap();
    vetube_bootstrap::windows::stop_tree(pid).unwrap();
}

#[test]
fn legacy_python_finalizer_protocol_accepts_six_arguments() {
    let sandbox = Sandbox::new();
    let dest = sandbox.directory("dest");
    package(&dest, "ready:0");
    fs::copy(
        env!("CARGO_BIN_EXE_bootstrap"),
        dest.join("bootstrap.next.exe"),
    )
    .unwrap();
    let phase_one = Command::new(env!("CARGO_BIN_EXE_startup-fixture"))
        .arg("--parent")
        .spawn()
        .unwrap();
    let mut phase_one = Running(phase_one);
    phase_one.0.kill().unwrap();
    let _ = phase_one.0.wait(); // exited process with an outstanding handle
    let mut bootstrap = Running(
        Command::new(dest.join("bootstrap.next.exe"))
            .arg("--finalize")
            .arg(phase_one.0.id().to_string())
            .arg(&dest)
            .arg(dest.join("run_main_window.exe"))
            .arg(dest.join("bootstrap.exe"))
            .arg(dest.join("bootstrap.next.exe"))
            .spawn()
            .unwrap(),
    );
    assert!(wait(&mut bootstrap, 15).success());
    let deadline = Instant::now() + Duration::from_secs(10);
    while !dest.join("ready-confirmed.txt").exists() {
        assert!(
            Instant::now() < deadline,
            "relocated finalizer did not confirm startup"
        );
        thread::sleep(Duration::from_millis(20));
    }
    assert!(!dest.join("bootstrap.next.exe").exists());
    assert!(dest.join("bootstrap.exe").exists());
    thread::sleep(Duration::from_millis(250));
}
