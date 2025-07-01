@echo off
nuitka ^
  --onefile ^
  --standalone ^
  --enable-plugin=pyqt5 ^
  --include-data-dir=img=img ^
  --output-dir=dist ^
  --follow-imports ^
  main.py
pause