#!/bin/bash
cd src

python3 -m nuitka \
  --onefile \
  --standalone \
  --macos-create-app-bundle \
  --macos-app-icon=assets/icons/macos_icon.icns \
  --macos-app-name=DIGMacro \
  --enable-plugin=pyside6 \
  --enable-plugin=tk-inter \
  --include-data-dir=assets=assets \
  --output-dir=dist/macos \
  --follow-imports main.py