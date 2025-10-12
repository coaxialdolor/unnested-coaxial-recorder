# Docker Setup Guide - GPU + MFA Support

## Overview

This Docker setup provides a **completely self-contained** environment with:
- ✅ NVIDIA GPU support (CUDA 12.1) - `Dockerfile.gpu`
- ✅ Apple Silicon ARM64 support (M1/M2/M3) - `Dockerfile.arm64` ⭐ NEW
- ✅ CPU-only x86_64 support - `Dockerfile.cpu`
- ✅ Montreal Forced Aligner (MFA) via Conda
- ✅ All dependencies pre-installed
- ✅ No need to install Conda on host system
- ✅ Works on Linux, Windows, and macOS

## Which Docker Image Should I Use?

| Your System | Recommended Image | Command | Performance |
|-------------|-------------------|---------|-------------|
| **NVIDIA GPU** (RTX 30/40/50-series) | `Dockerfile.gpu` | `--profile gpu` | ⚡ Fastest (GPU-accelerated) |
| **Apple Silicon** (M1/M2/M3 Mac) | `Dockerfile.arm64` | `--profile arm64` | ✅ Good (ARM64-optimized) |
| **Intel/AMD CPU** (No GPU) | `Dockerfile.cpu` | `--profile cpu` | ⚠️ Slower (CPU-only) |
| **Apple Silicon** (Best performance) | Native install | `bash install.sh` | ⚡⚡ Fastest (MPS support) |

**Recommendation for M1/M2/M3 Macs**: Use **native installation** (`bash install.sh`) for best performance, as it can leverage Metal Performance Shaders (MPS). Use Docker ARM64 only if you need isolation.

## Quick Start

### Prerequisites

**For GPU version (NVIDIA):**
1. Docker Engine 20.10+
2. NVIDIA GPU with driver 525.60.13+
3. NVIDIA Container Toolkit

**For CPU version:**
1. Docker Engine 20.10+

**For ARM64 version (Apple Silicon M1/M2/M3):**
1. Docker Desktop for Mac 4.0+
2. M1, M2, or M3 Mac

### Option 1: GPU Version (Recommended for NVIDIA GPUs)

```bash
# Build and start with GPU support
docker-compose --profile gpu up -d

# View logs
docker-compose logs -f coaxial-gpu

# Open browser to http://localhost:8000
```

### Option 2: ARM64 Version (For Apple Silicon Macs) ⭐ NEW

```bash
# Build and start on M1/M2/M3 Mac
docker-compose --profile arm64 up -d

# Or use the apple-silicon alias
docker-compose --profile apple-silicon up -d

# View logs
docker-compose logs -f coaxial-arm64

# Open browser to http://localhost:8000
```

**Note**: This version is optimized for Apple Silicon and includes MFA support. While it runs CPU-only in Docker, it's ARM64-native for better performance on M-series Macs.

### Option 3: CPU Version (For x86_64 Systems without GPU)

```bash
# Build and start CPU-only
docker-compose --profile cpu up -d

# View logs
docker-compose logs -f coaxial-cpu

# Open browser to http://localhost:8000
```

## Installation Steps

### Step 1: Install Docker

#### Ubuntu/Debian
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA Container Toolkit (for GPU)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

#### Windows
```powershell
# Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop

# Enable WSL 2 backend (required for GPU)
wsl --install

# Install NVIDIA drivers
# Download from: https://www.nvidia.com/Download/index.aspx
```

#### macOS (Apple Silicon M1/M2/M3)
```bash
# Install Docker Desktop for Mac
# Download from: https://www.docker.com/products/docker-desktop

# For Apple Silicon Macs, use the ARM64 version:
docker-compose --profile arm64 up -d

# Note: GPU support on macOS is limited to Metal API
# The ARM64 Docker image is CPU-only but ARM64-optimized
# For best performance on M-series Macs, use native installation instead
```

### Step 2: Verify NVIDIA Setup (GPU only)

```bash
# Test NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Should show your GPU(s)
```

### Step 3: Build and Run

```bash
# Clone or download project
cd coaxial-recorder

# GPU version (NVIDIA)
docker-compose --profile gpu up --build -d

# OR ARM64 version (Apple Silicon)
docker-compose --profile arm64 up --build -d

# OR CPU version (x86_64)
docker-compose --profile cpu up --build -d
```

## Usage

### Starting/Stopping

```bash
# Start
docker-compose --profile gpu up -d      # NVIDIA GPU
docker-compose --profile arm64 up -d    # Apple Silicon
docker-compose --profile cpu up -d      # CPU-only

# Stop
docker-compose --profile gpu down       # NVIDIA GPU
docker-compose --profile arm64 down     # Apple Silicon
docker-compose --profile cpu down       # CPU-only

# Restart
docker-compose --profile gpu restart    # NVIDIA GPU
docker-compose --profile arm64 restart  # Apple Silicon
docker-compose --profile cpu restart    # CPU-only

# View logs
docker-compose logs -f
```

### Accessing the Application

- **Web Interface:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Running Commands Inside Container

```bash
# Get a shell
docker exec -it coaxial-recorder-gpu bash

# Run training script
docker exec -it coaxial-recorder-gpu conda run -n coaxial python train_model.py

# Check GPU
docker exec -it coaxial-recorder-gpu nvidia-smi

# Test MFA
docker exec -it coaxial-recorder-gpu conda run -n coaxial mfa version
```

### Data Persistence

Data is automatically persisted in these directories on your host:
- `./voices/` - Voice profiles and recordings
- `./output/` - Exported datasets and models
- `./checkpoints/` - Training checkpoints
- `./logs/` - Application and training logs

## Advanced Configuration

### Custom PyTorch CUDA Version

Edit `Dockerfile.gpu` line 49:

```dockerfile
# For CUDA 12.8 (RTX 5060 Ti)
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128

# For CUDA 11.8 (older GPUs)
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Resource Limits

Edit `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 16G      # Adjust based on GPU RAM
      cpus: '8'        # Adjust based on CPU cores
```

### Multiple GPUs

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0,1  # Use first two GPUs
```

### Custom Port

```yaml
ports:
  - "8080:8000"  # Access via http://localhost:8080
```

## Building Images

### Build GPU Image

```bash
docker build -f Dockerfile.gpu -t coaxial-recorder:gpu .
```

### Build CPU Image

```bash
docker build -f Dockerfile.cpu -t coaxial-recorder:cpu .
```

### Multi-platform Build (Advanced)

```bash
# Build for multiple architectures
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
    -f Dockerfile.gpu -t coaxial-recorder:gpu --push .
```

## Troubleshooting

### GPU Not Detected

**Problem:** Container doesn't see GPU

**Solutions:**
```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker can access GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Restart Docker daemon
sudo systemctl restart docker

# Check NVIDIA Container Toolkit
sudo apt-get install --reinstall nvidia-container-toolkit
sudo systemctl restart docker
```

### Out of Memory

**Problem:** CUDA out of memory errors

**Solutions:**
1. Reduce batch size in training config
2. Increase Docker memory limit
3. Close other GPU applications

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 24G  # Increase this
```

### MFA Not Found

**Problem:** `mfa: command not found`

**Solution:**
```bash
# Check conda environment
docker exec -it coaxial-recorder-gpu conda run -n coaxial mfa version

# Rebuild container
docker-compose --profile gpu build --no-cache
```

### Slow Build Time

**Problem:** Docker build takes too long

**Solutions:**
1. Use pre-built image (if available)
2. Enable BuildKit:
   ```bash
   export DOCKER_BUILDKIT=1
   docker-compose build
   ```
3. Increase Docker resources in Docker Desktop settings

### Permission Errors

**Problem:** Can't write to volumes

**Solution:**
```bash
# Fix permissions
sudo chown -R $USER:$USER voices output checkpoints logs

# Or run container as specific user
docker run --user $(id -u):$(id -g) ...
```

## Performance Comparison

| Setup | MFA Support | GPU Training | Installation Time | Disk Space |
|-------|-------------|--------------|-------------------|------------|
| **Docker GPU** | ✅ Yes | ✅ Fast | 10-15 min | ~8 GB |
| **Docker CPU** | ✅ Yes | ⚠️ Slow | 5-10 min | ~4 GB |
| **Local pip** | ❌ No (Windows/Ubuntu) | ✅ Fast | 5-15 min | ~3 GB |
| **Local Conda** | ✅ Yes | ✅ Fast | 15-20 min | ~5 GB |

## Why Use Docker?

### Advantages ✅
- **Self-contained:** Everything included, no host dependencies
- **MFA works:** Conda + MFA pre-installed and tested
- **Reproducible:** Same environment everywhere
- **Easy cleanup:** `docker-compose down` removes everything
- **Isolated:** Doesn't affect host system
- **GPU support:** NVIDIA GPU works out of the box

### Disadvantages ⚠️
- Requires Docker installation
- Slightly larger disk usage
- Initial build time (one-time)
- May have slight performance overhead

## Docker vs Native Installation

**Use Docker if:**
- ✅ You want MFA without Conda on host
- ✅ You want guaranteed reproducibility
- ✅ You want easy cleanup
- ✅ You're deploying to servers

**Use Native if:**
- ✅ You already have Conda installed
- ✅ You want minimal disk usage
- ✅ You need direct GPU access for development
- ✅ Docker not available in your environment

## Pre-built Images (Future)

Once we publish to Docker Hub, you can skip building:

```bash
# Pull pre-built image
docker pull coaxialrecorder/coaxial-recorder:gpu

# Run directly
docker run -d --gpus all -p 8000:8000 \
  -v $(pwd)/voices:/app/voices \
  -v $(pwd)/output:/app/output \
  coaxialrecorder/coaxial-recorder:gpu
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile.gpu
          push: true
          tags: coaxialrecorder/coaxial-recorder:latest
```

## Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coaxial-recorder
spec:
  replicas: 1
  selector:
    matchLabels:
      app: coaxial-recorder
  template:
    metadata:
      labels:
        app: coaxial-recorder
    spec:
      containers:
      - name: coaxial-recorder
        image: coaxialrecorder/coaxial-recorder:gpu
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1
        volumeMounts:
        - name: data
          mountPath: /app/voices
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: coaxial-data
```

## Summary

### Quick Commands Reference

```bash
# GPU version
docker-compose --profile gpu up -d              # Start
docker-compose logs -f coaxial-gpu              # Logs
docker exec -it coaxial-recorder-gpu bash       # Shell
docker-compose --profile gpu down               # Stop

# CPU version
docker-compose --profile cpu up -d              # Start
docker-compose logs -f coaxial-cpu              # Logs
docker exec -it coaxial-recorder-cpu bash       # Shell
docker-compose --profile cpu down               # Stop

# Both
docker-compose ps                                # Status
docker-compose restart                           # Restart
docker system prune -a                          # Clean up
```

### What You Get

✅ **Working out of the box:**
- Python 3.10
- PyTorch with CUDA 12.1 (GPU) or CPU
- Montreal Forced Aligner via Conda
- All dependencies
- MFA English models pre-downloaded
- GPU support (NVIDIA)
- Persistent data storage

**No manual installation needed!** 🎉

