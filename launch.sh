#!/usr/bin/env bash

OS="$(uname -s)"

echo "Checking for virtual environment..."
if [ ! -d "digmacro_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv digmacro_venv
fi
case "$OS" in
    Linux*)     . digmacro_venv/bin/activate ;;
    Darwin*)    source digmacro_venv/bin/activate ;;
    *)          echo "Unsupported operating system: $OS"; exit 1 ;;
esac

echo "Starting the src version..."
python3 src/main.py