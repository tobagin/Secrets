#!/bin/bash
# Project cleanup script for Secrets Password Manager
# This script cleans up build artifacts and temporary files

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "🧹 Cleaning up Secrets project..."

# Remove build directories
echo "Removing build directories..."
rm -rf builddir/
rm -rf build/
rm -rf dist/
rm -rf .flatpak-builder/

# Remove Python cache
echo "Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove editor temporary files
echo "Removing editor temporary files..."
find . -type f -name "*~" -delete 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*.swo" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true

# Remove test artifacts
echo "Removing test artifacts..."
rm -rf .pytest_cache/
rm -rf .coverage
rm -rf htmlcov/
rm -rf .tox/

# Remove IDE files (optional - uncomment if needed)
# echo "Removing IDE files..."
# rm -rf .vscode/
# rm -rf .idea/

# Remove temporary files
echo "Removing temporary files..."
rm -rf /tmp/secrets-*
rm -rf /tmp/flatpak-*

echo "✅ Cleanup complete!"
echo ""
echo "To rebuild the project:"
echo "  meson setup builddir"
echo "  meson compile -C builddir"
echo ""
echo "To run the application:"
echo "  ./run-dev.sh"
