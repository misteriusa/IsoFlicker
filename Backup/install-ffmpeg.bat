@echo off
echo [*] FFmpeg Installation Helper for IsoFlicker Pro
echo.

echo [*] Checking for Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] Python not found in PATH. Please install Python 3.x and re-run.
    echo     Download Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [*] Activating virtual environment...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [*] Checking for ffmpeg...
WHERE ffmpeg >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] ffmpeg not found in PATH.
    echo.
    echo You have two options to install ffmpeg:
    echo.
    echo 1. Download and install ffmpeg from the official website:
    echo    https://ffmpeg.org/download.html
    echo.
    echo 2. Use a pre-compiled version. We can download it for you.
    echo.
    
    SET /P CHOICE="Would you like to download the pre-compiled version now? (y/n): "
    IF /I "%CHOICE%"=="y" (
        echo.
        echo [*] Downloading ffmpeg...
        
        REM Create downloads directory if it doesn't exist
        if not exist downloads mkdir downloads
        
        REM Download ffmpeg using Python
        python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip', 'downloads/ffmpeg.zip')"
        
        echo [*] Extracting ffmpeg...
        
        REM Extract using Python
        python -c "import zipfile; zipfile.ZipFile('downloads/ffmpeg.zip').extractall('downloads')"
        
        echo [*] Installing ffmpeg to local application directory...
        
        REM Create bin directory if it doesn't exist
        if not exist bin mkdir bin
        
        REM Move the executable to the bin directory
        copy "downloads\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" "bin\ffmpeg.exe"
        
        echo [*] Adding ffmpeg to PATH for this session...
        
        REM Add the bin directory to the PATH for the current session
        SET "PATH=%CD%\bin;%PATH%"
        
        echo.
        echo [*] ffmpeg has been installed to the bin directory.
        echo     You can now run IsoFlicker Pro using startEnhancedIsoFlicker.bat
        echo.
        
    ) ELSE (
        echo.
        echo Please download and install ffmpeg manually from:
        echo https://ffmpeg.org/download.html
        echo.
        echo After installation, make sure to add ffmpeg to your system PATH.
        echo.
    )
) ELSE (
    echo [*] ffmpeg found in PATH. No installation needed.
)

pause
