@echo off
setlocal enabledelayedexpansion

echo Checking for virtual environment...
if not exist "digmacro_venv_Windows" (
    echo Creating virtual environment...
    py -m venv digmacro_venv_Windows
)
call digmacro_venv_Windows\Scripts\activate

echo Starting the src version...
py src/main.py

pause
endlocal