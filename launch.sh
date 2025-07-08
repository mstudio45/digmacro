#!/usr/bin/env bash

OS="$(uname -s)"

if [ ! -d "env" ]; then
    mkdir env
fi

cd env

if [ ! -d "dev" ]; then
    mkdir dev
fi

cd dev

if [ ! -d "$OS" ]; then
    echo "Creating virtual environment for $OS..."
    python3 -m venv $OS
fi

case "$OS" in
    Linux*)     . $OS/bin/activate ;;
    Darwin*)    source $OS/bin/activate ;;
    *)          echo "Unsupported operating system: $OS"; exit 1 ;;
esac

cd ../..

echo "Starting the src version..."
python3 src/main.py