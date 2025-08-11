@echo off
setlocal enabledelayedexpansion

set "BUILD_VERSION=MATRIX.VERSION"

if "%BUILD_VERSION%"=="MATRIX.VERSION" (
    set "BUILD_VERSION=2.0.4"
    echo Using default BUILD_VERSION: !BUILD_VERSION!
) else (
    echo Using provided BUILD_VERSION: !BUILD_VERSION!
)

if not exist "output" (
    mkdir output
)

echo Building...
gcc -Wall -Wextra -Wno-format-truncation -std=c99 -o output\digmacro_windows.exe scripts\launcher_build\launcher.c

echo Editing metadata...
set RCEDIT_URL=https://github.com/electron/rcedit/releases/download/v1.1.1/rcedit-x64.exe
set RCEDIT_EXE="scripts\\launcher_build\\rcedit.exe"

if not exist "%RCEDIT_EXE%" (
    echo Downloading rcedit.exe...

    powershell -Command "Invoke-WebRequest -Uri '%RCEDIT_URL%' -OutFile '%RCEDIT_EXE%'"
    if %errorlevel% neq 0 (
        echo Failed to download rcedit.exe
        exit /b 1
    )

    echo Download complete.
)

"%RCEDIT_EXE%" "output\\digmacro_windows.exe" ^
    --set-version-string "CompanyName" "mstudio45" ^
    --set-version-string "ProductName" "DIG Macro" ^
    --set-version-string "FileVersion" "!BUILD_VERSION!" ^
    --set-version-string "FileDescription" "DIG Macro is a tool that automatically plays the minigame in the Roblox game DIG." ^
    --set-version-string "LegalCopyright" "(C) mstudio45 2025 - https://github.com/mstudio45/digmacro" ^
    --set-icon "src\\assets\\icons\\icon.ico"

echo Windows launcher created.