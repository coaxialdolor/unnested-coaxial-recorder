# Phoneme Sets and MFA Integration Guide

## Overview

Your Coaxial Recorder now includes comprehensive **phoneme set support** and **MFA (Montreal Forced Aligner)** integration for professional TTS training. This system supports **57 languages** with proper phoneme sets and text-audio alignment.

## How It Works

### 1. **Phoneme Sets (eSpeak NG)**
- **Piper TTS uses eSpeak NG** for phonemization (text → phonemes)
- **Each language has its own phoneme set** defined in eSpeak NG
- **Your system supports 57 languages** including:
  - **English variants**: en-US, en-GB, en-AU, en-CA, en-IN, en-IE
  - **European languages**: sv-SE, it-IT, fr-FR, de-DE, es-ES, pt-BR, nl-NL, etc.
  - **Asian languages**: ja-JP, ko-KR, zh-CN, zh-TW, th-TH, vi-VN
  - **Other languages**: ar-SA, he-IL, hi-IN, tr-TR, el-GR, etc.

### 2. **MFA (Montreal Forced Aligner)**
- **MFA aligns text with audio** for precise training data
- **Automatic phoneme-to-audio mapping** during training
- **Professional-grade alignment** used in commercial TTS systems
- **Supports all major languages** with pre-trained models

### 3. **Training Pipeline**
```
Text → eSpeak NG → Phonemes → MFA Alignment → Piper Training
```

## Language Support

### **Fully Supported Languages (57 total):**

#### **English Variants**
- `en-US` - English (United States)
- `en-GB` - English (United Kingdom)
- `en-AU` - English (Australia)
- `en-CA` - English (Canada)
- `en-IN` - English (India)
- `en-IE` - English (Ireland)

#### **European Languages**
- `sv-SE` - Swedish (Sweden)
- `it-IT` - Italian (Italy)
- `fr-FR` - French (France)
- `fr-CA` - French (Canada)
- `fr-BE` - French (Belgium)
- `fr-CH` - French (Switzerland)
- `de-DE` - German (Germany)
- `de-AT` - German (Austria)
- `de-CH` - German (Switzerland)
- `es-ES` - Spanish (Spain)
- `es-MX` - Spanish (Mexico)
- `pt-BR` - Portuguese (Brazil)
- `pt-PT` - Portuguese (Portugal)
- `nl-NL` - Dutch (Netherlands)
- `nl-BE` - Dutch (Belgium)

#### **Nordic Languages**
- `da-DK` - Danish (Denmark)
- `nb-NO` - Norwegian (Bokmål)
- `fi-FI` - Finnish (Finland)

#### **Slavic Languages**
- `ru-RU` - Russian (Russia)
- `pl-PL` - Polish (Poland)
- `cs-CZ` - Czech (Czech Republic)
- `sk-SK` - Slovak (Slovakia)
- `hr-HR` - Croatian (Croatia)
- `sl-SI` - Slovenian (Slovenia)
- `bg-BG` - Bulgarian (Bulgaria)
- `ro-RO` - Romanian (Romania)

#### **Asian Languages**
- `ja-JP` - Japanese (Japan)
- `ko-KR` - Korean (Korea)
- `zh-CN` - Chinese (Simplified)
- `zh-TW` - Chinese (Traditional)
- `zh-HK` - Chinese (Cantonese)
- `th-TH` - Thai (Thailand)
- `vi-VN` - Vietnamese (Vietnam)

#### **Other Languages**
- `ar-SA` - Arabic (Saudi Arabia)
- `ar-EG` - Arabic (Egypt)
- `he-IL` - Hebrew (Israel)
- `hi-IN` - Hindi (India)
- `tr-TR` - Turkish (Turkey)
- `el-GR` - Greek (Greece)
- `hu-HU` - Hungarian (Hungary)
- `ca-ES` - Catalan (Spain)
- `eu-ES` - Basque (Spain)
- `cy-GB` - Welsh (United Kingdom)
- `sq-AL` - Albanian (Albania)
- `af-ZA` - Afrikaans (South Africa)
- `id-ID` - Indonesian (Indonesia)
- `ms-MY` - Malay (Malaysia)
- `sw-KE` - Swahili (Kenya)
- `ta-IN` - Tamil (India)
- `te-IN` - Telugu (India)
- `ne-NP` - Nepali (Nepal)

## Installation

### **Automatic Installation (Recommended)**
```bash
./install.sh
```

This installs:
- ✅ **eSpeak NG** for phonemization
- ✅ **MFA** for text-audio alignment
- ✅ **All Python dependencies**
- ✅ **Piper TTS framework**
- ✅ **Pre-trained models**

### **Manual Installation**

#### **System Dependencies**
```bash
# macOS
brew install espeak-ng ffmpeg portaudio
conda install -c conda-forge montreal-forced-alignment

# Ubuntu/Debian
sudo apt-get install espeak-ng ffmpeg portaudio19-dev
conda install -c conda-forge montreal-forced-alignment

# Or via pip
pip install montreal-forced-alignment
```

#### **Python Dependencies**
```bash
pip install -r requirements_training.txt
```

## Usage

### **1. Training with Phoneme Support**
```bash
# Train with specific language
python train_model.py \
  --profile-id "YourProfile" \
  --prompt-list-id "YourPromptList" \
  --language-code "sv-SE" \
  --epochs 100
```

### **2. API Endpoints**

#### **Get Supported Languages**
```bash
curl http://localhost:8000/api/languages
```

#### **Convert Text to Phonemes**
```bash
curl -X POST http://localhost:8000/api/phonemes/convert \
  -F "text=Hello world" \
  -F "language_code=en-US"
```

#### **Check MFA Status**
```bash
curl http://localhost:8000/api/mfa/status
```

#### **Download MFA Model**
```bash
curl -X POST http://localhost:8000/api/mfa/download-model \
  -F "language_code=sv-SE"
```

### **3. Training Process**

1. **Record audio** with your voice
2. **Post-process** for consistent quality
3. **System automatically**:
   - Converts text to phonemes using eSpeak NG
   - Aligns phonemes with audio using MFA
   - Prepares data for Piper training
4. **Train model** with proper phoneme alignment

## Configuration

### **Language Configuration**
Each language has:
- **eSpeak voice**: For phonemization
- **MFA model**: For text-audio alignment
- **Sample rate**: Audio processing (usually 22050 Hz)
- **Phoneme set**: Language-specific phonemes

### **Example Configuration**
```json
{
  "sv-SE": {
    "espeak_voice": "sv",
    "phoneme_set": "sv",
    "description": "Swedish (Sweden)",
    "supported": true,
    "mfa_language": "swedish_mfa",
    "sample_rate": 22050
  }
}
```

## Troubleshooting

### **eSpeak NG Issues**
```bash
# Check if eSpeak NG is installed
espeak-ng --voices

# Install if missing
brew install espeak-ng  # macOS
sudo apt-get install espeak-ng  # Linux
```

### **MFA Issues**
```bash
# Check MFA installation
mfa --version

# Install if missing
conda install -c conda-forge montreal-forced-alignment
```

### **Language Support Issues**
```bash
# Test language support
python -c "from utils.phonemes import is_language_supported; print(is_language_supported('sv-SE'))"

# Check available languages
curl http://localhost:8000/api/languages
```

### **Training Issues**
```bash
# Validate phoneme system
curl http://localhost:8000/api/phonemes/validate

# Check training dependencies
python test_installation.py
```

## Advanced Features

### **Custom Phoneme Sets**
- Add new languages by extending the configuration
- Use existing phoneme sets for similar languages
- Validate phoneme conversion quality

### **MFA Model Management**
- Download specific language models
- Use custom MFA models
- Validate alignment quality

### **Training Optimization**
- GPU acceleration for faster training
- Mixed precision training
- Early stopping and checkpointing

## API Reference

### **Phoneme Endpoints**
- `GET /api/languages` - List all supported languages
- `GET /api/languages/{code}` - Get language details
- `POST /api/phonemes/convert` - Convert text to phonemes
- `GET /api/phonemes/validate` - Validate phoneme system

### **MFA Endpoints**
- `GET /api/mfa/status` - Check MFA availability
- `POST /api/mfa/download-model` - Download MFA model
- `GET /api/mfa/validate` - Validate MFA system

## Best Practices

1. **Use proper language codes** (e.g., `sv-SE`, not `swedish`)
2. **Ensure eSpeak NG is installed** for phonemization
3. **Download MFA models** before training
4. **Validate alignment quality** after MFA processing
5. **Use consistent audio quality** (44.1kHz WAV recommended)
6. **Test phoneme conversion** before training

## Support

For issues:
1. Check system dependencies are installed
2. Validate phoneme system: `/api/phonemes/validate`
3. Check MFA status: `/api/mfa/status`
4. Review training logs for specific errors
5. Test with a simple example first

---

**Your system now supports professional-grade TTS training with proper phoneme sets and text-audio alignment for 57 languages!** 🎉
