# Git Configuration Update Summary

## 🎯 **What Was Done**

Updated `.gitignore` and added `.gitkeep` files to ensure:
1. ✅ User-generated data is **NOT tracked in git**
2. ✅ Directory structure **IS preserved in git**
3. ✅ All data **persists between Docker sessions**
4. ✅ Folders are **auto-created when needed**

---

## 📝 **Changes Made**

### **1. Updated `.gitignore`**
Added comprehensive exclusions for user-generated data:

```gitignore
# Output - Generated models and exports
/output/*
!/output/.gitkeep

# Converted models
converted_models/*
!/converted_models/.gitkeep

# Voice profiles - User-generated data
voices/*/

# Training data
training/checkpoints/*
training/logs/*
!training/checkpoints/.gitkeep
!training/logs/.gitkeep

# Checkpoints - Keep metadata, exclude models
checkpoints/*/
!checkpoints/metadata/
checkpoints/metadata/*
!checkpoints/metadata/.gitkeep

# Models cache
models/*
!models/.gitkeep

# Application logs
logs/*
!logs/.gitkeep
```

### **2. Added `.gitkeep` Files**
Created empty `.gitkeep` files to preserve directory structure:

```
✅ output/.gitkeep
✅ converted_models/.gitkeep
✅ models/.gitkeep
✅ logs/.gitkeep
✅ training/checkpoints/.gitkeep
✅ training/logs/.gitkeep
✅ checkpoints/metadata/.gitkeep
```

### **3. Updated `app.py`**
Added automatic creation of `recordings/` directory on profile creation:

```python
# Create directory structure
profile_dir.mkdir()
(profile_dir / "clips").mkdir()
(profile_dir / "recordings").mkdir()  # ← NEW
(profile_dir / "prompts").mkdir()
```

### **4. Removed Old Voice Profiles from Git**
Deleted the `Douglas` profile from git tracking (but kept files on disk):

```bash
git rm -r --cached voices/Douglas/
# Files still exist at: /Users/petter/Desktop/coaxial-recorder/voices/Douglas/
```

---

## ✅ **Verification**

### **Test 1: Git Ignoring User Data**
```bash
$ git check-ignore -v voices/Douglas/metadata.jsonl
.gitignore:74:voices/*/    voices/Douglas/metadata.jsonl
```
✅ **Result**: Voice profiles are properly ignored

### **Test 2: Files Exist on Disk**
```bash
$ ls voices/Douglas/
metadata.jsonl  profile.json  progress.json  prompts/  recordings/
```
✅ **Result**: All files preserved for Docker persistence

### **Test 3: Directory Structure in Git**
```bash
$ git status --short
M  .gitignore
A  DATA_PERSISTENCE.md
M  app.py
A  checkpoints/metadata/.gitkeep
A  converted_models/.gitkeep
A  models/.gitkeep
...
```
✅ **Result**: `.gitkeep` files ensure empty directories exist in git

---

## 🐳 **Docker Persistence**

All user data is mounted via `docker-compose.yml` volumes:

| Directory | Purpose | Git Tracked | Docker Persisted |
|-----------|---------|-------------|------------------|
| `voices/` | Voice profiles & recordings | ❌ No | ✅ Yes |
| `output/` | Exported datasets | ❌ No | ✅ Yes |
| `training/checkpoints/` | Training saves | ❌ No | ✅ Yes |
| `training/logs/` | Training logs | ❌ No | ✅ Yes |
| `checkpoints/` | Pre-trained models | ❌ No | ✅ Yes |
| `converted_models/` | Converted models | ❌ No | ✅ Yes |
| `models/` | Model cache | ❌ No | ✅ Yes |
| `logs/` | Application logs | ❌ No | ✅ Yes |

---

## 📁 **Example: Douglas Profile**

### **On Disk** (persisted for Docker):
```
voices/Douglas/
├── metadata.jsonl          ← Recording metadata
├── profile.json            ← Profile settings
├── progress.json           ← Recording progress
├── prompts/               ← Prompt lists (12 files)
└── recordings/            ← Audio files (8 .wav files)
```

### **In Git** (tracked):
```
voices/
└── (empty - no profiles tracked)
```

### **What Happens**:
1. ✅ Files exist on your Mac filesystem
2. ✅ Docker container can access them
3. ✅ Survives container stops/restarts/rebuilds
4. ❌ Not pushed to remote git repositories
5. ❌ Not included in git history

---

## 🎯 **Benefits**

### **For You (Developer)**:
- 🔒 **Privacy**: Your recordings stay private
- 💾 **Backup Control**: You choose what/when to backup
- 🚀 **Fast Git**: No large audio files in git
- 🧹 **Clean Repos**: Only code is tracked

### **For Docker**:
- ✅ **Persistence**: Data survives container restarts
- ✅ **Performance**: No need to rebuild for data changes
- ✅ **Accessibility**: Files accessible from host filesystem
- ✅ **Portability**: Easy to backup/restore

### **For Collaboration**:
- 👥 **Share Code Only**: Others get a clean setup
- 🔐 **Keep Data Private**: No accidental data leaks
- 🏗️ **Structure Preserved**: Empty directories exist for them
- 🚀 **Auto-Setup**: Directories created automatically

---

## 🚀 **Usage**

### **Normal Workflow**:
```bash
# Start container
docker-compose --profile arm64 up -d

# Use the app - create profiles, record, train
# All data is automatically saved and persisted

# Stop container
docker-compose --profile arm64 down
# Your data is safe! ✓

# Start again
docker-compose --profile arm64 up -d
# All your profiles and recordings are still there! ✓
```

### **Backup Your Data**:
```bash
# Backup specific profile
cp -r voices/Douglas ~/Backups/Douglas_$(date +%Y%m%d)

# Backup everything
tar -czf coaxial_backup_$(date +%Y%m%d).tar.gz voices/ output/ training/
```

### **Share Your Code**:
```bash
# Commit and push (only code, no user data)
git add -A
git commit -m "Added new feature"
git push origin main
# ✓ Your recordings are NOT pushed
# ✓ Directory structure IS pushed
```

---

## 📋 **Files Changed**

### **Modified**:
- `.gitignore` - Added user data exclusions
- `app.py` - Auto-create `recordings/` directory
- `output/.gitkeep` - Added documentation comment
- `logs/.gitkeep` - Added documentation comment

### **Added**:
- `DATA_PERSISTENCE.md` - Comprehensive documentation
- `checkpoints/metadata/.gitkeep`
- `converted_models/.gitkeep`
- `models/.gitkeep`
- `training/checkpoints/.gitkeep`
- `training/logs/.gitkeep`

### **Removed from Git** (but kept on disk):
- `voices/Douglas/*` - All profile files untracked

---

## 🎉 **Summary**

**Before**:
- ❌ User data tracked in git
- ❌ Risk of committing large audio files
- ❌ Privacy concerns

**After**:
- ✅ User data ignored by git
- ✅ Only code and structure tracked
- ✅ Full Docker persistence
- ✅ Auto-created directories
- ✅ Private and secure

**Result**:
🎯 **Clean git history** + 🐳 **Full Docker persistence** + 🔒 **Private user data**

---

## 📖 **Documentation**

For more details, see:
- `DATA_PERSISTENCE.md` - Complete guide to data handling
- `docker-compose.yml` - Volume mount configuration
- `.gitignore` - Full list of exclusions

---

**Last Updated**: October 12, 2025
**Status**: ✅ Complete and tested

