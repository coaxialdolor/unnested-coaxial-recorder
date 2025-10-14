# Experimental Docker Setup Guide for RTX 5060 Ti

## Quick Start

### 1. Build the Docker Image

```bash
docker build -f Dockerfile.gpuexperimental -t coaxial-gpu:experimental .
```

This will:
- Install PyTorch nightly with CUDA 12.8
- Set up all dependencies including pydub and ffmpeg
- Apply all GPU training fixes automatically

### 2. Run the Container

```bash
docker run --gpus all \
  -p 8000:8000 \
  -v "%cd%/voices:/app/voices" \
  -v "%cd%/output:/app/output" \
  -v "%cd%/models:/app/models" \
  -v "%cd%/checkpoints:/app/checkpoints" \
  --name coaxial-gpu-experimental \
  -d \
  coaxial-gpu:experimental
```

**Note for Windows PowerShell**: Use `$PWD` instead of `%cd%`:
```powershell
docker run --gpus all `
  -p 8000:8000 `
  -v "$PWD/voices:/app/voices" `
  -v "$PWD/output:/app/output" `
  -v "$PWD/models:/app/models" `
  -v "$PWD/checkpoints:/app/checkpoints" `
  --name coaxial-gpu-experimental `
  -d `
  coaxial-gpu:experimental
```

### 3. Verify GPU is Working

```bash
docker exec coaxial-gpu-experimental nvidia-smi
```

You should see your RTX 5060 Ti listed.

### 4. Run Training

```bash
docker exec coaxial-gpu-experimental python train_model.py \
  --profile-id "YOUR_PROFILE_NAME" \
  --prompt-list-id "YOUR_PROMPT_LIST_ID" \
  --language-code "sv-SE" \
  --model-size medium \
  --learning-rate 0.0001 \
  --batch-size 16 \
  --epochs 100 \
  --use-gpu \
  --mixed-precision
```

## What Happens Automatically

When you build and run the Docker container, the following fixes are automatically applied:

1. **PyTorch Nightly Build**: Installs PyTorch 2.10.0.dev20251007+cu128 with CUDA 12.8 support
2. **CUDA Architecture**: Sets `TORCH_CUDA_ARCH_LIST="12.0+PTX"` for RTX 5060 Ti
3. **Audio Loading**: Uses `soundfile` instead of `torchaudio.load` (already in `utils/vits_training.py`)
4. **DataLoader**: Uses `num_workers=0` (already in `utils/vits_training.py`)
5. **Device Fixes**: MelSpectrogram transform device fix (already in `utils/vits_training.py`)
6. **Export Dependencies**: Installs `pydub` and `ffmpeg`
7. **Lightning Patches**: Applied automatically at container startup

## Container Startup Process

When the container starts, the entrypoint script (`docker-entrypoint-experimental.sh`) automatically:

1. Detects the GPU using `nvidia-smi`
2. Applies Lightning runtime patches for RTX 5060 Ti compatibility
3. Runs comprehensive CUDA sanity checks:
   - Basic CUDA operations
   - Conv2d operations
   - Matrix multiplication
4. Verifies GPU is ready for training
5. Starts the application

## Volume Mounts

The following directories should be mounted as volumes:

- `/app/voices` - Voice profiles and recordings
- `/app/output` - Training output and logs
- `/app/models` - Trained models
- `/app/checkpoints` - Training checkpoints

## Accessing the Web Interface

Once the container is running, access the web interface at:
```
http://localhost:8000
```

## Common Commands

### View Container Logs
```bash
docker logs coaxial-gpu-experimental
```

### Stop the Container
```bash
docker stop coaxial-gpu-experimental
```

### Start the Container
```bash
docker start coaxial-gpu-experimental
```

### Remove the Container
```bash
docker stop coaxial-gpu-experimental
docker rm coaxial-gpu-experimental
```

### Rebuild the Image
```bash
docker stop coaxial-gpu-experimental
docker rm coaxial-gpu-experimental
docker build -f Dockerfile.gpuexperimental -t coaxial-gpu:experimental .
docker run --gpus all -p 8000:8000 -v "%cd%/voices:/app/voices" -v "%cd%/output:/app/output" -v "%cd%/models:/app/models" -v "%cd%/checkpoints:/app/checkpoints" --name coaxial-gpu-experimental -d coaxial-gpu:experimental
```

## Troubleshooting

### GPU Not Detected
```bash
# Check if NVIDIA Docker runtime is installed
docker run --rm --gpus all nvidia/cuda:12.8.0-runtime-ubuntu22.04 nvidia-smi
```

If this fails, you need to install NVIDIA Container Toolkit:
- Windows: Install NVIDIA Container Toolkit from Docker Desktop settings
- Linux: Follow [NVIDIA Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### Training Fails with CUDA Errors
1. Check GPU is detected: `docker exec coaxial-gpu-experimental nvidia-smi`
2. Check PyTorch CUDA version: `docker exec coaxial-gpu-experimental python -c "import torch; print(torch.version.cuda)"`
3. Check TORCH_CUDA_ARCH_LIST: `docker exec coaxial-gpu-experimental env | grep TORCH_CUDA_ARCH_LIST`

### Export Fails
Make sure `pydub` and `ffmpeg` are installed:
```bash
docker exec coaxial-gpu-experimental python -c "import pydub; print('pydub OK')"
docker exec coaxial-gpu-experimental ffmpeg -version
```

## Performance Expectations

With RTX 5060 Ti and the experimental setup:
- **Training Speed**: ~1-2 seconds per epoch (with 25 samples)
- **GPU Utilization**: ~95-100%
- **Memory Usage**: ~2-3 GB GPU memory
- **Loss Convergence**: Typically from ~130 to <1 over 100 epochs

## Updating the Code

If you make changes to the code, you need to rebuild the image:

```bash
# Stop and remove old container
docker stop coaxial-gpu-experimental
docker rm coaxial-gpu-experimental

# Rebuild image
docker build -f Dockerfile.gpuexperimental -t coaxial-gpu:experimental .

# Run new container
docker run --gpus all -p 8000:8000 -v "%cd%/voices:/app/voices" -v "%cd%/output:/app/output" -v "%cd%/models:/app/models" -v "%cd%/checkpoints:/app/checkpoints" --name coaxial-gpu-experimental -d coaxial-gpu:experimental
```

## Next Steps

Once training is complete:
1. Models are saved to `models/checkpoints/final_model.ckpt`
2. You can export the dataset using the web interface
3. You can test the trained model using the inference API

## Support

For issues or questions:
1. Check `GPU_TRAINING_FIXES.md` for detailed explanation of all fixes
2. Check container logs: `docker logs coaxial-gpu-experimental`
3. Verify GPU setup: `docker exec coaxial-gpu-experimental nvidia-smi`

