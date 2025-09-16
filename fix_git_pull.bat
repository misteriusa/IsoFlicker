@echo off
cls
echo ====================================================
echo     IsoFlicker Git Pull Fix - Interactive Script
echo ====================================================
echo.

echo This script will help you fix git pull issues.
echo.

echo Current status:
echo ==============
git status
echo.

echo Checking remote configuration:
echo ==========================
git remote -v
echo.

echo If no remote is shown above, you need to configure one.
echo.

echo Solution Options:
echo ================
echo 1. Connect to existing remote repository
echo    git remote add origin [YOUR_REPOSITORY_URL]
echo.
echo 2. After adding remote, fetch and set upstream:
echo    git fetch origin
echo    git branch --set-upstream-to=origin/main main
echo.
echo 3. Then you can pull:
echo    git pull
echo.

echo Helper Scripts:
echo =============
echo Run 'python setup_git_remote.py' for interactive setup
echo.

echo Press any key to continue...
pause >nul

cls
echo.
echo For detailed instructions, see GIT_FIX_README.md
echo.
echo Example workflow:
echo ================
echo 1. Create repository on GitHub/GitLab
echo 2. Copy the repository URL
echo 3. Run: git remote add origin [PASTE_URL_HERE]
echo 4. Run: git fetch origin
echo 5. Run: git branch --set-upstream-to=origin/main main
echo 6. Run: git pull
echo.
pause