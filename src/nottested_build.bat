@echo off
nuitka ^
  --onefile ^
  --standalone ^
  --enable-plugin=pyqt5 ^
  --output-dir=dist ^
  --follow-imports ^
  main.py
pause