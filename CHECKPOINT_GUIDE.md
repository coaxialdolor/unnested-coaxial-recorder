# Piper Checkpoint Management Guide

## Overview

Your Coaxial Recorder now includes **automatic checkpoint management** for pre-trained Piper TTS models. This system allows you to easily download, manage, and use high-quality base voice models for fine-tuning your own voice models.

## Features

### ✅ **Automatic Downloads**
- **One-click download** of pre-trained models from Hugging Face and Rhasspy
- **Progress tracking** during downloads
- **Error handling** for network issues and missing files

### ✅ **Multi-Language Support**
- **US English**: Amy (Female, High), Lessac (Male, Medium)
- **British English**: Lessac (Male, Medium), Cori (Female, High)
- **Swedish**: NST (Female, Medium)
- **Italian**: Fallback support with English models

### ✅ **Smart Caching**
- **Local storage** to avoid re-downloading
- **Cache management** with size tracking
- **Validation** of downloaded checkpoints

### ✅ **Integration**
- **Training UI** with checkpoint selection
- **API endpoints** for programmatic access
- **Command-line support** for advanced users

## Available Checkpoints

### 🇺🇸 **US English**

| Voice | Gender | Quality | Dataset | Description |
|-------|--------|---------|---------|-------------|
| **Amy** | Female | High | LJSpeech | High-quality female voice, excellent for fine-tuning |
| **Lessac** | Male | Medium | Blizzard 2013 | Male voice with good quality |

### 🇬🇧 **British English**

| Voice | Gender | Quality | Dataset | Description |
|-------|--------|---------|---------|-------------|
| **Lessac** | Male | Medium | Blizzard 2013 | British English male voice |
| **Cori** | Female | High | LibriVox | High-quality British English female voice |

### 🇸🇪 **Swedish**

| Voice | Gender | Quality | Dataset | Description |
|-------|--------|---------|---------|-------------|
| **NST** | Female | Medium | NST Swedish | Swedish female voice from NST dataset |

### 🇮🇹 **Italian**

| Voice | Gender | Quality | Dataset | Description |
|-------|--------|---------|---------|-------------|
| **Fallback** | Unknown | Low | Unknown | Uses English models with espeak phonemes |

## Usage

### **1. Web Interface**

#### **Training Page**
1. Go to **Train** page
2. Select **"Fine-tune from Checkpoint"**
3. Choose a **base voice** from the dropdown
4. Click **"Download Selected Model"** if needed
5. Configure other training parameters
6. Start training

#### **Checkpoint Management**
- **Refresh Available Models**: Updates the list of available checkpoints
- **Download Selected Model**: Downloads the chosen checkpoint
- **Status Indicators**: Shows download progress and completion

### **2. API Endpoints**

#### **Get All Checkpoints**
```bash
curl http://localhost:8000/api/checkpoints
```

#### **Get Language-Specific Checkpoints**
```bash
curl http://localhost:8000/api/checkpoints/en-US
```

#### **Download Checkpoint**
```bash
curl -X POST http://localhost:8000/api/checkpoints/en-US/amy/download
```

#### **Get Checkpoint Info**
```bash
curl http://localhost:8000/api/checkpoints/en-US/amy
```

#### **Validate Checkpoint**
```bash
curl -X POST http://localhost:8000/api/checkpoints/validate/en-US/amy
```

#### **Cache Management**
```bash
# Get cache info
curl http://localhost:8000/api/checkpoints/cache/info

# Clear cache
curl -X DELETE http://localhost:8000/api/checkpoints/cache/clear
```

### **3. Command Line**

#### **Training with Base Voice**
```bash
# Use Amy (US English female) as base
python train_model.py \
  --profile-id "YourProfile" \
  --prompt-list-id "YourPromptList" \
  --language-code "en-US" \
  --base-voice "en-US.amy" \
  --epochs 100

# Use Lessac (US English male) as base
python train_model.py \
  --profile-id "YourProfile" \
  --prompt-list-id "YourPromptList" \
  --language-code "en-US" \
  --base-voice "en-US.lessac" \
  --epochs 100

# Use Swedish NST model
python train_model.py \
  --profile-id "YourProfile" \
  --prompt-list-id "YourPromptList" \
  --language-code "sv-SE" \
  --base-voice "sv-SE.nst" \
  --epochs 100
```

#### **Training with Custom Checkpoint**
```bash
python train_model.py \
  --profile-id "YourProfile" \
  --prompt-list-id "YourPromptList" \
  --language-code "en-US" \
  --checkpoint "/path/to/your/checkpoint.ckpt" \
  --epochs 100
```

## File Structure

```
checkpoints/
├── en-US_amy.ckpt                    # Downloaded checkpoint
├── en-US_amy_config.json             # Model configuration
├── en-US_amy_metadata.json           # Download metadata
├── en-US_lessac.ckpt                 # Another checkpoint
├── en-US_lessac_config.json
├── en-US_lessac_metadata.json
├── sv-SE_nst.ckpt                    # Swedish model
├── sv-SE_nst_config.json
├── sv-SE_nst_metadata.json
└── metadata/                         # Metadata directory
    ├── en-US_amy_metadata.json
    ├── en-US_lessac_metadata.json
    └── sv-SE_nst_metadata.json
```

## Configuration

### **Checkpoint Manifest**
The system uses a curated manifest of high-quality checkpoints:

```python
{
    "en-US": {
        "amy": {
            "name": "Amy",
            "gender": "Female",
            "dataset": "LJSpeech",
            "quality": "High",
            "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/epoch%3D6679-step%3D1554200.ckpt",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/config.json",
            "phoneme_type": "en-us-mfa",
            "sample_rate": 22050,
            "speaker_id": 0,
            "description": "High-quality female voice trained on LJSpeech dataset"
        }
    }
}
```

### **Phoneme Type Mapping**
- **en-US**: `en-us-mfa` (Montreal Forced Aligner)
- **en-GB**: `en-gb-mfa` (Montreal Forced Aligner)
- **sv-SE**: `sv-se-mfa` (Montreal Forced Aligner)
- **it-IT**: `espeak` (eSpeak NG fallback)

## Best Practices

### **1. Model Selection**
- **High Quality**: Choose "High" quality models for best results
- **Gender Match**: Select models that match your target voice gender
- **Language Match**: Use models in the same language as your training data

### **2. Training Strategy**
- **Fine-tuning**: Use pre-trained models for faster convergence
- **Learning Rate**: Use lower learning rates (0.0001) for fine-tuning
- **Epochs**: Fewer epochs needed when fine-tuning (50-100 vs 200+)

### **3. Data Requirements**
- **Minimum**: 30 minutes of high-quality recordings
- **Recommended**: 1-2 hours for good results
- **Optimal**: 3+ hours for professional quality

### **4. Hardware Considerations**
- **GPU**: Recommended for faster training
- **RAM**: 8GB+ for medium models, 16GB+ for large models
- **Storage**: 2-5GB per checkpoint

## Troubleshooting

### **Download Issues**
```bash
# Check network connectivity
curl -I https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/epoch%3D6679-step%3D1554200.ckpt

# Check available space
df -h checkpoints/

# Clear cache and retry
rm -rf checkpoints/*.ckpt
```

### **Validation Issues**
```bash
# Validate checkpoint
python -c "
import torch
checkpoint = torch.load('checkpoints/en-US_amy.ckpt', map_location='cpu')
print('Checkpoint keys:', list(checkpoint.keys()))
"
```

### **Training Issues**
```bash
# Check checkpoint compatibility
python train_model.py --help

# Test with small dataset first
python train_model.py --epochs 5 --batch-size 4
```

## API Reference

### **CheckpointManager Class**

```python
from utils.checkpoints import get_checkpoint_manager

manager = get_checkpoint_manager()

# Get available checkpoints
checkpoints = manager.get_available_checkpoints('en-US')

# Download checkpoint
success, message = manager.download_checkpoint('en-US', 'amy')

# Check if downloaded
downloaded = manager.is_checkpoint_downloaded('en-US', 'amy')

# Get checkpoint path
path = manager.get_checkpoint_path('en-US', 'amy')

# Validate checkpoint
valid = manager.validate_checkpoint('en-US', 'amy')

# Get cache info
info = manager.get_cache_info()
```

### **Convenience Functions**

```python
from utils.checkpoints import (
    download_checkpoint,
    get_available_checkpoints,
    is_checkpoint_downloaded,
    get_checkpoint_path
)

# Download
success, message = download_checkpoint('en-US', 'amy')

# Get available
checkpoints = get_available_checkpoints('en-US')

# Check status
downloaded = is_checkpoint_downloaded('en-US', 'amy')

# Get path
path = get_checkpoint_path('en-US', 'amy')
```

## Advanced Usage

### **Custom Checkpoint Sources**
You can extend the system to support additional checkpoint sources:

```python
# Add to checkpoint manifest
custom_checkpoint = {
    "name": "Custom Voice",
    "gender": "Female",
    "dataset": "Custom Dataset",
    "quality": "High",
    "url": "https://your-domain.com/model.ckpt",
    "config_url": "https://your-domain.com/config.json",
    "phoneme_type": "en-us-mfa",
    "sample_rate": 22050,
    "speaker_id": 0,
    "description": "Custom voice model"
}
```

### **Batch Operations**
```python
# Download multiple checkpoints
languages = ['en-US', 'en-GB', 'sv-SE']
for lang in languages:
    checkpoints = get_available_checkpoints(lang)
    for cp in checkpoints:
        if cp['quality'] == 'High':
            download_checkpoint(lang, cp['voice_id'])
```

### **Integration with Training Pipeline**
```python
# Automatic checkpoint selection
def get_best_checkpoint(language, gender_preference=None):
    manager = get_checkpoint_manager()
    return manager.get_recommended_checkpoint(language, gender_preference)

# Use in training
best_checkpoint = get_best_checkpoint('en-US', 'Female')
if best_checkpoint:
    checkpoint_path = manager.get_checkpoint_path(
        best_checkpoint['language_code'],
        best_checkpoint['voice_id']
    )
```

## Support

For issues and questions:
1. Check the console output for error messages
2. Validate your checkpoint: `/api/checkpoints/validate/{lang}/{voice}`
3. Check cache status: `/api/checkpoints/cache/info`
4. Review training logs for specific errors
5. Test with a simple example first

---

**Your system now supports professional-grade checkpoint management with automatic downloads, validation, and integration!** 🎉
