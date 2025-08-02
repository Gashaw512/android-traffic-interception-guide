@echo off
setlocal

:: Set UTF-8 support
chcp 65001 > nul
set PYTHONUTF8=1

:: Get the directory of the batch file
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%scripts\main.py"

:: Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python not found in PATH
    pause
    goto :eof
)

:: Check dependencies
echo Checking dependencies...
python -m pip install -r "%SCRIPT_DIR%scripts\requirements.txt" > nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Warning: Failed to install some dependencies
)

:: Launch the application
echo 🚀 Starting burpDrop...
python "%PYTHON_SCRIPT%" %*

endlocal