@echo off
call digmacro_venv_Windows\Scripts\activate
cd src

py -m nuitka ^
  --onefile ^
  --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" ^
  --standalone ^
  --follow-imports ^
  --assume-yes-for-downloads ^
  --company-name="mstudio45" ^
  --product-name="DIG Macro" ^
  --file-version="2.0.1" ^
  --file-description="DIG Macro is a tool that automatically plays the minigame in the roblox game DIG." ^
  --copyright="\xA9 mstudio45 2025 - https://github.com/mstudio45/digmacro" ^
  --enable-plugin=pyside6,tk-inter ^
  --nofollow-import-to=cryptography,unittest,test,doctest ^
  --include-data-dir=assets=assets ^
  --output-dir=dist/win ^
  --output-filename=digmacro_windows ^
  --windows-icon-from-ico=assets/icons/icon.ico ^
  main.py