#!/bin/bash

# Subtree
# Subtree repo was added with:
# git subtree add --prefix=rpi-rgb-led-matrix https://github.com/hzeller/rpi-rgb-led-matrix.git master --squash
# This should update the subtree to the latest version.
echo "Updating rpi-rgb-led-matrix subtree..."
git subtree pull --prefix rpi-rgb-led-matrix https://github.com/hzeller/rpi-rgb-led-matrix.git master --squash
