@echo off
echo [*] IsoFlicker Setup
echo.

echo [*] Checking for Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] Python not found in PATH. Please install Python 3.x and re-run.
    echo     Download Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [*] Checking Python version...
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYVER=%%I
echo     Detected Python %PYVER%

echo [*] Ensuring virtual environment exists...
if not exist venv (
    echo [*] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [!] Failed to create virtual environment.
        echo     Try installing the venv module: python -m pip install virtualenv
        pause
        exit /b 1
    )
)

echo [*] Activating virtual environment...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [*] Upgrading pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo [!] Warning: Failed to upgrade pip, but continuing anyway...
)

echo [*] Installing required Python packages...
pip install PyQt6 numpy opencv-python-headless pillow tqdm imageio librosa
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to install required packages.
    pause
    exit /b 1
)

echo [*] Setup completed successfully!
echo [*] You can now run the application with: python isoFlickerGUI.py
echo.

pause