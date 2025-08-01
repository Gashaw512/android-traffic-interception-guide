@echo off
setlocal

:: Set UTF-8 support
chcp 65001 > nul
set PYTHONUTF8=1

:: Get script directory
set "SCRIPT_DIR=%~dp0"

:: Path to Python script
set "PYTHON_SCRIPT=%SCRIPT_DIR%burpDrop.py"

:: Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python not found in PATH
    echo Please install Python: https://www.python.org/downloads/
    pause
    goto :eof
)

:: Check dependencies
echo Checking dependencies...
python -m pip install -r "%SCRIPT_DIR%requirements.txt" > nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Warning: Failed to install some dependencies
    echo Continuing anyway...
)

:: Launch application
echo 🚀 Starting burpDrop...
python "%PYTHON_SCRIPT%" %*

endlocal