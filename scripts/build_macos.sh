#!/bin/bash
cd src

python3 -m nuitka \
  --onefile \
  --standalone \
  --macos-create-app-bundle \
  --macos-app-icon=assets/icons/macos_icon.icns \
  --enable-plugin=pyside6 \
  --enable-plugin=tk-inter \
  --include-data-dir=assets=assets \
  --output-dir=dist \
  --follow-imports \
  main.py