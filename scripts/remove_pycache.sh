#!/bin/bash
echo "Deleting all __pycache__ folders recursively from $(pwd) ..."
find . -type d -name "__pycache__" -print -exec rm -rf {} +
echo "Done!"