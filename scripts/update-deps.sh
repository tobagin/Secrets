#!/bin/bash
# Standalone script to update Flatpak dependencies
# This script can be run independently to check for and update dependencies

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Checking and updating Flatpak dependencies${NC}"
echo

# Check if the update script exists
if [ ! -f "scripts/update-flatpak-deps.py" ]; then
    echo -e "${RED}❌ Dependency update script not found!${NC}"
    exit 1
fi

# Run the dependency update script
echo -e "${YELLOW}📦 Checking PyPI for latest package versions...${NC}"
python3 scripts/update-flatpak-deps.py

# Check if any changes were made
if ! git diff-index --quiet HEAD -- io.github.tobagin.secrets.yml 2>/dev/null; then
    echo
    echo -e "${YELLOW}📝 Changes detected in Flatpak manifest:${NC}"
    git diff --no-index /dev/null io.github.tobagin.secrets.yml | grep -E '^[+-].*url:|^[+-].*sha256:' | head -10 || true
    echo
    echo -e "${BLUE}💡 Next steps:${NC}"
    echo "1. Review the changes: git diff io.github.tobagin.secrets.yml"
    echo "2. Test the Flatpak build: flatpak-builder --force-clean build-dir io.github.tobagin.secrets.yml"
    echo "3. Commit the changes: git add io.github.tobagin.secrets.yml && git commit -m 'chore: Update Flatpak dependencies'"
    echo
    echo -e "${YELLOW}⚠️  Remember to test the build before committing!${NC}"
else
    echo
    echo -e "${GREEN}✅ All dependencies are already up to date!${NC}"
fi
