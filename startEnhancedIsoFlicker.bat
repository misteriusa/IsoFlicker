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

REM Use the venv's Python explicitly to avoid PATH issues
set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [!] Virtual environment Python not found at %PYTHON_EXE%
    pause
    exit /b 1
)

echo [*] Upgrading pip, setuptools, wheel...
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel
if %ERRORLEVEL% NEQ 0 (
    echo [!] Warning: Failed to upgrade pip, but continuing anyway...
)

echo [*] Installing required Python packages...
if exist requirements.txt (
    echo     Using requirements.txt
    "%PYTHON_EXE%" -m pip install -r requirements.txt
) else (
    echo     requirements.txt not found. Installing a compatible set directly...
    "%PYTHON_EXE%" -m pip install PyQt5==5.15.9 moviepy==2.2.1 librosa==0.11.0 numpy==2.2.6 scipy==1.15.3 ffmpeg-python==0.2.0 soundfile==0.13.1 pydub==0.25.1 opencv-python==4.12.0.88 Pillow==11.3.0
)
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to install required packages.
    pause
    exit /b 1
)

echo [*] Checking for ffmpeg...
WHERE ffmpeg >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] ffmpeg not found in PATH.

    echo [*] Attempting to automatically install ffmpeg...
    if exist install-ffmpeg.bat (
        call install-ffmpeg.bat --auto
    ) else (
        echo [!] install-ffmpeg.bat script not found. Unable to install ffmpeg automatically.
    )
    WHERE ffmpeg >nul 2>&1
    IF %ERRORLEVEL% EQU 0 (
        echo [*] ffmpeg installed successfully.
        if exist bin\ffmpeg.exe (
            SET "PATH=%CD%\bin;%PATH%"
        )
    ) ELSE (
        REM Fallback to bundled/local copies if available
        if exist bin\ffmpeg.exe (
            echo [*] Using local ffmpeg in bin
            SET "PATH=%CD%\bin;%PATH%"
        ) else if exist ffmpeg-7.1-full_build\bin\ffmpeg.exe (
            echo [*] Using bundled ffmpeg in ffmpeg-7.1-full_build\bin
            SET "PATH=%CD%\ffmpeg-7.1-full_build\bin;%PATH%"
        ) else (
            echo [!] WARNING: ffmpeg is required for video processing.
            echo     Please install it manually from https://ffmpeg.org/download.html
            echo.
            echo     Continuing without ffmpeg, but video processing may fail.
            echo.
        )
    )
) ELSE (
    echo [*] ffmpeg found in PATH.
)

echo [*] Checking for required files...
set MISSING=0
for %%F in (starter.py integrated_isoflicker.py isoFlickerGUI.py sine_widget.py sine_editor_with_xml.py text_overlay.py file_optimizer.py preset_converter.py advanced_isochronic_generator.py) do (
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
"%PYTHON_EXE%" starter.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Application exited with an error. Please see above messages for details.
) else (
    echo [*] Application closed successfully.
)

echo.
pause
