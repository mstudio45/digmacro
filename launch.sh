#!/usr/bin/env bash

OS="$(uname -s)"
MODE=""
ACTION=""
ARGS=""

if [ "$1" = "--run-source" ]; then
    MODE="source"
fi
if [ "$1" = "--run-standalone" ]; then
    MODE="standalone"
fi

if [ "$2" = "--edit" ]; then
    ACTION="edit"
fi
if [ "$2" = "--start" ]; then
    ACTION="start"
fi

if [ -z "$MODE" ]; then
    clear
    echo "How would you like to run the program?"
    echo "  1) Standalone: A ready-to-use version, simpler to run."
    echo "  2) From Source: For developers or to run the latest code."
    read -p "Please enter your choice (1 or 2) and press Enter: " MODE_CHOICE
    if [ "$MODE_CHOICE" = "1" ]; then
        MODE="standalone"
    elif [ "$MODE_CHOICE" = "2" ]; then
        MODE="source"
    fi
fi

if [ -z "$ACTION" ]; then
    echo
    echo "What would you like to do?"
    echo "  1) Start the program"
    echo "  2) Edit the configuration"
    read -p "Please enter your choice (1 or 2) and press Enter: " ACTION_CHOICE
    if [ "$ACTION_CHOICE" = "1" ]; then
        ACTION="start"
    elif [ "$ACTION_CHOICE" = "2" ]; then
        ACTION="edit"
    fi
fi

if [ "$ACTION" = "edit" ]; then
    ARGS="--edit-config"
fi

echo
echo "Running with mode: $MODE, action: $ACTION"
echo

if [ "$MODE" = "source" ]; then
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
    python3 src/main.py $ARGS --mode "$MODE"
elif [ "$MODE" = "standalone" ]; then
    case "$OS" in
        Linux*)     STANDALONE_EXEC="./digmacro.bin" ;;
        Darwin*)    STANDALONE_EXEC="./digmacro.app" ;;
        *)          echo "Unsupported operating system: $OS"; exit 1 ;;
    esac
    
    echo "Starting the built version... This might take a while."
    $STANDALONE_EXEC $ARGS --mode "$MODE" &
fi