@echo off

if not exist "env" (
    mkdir env
)

cd env

if not exist "build" (
    mkdir build
)

cd build

if not exist "Windows" (
    py -m venv Windows
)

cd ..
cd ..

if not exist "output" (
    mkdir output
)

call env\build\Windows\Scripts\activate

cd src

py main.py --only-install --force-reinstall

py -m nuitka --version >nul 2>&1
if errorlevel 1 (
  echo Installing nuitka...
  pip install nuitka
)

py -m nuitka ^
  --onefile ^
  --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" ^
  --standalone ^
  --follow-imports ^
  --assume-yes-for-downloads ^
  --company-name="mstudio45" ^
  --product-name="DIG Macro" ^
  --file-version="2.0.2" ^
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