# MFA is ESSENTIAL - Why & How to Install It

## 🎯 MFA Enhancement Options

**Montreal Forced Aligner (MFA) is OPTIONAL** for this application. Here's why you might want it:

### Core Purpose of This Application
This application is designed for **creating custom voice models** for AI voice synthesis. The core workflow is:

1. **Record voice samples** with text prompts
2. **Generate phoneme sequences** (G2P models work perfectly)
3. **Train TTS models** using phoneme-audio pairs
4. **Generate custom voices** for synthesis

### Why MFA is Beneficial (Optional)

**Without MFA (Standard Installation):**
- ✅ Create phoneme sequences using G2P models
- ✅ Train functional TTS models
- ✅ Build working voice synthesis systems
- ✅ Perfect for learning and experimentation

**With MFA (Enhanced Installation):**
- ✅ Create precise forced alignments (better quality)
- ✅ Train higher-quality TTS models
- ✅ Professional voice synthesis results
- ✅ Best for production use

## 🔧 Installation Options

The installer offers **multiple installation paths** so you can choose the approach that best fits your needs and system setup.

### Installation Strategy

The installer offers these installation options:

1. **Standard Installation** - No MFA, uses G2P phoneme generation (sufficient for most users)
2. **Enhanced Installation** - MFA via Conda for better quality (may require system changes)
3. **Docker Installation** - Everything included, isolated environment (zero system interference)
4. **Recording Only** - Skip MFA entirely if you just want to collect data

### Installation Method Comparison

| Method | Setup Complexity | System Impact | Training Quality | Best For |
|--------|------------------|---------------|------------------|----------|
| **Standard** | ⭐⭐⭐⭐⭐ (None) | ✅ Zero | ⚠️ Good | Most users, learning |
| **Conda** | ⭐⭐⭐ (Medium) | ⚠️ System-wide | ✅ Excellent | Professional results |
| **Docker** | ⭐⭐⭐⭐ (Low) | ✅ Isolated | ✅ Excellent | Complex setups, testing |
| **Skip MFA** | ⭐⭐⭐⭐⭐ (None) | ✅ Zero | ❌ None | Data collection only |

## 📋 Installation Methods

### Method 1: Standard Installation (Recommended)

**No MFA required - uses G2P phoneme generation**

```bash
# Run the installer
bash install.sh

# Choose option 1: Standard Installation
# This provides full TTS training capabilities
```

**What you get:**
- ✅ Complete TTS training pipeline
- ✅ No external dependencies
- ✅ Clean, isolated setup
- ✅ Sufficient for excellent results

### Method 2: Conda (For Enhanced Quality)

```bash
# Install Miniconda (system-wide, but manageable)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Or for macOS:
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh

# Install MFA (installs to conda environment)
conda install -c conda-forge montreal-forced-aligner

# Verify installation
mfa version
```

**Note:** Conda installs system-wide but creates isolated environments. You can completely remove everything with:
```bash
./uninstall.sh  # Removes venv, data, and MFA
```

This provides complete cleanup of all installed components.

### Method 3: Docker (Everything Included)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Run the application (includes MFA)
./docker-start.sh
```

### Method 3: System Package Manager (Advanced)

```bash
# Ubuntu/Debian
sudo apt-get install montreal-forced-aligner

# Or build from source (complex)
git clone https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner.git
cd Montreal-Forced-Aligner
pip install -e .
```

## 🛠️ Troubleshooting MFA Installation

### Issue: "conda: command not found"

**Solution:** Install Miniconda first
```bash
# Linux
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# macOS
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh
```

### Issue: "pip install montreal-forced-alignment" fails

**Solution:** Use Conda instead
```bash
conda install -c conda-forge montreal-forced-aligner
```

### Issue: "MFA requires different python version"

**Solution:** Use Conda (handles Python version compatibility)
```bash
conda create -n mfa python=3.10
conda activate mfa
conda install -c conda-forge montreal-forced-aligner
```

### Issue: "Permission denied" or "Cannot install in system"

**Solution:** Use user Conda installation
```bash
# Don't use sudo with conda
conda install -c conda-forge montreal-forced-aligner
```

## ✅ Verification

After installation, verify MFA works:

```bash
# Check version
mfa version

# Download test models
mfa model download acoustic english_us_arpa
mfa model download dictionary english_us_arpa

# Test with sample data
mfa align sample_audio/ sample_text/ english_us_arpa output/
```

## 🚀 What You Get With MFA

### Complete Voice Training Pipeline

1. **Recording Interface** - Web-based audio recording
2. **Phoneme Alignment** - MFA aligns audio with text
3. **Dataset Preparation** - Clean training data
4. **Model Training** - Train custom TTS models
5. **Voice Synthesis** - Generate speech with custom voices

### Professional Features

- **High-quality alignments** for better TTS training
- **Multiple language support** (English, Spanish, French, etc.)
- **Batch processing** for large datasets
- **Integration with Piper TTS** for model training

## 💡 Alternative: Docker Solution

If you prefer not to install Conda:

```bash
# One-command solution with everything included
./docker-start.sh

# This includes:
# - Conda environment
# - MFA pre-installed
# - All dependencies
# - GPU support
# - No host system changes
```

## Summary

| Installation Method | Ease | MFA Included | GPU Support | Cross-platform |
|-------------------|------|--------------|--------------|----------------|
| **Conda** | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ Via venv | ✅ Yes |
| **Docker** | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ Native | ✅ Yes |
| **pip only** | ⭐⭐ | ❌ No | ⚠️ Limited | ⚠️ Varies |

**Recommendation:** Use **Conda** for the best experience. It's reliable, handles MFA properly, and gives you the complete voice training pipeline.

**This application is designed for custom voice model training - MFA is essential for that purpose!** 🎯

