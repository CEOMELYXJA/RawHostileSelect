"""Create a portable Windows ZIP from a Python.org-style installation.

Run after installing the project's requirements into .deps.  The ZIP includes
Python, Tcl/Tk, NumPy and their licenses; it does not change the interpreter or
install anything system-wide.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "dist" / "RawHostileSelect-Windows.zip"
FILES = (
    "app.py", "arena_engine.py", "hostile_protocol_evolution.py",
    "Démarrer_RawHostileSelect.bat", "README.md", "README_V3.md",
    "requirements.txt", "LICENSE", "index.html", "download",
)


def main() -> None:
    if os.name != "nt":
        raise SystemExit("A Windows Python installation is required.")
    source = Path(sys.base_prefix)
    deps = ROOT / ".deps"
    if not (deps / "numpy").is_dir():
        raise SystemExit("Install requirements into .deps before packaging.")
    if DESTINATION.exists():
        raise SystemExit(f"Refusing to overwrite {DESTINATION}")
    for required in ("python.exe", "DLLs", "Lib", "tcl", "LICENSE.txt"):
        if not (source / required).exists():
            raise SystemExit(f"Missing Python runtime component: {source / required}")

    with tempfile.TemporaryDirectory(prefix="rawhostileselect-") as temp:
        package = Path(temp) / "RawHostileSelect"
        runtime = package / "runtime"
        runtime.mkdir(parents=True)
        for name in FILES:
            shutil.copy2(ROOT / name, package / name)
        for item in source.iterdir():
            if item.is_file() and (item.name in ("python.exe", "pythonw.exe", "LICENSE.txt")
                                   or item.suffix.lower() == ".dll"):
                shutil.copy2(item, runtime / item.name)
        ignore = shutil.ignore_patterns("site-packages", "__pycache__", "test", "*.pyc")
        for name in ("DLLs", "Lib", "tcl"):
            shutil.copytree(source / name, runtime / name, ignore=ignore)
        shutil.copytree(deps, package / ".deps", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        env = dict(os.environ, PYTHONPATH=str(package / ".deps"))
        subprocess.run([str(runtime / "python.exe"), "-c", "import tkinter, numpy, app"],
                       cwd=package, env=env, check=True)
        DESTINATION.parent.mkdir(exist_ok=True)
        archive = shutil.make_archive(str(DESTINATION.with_suffix("")), "zip", temp, "RawHostileSelect")
        print(f"Created {archive}")


if __name__ == "__main__":
    main()
