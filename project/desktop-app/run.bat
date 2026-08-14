@echo off
echo ========================================
echo   GameMaster - PUBG Controller
echo   Installing dependencies...
echo ========================================
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies.
    echo Make sure Python 3.11+ is installed and in PATH.
    pause
    exit /b 1
)
echo.
echo Starting GameMaster...
python main.py
pause
