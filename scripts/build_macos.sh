#!/bin/bash

BUILD_VERSION="MATRIX.VERSION"
if [[ "$BUILD_VERSION" == *"MATRIX."* ]]; then
  BUILD_VERSION="2.0.3"
  echo "Using default BUILD_VERSION: $BUILD_VERSION"
else
  echo "Using provided BUILD_VERSION: $BUILD_VERSION"
fi

if [ "$#" -eq 0 ]; then
  ARCHS=("$(uname -m)")
else
  ARCHS=()
  for arg in "$@"; do
    if [ "$arg" = "x64" ]; then
      ARCHS+=("x86_64")
    else
      ARCHS+=("$arg")
    fi
  done
fi

BUILT_APPS=()
USED_ARCHS=()

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

for arch in "${ARCHS[@]}"; do
  echo "================================================="
  echo "Building for architecture: $arch"
  echo "================================================="

  if ! arch -$arch /usr/bin/true 2>/dev/null; then
    echo "Architecture $arch is not available on this system. Skipping..."
    continue
  fi

  CMD_PREFIX="arch -$arch"
  export ARCHFLAGS="-arch $arch"

  cd env/build

  if [ ! -d "Darwin_$arch" ]; then
    echo "Creating virtual environment..."
    $CMD_PREFIX python3 -m venv Darwin_$arch
  fi

  source "Darwin_$arch/bin/activate"
  
  cd ../..

  # ensure correct arch wheel #
  echo "Installing dependencies..."
  $CMD_PREFIX pip install --upgrade --no-cache-dir pip 
  $CMD_PREFIX pip install --upgrade --no-cache-dir setuptools wheel
  $CMD_PREFIX pip install --upgrade --no-cache-dir nuitka
  $CMD_PREFIX python3 src/main.py --only-install --force-reinstall --force-$arch

  cd src

  $CMD_PREFIX python3 -m nuitka \
    --show-progress \
    --standalone \
    --follow-imports \
    --assume-yes-for-downloads \
    --company-name="mstudio45" \
    --product-name="DIG Macro" \
    --file-version="$BUILD_VERSION" \
    --file-description="DIG Macro is a tool that automatically plays the minigame in the Roblox game DIG." \
    --copyright="© mstudio45 2025 - https://github.com/mstudio45/digmacro" \
    --enable-plugin=pyside6,tk-inter \
    --nofollow-import-to=cryptography,unittest,test,doctest,pytest \
    --include-package=cv2 --include-package-data=cv2 --nofollow-import-to=cv2.test --nofollow-import-to=cv2.tests \
    --include-package=numpy --include-package-data=numpy --nofollow-import-to=numpy.testing --nofollow-import-to=numpy.tests --nofollow-import-to="numpy.*.tests" \
    --include-package=PIL --include-package-data=PIL \
    --include-data-dir=assets=assets \
    --output-dir=dist/macos_$arch \
    --output-filename=digmacro_macos \
    --macos-create-app-bundle \
    --macos-app-icon=assets/icons/macos_icon.icns \
    --macos-signed-app-name="com.mstudio45.digmacro" \
    --macos-app-name="DIG Macro" \
    --macos-app-version="$BUILD_VERSION" \
    --macos-target-arch=$arch \
    main.py

  cd dist
  cd macos_$arch

  if [ ! -d "digmacro_macos_$arch.app" ]; then
    if [ ! -d "main.app" ]; then
      echo "Error: digmacro_macos_$arch.app or main.app not found in dist/macos"
      exit 1
    else
      mv main.app digmacro_macos_$arch.app
    fi
  fi

  PLIST="digmacro_macos_$arch.app/Contents/Info.plist"
  /usr/libexec/PlistBuddy -c "Set :NSAppSleepDisabled bool true" "$PLIST" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :NSAppSleepDisabled bool true" "$PLIST"
  
  BUILT_APPS+=("$(pwd)/digmacro_macos_$arch.app")
  USED_ARCHS+=("$arch")

  cd ../../..

  deactivate

  echo "================================================="
  echo "Build for architecture $arch completed."
  echo "================================================="
done

echo "================================================="
echo "Creating universal binary..."
echo "================================================="

if [ ${#BUILT_APPS[@]} -eq 0 ]; then
  echo "Error: No app bundles were successfully built"
  exit 1
fi

UNIVERSAL_FILE_NAME="digmacro_macos_universal"
if [ ${#USED_ARCHS[@]} -eq 1 ]; then
  UNIVERSAL_FILE_NAME="digmacro_macos_${USED_ARCHS[0]}"
fi
UNIVERSAL_APP="output/$UNIVERSAL_FILE_NAME.app"

rm -rf "$UNIVERSAL_APP"

mkdir -p "$UNIVERSAL_APP/Contents/MacOS"
mkdir -p "$UNIVERSAL_APP/Contents/Resources"

cp -R "${BUILT_APPS[0]}/Contents/Info.plist" "$UNIVERSAL_APP/Contents/"
cp -R "${BUILT_APPS[0]}/Contents/Resources/"* "$UNIVERSAL_APP/Contents/Resources/"

for ((i=0; i<${#BUILT_APPS[@]}; i++)); do
  arch="${USED_ARCHS[i]}"
  echo "Copying $arch files to universal .app file..."

  mkdir -p "$UNIVERSAL_APP/Contents/MacOS/$arch"
  cp -R "${BUILT_APPS[i]}/Contents/MacOS/"* "$UNIVERSAL_APP/Contents/MacOS/$arch/"
done

echo "Creating launch script..."
cat > "output/launcher.c" << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libgen.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/utsname.h>
#include <mach-o/dyld.h>

// dialog functions
void show_applescript_dialog(const char *message, const char *icon) {
    char command[1024];
    snprintf(command, sizeof(command),
             "osascript -e 'display dialog \"%s\" with title \"DIG Macro\" buttons {\"OK\"} default button \"OK\" with icon %s'",
             message, icon);
    system(command);
}

void show_error(const char *message) {
    show_applescript_dialog(message, "stop");
}

void show_warning(const char *message) {
    show_applescript_dialog(message, "caution");
}

// exists functions
int file_exists(const char *path) {
    struct stat buffer;
    return (stat(path, &buffer) == 0);
}

int main(int argc, char *argv[]) {
    char exe_path[4096];
    uint32_t size = sizeof(exe_path);
    if (_NSGetExecutablePath(exe_path, &size) != 0) {
        show_error("Failed to get executable path.");
        return 1;
    }
    char *dir = dirname(exe_path);

    struct utsname sysinfo;
    uname(&sysinfo);

    char binary_path[4096] = {0};
    if (strcmp(sysinfo.machine, "arm64") == 0) {
        snprintf(binary_path, sizeof(binary_path), "%s/arm64/digmacro_macos", dir);

    } else if (strcmp(sysinfo.machine, "x86_64") == 0) {
        snprintf(binary_path, sizeof(binary_path), "%s/x86_64/digmacro_macos", dir);

    } else {
        char warn_message[512];
        snprintf(warn_message, sizeof(warn_message),
            "Your system architecture (%s) is not directly supported. Attempting to run x86_64 version.",
            sysinfo.machine);
        show_warning(warn_message);

        snprintf(binary_path, sizeof(binary_path), "%s/x86_64/digmacro_macos", dir);
    }

    if (!file_exists(binary_path)) {
        show_error("No compatible binary found for your system. Please reinstall the application.");
        return 1;
    }

    execv(binary_path, argv);
    perror("execv failed");

    char error_message[4096];
    snprintf(error_message, sizeof(error_message),
        "Failed to launch DIG Macro.\nArch: %s\nPath: %s",
        sysinfo.machine, binary_path);
    show_error(error_message);
    return 1;
}
EOF

BUILDED_CLANG=()
for curarch in "${USED_ARCHS[@]}"; do
  clang -target "$curarch-apple-darwin" -mmacos-version-min=10.12 -o "output/$curarch-digmacro_macos" output/launcher.c
  BUILDED_CLANG+=("output/$curarch-digmacro_macos")
done

if (( ${#BUILDED_CLANG[@]} == 1 )); then
  mv "${BUILDED_CLANG[0]}" "$UNIVERSAL_APP/Contents/MacOS/digmacro_macos"

elif (( ${#BUILDED_CLANG[@]} > 1 )); then
  lipo -create "${BUILDED_CLANG[@]}" -output "$UNIVERSAL_APP/Contents/MacOS/digmacro_macos"

  for buildedclang in "${BUILDED_CLANG[@]}"; do
    rm -rf "$buildedclang"
  done
else
  echo "No binaries were built, skipping lipo."
fi

rm -rf output/launcher.c

echo "Fixing Info.plist..."
UNIVERSAL_PLIST="$UNIVERSAL_APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Delete :LSArchitecturePriority" "$UNIVERSAL_PLIST" 2>/dev/null || true
if [ ${#USED_ARCHS[@]} -gt 1 ]; then
  /usr/libexec/PlistBuddy -c "Add :LSArchitecturePriority array" "$UNIVERSAL_PLIST"
  for arch in "${USED_ARCHS[@]}"; do
    /usr/libexec/PlistBuddy -c "Add :LSArchitecturePriority:0 string $arch" "$UNIVERSAL_PLIST"
  done
fi
/usr/libexec/PlistBuddy -c "Set :CFBundleExecutable \"digmacro_macos\"" "$UNIVERSAL_PLIST" || /usr/libexec/PlistBuddy -c "Add :CFBundleExecutable \"digmacro_macos\"" "$UNIVERSAL_PLIST"

/usr/libexec/PlistBuddy -c "Set :NSAppSleepDisabled bool true" "$UNIVERSAL_PLIST" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :NSAppSleepDisabled bool true" "$UNIVERSAL_PLIST"

for ((i=0; i<${#BUILT_APPS[@]}; i++)); do
  arch="${USED_ARCHS[i]}"
  echo "Signing $arch binary..."
  find "$UNIVERSAL_APP/Contents/MacOS/$arch" -type f -perm +111 | while read -r executable; do
    codesign --force --sign - "$executable" 2>/dev/null || true
  done
done

echo "Signing launch script and universal binary..."
codesign --force --sign - "$UNIVERSAL_APP/Contents/MacOS/digmacro_macos"
codesign --force --deep --sign - "$UNIVERSAL_APP"

cd output

# ditto -c -k --sequesterRsrc --keepParent "$UNIVERSAL_FILE_NAME.app" "$UNIVERSAL_FILE_NAME.zip"
# rm -rf "UNIVERSAL_FILE_NAME.app"

cd ..

echo "Built $UNIVERSAL_FILE_NAME.app successfully."

for app in "${BUILT_APPS[@]}"; do
  rm -rf "$app"
done

echo "================================================="
echo "Universal build completed!"
echo "================================================="