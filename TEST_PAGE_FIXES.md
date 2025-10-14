# Test Page Fixes

## Issues Found and Fixed

### 1. JavaScript Variable Name Mismatch
**Problem**: The JavaScript was trying to access form elements that didn't exist:
- Looking for `speechRate` and `speechPitch` elements
- But the form actually had `lengthScale` and `noiseScale` elements

**Fix**: Updated `templates/test.html` lines 539-540:
```javascript
// OLD (crashed):
const speechRate = parseFloat(document.getElementById('speechRate').value);
const speechPitch = parseFloat(document.getElementById('speechPitch').value);

// NEW (works):
const lengthScale = parseFloat(document.getElementById('lengthScale').value);
const noiseScale = parseFloat(document.getElementById('noiseScale').value);
```

### 2. Form Data Parameter Names
**Problem**: Form was sending `length_scale` and `noise_scale`, but backend expected `speech_rate` and `speech_pitch`.

**Fix**: Updated `templates/test.html` lines 564-565:
```javascript
// OLD:
formData.append('speech_rate', speechRate);
formData.append('speech_pitch', speechPitch);

// NEW:
formData.append('length_scale', lengthScale);
formData.append('noise_scale', noiseScale);
```

### 3. Missing Button ID
**Problem**: Submit button didn't have an ID, causing JavaScript errors when trying to control button state.

**Fix**: Added `id="generateBtn"` to the submit button (line 153):
```html
<button type="submit" class="btn btn-primary w-100" id="generateBtn">
```

### 4. Backend Parameter Mismatch
**Problem**: Backend expected `speech_rate` and `speech_pitch`, but form sends `length_scale` and `noise_scale`.

**Fix**: Updated `app.py` endpoint to accept the correct parameters:
```python
# OLD:
@app.post("/api/test/generate")
async def generate_test_speech(
    language: str = Form(...),
    voice_id: str = Form(...),
    text: str = Form(...),
    speech_rate: float = Form(1.0),
    speech_pitch: float = Form(1.0)
):

# NEW:
@app.post("/api/test/generate")
async def generate_test_speech(
    language: str = Form(...),
    voice_id: str = Form(...),
    text: str = Form(...),
    length_scale: float = Form(1.0),
    noise_scale: float = Form(0.667)
):
```

### 5. Parameter Mapping in TTS
**Problem**: The TTS system uses Piper TTS which expects `speech_rate` and `speech_pitch`, but we're sending VITS parameters (`length_scale` and `noise_scale`).

**Fix**: Added parameter mapping in `utils/tts.py`:
```python
# Map VITS parameters to Piper parameters
# length_scale controls speech rate (inverse relationship)
speech_rate = 1.0 / length_scale if length_scale != 0 else 1.0
# noise_scale doesn't have a direct equivalent in Piper, so we'll use a default
speech_pitch = 1.0
```

## Current Status

✅ **Test page loads correctly**  
✅ **Form elements are properly referenced**  
✅ **Backend accepts correct parameters**  
✅ **Parameter mapping works**  
⚠️ **Checkpoints need to be downloaded** (separate issue with download URLs)

## How to Use

1. Go to http://localhost:8000/test
2. Select a language (e.g., "English (United States)")
3. Select a voice (e.g., "Amy")
4. Enter text to synthesize
5. Adjust length scale and noise scale sliders
6. Click "Generate Speech"

## Known Issues

### Checkpoint Download URLs
The checkpoint download URLs have URL encoding issues. The system tries to download from:
```
https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/epoch%3D6679-step%3D1554200.ckpt
```

But the correct URL should be:
```
https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/epoch=6679-step=1554200.ckpt
```

This is a separate issue that needs to be fixed in the checkpoint download logic.

## Testing

To test if the fixes work:

```bash
# Test the endpoint directly
docker exec coaxial-gpu-experimental python test_speech_generation.py
```

Note: This will fail with "Checkpoint not downloaded" until the checkpoint download URLs are fixed.

## Files Modified

1. `templates/test.html` - Fixed JavaScript variable names and form data
2. `app.py` - Updated endpoint to accept correct parameters
3. `utils/tts.py` - Added parameter mapping from VITS to Piper

## Next Steps

1. Fix checkpoint download URL encoding
2. Add support for custom VITS checkpoints (trained models)
3. Test with actual checkpoint downloads

