#!/bin/bash
cd src

python3 -m nuitka \
  --onefile \
  --standalone \
  --enable-plugin=pyside6 \
  --include-data-dir=assets=assets \
  --output-dir=dist \
  --follow-imports \
  main.py