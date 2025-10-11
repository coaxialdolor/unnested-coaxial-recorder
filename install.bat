@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo    Coaxial Recorder - Windows Installer
echo ================================================================================
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo [1/5] Checking for bash (Git Bash/Cygwin/WSL)...
where bash >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: bash not found!
    echo.
    echo Please install Git Bash, Cygwin, or WSL first:
    echo   - Git for Windows: https://git-scm.com/download/win
    echo   - Cygwin: https://www.cygwin.com/
    echo.
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)
echo    Found bash: OK
echo.

echo [2/5] Checking for Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Python not in PATH
    echo.
    echo Install Python from https://www.python.org/downloads/
    echo Check "Add Python to PATH" during installation!
    echo.
    echo Continuing anyway - bash script will check more thoroughly...
    echo.
) else (
    python --version
)
echo.

echo [3/5] Verifying install.sh exists...
if not exist "install.sh" (
    echo.
    echo ERROR: install.sh not found!
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)
echo    Found install.sh: OK
echo.

echo [4/5] Launching bash installer...
echo.
echo ================================================================================
bash.exe install.sh
set INSTALL_EXIT_CODE=!errorlevel!
echo ================================================================================
echo.

echo [5/5] Checking installation result...
if !INSTALL_EXIT_CODE! neq 0 (
    echo.
    echo ERROR: Installation failed or was cancelled
    echo Exit code: !INSTALL_EXIT_CODE!
    echo.
    echo Try running directly in Git Bash: bash install.sh
    echo.
    pause
    exit /b !INSTALL_EXIT_CODE!
)

echo.
echo ================================================================================
echo    Installation Complete!
echo ================================================================================
echo.
echo To start the application:
echo   1. Double-click: launch_complete.bat
echo   2. Or in Git Bash: bash launch_complete.sh
echo.
echo Then open your browser to: http://localhost:8000
echo.
pause
