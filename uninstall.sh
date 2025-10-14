#!/usr/bin/env bash
#
# Coaxial Recorder - Complete Uninstall Script
# Removes all installed components and data
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    printf "\n${BLUE}===================================================================${NC}\n"
    printf "${BLUE}$1${NC}\n"
    printf "${BLUE}===================================================================${NC}\n\n"
}

print_success() {
    printf "${GREEN}✓${NC} $1\n"
}

print_error() {
    printf "${RED}✗${NC} $1\n"
}

print_warning() {
    printf "${YELLOW}⚠${NC} $1\n"
}

print_info() {
    printf "${BLUE}ℹ${NC} $1\n"
}

# Confirm uninstallation
confirm_uninstall() {
    echo ""
    print_warning "⚠️  WARNING: This will remove Coaxial Recorder installation and some data!"
    echo ""
    echo "This will delete:"
    echo "  • Virtual environment (venv/)"
    echo "  • Local Python installations (python310/, python311/)"
    echo "  • Output directory"
    echo "  • Application logs"
    echo "  • Converted models"
    echo "  • Training logs"
    echo ""
    echo "The following will be PRESERVED:"
    echo "  • Voice recordings and datasets (voices/)"
    echo "  • Training checkpoints (training/checkpoints/)"
    echo "  • Checkpoints (checkpoints/)"
    echo "  • Models (models/)"
    echo ""
    echo "The following will be KEPT:"
    echo "  • This uninstall script"
    echo "  • Installation scripts (*.sh, *.bat)"
    echo "  • Documentation (*.md)"
    echo "  • Docker files (Dockerfile*, docker-compose.yml)"
    echo ""
    read -p "Are you sure you want to uninstall? [y/N]: " confirm

    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_info "Uninstallation cancelled."
        exit 0
    fi
}

# Remove virtual environment
remove_venv() {
    if [ -d "venv" ]; then
        print_info "Removing virtual environment..."
        rm -rf venv
        print_success "Virtual environment removed"
    else
        print_info "Virtual environment not found (already removed)"
    fi
}

# Remove local Python installations
remove_local_python() {
    print_info "Removing local Python installations..."

    if [ -d "python310" ]; then
        print_info "Removing python310..."
        rm -rf python310
        print_success "python310 removed"
    fi

    if [ -d "python311" ]; then
        print_info "Removing python311..."
        rm -rf python311
        print_success "python311 removed"
    fi

    # Remove any python3* directories
    for dir in python3*; do
        if [ -d "$dir" ] && [ "$dir" != "python310" ] && [ "$dir" != "python311" ]; then
            print_info "Removing $dir..."
            rm -rf "$dir"
            print_success "$dir removed"
        fi
    done
}

# Remove application data
remove_app_data() {
    print_info "Removing application data..."

    # Remove data directories (preserving voices, checkpoints, and models)
    directories=("output" "logs" "converted_models" "training/logs")

    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            print_info "Removing $dir..."
            rm -rf "$dir"
            print_success "$dir removed"
        fi
    done

    # Remove generated files
    files=("test_installation.py" "launch_complete.sh" "launch_complete.bat" "requirements_training_compatible.txt")

    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            print_info "Removing $file..."
            rm -f "$file"
            print_success "$file removed"
        fi
    done
}

# Remove Docker containers and images (if Docker is available)
remove_docker() {
    if command -v docker >/dev/null 2>&1; then
        print_info "Checking for Docker containers..."

        # Stop and remove containers
        if docker ps -a | grep -q "coaxial-recorder"; then
            print_info "Stopping Docker containers..."
            docker-compose --profile gpu --profile cpu down 2>/dev/null || true
            print_success "Docker containers stopped"
        fi

        # Remove images
        if docker images | grep -q "coaxial-recorder"; then
            print_info "Removing Docker images..."
            docker rmi coaxial-recorder:gpu coaxial-recorder:cpu 2>/dev/null || true
            print_success "Docker images removed"
        fi
    else
        print_info "Docker not available - skipping Docker cleanup"
    fi
}

# Clean conda cache (if conda is available)
clean_conda() {
    if command -v conda >/dev/null 2>&1; then
        print_info "Cleaning Conda cache..."
        conda clean --all -y >/dev/null 2>&1 || true
        print_success "Conda cache cleaned"
    fi
}

# Remove MFA from conda (if available)
remove_mfa_conda() {
    if command -v conda >/dev/null 2>&1; then
        print_info "Checking for MFA in Conda..."
        if conda list | grep -q "montreal-forced-aligner"; then
            print_info "Removing MFA from Conda..."
            conda remove montreal-forced-aligner -y >/dev/null 2>&1 || true
            print_success "MFA removed from Conda"
        else
            print_info "MFA not found in Conda"
        fi
    fi
}

# Final cleanup
final_cleanup() {
    print_info "Final cleanup..."

    # Remove any remaining __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    # Remove any .pyc files
    find . -name "*.pyc" -delete 2>/dev/null || true

    print_success "Cleanup completed"
}

# Main uninstall function
main() {
    print_header "🗑️  Coaxial Recorder - Complete Uninstall"

    # Confirm before proceeding
    confirm_uninstall

    echo ""
    print_header "Starting Uninstallation"

    # Remove components
    remove_venv
    remove_local_python
    remove_app_data
    remove_docker
    remove_mfa_conda
    clean_conda
    final_cleanup

    echo ""
    print_header "✅ Uninstallation Complete!"

    echo "Coaxial Recorder has been completely removed from your system."
    echo ""
    echo "What was removed:"
    echo "  • Virtual environment and all Python packages"
    echo "  • Local Python installations"
    echo "  • Output directory"
    echo "  • Application logs"
    echo "  • Converted models"
    echo "  • Training logs"
    echo "  • Docker containers and images"
    echo "  • MFA installation (if applicable)"
    echo ""
    echo "What was preserved:"
    echo "  • Voice recordings and datasets (voices/)"
    echo "  • Training checkpoints (training/checkpoints/)"
    echo "  • Checkpoints (checkpoints/)"
    echo "  • Models (models/)"
    echo ""
    echo "What was kept:"
    echo "  • Installation scripts (*.sh, *.bat)"
    echo "  • Documentation (*.md)"
    echo "  • Docker configuration files"
    echo "  • This uninstall script"
    echo ""
    echo "To reinstall:"
    echo "  bash install.sh"
    echo ""
    print_success "Uninstallation completed successfully!"
}

# Run main function
main "$@"
