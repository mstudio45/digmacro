#!/bin/sh
BUILD_VERSION="MATRIX.VERSION"
if echo "$BUILD_VERSION" | grep -q "MATRIX."; then
  BUILD_VERSION="2.0.4"
  echo "Using default BUILD_VERSION: $BUILD_VERSION"
else
  echo "Using provided BUILD_VERSION: $BUILD_VERSION"
fi

if [ ! -d "output" ]; then
  mkdir output
fi

echo "Building..."
gcc -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Wno-format-truncation -std=gnu11 -o output/digmacro_linux.bin scripts/launcher_build/launcher.c

echo "Linux launcher created."