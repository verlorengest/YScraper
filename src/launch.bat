@echo off
setlocal

REM --- Configuration ---
set "VENV_NAME=venv"
set "PYTHON_SCRIPT=YScraper.py"
set "REQUIREMENTS_FILE=requirements.txt"

REM --- Check for Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not found in your PATH.
    echo Please install Python ^(e.g., from https://www.python.org/downloads/^) and ensure it's added to your PATH.
    pause
    exit /b 1
)

REM --- Check for virtual environment ---
if not exist "%VENV_NAME%\Scripts\activate.bat" (
    echo Creating virtual environment '%VENV_NAME%'...
    python -m venv "%VENV_NAME%"
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment '%VENV_NAME%' already exists.
)

REM --- Activate virtual environment ---
echo Activating virtual environment...
call "%VENV_NAME%\Scripts\activate.bat"
if not defined VIRTUAL_ENV (
    echo Failed to activate virtual environment.
    echo Make sure '%VENV_NAME%\Scripts\activate.bat' exists and works.
    pause
    exit /b 1
)
echo Virtual environment activated.

REM --- Install requirements ---
if not exist "%REQUIREMENTS_FILE%" (
    echo WARNING: '%REQUIREMENTS_FILE%' not found. Skipping dependency installation.
    echo If the script fails, please create '%REQUIREMENTS_FILE%' with the necessary packages.
) else (
    echo Installing dependencies from '%REQUIREMENTS_FILE%'...
    pip install -r "%REQUIREMENTS_FILE%"
    if errorlevel 1 (
        echo Failed to install requirements. Please check '%REQUIREMENTS_FILE%' and your internet connection.
        pause
        exit /b 1
    )
    echo Dependencies installed successfully.
)

REM --- Launch the Python script ---
if not exist "%PYTHON_SCRIPT%" (
    echo ERROR: Python script '%PYTHON_SCRIPT%' not found in the current directory.
    pause
    exit /b 1
)

echo Launching %PYTHON_SCRIPT%...
python "%PYTHON_SCRIPT%"
if errorlevel 1 (
    echo %PYTHON_SCRIPT% exited with an error.
) else (
    echo %PYTHON_SCRIPT% finished.
)

REM --- Deactivate (optional, happens automatically on script exit) ---
REM call deactivate

echo.
echo Script execution complete.
pause
endlocal
exit /b 0