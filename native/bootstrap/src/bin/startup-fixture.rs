//! Test-only application; never included in the VeTube package.
#[cfg(windows)]
fn main() {
    use std::{env, fs, thread, time::Duration};
    if env::args().any(|arg| arg == "--parent-tree") {
        let executable = env::current_exe().unwrap();
        let mut child = std::process::Command::new(&executable)
            .arg("--parent")
            .spawn()
            .unwrap();
        fs::write(
            executable.parent().unwrap().join("voice-child-pid.txt"),
            child.id().to_string(),
        )
        .unwrap();
        thread::sleep(Duration::from_secs(300));
        let _ = child.kill();
        let _ = child.wait();
        return;
    }
    if env::args().any(|arg| arg == "--parent") {
        thread::sleep(Duration::from_secs(300));
        return;
    }
    let root = env::current_exe().unwrap().parent().unwrap().to_path_buf();
    let mode = fs::read_to_string(root.join("fixture-mode.txt")).unwrap();
    if let Some(delay) = mode.trim().strip_prefix("ready:") {
        thread::sleep(Duration::from_millis(delay.parse().unwrap()));
        let event =
            vetube_bootstrap::windows::ReadyEvent::open(&env::var("VETUBE_UPDATE_READY").unwrap())
                .unwrap();
        event.signal().unwrap();
        fs::write(root.join("ready-confirmed.txt"), "ready").unwrap();
        thread::sleep(Duration::from_millis(200));
    } else if mode.trim() == "pending" {
        fs::write(root.join("fixture-pid.txt"), std::process::id().to_string()).unwrap();
        thread::sleep(Duration::from_secs(300));
    } else if mode.trim() == "old" {
        assert!(env::var_os("VETUBE_UPDATE_READY").is_none());
        fs::write(root.join("restored.txt"), "old app launched").unwrap();
    }
}

#[cfg(not(windows))]
fn main() {}
