@echo off

set "BUILD_VERSION=MATRIX.VERSION"

echo %BUILD_VERSION% | findstr "MATRIX." >nul
if %errorlevel%==0 (
    set "BUILD_VERSION=2.0.3"
    echo Using default BUILD_VERSION: %BUILD_VERSION%
)

echo Creating environment directories...

if not exist "env" (
    mkdir env
)

cd env

if not exist "build" (
    mkdir build
)

cd build

if not exist "Windows" (
    echo Creating virtual environment...
    py -m venv Windows
)

cd ..
cd ..

if not exist "output" (
    mkdir output
)

call env\build\Windows\Scripts\activate

cd src

echo Installing dependencies...
py main.py --only-install --force-reinstall

py -m nuitka --version >nul 2>&1
if errorlevel 1 (
  echo Installing nuitka...
  pip install nuitka
)

py -m nuitka ^
  --show-progress ^
  --onefile ^
  --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" ^
  --standalone ^
  --follow-imports ^
  --assume-yes-for-downloads ^
  --company-name="mstudio45" ^
  --product-name="DIG Macro" ^
  --file-version="%BUILD_VERSION%" ^
  --file-description="DIG Macro is a tool that automatically plays the minigame in the Roblox game DIG." ^
  --copyright="© mstudio45 2025 - https://github.com/mstudio45/digmacro" ^
  --enable-plugin=pyside6,tk-inter ^
  --nofollow-import-to=cryptography,unittest,test,doctest,pytest ^
  --include-data-dir=assets=assets ^
  --output-dir=dist/win ^
  --output-filename=digmacro_windows ^
  --windows-icon-from-ico=assets/icons/icon.ico ^
  main.py

move dist\win\digmacro_windows.exe ..\output\