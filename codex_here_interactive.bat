@echo off
setlocal enabledelayedexpansion

REM Use the folder where this script lives as the workspace
cd /d "%~dp0"
set "WIN_DIR=%cd%"

REM Convert Windows path to WSL path
for /f "usebackq delims=" %%i in (`wsl wslpath -a "%WIN_DIR%"`) do set "WSL_DIR=%%i"

REM Open an interactive Ubuntu shell in that folder and start Codex.
REM When Codex exits, leave you in the shell.
wsl bash -ic "command -v codex >/dev/null 2>&1 || { echo 'codex not found in WSL PATH.'; exit 127; }; cd \"$WSL_DIR\"; echo Using workspace: \"$WSL_DIR\"; codex; echo Codex finished. Dropping to interactive shell...; exec bash -i"

if %errorlevel% neq 0 (
  echo.
  echo [!] Codex exited with a non-zero status. See output above.
  pause
)
