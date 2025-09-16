@echo off
set "AUTO=0"
if /I "%~1"=="--auto" set "AUTO=1"

echo [*] FFmpeg Installation Helper for IsoFlicker Pro
echo.

echo [*] Checking for Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] Python not found in PATH. Please install Python 3.x and re-run.
    echo     Download Python from: https://www.python.org/downloads/
    if "%AUTO%"=="0" pause
    exit /b 1
)

echo [*] Activating virtual environment...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to activate virtual environment.
    if "%AUTO%"=="0" pause
    exit /b 1
)

call :EnsureFFmpeg
goto :End

:EnsureFFmpeg
WHERE ffmpeg >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [*] ffmpeg found in PATH. No installation needed.
    goto :EOF
)

echo [!] ffmpeg not found in PATH.
if "%AUTO%"=="1" goto :DownloadFFmpeg

echo.
echo You have two options to install ffmpeg:
echo.
echo 1. Download and install ffmpeg from the official website:
echo    https://ffmpeg.org/download.html
echo.
echo 2. Use a pre-compiled version. We can download it for you.
echo.
SET /P CHOICE=Would you like to download the pre-compiled version now? (y/n): 
IF /I "%CHOICE%"=="y" (
    goto :DownloadFFmpeg
) ELSE (
    echo.
    echo Please download and install ffmpeg manually from:
    echo https://ffmpeg.org/download.html
    echo.
    echo After installation, make sure to add ffmpeg to your system PATH.
    echo.
    goto :EOF
)

:DownloadFFmpeg
echo.
echo [*] Downloading ffmpeg...
if not exist downloads mkdir downloads
if exist downloads\ffmpeg.zip del /f /q downloads\ffmpeg.zip >nul 2>&1
if exist downloads\ffmpeg-master-latest-win64-gpl rd /s /q downloads\ffmpeg-master-latest-win64-gpl >nul 2>&1
python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip', 'downloads/ffmpeg.zip')"
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to download ffmpeg archive.
    goto :InstallFailed
)

echo [*] Extracting ffmpeg...
python -c "import zipfile; zipfile.ZipFile('downloads/ffmpeg.zip').extractall('downloads')"
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to extract ffmpeg archive.
    goto :InstallFailed
)

echo [*] Installing ffmpeg to local application directory...
if not exist bin mkdir bin
xcopy /Y /Q "downloads\ffmpeg-master-latest-win64-gpl\bin\*.exe" "bin\" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Failed to copy ffmpeg binaries.
    goto :InstallFailed
)

if exist "bin\ffmpeg.exe" (
    SET "PATH=%CD%\bin;%PATH%"
    echo [*] ffmpeg has been installed to the bin directory.
    echo     Added bin to PATH for this session.
) ELSE (
    echo [!] ffmpeg executable not found after installation.
    goto :InstallFailed
)

goto :EOF

:InstallFailed
echo [!] Automatic ffmpeg installation failed.
echo     Please install ffmpeg manually or rerun install-ffmpeg.bat.
goto :EOF

:End
if "%AUTO%"=="0" pause
exit /b 0
