#!/bin/bash
ARCS=("x86_64" "arm64")

if [ ! -d "env" ]; then
  mkdir env
fi

cd env

if [ ! -d "build" ]; then
  mkdir build
fi

cd ..

if [ ! -d "output" ]; then
  mkdir output
fi

for arch in "${ARCS[@]}"; do
  echo "================================================="
  echo "Building for architecture: $arch"
  echo "================================================="

  if [ "$arch" = "x86_64" ]; then
    CMD_PREFIX="arch -x86_64"
  else
    CMD_PREFIX=""
  fi

  cd env/build

  if [ ! -d "Darwin_$arch" ]; then
    $CMD_PREFIX python3 -m venv Darwin_$arch
  fi

  source "Darwin_$arch/bin/activate"
  
  cd ../..

  $CMD_PREFIX python3 src/main.py --only-install

  cd src

  $CMD_PREFIX python3 -m pip install nuitka

  $CMD_PREFIX python3 -m nuitka \
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

  if [ ! -d "digmacro_macos$arch.app" ]; then
    # then check for main.app in the current directory
    if [ ! -d "main.app" ]; then
      echo "Error: digmacro_macos$arch.app or main.app not found in dist/macos"
      exit 1
    else
      mv main.app digmacro_macos$arch.app
    fi
  fi

  PLIST="digmacro_macos$arch.app/Contents/Info.plist"
  if ! /usr/libexec/PlistBuddy -c "Print :NSAppSleepDisabled" "$PLIST" 2>/dev/null; then
      /usr/libexec/PlistBuddy -c "Add :NSAppSleepDisabled bool true" "$PLIST"
  else
      /usr/libexec/PlistBuddy -c "Set :NSAppSleepDisabled bool true" "$PLIST"
  fi

  codesign --force --deep --sign - digmacro_macos$arch.app
  ditto -c -k --sequesterRsrc --keepParent digmacro_macos$arch.app digmacro_macos$arch.zip

  mv digmacro_macos$arch.zip ../../../output/digmacro_macos_$arch.zip
  echo "Built digmacro_macos_$arch.zip successfully."
  
  rm -rf digmacro_macos$arch.app

  cd ../../..

  deactivate

  echo "================================================="
  echo "Build for architecture $arch completed."
  echo "================================================="
done

echo "================================================="
echo "All builds completed. Output files are in the 'output' directory."
echo "================================================="