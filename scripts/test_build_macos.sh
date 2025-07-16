#!/bin/bash

ARCHS=("x86_64" "arm64")
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
    $CMD_PREFIX python3 -m venv Darwin_$arch
  fi

  source "Darwin_$arch/bin/activate"
  
  cd ../..

  $CMD_PREFIX python3 -m pip install --upgrade --no-cache-dir pip
  $CMD_PREFIX python3 src/main.py --only-install --force-reinstall

  cd src

  $CMD_PREFIX python3 -m pip install --no-cache-dir nuitka
  $CMD_PREFIX python3 -m pip install --upgrade --no-cache-dir nuitka setuptools

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
    --nofollow-import-to=cryptography,unittest,test,doctest,pytest \
    --include-package=numpy --nofollow-import-to=numpy.tests --nofollow-import-to="numpy.*.tests" \
    --include-data-dir=assets=assets \
    --output-dir=dist/macos_$arch \
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

UNIVERSAL_APP="output/digmacro_macos_universal.app"
mkdir -p "$UNIVERSAL_APP/Contents/MacOS"
mkdir -p "$UNIVERSAL_APP/Contents/Resources"

cp -R "${BUILT_APPS[0]}/Contents/Info.plist" "$UNIVERSAL_APP/Contents/"
cp -R "${BUILT_APPS[0]}/Contents/Resources/"* "$UNIVERSAL_APP/Contents/Resources/"

for ((i=0; i<${#BUILT_APPS[@]}; i++)); do
  arch="${USED_ARCHS[i]}"
  mkdir -p "$UNIVERSAL_APP/Contents/MacOS/$arch"
  cp -R "${BUILT_APPS[i]}/Contents/MacOS/"* "$UNIVERSAL_APP/Contents/MacOS/$arch/"
done

cat > "$UNIVERSAL_APP/Contents/MacOS/DIG Macro" << 'EOF'
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARCH=$(uname -m)

show_error() {
    osascript -e "display dialog \"$1\" with title \"DIG Macro\" buttons {\"OK\"} default button \"OK\" with icon stop"
}

show_warning() {
    osascript -e "display dialog \"$1\" with title \"DIG Macro\" buttons {\"OK\"} default button \"OK\" with icon caution"
}

if [ "$ARCH" = "arm64" ] && [ -d "$DIR/arm64" ]; then
    exec "$DIR/arm64/DIG Macro" "$@"
elif [ "$ARCH" = "x86_64" ] && [ -d "$DIR/x86_64" ]; then
    exec "$DIR/x86_64/DIG Macro" "$@"
else
    for arch_dir in "$DIR"/*/; do
        if [ -d "$arch_dir" ]; then
            arch_name=$(basename "$arch_dir")
            show_warning "Your system architecture ($ARCH) is not directly supported. Running in $arch_name mode."
            exec "$arch_dir/DIG Macro" "$@"
        fi
    done
    
    show_error "No compatible architecture found for your system ($ARCH). Try reinstalling the application."
    exit 1
fi
EOF

chmod +x "$UNIVERSAL_APP/Contents/MacOS/DIG Macro"

UNIVERSAL_PLIST="$UNIVERSAL_APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Delete :LSArchitecturePriority" "$UNIVERSAL_PLIST" 2>/dev/null || true
if ! /usr/libexec/PlistBuddy -c "Print :NSAppSleepDisabled" "$UNIVERSAL_PLIST" 2>/dev/null; then
  /usr/libexec/PlistBuddy -c "Add :NSAppSleepDisabled bool true" "$UNIVERSAL_PLIST"
else
  /usr/libexec/PlistBuddy -c "Set :NSAppSleepDisabled bool true" "$UNIVERSAL_PLIST"
fi
/usr/libexec/PlistBuddy -c "Set :CFBundleExecutable \"DIG Macro\"" "$UNIVERSAL_PLIST"

/usr/libexec/PlistBuddy -c "Delete :LSArchitecturePriority" "$UNIVERSAL_PLIST" 2>/dev/null || true
if [ ${#USED_ARCHS[@]} -gt 1 ]; then
  /usr/libexec/PlistBuddy -c "Add :LSArchitecturePriority array" "$UNIVERSAL_PLIST"
  for arch in "${USED_ARCHS[@]}"; do
    /usr/libexec/PlistBuddy -c "Add :LSArchitecturePriority:0 string $arch" "$UNIVERSAL_PLIST"
  done
fi

for ((i=0; i<${#BUILT_APPS[@]}; i++)); do
  arch="${USED_ARCHS[i]}"
  echo "Signing $arch binaries..."
  find "$UNIVERSAL_APP/Contents/MacOS/$arch" -type f -perm +111 | while read -r executable; do
    codesign --force --sign - "$executable" 2>/dev/null || true
  done
done

codesign --force --sign - "$UNIVERSAL_APP/Contents/MacOS/DIG Macro"
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