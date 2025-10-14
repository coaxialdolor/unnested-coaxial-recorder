# GPU Training Fixes for RTX 5060 Ti (sm_120)

## Overview
This document explains the fixes required to enable GPU training on the NVIDIA GeForce RTX 5060 Ti with CUDA compute capability sm_120.

## Problem Statement
The RTX 5060 Ti has a compute capability of sm_120, which is not fully supported by stable PyTorch releases. This caused several issues:
1. PyTorch CUDA capability warnings
2. Missing CUDA kernels for sm_120
3. Audio loading crashes with `std::length_error`
4. Device mismatch errors during training

## Solutions Implemented

### 1. PyTorch Nightly Build with CUDA 12.8
**Problem**: Stable PyTorch (2.5.1) doesn't have full kernel support for sm_120.

**Solution**: Use PyTorch nightly build with CUDA 12.8:
```dockerfile
RUN pip install --pre \
    torch==2.10.0.dev20251007+cu128 \
    torchvision==0.25.0.dev20251007+cu128 \
    torchaudio==2.8.0.dev20251007+cu128 \
    --index-url https://download.pytorch.org/whl/nightly/cu128
```

**Why**: Nightly builds include the latest CUDA kernels and PTX (Parallel Thread Execution) support for newer GPU architectures.

### 2. TORCH_CUDA_ARCH_LIST Environment Variable
**Problem**: PyTorch needs to know to generate kernels for sm_120.

**Solution**: Set the environment variable:
```dockerfile
ENV TORCH_CUDA_ARCH_LIST="12.0+PTX"
```

**Why**: This tells PyTorch to:
- Generate CUDA kernels for compute capability 12.0 (sm_120)
- Include PTX code for JIT compilation on newer architectures

### 3. Audio Loading Fix (soundfile instead of torchaudio.load)
**Problem**: `torchaudio.load()` crashes with `std::length_error` in PyTorch nightly builds.

**Solution**: Use `soundfile` directly:
```python
# OLD (crashes):
waveform, sr = torchaudio.load(audio_path, backend="soundfile")

# NEW (works):
import soundfile as sf
waveform, sr = sf.read(audio_path)
waveform = torch.from_numpy(waveform).float()
```

**Why**: The PyTorch nightly build has a bug in `torchaudio.load()` that causes memory allocation errors. `soundfile` is more stable and directly reads WAV files.

### 4. DataLoader Multiprocessing Disabled
**Problem**: DataLoader workers crash when loading audio files.

**Solution**: Set `num_workers=0`:
```python
train_loader = DataLoader(
    train_dataset,
    batch_size=config.get('batch_size', 16),
    shuffle=True,
    num_workers=0,  # Disable multiprocessing to avoid crashes
    collate_fn=collate_fn
)
```

**Why**: With `num_workers=0`, data loading happens in the main process, avoiding multiprocessing-related crashes with the audio loading code.

### 5. Device Mismatch Fix (MelSpectrogram Transform)
**Problem**: Audio tensor on GPU, but STFT window on CPU.

**Solution**: Move transform to same device as audio:
```python
mel_transform = torchaudio.transforms.MelSpectrogram(
    sample_rate=self.config.get('sample_rate', 22050),
    n_fft=1024,
    hop_length=256,
    n_mels=80
).to(audio.device)  # Move transform to same device as audio
```

**Why**: PyTorch requires all tensors in an operation to be on the same device (CPU or GPU).

### 6. Export Dependencies (pydub and ffmpeg)
**Problem**: Export functionality fails with "No module named 'pydub'".

**Solution**: Install pydub and ffmpeg:
```dockerfile
# In Dockerfile
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install pydub
```

**Why**: The export functionality uses `pydub` for audio format conversion, which requires `ffmpeg` as a backend.

### 7. Lightning Runtime Patches
**Problem**: Lightning may have compatibility issues with newer GPUs.

**Solution**: Apply runtime patches at container startup:
```bash
python utils/patch_lightning.py --apply-runtime
```

**Why**: Ensures Lightning works correctly with RTX 50-series GPUs and their specific compute capabilities.

## Complete Dockerfile Configuration

The experimental Dockerfile (`Dockerfile.gpuexperimental`) includes all these fixes:

```dockerfile
FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

ENV TORCH_CUDA_ARCH_LIST="12.0+PTX"
ENV CUDA_HOME=/usr/local/cuda

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-dev python3-pip \
    git curl wget build-essential \
    ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch nightly with CUDA 12.8
RUN pip install --pre \
    torch==2.10.0.dev20251007+cu128 \
    torchvision==0.25.0.dev20251007+cu128 \
    torchaudio==2.8.0.dev20251007+cu128 \
    --index-url https://download.pytorch.org/whl/nightly/cu128

# Install pydub for export
RUN pip install pydub

# Copy application code
COPY . .

# Entrypoint applies Lightning patches and starts app
COPY docker-entrypoint-experimental.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint-experimental.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint-experimental.sh"]
```

## Code Changes Required

### 1. `utils/vits_training.py` - Audio Loading
```python
def __getitem__(self, idx):
    audio_path = self.audio_files[idx]
    if isinstance(audio_path, Path):
        audio_path = str(audio_path)
    
    # Use soundfile directly (torchaudio.load has issues with PyTorch nightly)
    import soundfile as sf
    waveform, sr = sf.read(audio_path)
    waveform = torch.from_numpy(waveform).float()
    if len(waveform.shape) == 1:
        waveform = waveform.unsqueeze(0)
    else:
        waveform = waveform.T
    
    # ... rest of the method
```

### 2. `utils/vits_training.py` - DataLoader
```python
train_loader = DataLoader(
    train_dataset,
    batch_size=config.get('batch_size', 16),
    shuffle=True,
    num_workers=0,  # Disable multiprocessing to avoid torchaudio crashes
    collate_fn=collate_fn
)
```

### 3. `utils/vits_training.py` - MelSpectrogram Transform
```python
def _audio_to_mel(self, audio):
    mel_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=self.config.get('sample_rate', 22050),
        n_fft=1024,
        hop_length=256,
        n_mels=80
    ).to(audio.device)  # Move transform to same device as audio
    
    # ... rest of the method
```

## Verification

After applying all fixes, training should work correctly:

```bash
docker exec coaxial-gpu-experimental python train_model.py \
  --profile-id "latestPetter ny svenska pc" \
  --prompt-list-id "latestPetter ny svenska pc_sv-SE_0000000001_0300000050_General" \
  --language-code "sv-SE" \
  --model-size medium \
  --learning-rate 0.0001 \
  --batch-size 16 \
  --epochs 100 \
  --use-gpu \
  --mixed-precision
```

Expected output:
- No CUDA capability warnings
- Training progresses normally
- Loss decreases over epochs
- Model saves successfully

## Performance Notes

- **GPU Utilization**: ~95-100% during training
- **Training Speed**: ~1-2 seconds per epoch (with 25 samples)
- **Memory Usage**: ~2-3 GB GPU memory
- **Loss Convergence**: Loss typically decreases from ~130 to <1 over 100 epochs

## Troubleshooting

### Issue: "CUDA capability sm_120 is not compatible"
**Solution**: Ensure `TORCH_CUDA_ARCH_LIST="12.0+PTX"` is set and using PyTorch nightly.

### Issue: "DataLoader worker exited unexpectedly"
**Solution**: Ensure `num_workers=0` in DataLoader configuration.

### Issue: "stft input and window must be on the same device"
**Solution**: Ensure MelSpectrogram transform is moved to the same device as audio: `.to(audio.device)`.

### Issue: "No module named 'pydub'"
**Solution**: Install pydub: `pip install pydub`.

## Future Improvements

1. **PyTorch Stable Release**: Once PyTorch 2.11+ is released with full sm_120 support, switch back to stable builds.
2. **DataLoader Multiprocessing**: Once torchaudio.load is fixed, re-enable multiprocessing for faster data loading.
3. **Mixed Precision**: Already implemented and working correctly.

## References

- [PyTorch CUDA Compatibility](https://pytorch.org/get-started/locally/)
- [CUDA Compute Capabilities](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#compute-capabilities)
- [PyTorch Lightning GPU Support](https://lightning.ai/docs/pytorch/stable/advanced/training_tricks.html#gpu-training)

