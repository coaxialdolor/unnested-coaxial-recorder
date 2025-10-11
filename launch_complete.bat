@echo off
echo Activating virtual environment...
call venv\Scripts\activate

echo Checking training dependencies...
python test_installation.py

if %errorlevel% neq 0 (
    echo ⚠️  Some training dependencies are missing. Training features may not work.
    echo You can still use recording and post-processing features.
)

echo 🚀 Launching Coaxial Recorder...
python app.py
pause
