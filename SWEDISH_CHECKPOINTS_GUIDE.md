# Swedish TTS Checkpoints - Download Guide

## Overview
Swedish checkpoints require manual download from HuggingFace as they're not publicly available via direct URLs (some require authentication).

---

## 🇸🇪 Available Swedish Checkpoints

### 1. **KBLab NST Swedish** (Recommended for Swedish)
- **Quality:** Medium-High
- **Gender:** Female
- **Dataset:** NST Swedish
- **URL:** https://huggingface.co/KBLab/piper-tts-nst-swedish

**How to Download:**
1. Visit https://huggingface.co/KBLab/piper-tts-nst-swedish
2. Look for `.ckpt` files (checkpoint files)
3. Download the checkpoint file (may require HuggingFace login)
4. Save to: `checkpoints/sv-SE/nst/model.ckpt`

### 2. **SubZeroAI Multi-Speaker Swedish**
- **Quality:** High
- **Gender:** Multiple speakers
- **Dataset:** Swedish Multi-Speaker
- **URL:** https://huggingface.co/SubZeroAI/piper-swedish-tts-multispeaker

**How to Download:**
1. Visit https://huggingface.co/SubZeroAI/piper-swedish-tts-multispeaker
2. Look for `.ckpt` files
3. Download the checkpoint file
4. Save to: `checkpoints/sv-SE/multispeaker/model.ckpt`

### 3. **Wezzmeister Piper Voices**
- **URL:** https://huggingface.co/wezzmeister/piper-voices
- This repository may contain additional Swedish voices

---

## 📁 Folder Structure

After downloading, your checkpoint folder should look like:

```
checkpoints/
├── sv-SE/
│   ├── nst/
│   │   └── model.ckpt          (KBLab NST checkpoint)
│   └── multispeaker/
│       └── model.ckpt          (SubZeroAI checkpoint)
└── en-US/
    └── amy/
        └── model.ckpt          (Auto-downloaded English)
```

---

## 🎯 How to Use in Training

### Option 1: Using Custom Checkpoint Path (Recommended for Manual Downloads)

1. Go to the **Train** page
2. Select **"Fine-tune from Checkpoint"**
3. **Leave "Pre-trained Base Voice" dropdown empty**
4. In **"Custom Checkpoint Path"** field, enter:
   - For KBLab NST: `checkpoints/sv-SE/nst/model.ckpt`
   - For SubZeroAI: `checkpoints/sv-SE/multispeaker/model.ckpt`
   - Or full path: `C:\Users\Petter\Desktop\coaxial-recorder\checkpoints\sv-SE\nst\model.ckpt`

### Option 2: Using Pre-trained Base Voice Dropdown

1. If the dropdown shows Swedish models, try clicking **Download**
2. If you get an error (404 or manual download required), follow Option 1 instead
3. The dropdown will show "NST (Requires Manual Download)" for Swedish models

---

## ❓ FAQs

### Q: Why can't I auto-download Swedish checkpoints?
**A:** Some HuggingFace repositories require authentication or have different access permissions. Manual download ensures you get the correct file.

### Q: Do I need both Custom Path AND dropdown selected?
**A:** No! Use ONE of:
- **Custom Checkpoint Path** (for manually downloaded files) - leave dropdown empty
- **Pre-trained Base Voice dropdown** (for auto-downloadable models) - leave custom path empty

### Q: Which Swedish checkpoint should I use?
**A:** 
- **KBLab NST:** Good general-purpose Swedish female voice
- **SubZeroAI Multi-Speaker:** Better if you want variety or male voices
- Try both and see which works better for your voice!

### Q: Where can I see download errors?
**A:** 
- When clicking download, you'll see an alert with the full error
- For manual download checkpoints, the error will include instructions
- Console (F12 in browser) shows technical details

### Q: The checkpoint path doesn't work in training?
**A:** Make sure:
1. File exists at the specified path
2. File is a `.ckpt` file (Piper checkpoint format)
3. Path uses forward slashes `/` or escaped backslashes `\\`
4. Example: `checkpoints/sv-SE/nst/model.ckpt`

---

## 🛠️ Alternative: Git Clone Method

If you prefer command-line:

```bash
# Clone entire repository
git clone https://huggingface.co/KBLab/piper-tts-nst-swedish checkpoints/sv-SE/nst

# Or just download specific file using git-lfs
cd checkpoints/sv-SE/nst
git lfs pull --include="*.ckpt"
```

Then use the checkpoint path: `checkpoints/sv-SE/nst/model.ckpt`

---

## ✅ Verification

After downloading, verify your checkpoint:

1. File should be >50MB (typically 100-300MB)
2. File extension should be `.ckpt`
3. Try using it in training - if it loads without error, it's good!

---

## 🔗 Useful Links

- **KBLab NST:** https://huggingface.co/KBLab/piper-tts-nst-swedish
- **SubZeroAI Multi-Speaker:** https://huggingface.co/SubZeroAI/piper-swedish-tts-multispeaker  
- **Wezzmeister Collection:** https://huggingface.co/wezzmeister/piper-voices
- **Piper TTS Documentation:** https://github.com/rhasspy/piper
- **HuggingFace Help:** https://huggingface.co/docs

---

## 💡 Pro Tip

If you're training from scratch (not fine-tuning), you don't need any checkpoint! Just:
1. Select "Train from Scratch"
2. Choose your voice profile and prompt lists
3. Start training

Fine-tuning from a Swedish checkpoint will give better results faster, but requires manual download.

