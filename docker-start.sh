#!/usr/bin/env bash
#
# Quick start script for Docker deployment
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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo ""
        echo "Install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker found: $(docker --version)"
}

# Check if Docker daemon is running
check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running!"
        echo ""
        echo "Start Docker Desktop or run: sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Check for NVIDIA GPU
check_nvidia() {
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
            print_success "NVIDIA GPU detected: $GPU_INFO"
            return 0
        fi
    fi
    print_warning "No NVIDIA GPU detected (will use CPU version)"
    return 1
}

# Check for NVIDIA Container Toolkit
check_nvidia_docker() {
    if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        print_success "NVIDIA Container Toolkit is working"
        return 0
    else
        print_warning "NVIDIA Container Toolkit not available"
        print_info "Install from: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        return 1
    fi
}

# Main script
main() {
    print_header "🚀 Coaxial Recorder - Docker Quick Start"

    # Check prerequisites
    print_info "Checking prerequisites..."
    check_docker
    check_docker_running

    # Detect GPU
    HAS_GPU=0
    if check_nvidia; then
        if check_nvidia_docker; then
            HAS_GPU=1
            PROFILE="gpu"
            print_success "Will use GPU version"
        else
            print_warning "GPU detected but Docker can't access it"
            print_warning "Falling back to CPU version"
            PROFILE="cpu"
        fi
    else
        PROFILE="cpu"
        print_info "Will use CPU version"
    fi

    echo ""

    # Ask user for confirmation
    if [ "$HAS_GPU" -eq 1 ]; then
        echo "Selected configuration:"
        echo "  • Profile: GPU-accelerated"
        echo "  • MFA Support: ✓ Yes (via Conda)"
        echo "  • Training Speed: Fast"
    else
        echo "Selected configuration:"
        echo "  • Profile: CPU-only"
        echo "  • MFA Support: ✓ Yes (via Conda)"
        echo "  • Training Speed: Slow"
    fi

    echo ""
    read -p "Continue with this configuration? [Y/n]: " confirm

    if [ "$confirm" = "n" ] || [ "$confirm" = "N" ]; then
        print_info "Cancelled by user"
        exit 0
    fi

    # Check if containers are already running
    if docker-compose ps | grep -q "Up"; then
        print_warning "Containers are already running"
        read -p "Restart them? [Y/n]: " restart
        if [ "$restart" != "n" ] && [ "$restart" != "N" ]; then
            print_info "Stopping existing containers..."
            docker-compose --profile gpu --profile cpu down
        else
            print_info "Using existing containers"
            echo ""
            print_success "Application is running at: http://localhost:8000"
            exit 0
        fi
    fi

    echo ""
    print_header "Building and Starting Container"

    # Build and start
    print_info "Building Docker image (this may take 10-15 minutes on first run)..."
    print_info "Downloading ~8GB of dependencies..."
    echo ""

    if docker-compose --profile "$PROFILE" up --build -d; then
        print_success "Container started successfully!"

        # Wait for health check
        echo ""
        print_info "Waiting for application to be ready..."
        sleep 5

        MAX_ATTEMPTS=30
        ATTEMPT=0
        while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
            if curl -f http://localhost:8000/health &> /dev/null; then
                print_success "Application is healthy!"
                break
            fi
            ATTEMPT=$((ATTEMPT + 1))
            sleep 2
            printf "."
        done

        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            print_warning "Health check timed out, but container may still be starting"
            print_info "Check logs with: docker-compose logs -f"
        fi

        echo ""
        print_header "🎉 Installation Complete!"

        echo "Access the application at:"
        printf "  ${GREEN}http://localhost:8000${NC}\n"
        echo ""

        echo "Useful commands:"
        echo "  • View logs:       docker-compose logs -f coaxial-$PROFILE"
        echo "  • Stop:            docker-compose --profile $PROFILE down"
        echo "  • Restart:         docker-compose --profile $PROFILE restart"
        echo "  • Shell access:    docker exec -it coaxial-recorder-$PROFILE bash"
        echo "  • Check GPU:       docker exec -it coaxial-recorder-$PROFILE nvidia-smi"
        echo "  • Test MFA:        docker exec -it coaxial-recorder-$PROFILE conda run -n coaxial mfa version"
        echo ""

        echo "Data directories (persistent):"
        echo "  • Voices:      $(pwd)/voices"
        echo "  • Output:      $(pwd)/output"
        echo "  • Checkpoints: $(pwd)/checkpoints"
        echo "  • Logs:        $(pwd)/logs"
        echo ""

        # Open browser
        if command -v xdg-open &> /dev/null; then
            read -p "Open browser now? [Y/n]: " open_browser
            if [ "$open_browser" != "n" ] && [ "$open_browser" != "N" ]; then
                xdg-open http://localhost:8000 &> /dev/null &
            fi
        elif command -v open &> /dev/null; then
            read -p "Open browser now? [Y/n]: " open_browser
            if [ "$open_browser" != "n" ] && [ "$open_browser" != "N" ]; then
                open http://localhost:8000 &> /dev/null &
            fi
        fi

    else
        print_error "Failed to start container!"
        echo ""
        echo "Check logs with: docker-compose logs"
        echo ""
        exit 1
    fi
}

# Run main
main "$@"

