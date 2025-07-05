@echo off
setlocal enabledelayedexpansion

echo Checking for virtual environment...
if not exist "digmacro_venv" (
    echo Creating virtual environment...
    py -m venv digmacro_venv
)
call digmacro_venv\Scripts\activate

echo Starting the src version...
py src/main.py

pause
endlocal