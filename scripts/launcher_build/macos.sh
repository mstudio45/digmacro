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

CURRENT_ARCH="$(uname -m)"

APP_NAME="digmacro_macos"
APP_BUNDLE_NAME="digmacro_macos_$CURRENT_ARCH.app"

ICON_PATH="src/assets/icons/macos_icon.icns"
BINARY_PATH="output/$APP_NAME"

APP_BUNDLE_PATH="output/$APP_BUNDLE_NAME"
PLIST_PATH="$APP_BUNDLE_PATH/Contents/Info.plist"

LAUNCHERC_PATH="scripts/launcher_build/launcher.c"
DYLIBBUNDLER_PATH="scripts/launcher_build/dylibbundler"

echo "Building..."
# gcc -Wall -Wextra -std=c99 -o output/$APP_NAME "$LAUNCHERC_PATH"
clang -target "$CURRENT_ARCH-apple-darwin" -mmacos-version-min=10.12 -o "$BINARY_PATH" "$LAUNCHERC_PATH"

if [ $? -ne 0 ]; then
  echo "Compilation failed. Exiting."
  exit 1
fi

echo "Creating .app bundle..."
rm -rf "$APP_BUNDLE_PATH"
mkdir -p "$APP_BUNDLE_PATH/Contents/MacOS"
mkdir -p "$APP_BUNDLE_PATH/Contents/Resources"

cp "$BINARY_PATH" "$APP_BUNDLE_PATH/Contents/MacOS/$APP_NAME"
chmod +x "$APP_BUNDLE_PATH/Contents/MacOS/$APP_NAME"
cp "$ICON_PATH" "$APP_BUNDLE_PATH/Contents/Resources/"

echo "Creating PList using PlistBuddy..." # macos wants to segfault with manually created plists (i hope this works or im gonna :boom:)
/usr/libexec/PlistBuddy -c "Clear dict" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :CFBundleExecutable string $APP_NAME" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string macos_icon.icns" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.mstudio45.digmacro" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :CFBundleName string DIG Macro" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $BUILD_VERSION" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $BUILD_VERSION" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :NSHumanReadableCopyright string © mstudio45 2025 - https://github.com/mstudio45/digmacro" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string 10.12" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :NSAppSleepDisabled bool true" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :LSBackgroundOnly bool false" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool false" "$PLIST_PATH"

echo "Fixing dylibs..."
if [ ! -f "$DYLIBBUNDLER_PATH" ]; then
  echo "dylibbundler not found, cloning and building from GitHub..."

  if [ ! -d "macdylibbundler" ]; then
    git clone https://github.com/auriamg/macdylibbundler.git
  fi

  cd "macdylibbundler" || { echo "Failed to enter macdylibbundler"; exit 1; }
  make || { echo "Failed to build dylibbundler"; exit 1; }
  cp "dylibbundler" "../$DYLIBBUNDLER_PATH"

  cd ..
  rm -rf "macdylibbundler"

  echo "dylibbundler built and ready."
fi

"$DYLIBBUNDLER_PATH" \
  -x "$APP_BUNDLE_PATH/Contents/MacOS/$APP_NAME" \
  -b \
  -d "$APP_BUNDLE_PATH/Contents/libs" \
  -p @executable_path/../libs/ \
  -od \
  --overwrite-files \
  --no-codesign

echo "Signing universal binary..."
codesign --force --sign - "$APP_BUNDLE_PATH/Contents/MacOS/$APP_NAME"
codesign --force --deep --sign - "$APP_BUNDLE_PATH"

echo "Deleting $BINARY_PATH..."
rm $BINARY_PATH

echo "Done."