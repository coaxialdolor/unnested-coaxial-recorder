# Data Persistence & Git Configuration

This document explains how user data is handled in the Coaxial Recorder application.

## 📊 **What's Tracked in Git**

### **Tracked (Code & Structure)**:
- ✅ Application code (`app.py`, `utils/`, `templates/`, etc.)
- ✅ Empty directory structure (`.gitkeep` files)
- ✅ Documentation
- ✅ Configuration files
- ✅ Prompt templates (in `prompts/`)

### **NOT Tracked (User Data)**:
- ❌ Voice profiles (`voices/*/`)
  - `voices/*/recordings/` - Your audio recordings
  - `voices/*/clips/` - Processed clips
  - `voices/*/metadata.jsonl` - Recording metadata
  - `voices/*/profile.json` - Profile settings
  - `voices/*/progress.json` - Recording progress
  - `voices/*/prompts/` - Profile-specific prompts
- ❌ Training output (`output/*`, `training/checkpoints/*`, `training/logs/*`)
- ❌ Generated models (`converted_models/*`, `models/*`)
- ❌ Application logs (`logs/*`)
- ❌ Checkpoint models (`checkpoints/*/`)
- ❌ Audio files (`*.wav`, `*.mp3`, `*.flac`, etc.)

---

## 🐳 **Docker Persistence**

All user data is persisted between Docker sessions via volume mounts in `docker-compose.yml`:

```yaml
volumes:
  - ./voices:/app/voices                      # Voice profiles & recordings
  - ./output:/app/output                      # Exported datasets
  - ./checkpoints:/app/checkpoints            # Pre-trained models
  - ./logs:/app/logs                          # Application logs
  - ./training/checkpoints:/app/training/checkpoints  # Training saves
  - ./training/logs:/app/training/logs        # Training logs
  - ./converted_models:/app/converted_models  # Converted models
  - ./models:/app/models                      # Model cache
  - ./prompts:/app/prompts                    # Prompt templates
```

### **What This Means**:
- 🔒 **Your data is safe** - Stopping/restarting containers preserves all data
- 🔄 **Survives rebuilds** - Even rebuilding the image keeps your files
- 💾 **Accessible from host** - Files are on your Mac at `./voices/`, `./output/`, etc.
- 🗑️ **Easy backup** - Just copy the directories from your filesystem

---

## 📁 **Directory Structure**

### **Auto-Created Directories**

The application automatically creates these directories when needed:

```
coaxial-recorder/
├── voices/                    # Created on startup
│   └── {profile_name}/       # Created when profile is created
│       ├── recordings/       # ✅ Auto-created
│       ├── clips/            # ✅ Auto-created
│       └── prompts/          # ✅ Auto-created
├── output/                   # Created on startup
├── checkpoints/              # Created on startup
│   └── metadata/            # Created on startup
├── logs/                     # Created on startup
├── training/                 # Exists in repo
│   ├── checkpoints/         # Created on startup
│   └── logs/                # Created on startup
├── converted_models/         # Created on startup
└── models/                   # Created on startup
```

### **When Directories Are Created**:

1. **On Application Startup**: `voices/`, `output/`, `checkpoints/`, etc.
2. **On Profile Creation**: `voices/{profile}/recordings/`, `voices/{profile}/clips/`, etc.
3. **On First Use**: `training/checkpoints/` when training starts
4. **On Demand**: Other directories as needed

---

## 🔧 **How It Works**

### **1. Profile Creation**
When you create a new voice profile (e.g., "Douglas"):

```python
# Automatically creates:
voices/Douglas/
├── recordings/      # Empty, ready for recordings
├── clips/          # Empty, ready for processed audio
├── prompts/        # Seeded with default prompt lists
├── metadata.jsonl  # Empty metadata file
├── profile.json    # Profile settings
└── progress.json   # Recording progress tracker
```

### **2. Recording Audio**
When you record:
- Audio saved to `voices/{profile}/recordings/{prompt}_{index}.wav`
- Metadata appended to `metadata.jsonl`
- Progress updated in `progress.json`
- **All persisted to disk immediately**

### **3. Processing/Export/Training**
- Processed files written to `output/`
- Training checkpoints saved to `training/checkpoints/`
- All data persisted via Docker volumes

---

## 🚀 **Usage**

### **Starting Fresh**
```bash
# First time - creates all directories
docker-compose --profile arm64 up -d
```

### **After Stopping**
```bash
# Your data is still there!
docker-compose --profile arm64 down
docker-compose --profile arm64 up -d
# All profiles, recordings, and progress preserved ✓
```

### **Backing Up Your Data**
```bash
# Backup everything
cp -r voices/ voices_backup/
cp -r output/ output_backup/

# Or just specific profiles
cp -r voices/Douglas/ ~/Backups/Douglas_voice_$(date +%Y%m%d)/
```

### **Cleaning Up**
```bash
# Remove specific profile (from host)
rm -rf voices/ProfileName/

# Remove all training data
rm -rf output/* training/checkpoints/* training/logs/*

# Keep recordings, delete processed data
rm -rf voices/*/clips/*
```

---

## 🔐 **Security & Privacy**

### **Your Data Stays Local**
- ✅ All recordings stay on your Mac
- ✅ Never uploaded to git repositories
- ✅ Not included in Docker images
- ✅ Only accessible on your filesystem

### **Sharing the Project**
When you push to git, only code is shared:
- ✅ Application code
- ✅ Documentation
- ✅ Configuration templates
- ❌ **Your recordings** (private)
- ❌ **Your voice profiles** (private)
- ❌ **Your training data** (private)

---

## 📋 **Verification**

### **Check What's Ignored**
```bash
# See what git is ignoring
git status --ignored

# Check specific directory
git check-ignore -v voices/Douglas/recordings/
```

### **Check Docker Volumes**
```bash
# See mounted volumes
docker inspect coaxial-recorder-arm64 | grep -A20 Mounts
```

### **Verify Persistence**
```bash
# 1. Create a test file
echo "test" > voices/test.txt

# 2. Restart container
docker-compose --profile arm64 restart

# 3. Check if file still exists
cat voices/test.txt
# Output: test ✓
```

---

## 🎯 **Summary**

| Data Type | Git Tracked | Docker Persisted | Location |
|-----------|-------------|------------------|----------|
| **Application Code** | ✅ Yes | N/A | `/app/` |
| **Voice Profiles** | ❌ No | ✅ Yes | `./voices/` |
| **Recordings** | ❌ No | ✅ Yes | `./voices/*/recordings/` |
| **Training Output** | ❌ No | ✅ Yes | `./output/`, `./training/` |
| **Models** | ❌ No | ✅ Yes | `./checkpoints/`, `./models/` |
| **Logs** | ❌ No | ✅ Yes | `./logs/` |
| **Directory Structure** | ✅ Yes | ✅ Yes | `.gitkeep` files |

**Bottom Line**:
- Your data is **safe** and **persistent**
- Your data is **private** (not in git)
- Your data **survives** container restarts and rebuilds
- Directory structure is **automatically created** when needed

🎉 **You can use the app without worrying about losing your data!**

