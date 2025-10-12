# Montreal Forced Aligner (MFA) - Installation Guide

## What is MFA?

**Montreal Forced Aligner** is a tool for automatic phoneme alignment in speech audio. It maps audio segments to their corresponding phonemes with precise timing.

## Do You Need It?

### ❌ You DON'T need MFA for:
- ✅ Recording voice samples
- ✅ Creating and managing datasets
- ✅ Exporting datasets for training
- ✅ Using pre-trained Piper TTS models
- ✅ Basic TTS inference
- ✅ 90% of use cases

### ✅ You DO need MFA for:
- Training custom Piper TTS models (improves quality)
- Advanced phoneme-level audio analysis
- Research requiring precise phoneme alignments
- Professional TTS model development

## Why MFA is Tricky to Install

MFA has **complex binary dependencies** that vary by platform:
- Requires specific system libraries (Kaldi, OpenFST, etc.)
- Different build requirements per OS
- Limited pre-built pip wheels
- **Best installed via Conda** on most systems

## Installation by Platform

### Ubuntu / Debian Linux

#### Option 1: Conda (Recommended)

```bash
# Install Miniconda if you don't have it
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Install MFA
conda install -c conda-forge montreal-forced-aligner

# Verify installation
mfa version
```

#### Option 2: Build from Source

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y build-essential libopenblas-dev python3-dev

# Install MFA (may require compilation)
pip install montreal-forced-aligner

# If that fails, try:
pip install --no-binary montreal-forced-aligner montreal-forced-aligner
```

### macOS

#### Option 1: Conda (Recommended)

```bash
# Install Miniconda
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh

# Or for Apple Silicon:
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh

# Install MFA
conda install -c conda-forge montreal-forced-aligner

# Verify
mfa version
```

#### Option 2: Homebrew + pip

```bash
# Install dependencies
brew install openssl readline sqlite3 xz zlib

# Install MFA
pip install montreal-forced-aligner
```

### Windows

#### Only Option: Conda

MFA **does not work with pip on Windows**. You must use Conda:

```bash
# Download Miniconda from:
# https://docs.conda.io/en/latest/miniconda.html

# After installation, in Anaconda Prompt or PowerShell:
conda install -c conda-forge montreal-forced-aligner

# Verify
mfa version
```

## Using MFA with Virtual Environments

### If You Installed via Conda

MFA creates its own Conda environment and can be used independently:

```bash
# Activate your venv for the main app
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# MFA will be available system-wide (from Conda)
mfa align /path/to/audio /path/to/transcripts english_us_arpa output/
```

### Mixed Environment Setup

```bash
# Your project venv
source venv/bin/activate
python train_model.py  # Uses venv Python and packages

# MFA is called as subprocess
# train_model.py internally calls: subprocess.run(['mfa', 'align', ...])
# This uses the Conda-installed MFA
```

## Verifying MFA Installation

### Test 1: Command Line

```bash
mfa version
# Should output: Montreal Forced Aligner 3.x.x
```

### Test 2: Python Import

```bash
python -c "import montreal_forced_aligner; print(montreal_forced_aligner.__version__)"
```

### Test 3: Download Models

```bash
# Download acoustic model for English
mfa model download acoustic english_us_arpa

# List available models
mfa model list
```

## Common Issues

### Issue: "mfa: command not found"

**Cause:** MFA not in PATH

**Solutions:**
1. Make sure Conda environment is activated
2. Add Conda bin to PATH:
   ```bash
   export PATH="$HOME/miniconda3/bin:$PATH"
   ```
3. Reinstall MFA via Conda

### Issue: "No module named 'montreal_forced_aligner'"

**Cause:** Installed in different Python environment

**Solutions:**
1. Use Conda environment where MFA is installed
2. Reinstall in current environment:
   ```bash
   conda install -c conda-forge montreal-forced-aligner
   ```

### Issue: "pip install montreal-forced-alignment" fails

**Cause:** No pre-built wheels, compilation fails

**Solution:** Use Conda instead:
```bash
conda install -c conda-forge montreal-forced-aligner
```

### Issue: MFA crashes or segfaults

**Cause:** Binary compatibility issues

**Solutions:**
1. Use Conda (handles binaries correctly)
2. Update system libraries:
   ```bash
   sudo apt-get update && sudo apt-get upgrade  # Linux
   brew upgrade  # macOS
   ```
3. Try different MFA version:
   ```bash
   conda install -c conda-forge montreal-forced-aligner=3.1.0
   ```

## Performance Notes

| Dataset Size | Recommended RAM | Approximate Time |
|-------------|----------------|------------------|
| 100 clips | 4 GB | 5-10 minutes |
| 1,000 clips | 8 GB | 30-60 minutes |
| 10,000 clips | 16 GB | 3-6 hours |
| 100,000 clips | 32+ GB | 1-2 days |

**Note:** MFA is CPU-intensive, not GPU-accelerated.

## Alternative: Skip MFA

You can train Piper TTS models **without** MFA:
- Slightly lower quality
- Faster training setup
- No alignment step
- Good for testing and iteration

To skip MFA in training:
```bash
# Edit your training config
use_mfa: false
```

## Quick Decision Guide

```
Do you need to train a custom TTS model?
├─ No → Don't install MFA (you don't need it!)
└─ Yes
   ├─ Just testing/experimenting? → Skip MFA for now
   └─ Production quality model?
      ├─ Windows → Install Conda, then MFA
      ├─ Linux/Mac → Try pip, fallback to Conda
      └─ Having issues? → Use Conda (most reliable)
```

## Resources

- **Official Docs:** https://montreal-forced-aligner.readthedocs.io/
- **GitHub:** https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner
- **Discord:** https://discord.gg/m8kYUBzz (MFA community)
- **Pre-trained Models:** https://mfa-models.readthedocs.io/

## Summary

| Platform | Best Installation Method | pip Support |
|----------|------------------------|-------------|
| **Linux** | Conda (reliable) or pip (may need compilation) | ⚠️ Sometimes |
| **macOS** | Conda (recommended) or pip with Homebrew | ⚠️ Sometimes |
| **Windows** | Conda (ONLY option) | ❌ No |

**Bottom line:** If you need MFA, use Conda. It's the most reliable method across all platforms.

**For most users:** You probably don't need MFA at all! 🎉

