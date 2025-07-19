#!/bin/bash
# Convenience script for building the Secrets password manager application

set -e

# Configuration
APP_ID="io.github.tobagin.secrets"
PROJECT_NAME="Secrets"
BUILD_DIR=".flatpak-builder"
REPO_DIR="repo"

# Default values
MANIFEST=""
INSTALL=false
FORCE_CLEAN=false
DEV_MODE=false
VERBOSE=false
SKIP_VERSION_SYNC=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Build the Secrets password manager application using Flatpak.

OPTIONS:
    --dev               Build from local sources (development mode)
    --install           Install the application after successful build
    --force-clean       Force a clean build, removing old build directory
    --skip-version-sync Skip automatic version synchronization
    --verbose           Enable verbose output
    -h, --help          Show this help message

EXAMPLES:
    $0 --dev --install          Build from local sources and install
    $0 --force-clean            Clean build from production sources
    $0 --dev --verbose          Development build with verbose output

NOTES:
    - By default, builds from production manifest (packaging/flatpak/${APP_ID}.yml)
    - Use --dev flag to build from local sources (packaging/flatpak/${APP_ID}.dev.yml)
    - Use --install to install after build completes
    - Use --force-clean to ensure a fresh build environment

EOF
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking build dependencies..."
    
    local missing_deps=()
    
    # Check for required tools
    if ! command -v flatpak-builder &> /dev/null; then
        missing_deps+=("flatpak-builder")
    fi
    
    if ! command -v flatpak &> /dev/null; then
        missing_deps+=("flatpak")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_info "Please install them with your package manager:"
        print_info "  Ubuntu/Debian: sudo apt install flatpak flatpak-builder"
        print_info "  Fedora: sudo dnf install flatpak flatpak-builder"
        print_info "  Arch: sudo pacman -S flatpak flatpak-builder"
        exit 1
    fi
    
    # Check for GNOME runtime
    if ! flatpak info org.gnome.Platform//48 &> /dev/null; then
        print_warning "GNOME Platform runtime not found. Installing..."
        flatpak install -y flathub org.gnome.Platform//48 org.gnome.Sdk//48
    fi
}

# Function to select manifest
select_manifest() {
    if [ "$DEV_MODE" = true ]; then
        MANIFEST="packaging/flatpak/${APP_ID}.dev.yml"
        print_info "Using development manifest: $MANIFEST"
    else
        MANIFEST="packaging/flatpak/${APP_ID}.yml"
        print_info "Using production manifest: $MANIFEST"
    fi
    
    if [ ! -f "$MANIFEST" ]; then
        print_error "Manifest file not found: $MANIFEST"
        exit 1
    fi
}

# Function to clean build environment
clean_build() {
    if [ "$FORCE_CLEAN" = true ] || [ "$DEV_MODE" = true ]; then
        print_info "Cleaning build environment..."
        rm -rf "$BUILD_DIR" "$REPO_DIR"
        print_success "Build environment cleaned"
    fi
}

# Function to sync version information
sync_version() {
    if [ "$SKIP_VERSION_SYNC" = true ]; then
        print_info "Skipping version synchronization (--skip-version-sync specified)"
        return 0
    fi
    
    print_info "Synchronizing version information..."
    
    # Check if we have the sync script
    if [ -f "scripts/sync_version.py" ]; then
        if python3 scripts/sync_version.py > /dev/null 2>&1; then
            print_success "Version synchronization completed"
        else
            print_warning "Version synchronization failed, continuing with build"
        fi
    else
        print_warning "Version sync script not found, skipping synchronization"
    fi
    
    # Comprehensive version validation - MANDATORY for production builds
    if [ -f "scripts/comprehensive_version_check.py" ]; then
        print_info "Running pre-build version validation..."
        validation_output=$(python3 scripts/comprehensive_version_check.py 2>&1)
        validation_exit_code=$?
        
        if [ $validation_exit_code -eq 0 ]; then
            print_success "Pre-build version validation passed"
        else
            print_error "Pre-build version validation failed!"
            echo "Details:"
            echo "$validation_output"
            echo
            print_info "Version validation is mandatory for production builds."
            read -p "Attempt automatic fix? (Y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                print_info "Attempting automatic fix..."
                if python3 scripts/comprehensive_version_check.py --auto-fix; then
                    print_info "Auto-fix completed, re-running validation..."
                    # Re-run validation after fix
                    if python3 scripts/comprehensive_version_check.py > /dev/null 2>&1; then
                        print_success "Version validation passed after auto-fix"
                    else
                        print_error "Auto-fix failed, validation still failing"
                        print_error "Build cannot continue with version inconsistencies"
                        exit 1
                    fi
                else
                    print_error "Auto-fix failed"
                    print_error "Build cannot continue with version inconsistencies"
                    exit 1
                fi
            else
                print_error "Build cannot continue without version validation"
                echo "Please fix version inconsistencies manually and try again."
                exit 1
            fi
        fi
    elif [ -f "scripts/validate_version.py" ]; then
        # Fallback to simple validation
        if python3 scripts/validate_version.py > /dev/null 2>&1; then
            print_success "Basic version validation passed"
        else
            print_warning "Basic version validation failed"
        fi
    fi
}

# Function to build application
build_app() {
    print_info "Building $PROJECT_NAME..."
    
    # Prepare flatpak-builder arguments
    local builder_args=()
    
    if [ "$VERBOSE" = true ]; then
        builder_args+=("--verbose")
    fi
    
    if [ "$FORCE_CLEAN" = true ]; then
        builder_args+=("--force-clean")
    fi
    
    # Add repo directory
    builder_args+=("--repo=$REPO_DIR")
    
    # Add disable-rofiles-fuse for better compatibility
    builder_args+=("--disable-rofiles-fuse")
    
    # Add default-branch
    builder_args+=("--default-branch=main")
    
    # Run flatpak-builder
    print_info "Running: flatpak-builder ${builder_args[*]} $BUILD_DIR $MANIFEST"
    
    if flatpak-builder "${builder_args[@]}" "$BUILD_DIR" "$MANIFEST"; then
        print_success "Build completed successfully"
        
        # Run post-build validation
        post_build_validation
    else
        print_error "Build failed"
        exit 1
    fi
}

# Function to run post-build validation
post_build_validation() {
    print_info "Running post-build validation..."
    
    # Re-run comprehensive version check to ensure build didn't change anything
    if [ -f "scripts/comprehensive_version_check.py" ]; then
        if python3 scripts/comprehensive_version_check.py > /dev/null 2>&1; then
            print_success "Post-build version validation passed"
        else
            print_error "Post-build version validation failed!"
            print_error "Build process may have introduced version inconsistencies"
            echo "Running detailed validation check..."
            python3 scripts/comprehensive_version_check.py
            exit 1
        fi
    fi
    
    # Validate Flatpak manifest version matches meson.build
    if [ -f "scripts/validate_flatpak_version.py" ]; then
        print_info "Validating Flatpak package version..."
        if python3 scripts/validate_flatpak_version.py "$MANIFEST" > /dev/null 2>&1; then
            print_success "Flatpak package version validation passed"
        else
            print_warning "Flatpak package version validation failed"
            python3 scripts/validate_flatpak_version.py "$MANIFEST"
        fi
    fi
    
    # Check if built files contain expected version
    print_info "Validating built package integrity..."
    
    # Extract the expected version from meson.build
    if [ -f "meson.build" ]; then
        expected_version=$(python3 -c "
import re
with open('meson.build', 'r') as f:
    content = f.read()
    match = re.search(r\"version\s*:\s*['\\\"]([^'\\\"]+)['\\\"],\", content)
    if match:
        print(match.group(1))
    else:
        print('UNKNOWN')
" 2>/dev/null)
        
        if [ "$expected_version" != "UNKNOWN" ] && [ -n "$expected_version" ]; then
            print_info "Expected version: $expected_version"
            
            # Check if the build directory contains files with the expected version
            if find "$BUILD_DIR" -name "*.py" -exec grep -l "__version__.*$expected_version" {} \; > /dev/null 2>&1; then
                print_success "Built files contain expected version: $expected_version"
            else
                print_warning "Could not verify version in built files"
            fi
        else
            print_warning "Could not extract version from meson.build"
        fi
    fi
    
    print_success "Post-build validation completed"
}

# Function to install application
install_app() {
    if [ "$INSTALL" = true ]; then
        print_info "Installing $PROJECT_NAME..."
        
        # Add local repo if not already added
        if ! flatpak remote-list | grep -q "secrets-local"; then
            flatpak remote-add --user --no-gpg-verify secrets-local "$REPO_DIR"
        fi
        
        # Determine the correct app ID based on mode
        local install_app_id="$APP_ID"
        if [ "$DEV_MODE" = true ]; then
            install_app_id="${APP_ID}.dev"
        fi
        
        # Install/update the application (force reinstall if already installed)
        if flatpak install -y --user --reinstall secrets-local "$install_app_id"; then
            print_success "Installation completed successfully"
            print_info "You can now run the application with:"
            print_info "  flatpak run $install_app_id"
        else
            print_error "Installation failed"
            exit 1
        fi
    fi
}

# Function to show build summary
show_summary() {
    local display_app_id="$APP_ID"
    if [ "$DEV_MODE" = true ]; then
        display_app_id="${APP_ID}.dev"
    fi
    
    print_success "Build Summary:"
    echo "  Application: $PROJECT_NAME"
    echo "  App ID: $display_app_id"
    echo "  Manifest: $MANIFEST"
    echo "  Build Mode: $([ "$DEV_MODE" = true ] && echo "Development" || echo "Production")"
    echo "  Installed: $([ "$INSTALL" = true ] && echo "Yes" || echo "No")"
    
    # Show version information
    if [ -f "meson.build" ]; then
        local version=$(python3 -c "
import re
with open('meson.build', 'r') as f:
    content = f.read()
    match = re.search(r\"version\s*:\s*['\\\"]([^'\\\"]+)['\\\"],\", content)
    if match:
        print(match.group(1))
    else:
        print('UNKNOWN')
" 2>/dev/null)
        echo "  Version: $version"
        
        # Version validation status
        if [ -f "scripts/comprehensive_version_check.py" ]; then
            if python3 scripts/comprehensive_version_check.py > /dev/null 2>&1; then
                echo "  Version Validation: ✓ PASSED"
            else
                echo "  Version Validation: ✗ FAILED"
            fi
        fi
    fi
    
    if [ "$INSTALL" = true ]; then
        echo ""
        print_info "To run the application:"
        print_info "  flatpak run $display_app_id"
        echo ""
        print_info "To uninstall:"
        print_info "  flatpak uninstall $display_app_id"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --install)
            INSTALL=true
            shift
            ;;
        --force-clean)
            FORCE_CLEAN=true
            shift
            ;;
        --skip-version-sync)
            SKIP_VERSION_SYNC=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_info "Starting build process for $PROJECT_NAME"
    
    # Check if we're in the right directory
    if [ ! -f "meson.build" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    check_dependencies
    select_manifest
    sync_version
    clean_build
    build_app
    install_app
    show_summary
    
    print_success "All done!"
}

# Run main function
main