#!/bin/sh
BUILD_VERSION="MATRIX.VERSION"
if echo "$BUILD_VERSION" | grep -q "MATRIX."; then
  BUILD_VERSION="2.0.4"
  echo "Using default BUILD_VERSION: $BUILD_VERSION"
else
  echo "Using provided BUILD_VERSION: $BUILD_VERSION"
fi

BUILD_BRANCH="MATRIX.BRANCH"
if echo "$BUILD_BRANCH" | grep -q "MATRIX."; then
  BUILD_BRANCH="dev"
  echo "Using default BUILD_BRANCH: $BUILD_BRANCH"
else
  echo "Using provided BUILD_BRANCH: $BUILD_BRANCH"
fi

if [ ! -d "output" ]; then
  mkdir output
fi

echo "Building..."
sed "s/MATRIX\.BRANCH/${BUILD_BRANCH}/g" scripts/launcher_build/launcher.c > scripts/launcher_build/launcher_copy.c
gcc -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Wno-format-truncation -std=gnu11 -o output/digmacro_linux.bin scripts/launcher_build/launcher_copy.c
rm scripts/launcher_build/launcher_copy.c

echo "Linux launcher created."