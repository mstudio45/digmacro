@echo off
setlocal enabledelayedexpansion

set "PY_CMD="

where py >nul 2>nul
if %errorlevel% == 0 (
    set "PY_CMD=py"
)

if not defined PY_CMD (
    where python >nul 2>nul
    if %errorlevel% == 0 (
        set "PY_CMD=python"
    )
)

if not defined PY_CMD (
    echo ERROR: Python is not installed or not in PATH.
    exit /b 1
)

echo Python Command: !PY_CMD!

if not exist "env" (
    mkdir env
)

cd env

if not exist "dev" (
    mkdir dev
)

cd dev

if not exist "Windows" (
    echo Creating virtual environment...
    !PY_CMD! -m venv Windows
)
call "Windows\Scripts\activate"
if errorlevel 1 (
    echo Activation failed, recreating virtual environment...
    rmdir /S /Q "Windows"
    !PY_CMD! -m venv Windows
    call "Windows\Scripts\activate"
)

cd ..
cd ..

echo Starting the src version...
!PY_CMD! src/main.py %*

endlocal