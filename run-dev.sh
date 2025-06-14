#!/bin/sh
# Script to run the Secrets application in a development environment

# Default to 'builddir' if not specified by $MESON_BUILD_ROOT
BUILD_DIR="${MESON_BUILD_ROOT:-builddir}"

if [ ! -f "${BUILD_DIR}/meson-info/meson-info.json" ]; then
    echo "Meson build directory '${BUILD_DIR}' not found or not configured."
    echo "Please run 'meson setup ${BUILD_DIR}' and 'meson compile -C ${BUILD_DIR}' first."
    exit 1
fi

# Execute the application using meson devenv
# 'secrets-dev' is the name of the executable defined in the root meson.build
# meson devenv will set up PYTHONPATH and other env vars.
echo "Running secrets-dev from ${BUILD_DIR}..."
meson devenv -C "${BUILD_DIR}" python3 -m secrets "$@"
