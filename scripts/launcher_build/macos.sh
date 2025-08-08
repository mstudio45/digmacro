#!/bin/bash

BUILD_VERSION="MATRIX.VERSION"
if [[ "$BUILD_VERSION" == *"MATRIX."* ]]; then
  BUILD_VERSION="2.0.4"
  echo "Using default BUILD_VERSION: $BUILD_VERSION"
else
  echo "Using provided BUILD_VERSION: $BUILD_VERSION"
fi

if [ ! -d "build" ]; then
  mkdir build
fi

APP_NAME="digmacro_macos"
APP_BUNDLE_NAME="digmacro_macos.app"

ICON_PATH="src/assets/icons/macos_icon.icns"
BINARY_PATH="output/digmacro_macos"
APP_BUNDLE_PATH="output/$APP_BUNDLE_NAME"

echo "Copying launcher.c to launcher_dynamic.c..."
cp scripts/launcher_build/launcher.c scripts/launcher_build/launcher_dynamic.c

echo "Building..."
gcc -Wall -Wextra -std=c99 -o output/$APP_NAME scripts/launcher_build/launcher_dynamic.c
if [ $? -ne 0 ]; then
  echo "Compilation failed. Exiting."
  exit 1
fi

echo "Deleting launcher_dynamic.c..."
rm scripts/launcher_build/launcher_dynamic.c

echo "Creating .app bundle..."
rm -rf "$APP_BUNDLE_PATH"
mkdir -p "$APP_BUNDLE_PATH/Contents/MacOS"
mkdir -p "$APP_BUNDLE_PATH/Contents/Resources"

cp "$BINARY_PATH" "$APP_BUNDLE_PATH/Contents/MacOS/$APP_NAME"
chmod +x "$APP_BUNDLE_PATH/Contents/MacOS/$APP_NAME"

cp "$ICON_PATH" "$APP_BUNDLE_PATH/Contents/Resources/"

cat > "$APP_BUNDLE_PATH/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>$APP_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleIconFile</key>
  <string>macos_icon.icns</string>
  <key>CFBundleIdentifier</key>
  <string>com.mstudio45.digmacro</string>
  <key>CFBundleName</key>
  <string>DIG Macro</string>
  <key>CFBundleVersion</key>
  <string>$APP_VERSION</string>
  <key>CFBundleShortVersionString</key>
  <string>$APP_VERSION</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.12</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSAppSleepDisabled</key>
  <true/>
</dict>
</plist>
EOF

echo "Signing launch script and universal binary..."
codesign --force --sign - "$APP_BUNDLE_PATH/Contents/MacOS/$APP_NAME"
codesign --force --deep --sign - "$APP_BUNDLE_PATH"

echo "Deleting $BINARY_PATH..."
rm $BINARY_PATH

echo "Done."