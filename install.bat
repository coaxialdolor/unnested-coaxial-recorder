@echo off
REM Windows Batch Installer for Coaxial Recorder
REM This is a wrapper that calls the bash install script

echo ================================================================================
echo Coaxial Recorder - Windows Installer
echo ================================================================================
echo.

REM Check if Git Bash is available
where bash >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: bash not found!
    echo.
    echo This installer requires Git Bash, Cygwin, or WSL.
    echo.
    echo Please install one of the following:
    echo   1. Git for Windows ^(includes Git Bash^): https://git-scm.com/download/win
    echo   2. Cygwin: https://www.cygwin.com/
    echo   3. WSL: https://docs.microsoft.com/en-us/windows/wsl/install
    echo.
    echo After installation, run this script again.
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Python not found in PATH!
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    echo Note: Do NOT use the Microsoft Store version of Python.
    echo.
    pause
    echo Continuing anyway, the bash script will check for Python...
    echo.
)

REM Check Python version
python --version 2>nul
if %errorlevel% equ 0 (
    echo Found:
    python --version
    echo.
)

REM Run the bash installer
echo Running bash installer...
echo.
bash install.sh

if %errorlevel% neq 0 (
    echo.
    echo ================================================================================
    echo Installation failed or was cancelled.
    echo ================================================================================
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo Installation completed!
echo ================================================================================
echo.
echo To start the application:
echo   1. Run: launch_complete.bat
echo   2. Or in Git Bash: bash launch_complete.sh
echo.
pause

