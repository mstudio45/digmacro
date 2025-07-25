#!/bin/bash

BUILD_VERSION="MATRIX.VERSION"
if [[ "$BUILD_VERSION" == *"MATRIX."* ]]; then
  BUILD_VERSION="2.0.3"
  echo "Using default BUILD_VERSION: $BUILD_VERSION"
else
  echo "Using provided BUILD_VERSION: $BUILD_VERSION"
fi

echo "Creating environment directories..."
if [ ! -d "env" ]; then
  mkdir env
fi

cd env

if [ ! -d "build" ]; then
  mkdir build
fi

cd build

if [ ! -d "Linux" ]; then
  echo "Creating virtual environment..."
  python3 -m venv Linux
fi

cd ..
cd ..

if [ ! -d "output" ]; then
  mkdir output
fi

. env/build/Linux/bin/activate

cd src

echo "Installing dependencies..."

# for pywebview[gtk] #
sudo apt-get update
sudo apt-get install -y libcairo2-dev pkg-config python3-dev

python3 main.py --only-install --force-reinstall

if ! python3 -m nuitka --version >/dev/null 2>&1; then
  echo "Installing nuitka..."
  python3 -m pip install nuitka
fi

python3 -m nuitka \
  --show-progress \
  --onefile \
  --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" \
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
  --include-data-dir=assets=assets \
  --include-package=webview --include-package=gi \
  --output-dir=dist/linux \
  --output-filename=digmacro_linux.bin \
  main.py

mv dist/linux/digmacro_linux.bin ../output/digmacro_linux.bin