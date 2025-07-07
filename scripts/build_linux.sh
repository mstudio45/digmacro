#!/bin/bash
. digmacro_venv_Linux/bin/activate
cd src

python3 -m nuitka \
  --onefile \
  --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" \
  --standalone \
  --follow-imports \
  --assume-yes-for-downloads \
  --company-name="mstudio45" \
  --product-name="DIG Macro" \
  --file-version="2.0.1" \
  --file-description="DIG Macro is a tool that automatically plays the minigame in the roblox game DIG." \
  --copyright="© mstudio45 2025 - https://github.com/mstudio45/digmacro" \
  --enable-plugin=pyside6,tk-inter \
  --nofollow-import-to=cryptography,unittest,test,doctest \
  --include-data-dir=assets=assets \
  --include-package=webview --include-package=gi \
  --output-dir=dist/linux \
  --output-filename=digmacro_linux \
  --linux-icon=assets/icons/icon.ico \
  main.py