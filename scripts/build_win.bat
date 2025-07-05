@echo off
cd ..
cd src

nuitka ^
  --onefile ^
  --standalone ^
  --enable-plugin=pyside6 ^
  --include-data-dir=assets=assets ^
  --output-dir=dist ^
  --follow-imports ^
  main.py