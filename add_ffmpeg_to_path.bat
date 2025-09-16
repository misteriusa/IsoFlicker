@echo off
setlocal
echo [*] Adding bundled FFmpeg to your user PATH

REM Resolve the repository root based on this script location
set "ROOT=%~dp0"
set "BIN=%ROOT%ffmpeg-7.1-full_build\bin"

if not exist "%BIN%\ffmpeg.exe" (
  echo [!] Bundled FFmpeg not found at: %BIN%
  echo     Make sure the folder ffmpeg-7.1-full_build\bin exists next to this script.
  exit /b 1
)

REM Add to current session immediately
set "PATH=%BIN%;%PATH%"

REM Persist for current user using PowerShell to avoid PATH truncation with setx
powershell -NoProfile -ExecutionPolicy Bypass -Command "^$bin = '%BIN%'; ^$cur = [Environment]::GetEnvironmentVariable('Path','User'); if (-not ^$cur) { ^$cur = '' }; if (^$cur -notlike ('*' + ^$bin + '*')) { [Environment]::SetEnvironmentVariable('Path', (^
  if (^$cur) { ^$cur + ';' + ^$bin } else { ^$bin }), 'User'); Write-Host 'Added to user PATH:' ^$bin } else { Write-Host 'Already present in user PATH:' ^$bin }"

REM Export MoviePy/imageio hints for this session
set "IMAGEIO_FFMPEG_EXE=%BIN%\ffmpeg.exe"
set "FFMPEG_BINARY=%BIN%\ffmpeg.exe"

where ffmpeg >nul 2>&1 && (
  echo [*] Verified ffmpeg is callable in this session.
) || (
  echo [!] Could not verify ffmpeg on PATH in this session.
)

echo.
echo [*] Done. Open a NEW terminal to pick up the persistent PATH change.
exit /b 0

