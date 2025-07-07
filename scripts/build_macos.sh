#!/bin/bash
source digmacro_venv_Darwin/bin/activate
cd src

python3 -m nuitka \
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
  --output-dir=dist/macos \
  --output-filename=digmacro_macos \
  --macos-create-app-bundle \
  --macos-app-icon=assets/icons/macos_icon.icns \
  --macos-signed-app-name="com.mstudio45.digmacro" \
  --macos-app-name="DIG Macro" \
  --macos-app-version="2.0.1" \
  --macos-prohibit-multiple-instances \
  --macos-app-protected-resource=NSAccessibilityUsageDescription:"DIG Macro needs Accessibility access to control mouse, keyboard inside Roblox." \
  --macos-app-protected-resource=NSScreenCaptureUsageDescription:"DIG Macro needs Screen Recording access to take screenshots for computer vision (opencv)." \
  --macos-app-protected-resource=NSInputMonitoringUsageDescription:"DIG Macro needs Input Monitoring access to monitor keyboard and mouse." \
  main.py

cd dist
cd macos

codesign --force --deep --sign - digmacro_macos.app
ditto -c -k --sequesterRsrc --keepParent digmacro_macos.app digmacro_macos.zip

echo "Build completed successfully. The app is located at dist/macos/digmacro_macos.zip"