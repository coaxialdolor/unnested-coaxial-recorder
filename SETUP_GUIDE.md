# Coaxial Recorder - Quick Setup Guide

## Installation

### Linux / macOS / WSL

```bash
# Run the installer
bash install.sh
```

### Windows (Git Bash / Cygwin)

```bash
# Make sure you're using Git Bash, Cygwin, or similar
# NOT Windows CMD or PowerShell
bash install.sh
```

**Note:** On Windows, make sure you have Python installed from python.org (not Microsoft Store version).

The installer automatically:
- ✅ Detects your Python version
- ✅ Detects your GPU (if any)
- ✅ Installs correct PyTorch for your hardware
- ✅ Tests GPU compatibility
- ✅ Installs all dependencies

## Python Version Compatibility

| Version | Status | MFA Support | Notes |
|---------|--------|-------------|-------|
| **3.10** | ✅ **Best** | ✅ Full | All features work perfectly |
| **3.11** | ✅ Good | ✅ Yes | MFA updated to 3.x, works well |
| **3.12+** | ⚠️ Limited | ❌ No | MFA skipped, core features work |

### Recommended: Python 3.10

```bash
# Install with pyenv (recommended)
brew install pyenv
pyenv install 3.10.13
pyenv local 3.10.13

# Then run installer
bash install.sh
```

## GPU Compatibility (RTX 5060 Ti Support)

The installer **automatically detects your GPU** and installs the correct PyTorch version:

| GPU Series | Compute Capability | PyTorch Build | Auto-Installed |
|------------|-------------------|---------------|----------------|
| RTX 5060 Ti / 50-series | 12.0 (sm_120) | CUDA 12.8 (cu128) | ✅ Yes |
| RTX 4090 / 40-series | 8.9 (sm_89) | CUDA 12.1 (cu121) | ✅ Yes |
| RTX 3090 / 30-series | 8.6 (sm_86) | CUDA 11.8 (cu118) | ✅ Yes |
| Older GPUs | <8.6 | CUDA 11.8 (cu118) | ✅ Yes |
| No GPU / macOS | N/A | CPU/MPS | ✅ Yes |

### Verify GPU After Installation

```bash
# Activate environment
source venv/bin/activate

# Check GPU status
python utils/gpu_compat.py
```

## Quick Commands

```bash
# Install everything
bash install.sh

# Test installation
python test_installation.py

# Check GPU compatibility
python utils/gpu_compat.py

# Start application
python app.py
```

## Troubleshooting

### Script Hangs
**Cause:** Running with `sh` instead of `bash`
**Fix:** Use `bash install.sh` not `sh install.sh`

### MFA Won't Install
**Cause:** Python 3.12+ doesn't support MFA dependencies
**Fix:** Install Python 3.10 or 3.11, or continue without MFA (core features still work)

### GPU Not Working
**Cause:** Wrong PyTorch version for your GPU
**Fix:** Run `python utils/gpu_compat.py` and follow recommendations

### "no kernel image available"
**Cause:** RTX 50-series needs CUDA 12.8+
**Fix:**
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
```

## What Each Python Version Gets You

### Python 3.10 ✅
- Recording interface ✅
- Audio processing ✅
- Dataset export ✅
- GPU training ✅
- Montreal Forced Aligner ✅
- Phoneme alignment ✅
- **All features available**

### Python 3.11 ✅
- Recording interface ✅
- Audio processing ✅
- Dataset export ✅
- GPU training ✅
- Montreal Forced Aligner ✅ (MFA 3.x)
- Phoneme alignment ⚠️ (may have minor issues)
- **Most features available**

### Python 3.12 ⚠️
- Recording interface ✅
- Audio processing ✅
- Dataset export ✅
- GPU training ✅
- Montreal Forced Aligner ❌ (not compatible)
- Phoneme alignment ❌ (not available)
- **Core features only**

## Best Setup for RTX 5060 Ti

```bash
# 1. Install Python 3.10
brew install pyenv
pyenv install 3.10.13
cd /path/to/coaxial-recorder
pyenv local 3.10.13

# 2. Clean any existing install
rm -rf venv python311

# 3. Run installer
bash install.sh

# Result:
# ✅ Python 3.10 (all packages compatible)
# ✅ PyTorch with CUDA 12.8 (RTX 5060 Ti support)
# ✅ Montreal Forced Aligner (full features)
# ✅ GPU accelerated training
# ✅ Everything works!
```

## Support

Check installation:
```bash
python test_installation.py
python utils/gpu_compat.py
python --version
nvidia-smi  # if you have GPU
```

## Summary

- **Use Python 3.10 for best results**
- **Run with `bash install.sh` not `sh install.sh`**
- **RTX 5060 Ti and all GPUs auto-detected and configured**
- **Python 3.12 works but skips MFA**
- **GPU testing built into installer**

