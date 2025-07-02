@echo off
IF Exist "%cd%\src\main.py" (
    echo Starting the src version of mstudio45/digmacro...
    py src/main.py
    goto stop
)

IF Exist "%cd%\digmacro.exe" (
    echo Starting the builded version of mstudio45/digmacro...
    start "%cd%\digmacro.exe"
    goto stop
)

echo src/main.py and digmacro.exe don't exist.
pause

:stop
echo Closing...