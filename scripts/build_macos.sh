#!/bin/bash
cd src

python3 -m nuitka \
  --output-filename=digmacro_macos \
  --standalone \
  --macos-create-app-bundle \
  --macos-app-icon=assets/icons/macos_icon.icns \
  --macos-app-name=DIGMacro \
  --enable-plugin=pyside6 \
  --enable-plugin=tk-inter \
  --include-data-dir=assets=assets \
  --output-dir=dist/macos \
  --follow-imports main.py

cd dist
cd macos

# Rename the generated app to match the expected name
mv main.app digmacro_macos.app

# Sign the app
codesign --force --deep --sign - digmacro_macos.app

# Create a zip file of the app
ditto -c -k --sequesterRsrc --keepParent digmacro_macos.app digmacro_macos.zip

echo "Build completed successfully. The app is located at dist/macos/digmacro_macos.zip"
