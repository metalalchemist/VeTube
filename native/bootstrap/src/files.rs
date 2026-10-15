//! File installation is independent of Python and of Windows process handles.
use std::collections::BTreeSet;
use std::fs::{self, File, OpenOptions};
use std::io::{self, Write};
use std::path::{Component, Path, PathBuf};

pub const MANIFEST: &str = "program-files.txt";
pub const CLEANUP: &str = "_update_cleanup.txt";
pub const TRANSACTION: &str = "_update_transaction";

fn invalid(message: &str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidInput, message)
}

fn copy_file(source: &Path, target: &Path) -> io::Result<u64> {
    #[cfg(not(miri))]
    {
        fs::copy(source, target)
    }
    #[cfg(miri)]
    {
        // Miri cannot emulate Linux's copy_file_range used by fs::copy.
        // Explicit reads/writes also avoid io::copy's kernel specialization.
        use std::io::Read;
        let mut source = File::open(source)?;
        let permissions = source.metadata()?.permissions();
        let mut target = File::create(target)?;
        let mut buffer = [0; 8192];
        let mut copied = 0;
        loop {
            let count = match source.read(&mut buffer) {
                Err(error) if error.kind() == io::ErrorKind::Interrupted => continue,
                result => result?,
            };
            if count == 0 {
                break;
            }
            target.write_all(&buffer[..count])?;
            copied += count as u64;
        }
        target.set_permissions(permissions)?;
        Ok(copied)
    }
}

pub fn relative(name: &str) -> io::Result<PathBuf> {
    let path = PathBuf::from(name.replace('\\', "/"));
    if name.is_empty()
        || name.contains(['\r', '\n', '\t', ':'])
        || path
            .components()
            .any(|c| !matches!(c, Component::Normal(_)))
    {
        return Err(invalid("invalid manifest path"));
    }
    Ok(path)
}

pub fn protected(path: &Path) -> bool {
    let first = path
        .components()
        .next()
        .unwrap()
        .as_os_str()
        .to_string_lossy()
        .to_lowercase();
    matches!(
        first.as_str(),
        "data.json"
            | "keymaps"
            | "voices"
            | "engines"
            | "logs"
            | "favoritos.json"
            | "mensajes_destacados.json"
            | "keys.txt"
            | "_update_transaction"
            | "_update_cleanup.txt"
            | "_update_leftovers.txt"
            | "_rollback_needed"
    )
}

fn is_link(metadata: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        metadata.file_attributes() & 0x400 != 0 // includes directory junctions
    }
    #[cfg(not(windows))]
    {
        metadata.is_symlink()
    }
}

/// Reject links in every existing ancestor, not just the leaf being copied.
pub fn confined(root: &Path, path: &Path) -> io::Result<PathBuf> {
    let mut result = root.to_path_buf();
    if is_link(&fs::symlink_metadata(root)?) {
        return Err(invalid("installation root is a link"));
    }
    for part in path.components() {
        if !matches!(part, Component::Normal(_)) {
            return Err(invalid("path escapes installation"));
        }
        result.push(part);
        match fs::symlink_metadata(&result) {
            Ok(meta) if is_link(&meta) => return Err(invalid("linked installation path")),
            Ok(_) => (),
            Err(e) if e.kind() == io::ErrorKind::NotFound => (),
            Err(e) => return Err(e),
        }
    }
    Ok(result)
}

pub fn manifest(root: &Path) -> io::Result<BTreeSet<PathBuf>> {
    let path = confined(root, Path::new(MANIFEST))?;
    match fs::read_to_string(path) {
        Ok(text) => text.lines().map(relative).collect(),
        Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(BTreeSet::new()),
        Err(e) => Err(e),
    }
}

fn entries(root: &Path, sub: &Path, out: &mut Vec<PathBuf>) -> io::Result<()> {
    let mut children: Vec<_> = fs::read_dir(root.join(sub))?.collect::<Result<_, _>>()?;
    children.sort_by_key(|entry| entry.file_name());
    for entry in children {
        let path = sub.join(entry.file_name());
        // Validate text paths even when they did not come from a manifest.
        relative(
            path.to_str()
                .ok_or_else(|| invalid("non-Unicode package path"))?,
        )?;
        if protected(&path) {
            continue;
        }
        let meta = fs::symlink_metadata(entry.path())?;
        if is_link(&meta) {
            return Err(invalid("package contains a link"));
        }
        if meta.is_dir() {
            entries(root, &path, out)?;
        } else if meta.is_file() {
            out.push(path);
        } else {
            return Err(invalid("package contains a special file"));
        }
    }
    Ok(())
}

/// A durable journal retains originals until the new app confirms its startup.
/// Rollback touches only files changed by this transaction, never user data.
pub struct Transaction {
    dest: PathBuf,
    storage: PathBuf,
    journal: File,
    changes: Vec<(PathBuf, bool)>,
}

impl Transaction {
    pub fn recover(dest: &Path) -> io::Result<Self> {
        let storage = confined(dest, Path::new(TRANSACTION))?;
        let journal_path = confined(&storage, Path::new("journal.txt"))?;
        if confined(&storage, Path::new("settled"))?.exists() {
            return Err(invalid(
                "transaction already settled; only cleanup is allowed",
            ));
        }
        let text = fs::read_to_string(&journal_path)?;
        let mut changes = Vec::new();
        for line in text.lines() {
            let (kind, name) = line
                .split_once('\t')
                .ok_or_else(|| invalid("invalid recovery journal"))?;
            let path = relative(name)?;
            if protected(&path) && path != Path::new(CLEANUP) {
                return Err(invalid("journal contains user data"));
            }
            match kind {
                "OLD" => changes.push((path, true)),
                "NEW" => changes.push((path, false)),
                _ => return Err(invalid("invalid journal operation")),
            }
        }
        let journal = OpenOptions::new().append(true).open(journal_path)?;
        Ok(Self {
            dest: dest.into(),
            storage,
            journal,
            changes,
        })
    }

    pub fn begin(dest: &Path) -> io::Result<Self> {
        let storage = confined(dest, Path::new(TRANSACTION))?;
        // An interrupted/unconfirmed update must be recovered before another one.
        fs::create_dir(&storage)?;
        let journal = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(storage.join("journal.txt"))?;
        Ok(Self {
            dest: dest.into(),
            storage,
            journal,
            changes: Vec::new(),
        })
    }

    fn save(&mut self, path: &Path) -> io::Result<PathBuf> {
        let target = confined(&self.dest, path)?;
        let existed = target.try_exists()?;
        if existed && !target.is_file() {
            return Err(invalid("file replaced by directory"));
        }
        writeln!(
            self.journal,
            "{}\t{}",
            if existed { "OLD" } else { "NEW" },
            path.display()
        )?;
        self.journal.sync_all()?;
        self.changes.push((path.into(), existed));
        if existed {
            let old = self.storage.join("files").join(path);
            fs::create_dir_all(old.parent().unwrap())?;
            fs::rename(&target, old)?;
        }
        Ok(target)
    }

    pub fn install(&mut self, source: &Path) -> io::Result<()> {
        let mut files = Vec::new();
        entries(source, Path::new(""), &mut files)?;
        let old_manifest = manifest(&self.dest)?;
        let new_manifest = manifest(source)?;
        if new_manifest.is_empty() {
            return Err(invalid("package has no program manifest"));
        }
        let listed: BTreeSet<_> = files
            .iter()
            .filter(|p| !p.starts_with("sounds"))
            .cloned()
            .collect();
        if listed != new_manifest {
            return Err(invalid("program manifest does not match package files"));
        }
        let mut deferred = Vec::new();
        for obsolete in old_manifest.iter().filter(|old| {
            !new_manifest.iter().any(|new| {
                new.to_string_lossy()
                    .eq_ignore_ascii_case(&old.to_string_lossy())
            })
        }) {
            if protected(obsolete) || obsolete.starts_with("sounds") {
                continue;
            }
            let target = confined(&self.dest, obsolete)?;
            if !target.is_file() {
                continue;
            }
            // Stale importable code/runtime must be removed before Python starts.
            if obsolete.starts_with("lib")
                || obsolete
                    .extension()
                    .is_some_and(|e| e == "dll" || e == "pyd" || e == "exe")
            {
                self.save(obsolete)?;
            } else {
                deferred.push(obsolete.to_string_lossy().into_owned());
            }
        }
        for path in files {
            let target = confined(&self.dest, &path)?;
            if path.starts_with("sounds") && target.exists() {
                continue;
            }
            let target = self.save(&path)?;
            fs::create_dir_all(target.parent().unwrap())?;
            copy_file(&source.join(&path), &target)?;
        }
        // This file is consumed only after the application signals readiness.
        let cleanup = self.save(Path::new(CLEANUP))?;
        fs::write(cleanup, deferred.join("\n"))?;
        Ok(())
    }

    pub fn rollback(&mut self) -> io::Result<()> {
        for (path, existed) in self.changes.iter().rev() {
            let target = confined(&self.dest, path)?;
            let old = confined(&self.storage, &Path::new("files").join(path))?;
            if *existed {
                if old.exists() {
                    if target.exists() {
                        fs::remove_file(&target)?;
                    }
                    fs::rename(old, target)?;
                }
            } else if target.exists() {
                fs::remove_file(target)?;
            }
        }
        self.changes.clear();
        self.finish()
    }

    pub fn finish(&self) -> io::Result<()> {
        // Never recover only the subset of originals surviving a partial cleanup.
        let settled = File::create(self.storage.join("settled"))?;
        settled.sync_all()?;
        // The open journal is closed by Drop; Windows allows deletion when its
        // handle shares delete access (Rust's File default).
        fs::remove_dir_all(&self.storage)
    }
}

/// Used only when an older Python bootstrap passed a full backup to --finalize.
/// Overlay immutable program files without deleting user-owned directories.
pub fn restore_snapshot(backup: &Path, dest: &Path) -> io::Result<()> {
    let previous = manifest(backup)?;
    if previous.is_empty() {
        return Err(invalid(
            "backup has no authoritative program manifest; manual recovery required",
        ));
    }
    {
        for introduced in manifest(dest)?.difference(&previous) {
            if protected(introduced) || introduced.starts_with("sounds") {
                continue;
            }
            let target = confined(dest, introduced)?;
            if target.is_file() {
                fs::remove_file(target)?;
            }
        }
    }
    let mut files = Vec::new();
    entries(backup, Path::new(""), &mut files)?;
    for path in files {
        if !previous.contains(&path) {
            continue;
        }
        let target = confined(dest, &path)?;
        if path.starts_with("sounds") {
            continue;
        }
        fs::create_dir_all(target.parent().unwrap())?;
        copy_file(&backup.join(path), &target)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn interrupted_copy_can_be_recovered_from_disk() {
        let root = std::env::temp_dir().join(format!("vetube-recover-{}", std::process::id()));
        fs::create_dir(&root).unwrap();
        let source = root.join("source");
        let dest = root.join("dest");
        fs::create_dir(&source).unwrap();
        fs::create_dir(&dest).unwrap();
        fs::write(dest.join("VERSION"), "old").unwrap();
        fs::write(source.join("VERSION"), "new").unwrap();
        fs::write(source.join(MANIFEST), "VERSION\nprogram-files.txt").unwrap();
        {
            let mut tx = Transaction::begin(&dest).unwrap();
            tx.install(&source).unwrap();
            // Simulate a supervisor that exits without committing/rolling back.
        }
        let mut recovered = Transaction::recover(&dest).unwrap();
        recovered.rollback().unwrap();
        drop(recovered);
        assert_eq!(fs::read_to_string(dest.join("VERSION")).unwrap(), "old");
        assert!(!dest.join(MANIFEST).exists());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_escaping_paths() {
        for path in [
            "",
            "../outside",
            "lib/../../outside",
            "/root",
            "C:\\outside",
            "lib/a\nb",
            "lib/a:b",
        ] {
            assert!(relative(path).is_err(), "{path}");
        }
        assert_eq!(
            relative("lib\\module.pyd").unwrap(),
            Path::new("lib/module.pyd")
        );
    }

    #[test]
    fn interrupted_commit_cannot_be_mistaken_for_pending_installation() {
        let root = std::env::temp_dir().join(format!("vetube-settled-{}", std::process::id()));
        fs::create_dir(&root).unwrap();
        let tx = Transaction::begin(&root).unwrap();
        fs::write(root.join(TRANSACTION).join("settled"), "").unwrap();
        assert!(Transaction::recover(&root).is_err());
        tx.finish().unwrap();
        drop(tx);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn user_data_is_never_managed() {
        for path in [
            "data.json",
            "voices/custom.onnx",
            "engines/sonata/a.dll",
            "logs/vetube.log",
            "keymaps/custom",
        ] {
            assert!(protected(Path::new(path)));
        }
        assert!(!protected(Path::new("lib/module.pyd")));
    }
}
