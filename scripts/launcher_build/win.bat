@echo off
setlocal enabledelayedexpansion

set "BUILD_VERSION=MATRIX.VERSION"
if "%BUILD_VERSION%"=="MATRIX.VERSION" (
    set "BUILD_VERSION=2.0.4"
    echo Using default BUILD_VERSION: !BUILD_VERSION!
) else (
    echo Using provided BUILD_VERSION: !BUILD_VERSION!
)

set "BUILD_BRANCH=MATRIX.BRANCH"
if "%BUILD_BRANCH%"=="MATRIX.BRANCH" (
    set "BUILD_BRANCH=dev"
    echo Using default BUILD_BRANCH: !BUILD_BRANCH!
) else (
    echo Using provided BUILD_BRANCH: !BUILD_BRANCH!
)

if not exist "output" (
    mkdir output
)

echo Building...
set LAUNCHERC_PATH=scripts\launcher_build\launcher.c
set LAUNCHERC_COPY_PATH=scripts\launcher_build\launcher_copy.c

powershell -NoProfile -Command "(Get-Content '%LAUNCHERC_PATH%') -replace 'MATRIX.BRANCH', '!BUILD_BRANCH!' | Set-Content '%LAUNCHERC_COPY_PATH%'"
gcc -Wall -Wextra -Wno-format-truncation -std=c99 -o output\digmacro_windows.exe "%LAUNCHERC_COPY_PATH%"
del "%LAUNCHERC_COPY_PATH%"

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