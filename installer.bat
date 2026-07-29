@echo off
Title TurboOne Setup & Launcher
color 0b
echo ===================================================
echo             TurboOne Setup & Launcher
echo ===================================================
echo.

REM 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [+] Python not found! Downloading and installing Python...
    echo [+] Please follow the Python installer window and MAKE SURE to check "Add Python to PATH".
    
    :: Download Python official installer
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    
    :: Run installer
    "%TEMP%\python_installer.exe"
    
    echo [+] Please restart this batch script after Python installation completes!
    pause
    exit
) else (
    echo [OK] Python is already installed.
)

echo.
echo [+] Installing/Upgrading required dependencies...
python -m pip install --upgrade pip
python -m pip install vgamepad XInput-Python

echo.
echo [+] Downloading latest version of TurboOne...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/easytypeneocitiesorg-lgtm/TurboOne/refs/heads/main/TurboOne.py' -OutFile 'TurboOne.py'"

echo.
echo ===================================================
echo [SUCCESS] Setup complete! Launching TurboOne...
echo ===================================================
timeout /t 2 >nul

start python TurboOne.py
exit