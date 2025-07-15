#!/bin/bash

ARCHS=("x86_64" "arm64")
BUILT_APPS=()

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
    --file-version="2.0.2" \
    --file-description="DIG Macro is a tool that automatically plays the minigame in the Roblox game DIG." \
    --copyright="\xA9 mstudio45 2025 - https://github.com/mstudio45/digmacro" \
    --enable-plugin=pyside6,tk-inter \
    --nofollow-import-to=cryptography,unittest,test,doctest \
    --include-package=opencv-python,numpy \
    --include-data-dir=assets=assets \
    --output-dir=dist/macos_$arch \
    --output-filename=digmacro_macos \
    --macos-create-app-bundle \
    --macos-app-icon=assets/icons/macos_icon.icns \
    --macos-signed-app-name="com.mstudio45.digmacro" \
    --macos-app-name="DIG Macro" \
    --macos-app-version="2.0.2" \
    --macos-target-arch=$arch \
    main.py

  cd dist
  cd macos_$arch

  if [ ! -d "digmacro_macos_$arch.app" ]; then
    # then check for main.app in the current directory
    if [ ! -d "main.app" ]; then
      echo "Error: digmacro_macos_$arch.app or main.app not found in dist/macos"
      exit 1
    else
      mv main.app digmacro_macos_$arch.app
    fi
  fi

  PLIST="digmacro_macos_$arch.app/Contents/Info.plist"
  if ! /usr/libexec/PlistBuddy -c "Print :NSAppSleepDisabled" "$PLIST" 2>/dev/null; then
    /usr/libexec/PlistBuddy -c "Add :NSAppSleepDisabled bool true" "$PLIST"
  else
    /usr/libexec/PlistBuddy -c "Set :NSAppSleepDisabled bool true" "$PLIST"
  fi

  BUILT_APPS+=("$(pwd)/digmacro_macos_$arch.app")
  cp -R digmacro_macos_$arch.app ../../../output/

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

if [ ${#BUILT_APPS[@]} -eq 1 ]; then
  echo "Only one architecture built, copying as universal..."
  UNIVERSAL_APP="output/digmacro_macos_universal.app"
  cp -R "${BUILT_APPS[0]}" "$UNIVERSAL_APP"
  
  # Sign and zip
  codesign --force --deep --sign - "$UNIVERSAL_APP"
  cd output
  ditto -c -k --sequesterRsrc --keepParent digmacro_macos_universal.app digmacro_macos_universal.zip
  cd ..

  UNIVERSAL_PLIST="$UNIVERSAL_APP/Contents/Info.plist"
  if ! /usr/libexec/PlistBuddy -c "Print :NSAppSleepDisabled" "$UNIVERSAL_PLIST" 2>/dev/null; then
    /usr/libexec/PlistBuddy -c "Add :NSAppSleepDisabled bool true" "$UNIVERSAL_PLIST"
  else
    /usr/libexec/PlistBuddy -c "Set :NSAppSleepDisabled bool true" "$UNIVERSAL_PLIST"
  fi
  
  echo "Single architecture app copied as universal: output/digmacro_macos_universal.zip"
  exit 1
fi

UNIVERSAL_APP="output/digmacro_macos_universal.app"
cp -R "${BUILT_APPS[0]}" "$UNIVERSAL_APP"

find "$UNIVERSAL_APP" -type f -perm +111 | while read -r executable; do
  if file "$executable" | grep -q "Mach-O"; then
    echo "    - Merging executable: $executable"
    
    ARCH_EXECUTABLES=()
    for ((i=0; i<${#BUILT_APPS[@]}; i++)); do
      arch_executable="${executable/$UNIVERSAL_APP/${BUILT_APPS[i]}}"
      if [ -f "$arch_executable" ]; then
        ARCH_EXECUTABLES+=("$arch_executable")
      fi
    done
    
    if [ ${#ARCH_EXECUTABLES[@]} -gt 1 ]; then
      lipo -create "${ARCH_EXECUTABLES[@]}" -output "$executable"
      echo "Created universal binary: $executable"
    fi
  fi
done

echo "================================================="
echo "Merging libraries..."
echo "================================================="

find "$UNIVERSAL_APP" -name "*.dylib" -o -name "*.so" | while read -r library; do
  echo "    - Merging library: $library"
  
  ARCH_LIBRARIES=()
  for ((i=0; i<${#BUILT_APPS[@]}; i++)); do
    arch_library="${library/$UNIVERSAL_APP/${BUILT_APPS[i]}}"
    if [ -f "$arch_library" ]; then
      ARCH_LIBRARIES+=("$arch_library")
    fi
  done
  
  if [ ${#ARCH_LIBRARIES[@]} -gt 1 ]; then
    lipo -create "${ARCH_LIBRARIES[@]}" -output "$library"
    echo "Created universal library: $library"
  fi
done

UNIVERSAL_PLIST="$UNIVERSAL_APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Delete :LSArchitecturePriority" "$UNIVERSAL_PLIST" 2>/dev/null || true
if ! /usr/libexec/PlistBuddy -c "Print :NSAppSleepDisabled" "$UNIVERSAL_PLIST" 2>/dev/null; then
  /usr/libexec/PlistBuddy -c "Add :NSAppSleepDisabled bool true" "$UNIVERSAL_PLIST"
else
  /usr/libexec/PlistBuddy -c "Set :NSAppSleepDisabled bool true" "$UNIVERSAL_PLIST"
fi

codesign --force --deep --sign - "$UNIVERSAL_APP"

cd output

ditto -c -k --sequesterRsrc --keepParent digmacro_macos_universal.app digmacro_macos_universal.zip
rm -rf digmacro_macos_universal.app

cd ..

echo "Built digmacro_macos_universal.zip successfully."

for app in "${BUILT_APPS[@]}"; do
  rm -rf "$app"
done

echo "================================================="
echo "Universal build completed!"
echo "================================================="