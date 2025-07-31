@echo off
setlocal

:: burpdrop.bat
:: Launcher script for burpDrop.py on Windows.

:: Get the directory where this batch script is located
set "SCRIPT_DIR=%~dp0"

:: Path to the main Python script
set "PYTHON_SCRIPT=%SCRIPT_DIR%burpDrop.py"

:: --- Check for Python ---
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not found in your PATH.
    echo Please install Python and ensure it's accessible.
    goto :eof
)

:: --- Install Python Dependencies (Optional but Recommended) ---
:: This part can be uncommented if you want the launcher to
:: automatically install dependencies if they are missing.
:: However, for a cleaner setup, it's often better to instruct
:: the user to run 'pip install -r requirements.txt' manually.
::
:: echo Installing/updating Python dependencies...
:: python -m pip install -r "%SCRIPT_DIR%requirements.txt"
:: if %errorlevel% neq 0 (
::     echo ❌ Failed to install Python dependencies. Please run 'pip install -r requirements.txt' manually.
::     goto :eof
:: )

:: --- Execute the Python script ---
echo 🚀 Launching burpDrop...
python "%PYTHON_SCRIPT%" %*

endlocal
