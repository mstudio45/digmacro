@echo off
cd ..
cd src

nuitka ^
  --onefile ^
  --standalone ^
  --enable-plugin=pyside6 ^
  --enable-plugin=tk-inter ^
  --windows-icon-from-ico=assets/icons/icon.ico ^
  --include-data-dir=assets=assets ^
  --output-dir=dist ^
  --follow-imports ^
  main.py