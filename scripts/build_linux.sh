#!/bin/bash
. env/dev/Linux/bin/activate

if [ ! -d "output" ]; then
  mkdir output
fi

cd src

if ! python3 -m nuitka --version >/dev/null 2>&1; then
  echo "Installing nuitka..."
  python3 -m pip install nuitka
fi

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
  --copyright="\xA9 mstudio45 2025 - https://github.com/mstudio45/digmacro" \
  --enable-plugin=pyside6,tk-inter \
  --nofollow-import-to=cryptography,unittest,test,doctest \
  --include-data-dir=assets=assets \
  --include-package=webview --include-package=gi \
  --output-dir=dist/linux \
  --output-filename=digmacro_linux.bin \
  main.py

mv dist/linux/digmacro_linux.bin ../../output/digmacro_linux.bin