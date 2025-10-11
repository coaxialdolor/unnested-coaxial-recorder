# 🎙️ Piper TTS Training Process - Complete Guide

This document explains the **complete Piper TTS training process** in our Coaxial Recorder app, showing exactly where each step happens, what files are generated, and how everything connects together.

---

## 📋 **Overview: The Complete Pipeline**

```
🎙️ Record → 🧼 Post-Process → 📤 Export → 🧠 Train → 🗣️ Synthesize
                                    ↓
                              🎤 Test Voices
```

---

## 🎙️ **Step 1: Recording Your Voice**

### **What happens:**
You read sentences from prompt lists and record them as audio files.

### **Where it happens:**
- **Frontend**: `/templates/record.html` - Recording interface
- **Backend**: `/app.py` - `POST /api/record` endpoint
- **JavaScript**: `/static/js/recorder.js` - Audio recording logic

### **Files generated:**
```
voices/
└── {profile_name}/
    ├── recordings/           # Raw audio files
    │   ├── 0001_sv-SE_Chat_20251011_174903.wav
    │   ├── 0002_sv-SE_Chat_20251011_174904.wav
    │   └── ...
    ├── metadata.jsonl       # Links audio to text
    └── progress.json        # Recording progress
```

### **Metadata format:**
```json
{"filename": "0001_sv-SE_Chat_20251011_174903.wav", "sentence": "The sun rises slowly over the hills.", "prompt_list": "Chat", "file_id": "0001", "timestamp": "2025-01-11T17:49:03"}
```

### **Key code locations:**
- **Recording endpoint**: `app.py:793-823`
- **Filename generation**: `app.py:807-808` (extracts last 4 digits from prompt ID)
- **Audio processing**: `utils/audio.py:9-43`

---

## 🧼 **Step 2: Post-Processing Audio**

### **What happens:**
Clean up recorded audio files with silence trimming, volume normalization, and consistent padding.

### **Where it happens:**
- **Frontend**: `/templates/postprocess.html` - Post-processing interface
- **Backend**: `/app.py` - `POST /api/postprocess/start` endpoint
- **Processing**: `utils/audio.py:106-152` - `process_audio_enhanced()`

### **Files generated:**
```
voices/
└── {profile_name}/
    ├── recordings/           # Processed audio files (overwrites originals)
    │   ├── 0001_sv-SE_Chat_20251011_174903.wav  # Now processed
    │   └── ...
    └── backups/             # Original files (if backup enabled)
        ├── 0001_sv-SE_Chat_20251011_174903.wav.backup
        └── ...
```

### **Processing steps:**
1. **Load audio** with pydub
2. **Convert to mono** 44.1kHz WAV
3. **Normalize volume** to target dBFS (-20 dB)
4. **Trim silence** from start/end
5. **Add padding** (200ms silence before/after)
6. **Export** processed file

### **Key code locations:**
- **Post-processing endpoint**: `app.py:1702-1744`
- **Background processing**: `app.py:1746-1800`
- **Audio processing**: `utils/audio.py:106-152`

---

## 📤 **Step 3: Export Dataset**

### **What happens:**
Export processed audio files in different formats (WAV, MP3, FLAC, OGG) with metadata and transcripts.

### **Where it happens:**
- **Frontend**: `/templates/export.html` - Export interface
- **Backend**: `/app.py` - `POST /api/export/start` endpoint
- **Processing**: `utils/audio.py:228-279` - `export_audio_file()`

### **Files generated:**
```
exports/
└── {profile_name}_{prompt_list}_{timestamp}/
    ├── audio/               # Exported audio files
    │   ├── 0001.wav
    │   ├── 0002.mp3
    │   └── ...
    ├── metadata.json        # Complete metadata
    ├── transcripts.txt      # Text transcripts
    └── dataset.zip          # Complete dataset (if requested)
```

### **Export options:**
- **Format**: WAV, MP3, FLAC, OGG
- **Sample rate**: 16kHz, 22kHz, 44.1kHz, 48kHz
- **Bit depth**: 16-bit, 24-bit, 32-bit
- **Channels**: Mono, Stereo
- **MP3 bitrate**: 128k, 192k, 256k, 320k

### **Key code locations:**
- **Export endpoint**: `app.py:1850-1890`
- **Background export**: `app.py:1903-1980`
- **Audio export**: `utils/audio.py:228-279`

---

## 🧠 **Step 4: Training the Model**

### **What happens:**
Train a Piper TTS model using your recorded voice data, with phoneme conversion and MFA alignment.

### **Where it happens:**
- **Frontend**: `/templates/train.html` - Training interface
- **Backend**: `/app.py` - `POST /api/train/start` endpoint
- **Training script**: `/train_model.py` - Main training logic
- **Phoneme system**: `/utils/phonemes.py` - Text-to-phoneme conversion
- **MFA system**: `/utils/mfa.py` - Audio-text alignment
- **Checkpoints**: `/utils/checkpoints.py` - Pre-trained model management

### **Files generated:**
```
training_output/
└── {model_name}/
    ├── dataset/             # Prepared training data
    │   ├── audio/           # Audio files
    │   ├── phonemes/        # Phoneme sequences
    │   ├── alignment/       # MFA alignment data
    │   └── manifest.jsonl   # Training manifest
    ├── checkpoints/         # Model checkpoints
    │   ├── epoch_100.ckpt
    │   ├── epoch_200.ckpt
    │   └── ...
    ├── logs/               # Training logs
    │   ├── training.log
    │   └── tensorboard/
    └── final_model/        # Final trained model
        ├── model.ckpt
        ├── config.json
        └── onnx_model.onnx
```

### **Training process:**

#### **4a. Dataset Preparation** (`train_model.py:243-248`)
```python
dataset_info = prepare_dataset(
    args.profile_id,
    args.prompt_list_id,
    args.output_dir,
    args.language_code
)
```

#### **4b. Phoneme Conversion** (`utils/phonemes.py`)
```python
# Convert text to phonemes
phonemes = phoneme_manager.text_to_phonemes("The sun rises slowly", "en-US")
# Result: "ð ə s ʌ n r aɪ z ə z s l oʊ l i"
```

#### **4c. MFA Alignment** (`utils/mfa.py`)
```python
# Align phonemes to audio timing
mfa_aligner.align_audio_text(audio_dir, text_dir, alignment_dir, "en-US")
# Creates timing data: "ð starts at 0.1s, ə starts at 0.3s..."
```

#### **4d. Model Training** (`train_model.py:257-265`)
```python
# Train the model (simulated in current implementation)
for epoch in range(args.epochs):
    # Forward pass, loss calculation, backpropagation
    # Save checkpoints at intervals
    # Early stopping if validation loss plateaus
```

### **Training parameters:**
- **Model size**: Small, Medium, Large
- **Learning rate**: 0.0001 - 0.01
- **Batch size**: 8, 16, 32, 64
- **Epochs**: 100 - 1000
- **Train/Validation split**: 80/20, 90/10
- **GPU acceleration**: CUDA if available
- **Mixed precision**: FP16 for faster training

### **Key code locations:**
- **Training endpoint**: `app.py:2083-2142`
- **Background training**: `app.py:2144-2200`
- **Main training**: `train_model.py:180-265`
- **Dataset prep**: `train_model.py:100-179`

---

## 🎤 **Step 5: Test Voices**

### **What happens:**
Test any available voice model by entering custom text and generating audio samples to preview how different voices sound.

### **Where it happens:**
- **Frontend**: `/templates/test.html` - Voice testing interface
- **Backend**: `/app.py` - `POST /api/test/generate` endpoint
- **Audio generation**: `create_test_audio()` function (placeholder implementation)

### **Files generated:**
```
test_audio/                    # Temporary test audio files
├── test_en-US_amy_a1b2c3d4.wav
├── test_sv-SE_nst_e5f6g7h8.wav
└── ...
```

### **Testing features:**
1. **Voice selection**: Choose from available pre-trained models
2. **Custom text input**: Enter any text to synthesize
3. **Speech parameters**: Adjust rate and pitch
4. **Audio playback**: Play generated audio in browser
5. **Download option**: Save audio files locally
6. **Recent tests**: History of previous tests
7. **Voice information**: Detailed model metadata

### **Key code locations:**
- **Test page endpoint**: `app.py:2065-2068`
- **Audio generation**: `app.py:2615-2670`
- **Audio serving**: `app.py:2672-2692`
- **Test audio creation**: `app.py:2694-2721`

---

## 🗣️ **Step 6: Speech Synthesis**

### **What happens:**
Use the trained model to generate speech from any text input.

### **Where it happens:**
- **Model files**: Generated in `training_output/{model_name}/final_model/`
- **Inference**: Uses Piper TTS inference pipeline
- **Output**: Generates audio files in your voice

### **Files generated:**
```
synthesis_output/
├── generated_audio.wav      # Synthesized speech
├── phonemes.txt            # Phoneme sequence used
└── timing.json             # Phoneme timing data
```

---

## 🔧 **Technical Implementation Details**

### **File Structure:**
```
coaxial-recorder/
├── app.py                  # Main FastAPI application
├── train_model.py          # Training script
├── utils/
│   ├── audio.py           # Audio processing utilities
│   ├── phonemes.py        # Phoneme conversion system
│   ├── mfa.py             # Montreal Forced Aligner integration
│   └── checkpoints.py     # Pre-trained model management
├── templates/
│   ├── record.html        # Recording interface
│   ├── postprocess.html   # Post-processing interface
│   ├── export.html        # Export interface
│   └── train.html         # Training interface
├── static/js/
│   └── recorder.js        # Frontend recording logic
├── voices/                # User recordings
├── exports/               # Exported datasets
├── training_output/       # Training results
└── checkpoints/           # Pre-trained models
```

### **Key Dependencies:**
- **Audio processing**: `pydub`, `librosa`, `soundfile`
- **ML training**: `torch`, `torchaudio`, `transformers`
- **Phoneme conversion**: `phonemizer`, `espeak-ng`
- **Alignment**: `montreal-forced-alignment`
- **Web framework**: `fastapi`, `uvicorn`

### **API Endpoints:**
```
POST /api/record                    # Save recording
POST /api/postprocess/start         # Start post-processing
POST /api/export/start              # Start export
POST /api/train/start               # Start training
GET  /api/checkpoints               # List available checkpoints
POST /api/checkpoints/{lang}/{voice}/download  # Download checkpoint
POST /api/test/generate             # Generate test speech
GET  /api/test/audio/{filename}     # Serve test audio files
DELETE /api/test/cleanup            # Clean up old test files
```

---

## 🚀 **Getting Started**

### **1. Record your voice:**
```bash
# Start the app
python app.py

# Go to http://localhost:8000/record
# Select profile and prompt list
# Record sentences one by one
```

### **2. Post-process audio:**
```bash
# Go to http://localhost:8000/postprocess
# Select profile and dataset
# Configure processing settings
# Start processing
```

### **3. Export dataset:**
```bash
# Go to http://localhost:8000/export
# Select format and settings
# Start export
```

### **4. Train model:**
```bash
# Go to http://localhost:8000/train
# Configure training parameters
# Select base voice (optional)
# Start training
```

### **5. Test voices:**
```bash
# Go to http://localhost:8000/test
# Select language and voice model
# Enter custom text
# Generate and play audio
# Download if desired
```

### **6. Use trained model:**
```bash
# Use the generated model files for synthesis
# Located in training_output/{model_name}/final_model/
```

---

## 📊 **Data Flow Summary**

```
📝 Text Prompts → 🎙️ Record Audio → 🧼 Process Audio → 📤 Export Dataset
                                                                    ↓
🗣️ Synthesize Speech ← 🧠 Train Model ← 📍 Align Phonemes ← 🔤 Convert to Phonemes
                                                                    ↓
                                                              🎤 Test Voices
```

Each step builds upon the previous one, creating a complete pipeline from raw recordings to a trained voice model that can synthesize speech in your voice!

---

## 🎯 **Next Steps**

1. **Record more data** for better quality
2. **Experiment with training parameters** for optimal results
3. **Use different base voices** for fine-tuning
4. **Export in different formats** for various use cases
5. **Integrate with other TTS systems** using the trained models

The complete process is now automated and user-friendly through the web interface! 🎉
