//! All owned Win32 handles are closed by Drop, including every error path.
use std::ffi::OsStr;
use std::io;
use std::os::windows::ffi::OsStrExt;
use std::os::windows::io::AsRawHandle;
use std::process::Child;
use std::ptr;
use windows_sys::Win32::Foundation::*;
use windows_sys::Win32::System::Diagnostics::ToolHelp::*;
use windows_sys::Win32::System::Threading::*;

pub struct Handle(HANDLE);

impl Handle {
    fn owned(raw: HANDLE) -> io::Result<Self> {
        if raw.is_null() || raw == INVALID_HANDLE_VALUE {
            Err(io::Error::last_os_error())
        } else {
            Ok(Self(raw))
        }
    }
}

impl Drop for Handle {
    fn drop(&mut self) {
        // SAFETY: Handle owns a valid non-pseudo handle, closed exactly once.
        unsafe {
            CloseHandle(self.0);
        }
    }
}

pub struct ReadyEvent(Handle);

#[derive(Debug, PartialEq, Eq)]
pub enum Startup {
    Ready,
    Exited,
    Pending,
}

impl ReadyEvent {
    pub fn open(name: &str) -> io::Result<Self> {
        let name: Vec<u16> = OsStr::new(name).encode_wide().chain(Some(0)).collect();
        // SAFETY: NUL-terminated name lives through the call; Handle owns result.
        Handle::owned(unsafe { OpenEventW(EVENT_MODIFY_STATE, 0, name.as_ptr()) }).map(Self)
    }
    pub fn create(name: &str) -> io::Result<Self> {
        let name: Vec<u16> = OsStr::new(name).encode_wide().chain(Some(0)).collect();
        // SAFETY: name is NUL-terminated and lives through the call. Default
        // security attributes; the returned event is owned by Handle.
        let raw = unsafe { CreateEventW(ptr::null(), 1, 0, name.as_ptr()) };
        let handle = Handle::owned(raw)?;
        // SAFETY: GetLastError has no pointer arguments and follows CreateEventW.
        if unsafe { GetLastError() } == ERROR_ALREADY_EXISTS {
            return Err(io::Error::new(
                io::ErrorKind::AlreadyExists,
                "ready event already exists",
            ));
        }
        Ok(Self(handle))
    }

    pub fn wait(&self, child: &Child, timeout_ms: u32) -> io::Result<Startup> {
        // Prefer readiness if both handles are signalled (a normal quick exit
        // immediately after successful initialization must not trigger rollback).
        let handles = [self.0.0, child.as_raw_handle()];
        // SAFETY: both handles remain owned/live for the whole blocking wait.
        match unsafe { WaitForMultipleObjects(2, handles.as_ptr(), 0, timeout_ms) } {
            WAIT_OBJECT_0 => Ok(Startup::Ready),
            value if value == WAIT_OBJECT_0 + 1 => Ok(Startup::Exited),
            WAIT_TIMEOUT => Ok(Startup::Pending),
            _ => Err(io::Error::last_os_error()),
        }
    }

    pub fn signal(&self) -> io::Result<()> {
        // SAFETY: the event handle is valid and still owned by self.
        if unsafe { SetEvent(self.0.0) } == 0 {
            Err(io::Error::last_os_error())
        } else {
            Ok(())
        }
    }
}

fn process(pid: u32, access: u32) -> io::Result<Option<Handle>> {
    // SAFETY: OpenProcess has value arguments; a successful handle is owned.
    let raw = unsafe { OpenProcess(access, 0, pid) };
    if raw.is_null() {
        let error = io::Error::last_os_error();
        if error.raw_os_error() == Some(ERROR_INVALID_PARAMETER as i32) {
            Ok(None)
        } else {
            Err(error)
        }
    } else {
        Handle::owned(raw).map(Some)
    }
}

pub fn wait_for_exit(pid: u32, timeout_ms: u32) -> io::Result<()> {
    if let Some(handle) = process(pid, PROCESS_SYNCHRONIZE)? {
        // SAFETY: the process handle remains live throughout the wait.
        if unsafe { WaitForSingleObject(handle.0, timeout_ms) } != WAIT_OBJECT_0 {
            return Err(io::Error::new(
                io::ErrorKind::TimedOut,
                "process did not exit",
            ));
        }
    }
    Ok(())
}

/// Snapshot descendants and open their handles BEFORE stopping the parent.
/// Using held handles prevents PID reuse from terminating an unrelated process.
pub fn stop_tree(pid: u32) -> io::Result<()> {
    if pid == 0 || pid == std::process::id() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "invalid VeTube PID",
        ));
    }
    // SAFETY: value arguments; snapshot ownership immediately transferred.
    let snapshot = Handle::owned(unsafe { CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0) })?;
    // SAFETY: PROCESSENTRY32W is a C struct whose fields admit all-zero values.
    let mut entry: PROCESSENTRY32W = unsafe { std::mem::zeroed() };
    entry.dwSize = std::mem::size_of::<PROCESSENTRY32W>() as u32;
    let mut all = Vec::new();
    // SAFETY: snapshot is valid and entry has the required initialized size.
    let mut found = unsafe { Process32FirstW(snapshot.0, &mut entry) };
    while found != 0 {
        all.push((entry.th32ProcessID, entry.th32ParentProcessID));
        // SAFETY: same valid snapshot and writable entry as above.
        found = unsafe { Process32NextW(snapshot.0, &mut entry) };
    }
    let mut pids = vec![pid];
    let mut index = 0;
    while index < pids.len() {
        let parent = pids[index];
        for &(child, owner) in &all {
            if owner == parent && child != std::process::id() && !pids.contains(&child) {
                pids.push(child);
            }
        }
        index += 1;
    }
    let mut handles = Vec::new();
    for pid in pids {
        if let Some(handle) = process(pid, PROCESS_TERMINATE | PROCESS_SYNCHRONIZE)? {
            handles.push(handle);
        }
    }
    for handle in &handles {
        // SAFETY: held process handles have TERMINATE and SYNCHRONIZE rights.
        unsafe {
            if WaitForSingleObject(handle.0, 0) == WAIT_OBJECT_0 {
                continue;
            }
            if TerminateProcess(handle.0, 1) == 0 {
                return Err(io::Error::last_os_error());
            }
        }
    }
    for handle in &handles {
        // SAFETY: all process handles remain owned until all waits complete.
        if unsafe { WaitForSingleObject(handle.0, 30_000) } != WAIT_OBJECT_0 {
            return Err(io::Error::new(
                io::ErrorKind::TimedOut,
                "VeTube child still running",
            ));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use windows_sys::Win32::System::ProcessStatus::{
        GetProcessMemoryInfo, PROCESS_MEMORY_COUNTERS_EX,
    };
    use windows_sys::Win32::System::Threading::{GetCurrentProcess, GetProcessHandleCount};

    #[test]
    fn repeated_events_do_not_leak_handles() {
        fn private_bytes() -> usize {
            // SAFETY: the C struct admits zero initialization.
            let mut counters: PROCESS_MEMORY_COUNTERS_EX = unsafe { std::mem::zeroed() };
            counters.cb = std::mem::size_of_val(&counters) as u32;
            // SAFETY: correctly sized writable structure and current-process handle.
            let result = unsafe {
                GetProcessMemoryInfo(
                    GetCurrentProcess(),
                    (&mut counters as *mut PROCESS_MEMORY_COUNTERS_EX).cast(),
                    counters.cb,
                )
            };
            assert_ne!(result, 0);
            counters.PrivateUsage
        }
        fn count() -> u32 {
            let mut count = 0;
            // SAFETY: current-process pseudo handle is valid; count is writable.
            assert_ne!(
                // SAFETY: valid pseudo handle and writable count, as above.
                unsafe { GetProcessHandleCount(GetCurrentProcess(), &mut count) },
                0
            );
            count
        }
        let before = count();
        for i in 0..2000 {
            let event =
                ReadyEvent::create(&format!("Local\\VeTubeLeakTest-{}-{i}", std::process::id()))
                    .unwrap();
            event.signal().unwrap();
            let opened =
                ReadyEvent::open(&format!("Local\\VeTubeLeakTest-{}-{i}", std::process::id()))
                    .unwrap();
            opened.signal().unwrap();
            assert!(
                ReadyEvent::create(&format!("Local\\VeTubeLeakTest-{}-{i}", std::process::id()))
                    .is_err()
            );
            let _process = process(std::process::id(), PROCESS_SYNCHRONIZE).unwrap();
        }
        assert!(count() <= before + 2, "event handles accumulated");
        let warmed = private_bytes();
        for i in 0..20_000 {
            let event = ReadyEvent::create(&format!(
                "Local\\VeTubeMemoryTest-{}-{i}",
                std::process::id()
            ))
            .unwrap();
            event.signal().unwrap();
            let _process = process(std::process::id(), PROCESS_SYNCHRONIZE).unwrap();
        }
        let final_bytes = private_bytes();
        let final_handles = count();
        eprintln!(
            "Win32 soak: handles {before} -> {final_handles}; private bytes {warmed} -> {final_bytes}"
        );
        assert!(
            final_bytes <= warmed + 4 * 1024 * 1024,
            "private memory grew after warmup"
        );
        assert!(final_handles <= before + 2, "process handles accumulated");
    }
}
