# Windows Installation Guide

## Quick Start

### Option 1: Double-Click Install (Easiest)
1. Double-click `install.bat`
2. Follow the on-screen prompts
3. When done, double-click `launch_complete.bat` to start

### Option 2: Git Bash / Cygwin
1. Open Git Bash or Cygwin terminal
2. Navigate to this folder
3. Run: `bash install.sh`
4. When done, run: `bash launch_complete.sh`

## Prerequisites

### Required:
1. **Git for Windows** (includes Git Bash)
   - Download: https://git-scm.com/download/win
   - During install, select "Git Bash" option

2. **Python 3.10, 3.11, or 3.12**
   - Download: https://www.python.org/downloads/
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
   - ⚠️ **DO NOT** use Microsoft Store Python version

### Optional (for GPU training):
3. **NVIDIA GPU with CUDA support**
   - RTX 5060 Ti, 4090, 3090, etc.
   - Install latest NVIDIA drivers
   - The installer will automatically detect your GPU

4. **Visual Studio Build Tools** (for some packages)
   - Download: https://visualstudio.microsoft.com/downloads/
   - Select "Desktop development with C++" workload
   - Only needed if you see compilation errors

## Installation Steps

### Step 1: Install Git Bash
If you don't have Git Bash:
1. Download Git for Windows: https://git-scm.com/download/win
2. Run installer
3. Accept defaults (Git Bash will be included)

### Step 2: Install Python
If you don't have Python:
1. Download from https://www.python.org/downloads/
2. Run installer
3. ✅ **CHECK** "Add Python to PATH"
4. Choose "Install Now"

### Step 3: Run Installer
**Method A - Easy (Double-click):**
1. Double-click `install.bat` in File Explorer
2. Follow prompts
3. Wait for installation to complete

**Method B - Git Bash:**
1. Right-click in this folder → "Git Bash Here"
2. Type: `bash install.sh`
3. Follow prompts

### Step 4: Start Application
**Method A:**
- Double-click `launch_complete.bat`

**Method B:**
- In Git Bash: `bash launch_complete.sh`

## Python Version Compatibility

| Python | GPU Support | MFA Support (Windows) | Recommended |
|--------|-------------|----------------------|-------------|
| 3.10 | ✅ | ⚠️ Conda only | **Best** |
| 3.11 | ✅ | ⚠️ Conda only | Good |
| 3.12 | ✅ | ❌ Not available | Good |

**Windows Note:** Montreal Forced Aligner (MFA) doesn't have pip wheels for Windows.
- **MFA is optional** - the app works fine without it
- If you need MFA, install via Conda: `conda install -c conda-forge montreal-forced-aligner`
- For most users: **Python 3.10 or 3.12 work great without MFA**

The installer can download Python 3.10 locally if you have 3.12.

## GPU Support (RTX 5060 Ti and others)

The installer **automatically detects** your NVIDIA GPU:
- RTX 5060 Ti → Installs CUDA 12.8
- RTX 4090 → Installs CUDA 12.1
- RTX 3090 → Installs CUDA 11.8
- No GPU → Installs CPU version

No manual configuration needed!

## Troubleshooting

### "bash not found"
**Problem:** Git Bash not installed
**Solution:** Install Git for Windows (includes Git Bash)

### "Python not found"
**Problem:** Python not in PATHb
**Solutions:**
1. Reinstall Python and check "Add Python to PATH"
2. Or manually add Python to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python310`

### "pip not found" or "pip install fails"
**Problem:** Using Microsoft Store Python or corrupted pip
**Solutions:**
1. Uninstall Microsoft Store Python
2. Install Python from python.org
3. Run: `python -m ensurepip --upgrade`

### "No module named 'venv'"
**Problem:** Python installation incomplete
**Solution:** Reinstall Python from python.org with "pip" option checked

### Virtual environment activation fails
**Problem:** PowerShell execution policy
**Solution:**
- Use Git Bash instead of PowerShell
- Or in PowerShell (admin): `Set-ExecutionPolicy RemoteSigned`

### GPU not detected / CUDA errors
**Problems & Solutions:**
1. **NVIDIA drivers outdated**
   - Update from: https://www.nvidia.com/Download/index.aspx

2. **GPU test fails: "no kernel image"**
   - RTX 5060 Ti needs CUDA 12.8
   - Run: `python utils/gpu_compat.py` for diagnosis
   - Reinstall PyTorch:
     ```bash
     pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
     ```

3. **nvidia-smi not found**
   - Reinstall NVIDIA drivers
   - Reboot

### Compilation errors during installation
**Problem:** Missing build tools
**Solution:**
1. Install Visual Studio Build Tools
2. Download: https://visualstudio.microsoft.com/downloads/
3. Select "Desktop development with C++"
4. Restart terminal and retry

### FFmpeg not found
**Solutions:**
1. Via winget: `winget install Gyan.FFmpeg`
2. Via chocolatey: `choco install ffmpeg`
3. Manual: Download from https://ffmpeg.org/download.html and add to PATH

## Common Windows Issues

### Issue: "Permission denied" errors
**Solution:** Run Git Bash as Administrator

### Issue: Long path errors
**Solution:** Enable long paths:
1. Run as admin: `reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1`
2. Or: Open Group Policy → Enable "Enable Win32 long paths"

### Issue: Antivirus blocks installation
**Solution:** Temporarily disable antivirus or add folder to exclusions

### Issue: Slow download speeds
**Solution:** The installer downloads large files (PyTorch ~2GB). Be patient.

## About Montreal Forced Aligner (MFA)

**What is MFA?**
- Montreal Forced Aligner is a tool for phoneme alignment
- Used in advanced TTS training pipelines
- **Optional for most users**

**Do you need it?**
- ❌ **Basic recording & dataset creation** - No, not needed
- ❌ **Using pre-trained Piper models** - No, not needed
- ✅ **Training custom Piper TTS models** - Yes, improves quality
- ✅ **Advanced phoneme-level control** - Yes, required

**Windows Installation:**
MFA doesn't work with pip on Windows. If you need it:

1. Install Miniconda:
   ```bash
   # Download from: https://docs.conda.io/en/latest/miniconda.html
   ```

2. Install MFA via Conda:
   ```bash
   conda install -c conda-forge montreal-forced-aligner
   ```

3. Use MFA separately from your venv

**Bottom line:** Most Windows users don't need MFA. The installer skips it automatically.

## What Gets Installed

- **Virtual Environment**: `venv/` folder (~2-4 GB)
- **Local Python** (if chosen): `python310/` or `python311/` folder (~500 MB)
- **PyTorch**: CUDA version specific to your GPU
- **Dependencies**: ~1000 Python packages
- **System tools**: espeak, ffmpeg (via package managers)

## Uninstallation

To completely remove:
1. Delete the entire `coaxial-recorder` folder
2. That's it! Everything is self-contained

No system-wide changes are made (except optional ffmpeg).

## Performance on Windows

| Setup | Expected Performance |
|-------|---------------------|
| RTX 5060 Ti + Python 3.10 | Excellent (8-10x CPU) |
| RTX 4090 + Python 3.10 | Excellent (10-12x CPU) |
| RTX 3090 + Python 3.10 | Excellent (7-9x CPU) |
| CPU only + Python 3.10 | Good (usable) |
| Python 3.12 (no MFA) | Good (limited features) |

## Getting Help

1. Check error messages carefully
2. Run: `python test_installation.py` to diagnose
3. Run: `python utils/gpu_compat.py` for GPU issues
4. Check `training.log` for training errors

## File Locations

```
coaxial-recorder/
├── install.bat          ← Windows installer (double-click this)
├── install.sh           ← Bash installer
├── launch_complete.bat  ← Start app (Windows)
├── launch_complete.sh   ← Start app (Git Bash)
├── venv/                ← Virtual environment
├── python310/           ← Local Python (if installed)
├── app.py               ← Main application
└── README.md            ← General readme
```

## Tips for Windows Users

1. **Use Git Bash** for best compatibility
2. **Don't use** Windows CMD or PowerShell for installation
3. **Install Python 3.10** for best results
4. **Keep NVIDIA drivers updated** if you have a GPU
5. **Be patient** - first install takes 10-30 minutes depending on internet speed
6. **Reboot** after installing NVIDIA drivers or Visual Studio Build Tools

## Quick Commands Reference

```bash
# In Git Bash:
bash install.sh           # Install everything
bash launch_complete.sh   # Start application
python test_installation.py   # Test installation
python utils/gpu_compat.py   # Check GPU
python --version          # Check Python version
nvidia-smi                # Check GPU (if NVIDIA)
```

```batch
REM In Command Prompt or by double-clicking:
install.bat               REM Install everything
launch_complete.bat       REM Start application
```

## Success Indicators

Installation succeeded if you see:
- ✅ "Installation completed!"
- ✅ "PyTorch installation completed"
- ✅ "GPU test passed" (if you have GPU)
- ✅ "Virtual environment activated"
- ✅ No red ERROR messages at the end

## Next Steps After Installation

1. Open browser to: http://localhost:8000
2. Create a voice profile
3. Add prompt lists
4. Start recording!

---

**Need more help?** Check:
- Main README.md
- SETUP_GUIDE.md
- GPU_COMPATIBILITY_GUIDE.md (if GPU issues)

