@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0.deps" set "PYTHONPATH=%~dp0.deps;%PYTHONPATH%"
set "RHS_PYTHON="
rem Prefer an available Python that can actually launch the application.
if exist "%~dp0runtime\python.exe" (
    "%~dp0runtime\python.exe" -c "import tkinter, numpy" >nul 2>&1
    if not errorlevel 1 set RHS_PYTHON="%~dp0runtime\python.exe"
)
if not defined RHS_PYTHON (
    py -3 -c "import tkinter, numpy" >nul 2>&1
    if not errorlevel 1 set "RHS_PYTHON=py -3"
)
if not defined RHS_PYTHON (
    python -c "import tkinter, numpy" >nul 2>&1
    if not errorlevel 1 set "RHS_PYTHON=python"
)
if not defined RHS_PYTHON if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -c "import tkinter, numpy" >nul 2>&1
    if not errorlevel 1 set RHS_PYTHON="%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)
rem If no ready environment was found, pick Python for useful diagnostics.
if not defined RHS_PYTHON (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "RHS_PYTHON=py -3"
)
if not defined RHS_PYTHON (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 set "RHS_PYTHON=python"
)
if not defined RHS_PYTHON (
    echo Python 3 was not found. Install Python 3 from python.org.
    echo See README_V3.md.
    pause
    exit /b 1
)
if not exist "app.py" (
    echo app.py was not found in this folder.
    pause
    exit /b 1
)
%RHS_PYTHON% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo Tkinter was not found in this Python installation.
    echo Reinstall Python with Tcl/Tk.
    pause
    exit /b 1
)
%RHS_PYTHON% -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo NumPy is required.
    echo Open a terminal in this folder and run:
    echo %RHS_PYTHON% -m pip install -r requirements.txt --target .deps
    pause
    exit /b 1
)
%RHS_PYTHON% app.py
if errorlevel 1 (
    echo The application stopped with an error.
    pause
    exit /b 1
)
endlocal
