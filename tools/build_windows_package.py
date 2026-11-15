"""Create a portable Windows ZIP from a Python.org-style installation.

Run after installing the project's requirements into .deps.  The ZIP includes
Python, Tcl/Tk, NumPy and their licenses; it does not change the interpreter or
install anything system-wide.
"""
from __future__ import annotations

import os
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "dist" / "RawHostileSelect-Windows.zip"
FILES = (
    "app.py", "arena_engine.py", "hostile_protocol_evolution.py",
    "START_RawHostileSelect.bat", "README.md", "README_V3.md",
    "requirements.txt", "LICENSE", "index.html", "download",
)


def main(destination: Path = DESTINATION) -> None:
    if os.name != "nt":
        raise SystemExit("A Windows Python installation is required.")
    source = Path(sys.base_prefix)
    deps = ROOT / ".deps"
    if not (deps / "numpy").is_dir():
        raise SystemExit("Install requirements into .deps before packaging.")
    if destination.exists():
        raise SystemExit(f"Refusing to overwrite {destination}")
    if destination.suffix.lower() != ".zip":
        raise SystemExit("Output filename must end in .zip")
    for required in ("python.exe", "DLLs", "Lib", "tcl", "LICENSE.txt"):
        if not (source / required).exists():
            raise SystemExit(f"Missing Python runtime component: {source / required}")

    with tempfile.TemporaryDirectory(prefix="rawhostileselect-") as temp:
        package = Path(temp) / "RawHostileSelect"
        # Keep the extracted folder simple: one visible launcher and one
        # directory containing the program and its bundled dependencies.
        internal = package / "Program files"
        runtime = internal / "runtime"
        runtime.mkdir(parents=True)
        for name in FILES:
            shutil.copy2(ROOT / name, internal / name)
        shutil.copy2(internal / "START_RawHostileSelect.bat", internal / "START_INTERNAL.bat")
        (package / "START THE APP.bat").write_text(
            '@echo off\ncall "%~dp0Program files\\START_INTERNAL.bat"\n',
            encoding="ascii", newline="\r\n")
        for item in source.iterdir():
            if item.is_file() and (item.name in ("python.exe", "pythonw.exe", "LICENSE.txt")
                                   or item.suffix.lower() == ".dll"):
                shutil.copy2(item, runtime / item.name)
        ignore = shutil.ignore_patterns("site-packages", "__pycache__", "test", "*.pyc")
        for name in ("DLLs", "Lib", "tcl"):
            shutil.copytree(source / name, runtime / name, ignore=ignore)
        shutil.copytree(deps, internal / ".deps", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        env = dict(os.environ, PYTHONPATH=str(internal / ".deps"))
        subprocess.run([str(runtime / "python.exe"), "-c", "import tkinter, numpy, app"],
                       cwd=internal, env=env, check=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        archive = shutil.make_archive(str(destination.with_suffix("")), "zip", temp, "RawHostileSelect")
        print(f"Created {archive}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DESTINATION)
    main(parser.parse_args().output)
