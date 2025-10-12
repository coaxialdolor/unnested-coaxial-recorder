# Coaxial Recorder - File Structure Documentation

Complete guide to the repository structure and what each file does.

---

## 📁 Root Directory

### 🚀 Installation & Setup Scripts

| File | Purpose | When to Use |
|------|---------|-------------|
| **install.sh** | Comprehensive installer with GPU detection, Python version management, MFA options | First-time setup on Linux/macOS |
| **install.bat** | Windows wrapper for install.sh | First-time setup on Windows (Git Bash/Cygwin) |
| **uninstall.sh** | Complete uninstaller - removes venv, Python installations, data, Docker containers | When you want to completely remove the application |

### 🎯 Launch Scripts

| File | Purpose | When to Use |
|------|---------|-------------|
| **launch_complete.sh** | Main launch script - starts the web application | Every time you want to run the app (Linux/macOS) |
| **launch_complete.bat** | Windows launcher | Every time you want to run the app (Windows) |
| **kill_app.sh** | Stops the application and frees ports 8000, 8001, 5000 | When you need to stop the app or free up ports |

### 🐳 Docker Files

| File | Purpose | Architecture | GPU Support |
|------|---------|--------------|-------------|
| **Dockerfile.gpu** | NVIDIA GPU-enabled image with CUDA 12.1 + Conda + MFA | x86_64 | ✅ NVIDIA CUDA |
| **Dockerfile.cpu** | CPU-only image with Conda + MFA | x86_64 | ❌ CPU-only |
| **Dockerfile.arm64** | Apple Silicon optimized image (pip-only, NO Conda/MFA) | ARM64 | ❌ CPU-only (ARM64-optimized) |
| **docker-compose.yml** | Orchestrates all three Docker images with profiles | All | Depends on profile |
| **docker-start.sh** | Convenience script to detect GPU and start appropriate container | All | Auto-detects |
| **.dockerignore** | Excludes unnecessary files from Docker builds (venv, cache, etc.) | N/A | N/A |

### 🧪 Testing & Verification

| File | Purpose | When to Use |
|------|---------|-------------|
| **test_installation.py** | Verifies all components are installed correctly | After installation to check everything works |

### 📚 Documentation

| File | Purpose | Audience |
|------|---------|----------|
| **README.md** | Main project documentation with overview, features, quick start | Everyone - start here |
| **INSTALL.md** | Detailed installation instructions and system requirements | Users setting up for first time |
| **TRAINING_README.md** | Guide for training custom TTS models | Users who want to train voices |
| **MFA_ESSENTIAL_README.md** | Explains MFA (Montreal Forced Aligner) options and installation | Users deciding on MFA installation |
| **DOCKER_README.md** | Complete Docker setup guide for all platforms | Users who prefer Docker |
| **WINDOWS_README.md** | Windows-specific setup instructions and troubleshooting | Windows users |
| **SETUP_GUIDE.md** | Quick setup reference with Python/GPU compatibility info | Quick reference |
| **CHECKPOINT_GUIDE.md** | Guide for using pre-trained models and checkpoints | Users working with pre-trained models |
| **CLEANUP_SUMMARY.md** | Documents the repository cleanup and redundant files | Reference for what was moved/removed |
| **FILE_STRUCTURE.md** | This file - complete repository structure guide | Everyone - understanding the codebase |
| **CHANGELOG.md** | Version history and changes | Tracking project evolution |
| **LICENSE.md** | Project license information | Legal/licensing questions |
| **explanation_of_process.md** | Detailed explanation of the TTS training pipeline | Understanding the workflow |
| **process_flow_diagram.txt** | ASCII diagram of the training process | Visual learners |

### 🐍 Core Application Files

| File | Purpose | Lines | Description |
|------|---------|-------|-------------|
| **app.py** | Main FastAPI web application | ~3000 | Handles all web routes, recording, training, export, etc. |
| **train_model.py** | Training script for TTS models | ~350 | Orchestrates the model training process |

### 📦 Requirements Files

| File | Purpose | When Installed |
|------|---------|----------------|
| **requirements.txt** | Core application dependencies (FastAPI, audio processing) | Always |
| **requirements_training.txt** | Training dependencies (PyTorch, MFA, ML libraries) | With training installation |
| **requirements_export.txt** | Export utilities | With export features |
| **requirements_dev.txt** | Development tools (linting, formatting) | For developers only |

### ⚙️ Configuration Files

| File | Purpose |
|------|---------|
| **setup.cfg** | Python package configuration |
| **mypy.ini** | Type checking configuration |
| **.isort.cfg** | Import sorting configuration |
| **.projectile** | Emacs projectile configuration |
| **.tool-versions** | Version management (asdf) |
| **Makefile** | Build automation shortcuts |

---

## 📁 Directories

### `/utils/` - Utility Modules

Python utility modules for core functionality:

| File | Purpose |
|------|---------|
| **audio.py** | Audio processing utilities (trimming, normalization, VAD) |
| **phonemes.py** | Phoneme conversion system (text → phonemes using eSpeak NG) |
| **mfa.py** | Montreal Forced Aligner integration |
| **checkpoints.py** | Pre-trained model management |
| **export.py** | Dataset export functionality |
| **tts.py** | TTS inference utilities |

### `/templates/` - Web UI Templates

HTML templates for the web interface:

| File | Purpose |
|------|---------|
| **index.html** | Main dashboard/home page |
| **record.html** | Voice recording interface |
| **postprocess.html** | Audio post-processing interface |
| **export.html** | Dataset export interface |
| **train.html** | Model training interface |
| **test.html** | Model testing interface |
| **profiles.html** | Voice profile management |
| **convert.html** | Model conversion interface |

### `/static/` - Static Assets

Web assets (CSS, JavaScript):

- **css/** - Stylesheets for the web interface
- **js/** - JavaScript for recording, audio processing, UI interactions

### `/prompts/` - Prompt Lists by Language

Pre-made prompt lists for 57+ languages:

- Each folder contains text files with sentences for recording
- Format: `Language (Country)_locale-CODE/`
- Examples: `English (United States)_en-US/`, `Swedish (Sweden)_sv-SE/`
- Used for creating diverse training datasets

### `/voices/` - User Voice Data

**User-generated content** - your recordings and metadata:

```
voices/
└── {profile_name}/
    ├── recordings/           # Raw audio files (.wav)
    ├── clips/               # Processed audio clips
    ├── metadata.jsonl       # Links audio to text
    ├── progress.json        # Recording progress
    ├── config.json          # Voice profile configuration
    └── phonemes.txt         # Generated phoneme sequences
```

**Important**: Backup this folder before uninstalling!

### `/output/` - Training Output

Generated during model training:

```
output/
└── {model_name}/
    ├── checkpoints/         # Training checkpoints
    ├── logs/               # Training logs
    ├── final_model/        # Trained TTS model
    └── config.json         # Model configuration
```

### `/checkpoints/` - Pre-trained Models

Pre-trained TTS models and checkpoints:

```
checkpoints/
└── {language}/
    └── {voice_name}/
        ├── model.onnx      # ONNX model file
        ├── config.json     # Model configuration
        └── metadata.json   # Model metadata
```

### `/training/` - Training Artifacts

Temporary training data and logs:

- **checkpoints/** - Intermediate training checkpoints
- **logs/** - TensorBoard logs and training metrics

### `/models/` - Model Cache

Cached models and weights used during inference.

### `/script/` - Development Scripts

Development utilities (for contributors):

| File | Purpose |
|------|---------|
| **setup** | Development environment setup |
| **run** | Run the application in dev mode |
| **format** | Code formatting (black, isort) |
| **lint** | Code linting (flake8, mypy) |
| **find_complete** | Find completed recordings |

### `/probably_redundant/` - Archived Files

**Redundant files moved during cleanup** (see `CLEANUP_SUMMARY.md`):

- Old Dockerfile with security vulnerabilities
- Duplicate documentation
- Superseded scripts
- Old web interface (`piper_recording_studio/`)
- Duplicate prompt folders

**Safe to delete** after verifying everything works.

### `/venv/` - Virtual Environment

Python virtual environment (created by installer):

- Contains all Python dependencies
- **Do not commit to git** (in `.gitignore`)
- Recreate with `bash install.sh`

### `/python310/` & `/python311/` - Local Python Installations

Locally installed Python versions (if downloaded by installer):

- **Do not commit to git** (in `.gitignore`)
- Used when system Python is incompatible
- Can be deleted and re-downloaded

### `/__pycache__/` - Python Cache

Python bytecode cache (auto-generated):

- **Do not commit to git** (in `.gitignore`)
- Safe to delete (will regenerate)

### `/converted_models/` - Converted Models

Models converted to different formats (ONNX, etc.).

### `/test_audio/` - Test Audio Files

Sample audio files for testing.

### `/.git/` - Git Repository

Git version control data:

- **Never delete** unless you want to lose version history
- Contains all commits, branches, history

---

## 🎯 Workflow: Which Files Do What?

### 1️⃣ **Installation**
```
install.sh → downloads Python → creates venv → installs requirements → tests installation
```

### 2️⃣ **Launching the App**
```
launch_complete.sh → activates venv → starts app.py → opens http://localhost:8000
```

### 3️⃣ **Recording Voices**
```
app.py (record.html) → saves to voices/{profile}/recordings/ → updates metadata.jsonl
```

### 4️⃣ **Post-Processing**
```
app.py (postprocess.html) → utils/audio.py → processes recordings → saves to clips/
```

### 5️⃣ **Exporting Dataset**
```
app.py (export.html) → utils/export.py → creates training dataset → saves to output/
```

### 6️⃣ **Training Model**
```
train_model.py → uses utils/phonemes.py, utils/mfa.py → trains model → saves to output/{model}/
```

### 7️⃣ **Testing Model**
```
app.py (test.html) → utils/tts.py → generates audio → plays in browser
```

---

## 📊 File Size Reference

| Category | Approximate Size |
|----------|------------------|
| Core application (`app.py`, `train_model.py`) | ~130 KB |
| Documentation (all `.md` files) | ~100 KB |
| Templates & static assets | ~50 KB |
| Utilities (`utils/`) | ~30 KB |
| Scripts & config | ~20 KB |
| Prompts (all languages) | ~500 KB |
| **Total (without data/models)** | **~1 MB** |

**Data directories** (not in git):
- `/venv/` - ~500 MB (Python packages)
- `/voices/` - Varies (your recordings)
- `/output/` - Varies (trained models)
- `/checkpoints/` - Varies (pre-trained models)
- `/python310/` or `/python311/` - ~50 MB (if installed)

---

## 🔍 Finding Specific Functionality

| I want to... | Look in... |
|--------------|------------|
| Change the web interface | `templates/*.html` |
| Modify audio processing | `utils/audio.py` |
| Adjust training parameters | `train_model.py` |
| Add new API endpoints | `app.py` |
| Change phoneme generation | `utils/phonemes.py` |
| Modify MFA integration | `utils/mfa.py` |
| Update installation logic | `install.sh` |
| Add new language support | `prompts/` (add new folder) |
| Change Docker configuration | `Dockerfile.*`, `docker-compose.yml` |

---

## 🚫 Files You Should NOT Edit

Unless you know what you're doing:

- ❌ `.git/` - Version control data
- ❌ `venv/` - Virtual environment (regenerate instead)
- ❌ `__pycache__/` - Python cache (auto-generated)
- ❌ `.gitignore` - Unless adding new patterns
- ❌ `requirements*.txt` - Unless changing dependencies

---

## ✅ Files You CAN Safely Edit

- ✅ `voices/` - Your recordings (but backup first!)
- ✅ `prompts/` - Add your own prompt lists
- ✅ `templates/*.html` - Customize the UI
- ✅ `static/css/*.css` - Change styling
- ✅ Configuration in `app.py` (e.g., port, host)

---

## 🗑️ Safe to Delete

- ✅ `probably_redundant/` - After verifying everything works
- ✅ `venv/` - Can recreate with `bash install.sh`
- ✅ `python310/` or `python311/` - Can re-download
- ✅ `__pycache__/` - Will regenerate
- ✅ `output/` - If you don't need trained models
- ✅ `training/` - Temporary training data

---

## 📦 What Gets Committed to Git?

**Included** (tracked):
- ✅ All `.py` files (application code)
- ✅ All `.sh` and `.bat` scripts
- ✅ All `.md` documentation
- ✅ `templates/` and `static/`
- ✅ `prompts/` (prompt lists)
- ✅ `requirements*.txt`
- ✅ Docker files
- ✅ Configuration files

**Excluded** (in `.gitignore`):
- ❌ `venv/`, `env/`, `.venv/`
- ❌ `python310/`, `python311/`, `python3*/`
- ❌ `__pycache__/`, `*.pyc`
- ❌ `*.wav`, `*.mp3`, `*.flac` (audio files)
- ❌ `output/` (training results)
- ❌ `logs/` (log files)
- ❌ `probably_redundant/` (archived files)
- ❌ `.DS_Store`, `Thumbs.db` (OS files)

---

## 🎓 Learning Path

**New users** - Read in this order:
1. `README.md` - Overview
2. `INSTALL.md` - Installation
3. `TRAINING_README.md` - Training guide
4. `FILE_STRUCTURE.md` - This file

**Docker users**:
1. `README.md`
2. `DOCKER_README.md`
3. `TRAINING_README.md`

**Developers**:
1. `README.md`
2. `FILE_STRUCTURE.md` - This file
3. `explanation_of_process.md` - Technical details
4. `app.py` - Main application
5. `utils/*.py` - Core utilities

---

**Last Updated**: 2025-10-12
**Version**: Post-cleanup with ARM64 Docker support

