#!/bin/bash
# Script to run the Secrets application in a development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default to 'builddir' if not specified by $MESON_BUILD_ROOT
BUILD_DIR="${MESON_BUILD_ROOT:-builddir}"
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}Secrets Password Manager - Development Runner${NC}"
echo "Project root: $PROJECT_ROOT"
echo "Build directory: $BUILD_DIR"
echo

# Function to check if meson build is configured
check_meson_build() {
    if [ ! -f "${BUILD_DIR}/meson-info/meson-info.json" ]; then
        echo -e "${RED}Error: Meson build directory '${BUILD_DIR}' not found or not configured.${NC}"
        echo -e "${YELLOW}Please run the following commands first:${NC}"
        echo "  meson setup ${BUILD_DIR}"
        echo "  meson compile -C ${BUILD_DIR}"
        return 1
    fi
    return 0
}

# Function to check if GResource file exists
check_gresource() {
    local gresource_path="${BUILD_DIR}/secrets/secrets.gresource"
    if [ ! -f "$gresource_path" ]; then
        echo -e "${YELLOW}Warning: GResource file not found at $gresource_path${NC}"
        echo -e "${YELLOW}Running meson compile to generate resources...${NC}"
        meson compile -C "${BUILD_DIR}"
        if [ ! -f "$gresource_path" ]; then
            echo -e "${RED}Error: Failed to generate GResource file${NC}"
            return 1
        fi
    fi
    return 0
}

# Function to run with meson devenv (preferred method)
run_with_meson() {
    echo -e "${GREEN}Running with meson devenv (recommended)...${NC}"
    cd "$PROJECT_ROOT"
    meson devenv -C "${BUILD_DIR}" python3 secrets/main.py "$@"
}

# Function to run directly (fallback method)
run_direct() {
    echo -e "${GREEN}Running directly...${NC}"
    cd "$PROJECT_ROOT"
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    python3 secrets/main.py "$@"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --direct     Run directly without meson devenv"
    echo "  --meson      Run with meson devenv (default)"
    echo "  --help       Show this help message"
    echo
    echo "Examples:"
    echo "  $0                    # Run with meson devenv"
    echo "  $0 --direct          # Run directly"
    echo "  $0 --verbose         # Pass --verbose to the application"
}

# Parse command line arguments
USE_MESON=true
SHOW_HELP=false

for arg in "$@"; do
    case $arg in
        --direct)
            USE_MESON=false
            shift
            ;;
        --meson)
            USE_MESON=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            # Keep other arguments to pass to the application
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    show_usage
    exit 0
fi

# Main execution
echo -e "${BLUE}Checking build environment...${NC}"

if [ "$USE_MESON" = true ]; then
    if check_meson_build && check_gresource; then
        run_with_meson "$@"
    else
        echo -e "${YELLOW}Falling back to direct execution...${NC}"
        run_direct "$@"
    fi
else
    run_direct "$@"
fi
