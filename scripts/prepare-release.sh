#!/bin/bash
# Release preparation script for Secrets Password Manager
# This script helps prepare a release for Flathub submission

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VERSION=${1:-"0.1.0"}

echo -e "${BLUE}🚀 Preparing release v${VERSION} for Secrets Password Manager${NC}"
echo

# Pre-flight checks
echo -e "${YELLOW}📋 Running pre-flight checks...${NC}"

# Update Flatpak dependencies
echo -e "${YELLOW}🔄 Updating Flatpak dependencies...${NC}"
if [ -f "scripts/update-flatpak-deps.py" ]; then
    python3 scripts/update-flatpak-deps.py

    # Check if any dependencies were updated
    if ! git diff-index --quiet HEAD -- io.github.tobagin.secrets.yml; then
        echo -e "${GREEN}✅ Flatpak dependencies updated${NC}"
        echo "Committing dependency updates..."
        git add io.github.tobagin.secrets.yml
        git commit -m "chore: Update Flatpak dependencies to latest versions

$(git diff HEAD~1 io.github.tobagin.secrets.yml | grep -E '^[+-].*url:|^[+-].*sha256:' | head -10)"
    else
        echo "✅ All Flatpak dependencies are up to date"
    fi
else
    echo "⚠️  Dependency update script not found, skipping..."
fi

# Check if git is clean
echo "Checking git status..."
git status --porcelain
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ Git working directory is not clean. Please commit or stash changes.${NC}"
    exit 1
else
    echo "✅ Git working directory is clean"
fi

# Check if on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠️  You're on branch '$CURRENT_BRANCH', not 'main'. Continue? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build and test
echo -e "${YELLOW}🔨 Building project...${NC}"
meson setup build --wipe
meson compile -C build

echo -e "${YELLOW}🧪 Running tests...${NC}"
if [ -f "run_tests.py" ]; then
    python3 run_tests.py
else
    echo "No tests found, skipping..."
fi

# Validate metadata
echo -e "${YELLOW}✅ Validating metadata...${NC}"

# Validate desktop file
if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate build/data/io.github.tobagin.secrets.desktop
    echo "✅ Desktop file is valid"
else
    echo "⚠️  desktop-file-validate not found, skipping validation"
fi

# Validate appdata
if command -v appstream-util >/dev/null 2>&1; then
    appstream-util validate build/data/io.github.tobagin.secrets.appdata.xml
    echo "✅ AppData file is valid"
else
    echo "⚠️  appstream-util not found, skipping validation"
fi

# Test Flatpak build (if flatpak-builder is available and not skipped)
echo -e "${YELLOW}📦 Testing Flatpak build...${NC}"
if [ "${SKIP_FLATPAK_TEST}" = "1" ]; then
    echo "⚠️  Flatpak build test skipped (SKIP_FLATPAK_TEST=1)"
elif command -v flatpak-builder >/dev/null 2>&1; then
    echo "Building Flatpak (this may take a while)..."
    flatpak-builder --force-clean --disable-rofiles-fuse flatpak-build io.github.tobagin.secrets.yml --install-deps-from=flathub
    echo "✅ Flatpak builds successfully"

    # Test run
    echo "Testing Flatpak run..."
    timeout 10s flatpak-builder --run flatpak-build io.github.tobagin.secrets.yml io.github.tobagin.secrets --help || true
    echo "✅ Flatpak runs successfully"

    # Cleanup
    rm -rf flatpak-build
else
    echo "⚠️  flatpak-builder not found, skipping Flatpak build test"
fi

# Update version in files
echo -e "${YELLOW}📝 Updating version to ${VERSION}...${NC}"

# Update meson.build (be more specific to avoid changing meson_version)
sed -i "s/project('secrets', version : '[^']*'/project('secrets', version : '${VERSION}'/" meson.build

# Update app_info.py
sed -i "s/VERSION = \"[^\"]*\"/VERSION = \"${VERSION}\"/" secrets/app_info.py

# Update appdata.xml.in release date
TODAY=$(date +%Y-%m-%d)
sed -i "s/date=\"[^\"]*\"/date=\"${TODAY}\"/" data/io.github.tobagin.secrets.appdata.xml.in

echo -e "${GREEN}✅ All checks passed!${NC}"
echo
echo -e "${BLUE}📋 Release checklist:${NC}"
echo "1. Review and commit version changes"
echo "2. Create and push git tag: git tag -a v${VERSION} -m 'Release v${VERSION}'"
echo "3. Update Flatpak manifest commit hash"
echo "4. Edit Flatpak manifest for any needed changes"
echo "5. Edit appdata file to add release notes"
echo "6. Commit manifest and appdata changes"
echo "7. Take screenshots and add to data/screenshots/"
echo "8. Submit to Flathub"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "  git add -A"
echo "  git commit -m 'Prepare release v${VERSION}'"
echo "  git tag -a v${VERSION} -m 'Release v${VERSION}'"
echo "  git push origin main --tags"
