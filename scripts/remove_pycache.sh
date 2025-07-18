#!/bin/bash
echo "Deleting all __pycache__ folders recursively from $(pwd) ..."
find . -type d | grep '__pycache__$' | xargs rm -rf
echo "Done!"