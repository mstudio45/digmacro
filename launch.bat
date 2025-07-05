@echo off
setlocal enabledelayedexpansion

set "MODE="
set "ACTION="
set "ARGS="

if /i "%1" == "--run-source" set "MODE=source"
if /i "%1" == "--run-standalone" set "MODE=standalone"
if /i "%2" == "--edit" set "ACTION=edit"
if /i "%2" == "--start" set "ACTION=start"

if not defined MODE (
    cls
    echo How would you like to run the program?
    echo   1^) Standalone: A ready-to-use version, simpler to run.
    echo   2^) From Source: For developers or to run the latest code.
    set /p "MODE_CHOICE=Please enter your choice (1 or 2) and press Enter: "
    if "!MODE_CHOICE!"=="1" set "MODE=standalone"
    if "!MODE_CHOICE!"=="2" set "MODE=source"
)

if not defined ACTION (
    echo.
    echo What would you like to do?
    echo   1^) Start the program
    echo   2^) Edit the configuration
    set /p "ACTION_CHOICE=Please enter your choice (1 or 2) and press Enter: "
    if "!ACTION_CHOICE!"=="1" set "ACTION=start"
    if "!ACTION_CHOICE!"=="2" set "ACTION=edit"
)

if "!ACTION!" == "edit" set "ARGS=--edit-config"

echo.
echo Running with mode: !MODE!, action: !ACTION!
echo.

if "!MODE!" == "source" (
    echo Checking for virtual environment...
    if not exist "digmacro_venv" (
        echo Creating virtual environment...
        py -m venv digmacro_venv
    )
    call digmacro_venv\Scripts\activate
    
    echo Starting the src version...
    py src/main.py !ARGS! --mode !MODE!
    goto :end
)

if "!MODE!" == "standalone" (
    echo Starting the built version... This might take a while.
    start "" "%cd%\digmacro.exe" !ARGS! --mode !MODE!
    goto :end
)

:end
pause
endlocal