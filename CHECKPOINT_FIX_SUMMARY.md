# Swedish Checkpoint Download - Fix Summary

## ✅ What Was Fixed

### 1. **Corrected Swedish Checkpoint URLs**
- **Problem:** NST Swedish checkpoint URL was returning 404 (Not Found)
- **Root Cause:** HuggingFace repository requires authentication or direct download URLs are not available
- **Solution:** Updated to indicate manual download required, added proper instructions

### 2. **Added Manual Download Instructions**
- Checkpoints that require manual download now show clear instructions when download fails
- Instructions include:
  - Direct HuggingFace repository URL
  - Step-by-step download guide
  - Where to save the file locally
  - How to use it in training

### 3. **Improved Error Messages**
- Changed from generic "not valid JSON" error to specific instructions
- Error now shows:
  ```
  MANUAL DOWNLOAD REQUIRED:
  
  1. Visit https://huggingface.co/KBLab/piper-tts-nst-swedish
  2. Download the .ckpt file
  3. Save to: checkpoints/sv-SE/nst/
  4. Or use Custom Checkpoint Path field
  
  URL: https://huggingface.co/KBLab/piper-tts-nst-swedish
  ```

### 4. **Added Swedish Multi-Speaker Model**
- Added SubZeroAI multi-speaker Swedish model to the catalog
- Added Wezzmeister collection reference
- Both with proper manual download instructions

### 5. **Enhanced Training UI**
- Added info box explaining checkpoint options
- Clear labeling of "Custom Checkpoint Path" for manual downloads
- Better helper text explaining when to use each option
- Placeholder shows example path format

---

## 📚 Available Documentation

Created comprehensive guides:

1. **SWEDISH_CHECKPOINTS_GUIDE.md** - Complete guide for Swedish checkpoint downloads
2. **CHECKPOINT_FIX_SUMMARY.md** (this file) - What was fixed and why
3. **IMPLEMENTATION_SUMMARY.md** - All audio processing improvements

---

## 🎯 How to Download Swedish Checkpoints

### Quick Start:

1. **Visit the HuggingFace repository:**
   - KBLab NST: https://huggingface.co/KBLab/piper-tts-nst-swedish
   - SubZeroAI: https://huggingface.co/SubZeroAI/piper-swedish-tts-multispeaker

2. **Download the .ckpt file:**
   - May require HuggingFace account/login
   - Look for files ending in `.ckpt`

3. **Save to checkpoints folder:**
   ```
   checkpoints/sv-SE/nst/model.ckpt
   ```
   or
   ```
   checkpoints/sv-SE/multispeaker/model.ckpt
   ```

4. **Use in training:**
   - Go to Train page
   - Select "Fine-tune from Checkpoint"
   - Leave "Pre-trained Base Voice" dropdown **empty**
   - In "Custom Checkpoint Path" enter: `checkpoints/sv-SE/nst/model.ckpt`

---

## ❓ Your Questions Answered

### Q: "I think you need to be logged in?"
**A:** Yes! Some HuggingFace repositories require authentication. That's why we now show manual download instructions instead of trying to auto-download.

### Q: "Where to manually download and where to put them?"
**A:** 
- **Download from:** Links shown in error message or in SWEDISH_CHECKPOINTS_GUIDE.md
- **Save to:** `checkpoints/sv-SE/nst/` or `checkpoints/sv-SE/multispeaker/`
- **Name:** `model.ckpt` (or keep original name)

### Q: "Just enter them in Custom Checkpoint path?"
**A:** Yes! Exactly:
1. Download checkpoint file manually
2. Save it somewhere (e.g., `checkpoints/sv-SE/nst/model.ckpt`)
3. In training page, enter that path in "Custom Checkpoint Path" field
4. Leave the dropdown empty

### Q: "What should you put in the pre-trained base voice dropdown in that custom case?"
**A:** **Leave it empty!** The dropdown and custom path are two different ways to specify a checkpoint:
- **Use dropdown** = Auto-downloadable checkpoints (English, etc.)
- **Use custom path** = Manually downloaded checkpoints (Swedish, custom models)
- **Don't use both at the same time**

---

## 🔄 Updated Checkpoint Manifest

The checkpoint manifest now includes:

```python
"sv-SE": {
    "nst": {
        "name": "NST (Requires Manual Download)",
        "url": None,  # Triggers manual download instructions
        "manual_download_url": "https://huggingface.co/KBLab/piper-tts-nst-swedish",
        "manual_instructions": "1. Visit URL\n2. Download .ckpt\n3. Save to checkpoints/..."
    },
    "multispeaker": {
        "name": "SubZeroAI Multi-Speaker",
        # ... similar structure
    }
}
```

When `url` is `None`, the download function now returns helpful instructions instead of failing silently.

---

## 🧪 Testing

**Test the fix:**
1. Go to http://localhost:8000/train
2. Select "Fine-tune from Checkpoint"
3. Select "sv-SE" Swedish model from dropdown
4. Click "Download Selected Model"
5. You should now see clear instructions in the error message!

**Or use custom path directly:**
1. Manually download checkpoint
2. Save to `checkpoints/sv-SE/nst/model.ckpt`
3. In training, enter that path in "Custom Checkpoint Path"
4. Leave dropdown empty
5. Start training!

---

## 📝 Files Modified

1. **utils/checkpoints.py**
   - Updated Swedish checkpoint entries with manual download info
   - Added manual download instruction handling
   - Returns helpful error messages instead of failing

2. **templates/train.html**
   - Added info box explaining checkpoint options
   - Updated labels and helper text
   - Better placeholder text showing path format

3. **Created Documentation:**
   - SWEDISH_CHECKPOINTS_GUIDE.md
   - CHECKPOINT_FIX_SUMMARY.md

---

## 🎉 Result

You now have:
- ✅ Clear error messages when checkpoints can't auto-download
- ✅ Manual download instructions shown in the UI
- ✅ Multiple Swedish checkpoint options documented
- ✅ Clear guidance on using custom checkpoint path
- ✅ Separate documentation file for reference

The browser should now be showing the updated training page with the improved checkpoint UI. Try selecting a Swedish model and clicking download - you'll see the new helpful error message with instructions!

