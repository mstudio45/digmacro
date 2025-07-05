#!/bin/bash
cd src

python3 -m nuitka \
  --onefile \
  --standalone \
  --enable-plugin=pyside6 \
  --enable-plugin=tk-inter \
  --include-package=webview --include-package=gi \
  --include-data-dir=assets=assets \
  --output-dir=dist_linux \
  --follow-imports main.py