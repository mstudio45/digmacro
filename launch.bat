@echo off
setlocal enabledelayedexpansion

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
    py -m venv Windows
)
call Windows\Scripts\activate

cd ..
cd ..

echo Starting the src version...
py src/main.py

pause
endlocal