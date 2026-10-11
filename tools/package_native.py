"""Write the authoritative program-file list after freezing and any renaming."""

import argparse
import importlib.machinery
import shutil
from pathlib import Path

PROTECTED = {
    "data.json",
    "sounds",
    "voices",
    "engines",
    "logs",
    "keymaps",
    "favoritos.json",
    "mensajes_destacados.json",
    "keys.txt",
}


def package(build_dir, executable, legacy_pyd=False):
    build_dir = Path(build_dir)
    if legacy_pyd:
        suffix = importlib.machinery.EXTENSION_SUFFIXES[0]
        if suffix != ".cp314-win_amd64.pyd":
            raise ValueError("The transition package must use Python 3.14")
        for name in ("_bz2", "_ctypes", "_lzma", "_zstd"):
            short = build_dir / "lib" / f"{name}.pyd"
            long = short.with_name(f"{name}{suffix}")
            if short.exists():
                short.replace(long)
            elif not long.exists():
                raise ValueError(f"Missing compatibility module: {name}")
    shutil.copy2(executable, build_dir / "bootstrap.exe")
    paths = []
    for path in build_dir.rglob("*"):
        relative = path.relative_to(build_dir)
        if path.is_file() and relative.parts[0].lower() not in PROTECTED:
            if path.is_symlink():
                raise ValueError("Package contains a symbolic link")
            paths.append(relative.as_posix())
    paths.append("program-files.txt")
    (build_dir / "program-files.txt").write_text(
        "\n".join(sorted(set(paths))) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("build_dir", type=Path)
    parser.add_argument("--bootstrap", type=Path, default=Path("bootstrap.exe"))
    parser.add_argument("--legacy-pyd", action="store_true")
    args = parser.parse_args()
    package(args.build_dir, args.bootstrap, args.legacy_pyd)
