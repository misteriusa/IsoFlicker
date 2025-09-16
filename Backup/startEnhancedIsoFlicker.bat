@echo off
echo [*] IsoFlicker Pro Startup
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
pip install PyQt5==5.15.9 moviepy==2.0.0.dev2 librosa==0.10.1 numpy==1.24.3 scipy==1.10.1 ffmpeg-python==0.2.0 soundfile==0.12.1 pydub
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to install required packages.
    pause
    exit /b 1
)

echo [*] Checking for ffmpeg...
WHERE ffmpeg >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] ffmpeg not found in PATH.
    
    REM Check if we have a local installation
    if exist bin\ffmpeg.exe (
        echo [*] Using local ffmpeg installation...
        SET "PATH=%CD%\bin;%PATH%"
    ) else (
        echo [!] WARNING: ffmpeg is required for video processing.
        echo     Run install-ffmpeg.bat to install it, or download from:
        echo     https://ffmpeg.org/download.html
        echo.
        echo     Continuing without ffmpeg, but video processing may fail.
        echo.
    )
) ELSE (
    echo [*] ffmpeg found in PATH.
)

echo [*] Checking for required files...
set MISSING=0
for %%F in (isoFlickerGUI.py advanced_isochronic_generator.py isochronic_timeline.py sine_editor.py integrated_isoflicker.py) do (
    if not exist %%F (
        echo [!] Missing required file: %%F
        set MISSING=1
    )
)

if %MISSING% NEQ 0 (
    echo [!] Some required files are missing. Please ensure you have all program files.
    pause
    exit /b 1
)

echo [*] Running Integrated IsoFlicker Pro with SINE Editor...
python starter.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Application exited with an error. Please see above messages for details.
) else (
    echo [*] Application closed successfully.
)

echo.
pause