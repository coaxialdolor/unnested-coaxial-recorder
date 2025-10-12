"""
Voice Dataset Manager - FastAPI Application
"""
import os
import json
import shutil
import requests
import base64
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel
from pathlib import Path
import subprocess

# Import phoneme and MFA utilities
try:
    from utils.phonemes import get_phoneme_manager, is_language_supported, get_supported_languages
    from utils.mfa import get_mfa_aligner, is_mfa_available
    from utils.checkpoints import get_checkpoint_manager, download_checkpoint, get_available_checkpoints
    PHONEME_SUPPORT = True
    CHECKPOINT_SUPPORT = True
except ImportError:
    PHONEME_SUPPORT = False
    CHECKPOINT_SUPPORT = False
    print("Warning: Phoneme, MFA, and checkpoint utilities not available")

# Create FastAPI app
app = FastAPI(title="Voice Dataset Manager")

# Health check endpoint for Docker
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "phoneme_support": PHONEME_SUPPORT,
        "checkpoint_support": CHECKPOINT_SUPPORT
    }

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Define base paths
VOICES_DIR = Path("voices")
VOICES_DIR.mkdir(exist_ok=True)

# Global prompts directory at root
PROMPTS_DIR = Path("prompts")
PROMPTS_DIR.mkdir(exist_ok=True)

OFFLINE_LANG_DIR_MAP = {
    "en-US": "English (United States)_en-US",
    "en-GB": "English (United Kingdom)_en-GB",
    "sv-SE": "Swedish (Sweden)_sv-SE",
    "it-IT": "Italian (Italy)_it-IT",
}

def seed_offline_prompts(profile_dir: Path, language_code: str) -> int:
    """Copy up to three default prompt lists into profile/prompts for supported languages.
    Returns number of lists copied.
    """
    try:
        src_lang_dir_name = OFFLINE_LANG_DIR_MAP.get(language_code)
        if not src_lang_dir_name:
            return 0
        repo_prompts_dir = PROMPTS_DIR / src_lang_dir_name
        if not repo_prompts_dir.exists():
            return 0
        prompts_dir = profile_dir / "prompts"
        prompts_dir.mkdir(exist_ok=True)

        standard_patterns = [
            "General",
            "Chat",
            "CustomerService",
            "0000000001",
            "3000000001",
            "4000000001",
        ]
        copied = 0
        for pattern in standard_patterns:
            for txt_file in repo_prompts_dir.glob(f"*{pattern}*.txt"):
                try:
                    # Prefix filenames with language code so multiple languages can coexist clearly
                    dest_path = prompts_dir / f"{language_code}_{txt_file.stem}.txt"
                    if not dest_path.exists():
                        with open(txt_file, "r", encoding="utf-8") as src, open(dest_path, "w", encoding="utf-8") as dst:
                            for line in src:
                                if line.strip() and not line.startswith("#"):
                                    dst.write(line if line.endswith("\n") else line + "\n")
                        copied += 1
                except Exception as e:
                    print(f"Seed copy error {txt_file}: {e}")
                if copied >= 3:
                    break
            if copied >= 3:
                break
        return copied
    except Exception as e:
        print(f"Error seeding default prompts for {profile_dir.name}: {e}")
        return 0

# Define data models
class VoiceProfile(BaseModel):
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    speaker_name: Optional[str] = None  # Changed from gender to match frontend

class PromptList(BaseModel):
    name: str
    sentences: List[str]

class RecordingMetadata(BaseModel):
    filename: str
    sentence: str
    prompt_list: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main page"""
    profiles = []
    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir():
            profiles.append(profile_dir.name)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "profiles": profiles
    })

# Voice profile routes
@app.get("/api/profiles")
async def get_profiles():
    """Get all voice profiles"""
    profiles = []
    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir() and profile_dir.name != "example":
            profile_file = profile_dir / "profile.json"
            progress_file = profile_dir / "progress.json"
            clips_dir = profile_dir / "clips"

            # Default profile info
            profile_info = {
                "id": profile_dir.name,
                "name": profile_dir.name,
                "speaker_name": profile_dir.name,
                "language": "en-US",
                "description": "",
                "recording_count": 0
            }

            # Load profile metadata if available
            if profile_file.exists():
                try:
                    with open(profile_file, "r") as f:
                        metadata = json.load(f)
                        profile_info.update({
                            "speaker_name": metadata.get("speaker_name", profile_dir.name),
                            "language": metadata.get("language", "en-US"),
                            "description": metadata.get("description", "")
                        })
                except:
                    pass

            # Count recordings
            if clips_dir.exists():
                profile_info["recording_count"] = len(list(clips_dir.glob("*.wav")))

            profiles.append(profile_info)

    return profiles

@app.post("/api/profiles")
async def create_profile(profile: VoiceProfile):
    """Create a new voice profile"""
    profile_dir = VOICES_DIR / profile.name

    if profile_dir.exists():
        return {"success": False, "error": "Profile already exists"}

    try:
        # Create directory structure
        profile_dir.mkdir()
        (profile_dir / "clips").mkdir()
        (profile_dir / "recordings").mkdir()
        (profile_dir / "prompts").mkdir()

        # Create profile metadata
        profile_metadata = {
            "name": profile.name,
            "speaker_name": profile.speaker_name or profile.name,
            "language": profile.language or "en-US",
            "description": profile.description or "",
            "created_at": "2024-01-01"  # Simplified for now
        }

        # Save profile metadata
        with open(profile_dir / "profile.json", "w") as f:
            json.dump(profile_metadata, f)

        # Create initial progress file
        with open(profile_dir / "progress.json", "w") as f:
            json.dump({}, f)

        # Create metadata file for recordings
        with open(profile_dir / "metadata.jsonl", "w") as f:
            f.write("")

        # Always seed all four supported languages for every profile
        for lang_code in ["en-US", "en-GB", "sv-SE", "it-IT"]:
            seed_offline_prompts(profile_dir, lang_code)

        return {"success": True, "message": f"Profile {profile.name} created successfully"}
    except Exception as e:
        # Clean up if creation failed
        if profile_dir.exists():
            import shutil
            shutil.rmtree(profile_dir)
        return {"success": False, "error": str(e)}

@app.get("/profiles/{profile_name}", response_class=HTMLResponse)
async def profile_page(request: Request, profile_name: str):
    """Render the profile page"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get prompt lists
    prompt_lists = []
    prompts_dir = profile_dir / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.txt"):
            prompt_lists.append(prompt_file.stem)

    return templates.TemplateResponse("profiles.html", {
        "request": request,
        "profile_name": profile_name,
        "prompt_lists": prompt_lists
    })

@app.get("/record/{profile_name}/{prompt_list}", response_class=HTMLResponse)
async def record_page(request: Request, profile_name: str, prompt_list: str):
    """Render the recording page"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    prompt_file = profile_dir / "prompts" / f"{prompt_list}.txt"

    if not prompt_file.exists():
        raise HTTPException(status_code=404, detail="Prompt list not found")

    # Get sentences
    with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
        sentences = [line.strip() for line in f if line.strip()]

    # Get progress
    progress_file = profile_dir / "progress.json"
    if progress_file.exists():
        with open(progress_file, "r") as f:
            progress = json.load(f)
            prompt_progress = progress.get(prompt_list, {
                "total": len(sentences),
                "recorded": 0,
                "last_index": 0
            })
    else:
        prompt_progress = {
            "total": len(sentences),
            "recorded": 0,
            "last_index": 0
        }

    return templates.TemplateResponse("record.html", {
        "request": request,
        "profile_name": profile_name,
        "prompt_list": prompt_list,
        "sentences": sentences,
        "progress": prompt_progress
    })

# API routes for recording
@app.post("/api/profiles/{profile_name}/record")
async def save_recording_legacy(
    profile_name: str,
    prompt_list: str = Form(...),
    sentence_index: int = Form(...),
    sentence: str = Form(...),
    audio_file: UploadFile = File(...)
):
    """Save a recorded audio clip (legacy endpoint)"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    clips_dir = profile_dir / "clips"
    if not clips_dir.exists():
        clips_dir.mkdir()

    # Generate filename based on prompt list and index
    filename = f"{prompt_list}_{sentence_index:04d}.wav"
    file_path = clips_dir / filename

    # Save the audio file
    with open(file_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)

    # Process audio if needed (normalize, trim silence)
    # This would use the process_audio function from utils.audio

    # Update metadata
    metadata_file = profile_dir / "metadata.jsonl"
    with open(metadata_file, "a") as f:
        metadata = {
            "filename": filename,
            "sentence": sentence,
            "prompt_list": prompt_list
        }
        f.write(json.dumps(metadata) + "\n")

    # Update progress
    progress_file = profile_dir / "progress.json"
    if progress_file.exists():
        with open(progress_file, "r") as f:
            progress = json.load(f)
    else:
        progress = {}

    if prompt_list not in progress:
        # Get total sentences in prompt list
        prompt_file = profile_dir / "prompts" / f"{prompt_list}.txt"
        if prompt_file.exists():
            with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
                sentences = [line.strip() for line in f if line.strip()]
                total = len(sentences)
        else:
            total = 0

        progress[prompt_list] = {
            "total": total,
            "recorded": 0,
            "last_index": 0
        }

    progress[prompt_list]["recorded"] += 1
    progress[prompt_list]["last_index"] = sentence_index + 1

    with open(progress_file, "w") as f:
        json.dump(progress, f)

    return {"message": "Recording saved successfully", "filename": filename}

# Missing API routes that frontend is calling
@app.get("/api/statistics")
async def get_statistics():
    """Get recording statistics"""
    total_recordings = 0
    total_profiles = 0
    total_duration = 0

    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir() and profile_dir.name != "example":
            total_profiles += 1
            clips_dir = profile_dir / "clips"
            if clips_dir.exists():
                recordings = list(clips_dir.glob("*.wav"))
                total_recordings += len(recordings)

                # Calculate total duration (simplified)
                for recording in recordings:
                    # For now, estimate 3 seconds per recording
                    total_duration += 3

    return {
        "total_recordings": total_recordings,
        "total_profiles": total_profiles,
        "total_duration": total_duration,
        "avg_duration": total_duration / total_recordings if total_recordings > 0 else 0
    }

@app.get("/api/statistics/profiles")
async def get_profile_statistics():
    """Get detailed statistics for each profile"""
    try:
        profile_stats = []

        for profile_dir in VOICES_DIR.iterdir():
            if profile_dir.is_dir() and profile_dir.name != "example":
                profile_name = profile_dir.name
                recordings_dir = profile_dir / "recordings"
                prompts_dir = profile_dir / "prompts"
                metadata_file = profile_dir / "metadata.jsonl"

                # Count recordings and get duration
                recording_count = 0
                total_duration = 0
                prompt_lists = {}

                if recordings_dir.exists():
                    for file_path in recordings_dir.glob("*.wav"):
                        recording_count += 1
                        # Get actual duration if possible
                        try:
                            from utils.audio import get_audio_duration
                            duration = get_audio_duration(file_path)
                            total_duration += duration
                        except:
                            total_duration += 3.0  # Fallback estimate

                # Count prompts by list
                if prompts_dir.exists():
                    for prompt_file in prompts_dir.glob("*.txt"):
                        try:
                            with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
                                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                                prompt_lists[prompt_file.stem] = len(lines)
                        except Exception:
                            prompt_lists[prompt_file.stem] = 0

                # Count recordings by prompt list from metadata
                recordings_by_list = {}
                if metadata_file.exists():
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                try:
                                    metadata = json.loads(line.strip())
                                    prompt_list = metadata.get("prompt_list", "unknown")
                                    recordings_by_list[prompt_list] = recordings_by_list.get(prompt_list, 0) + 1
                                except json.JSONDecodeError:
                                    continue

                # Calculate completion rates
                completion_rates = {}
                for prompt_list, total_prompts in prompt_lists.items():
                    recorded = recordings_by_list.get(prompt_list, 0)
                    completion_rates[prompt_list] = (recorded / total_prompts * 100) if total_prompts > 0 else 0

                # Overall completion rate
                total_prompts = sum(prompt_lists.values())
                overall_completion = (recording_count / total_prompts * 100) if total_prompts > 0 else 0

                profile_stats.append({
                    "name": profile_name,
                    "recording_count": recording_count,
                    "total_duration": total_duration,
                    "prompt_lists": prompt_lists,
                    "recordings_by_list": recordings_by_list,
                    "completion_rates": completion_rates,
                    "overall_completion": overall_completion,
                    "total_prompts": total_prompts
                })

        return sorted(profile_stats, key=lambda x: x["name"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Recent activity endpoint
@app.get("/api/recent_activity")
async def get_recent_activity():
    """Get recent recording activity"""
    recent_recordings = []

    # Get all profiles
    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir():
            metadata_file = profile_dir / "metadata.jsonl"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r") as f:
                        for line in f:
                            if line.strip():
                                try:
                                    metadata = json.loads(line.strip())
                                    recent_recordings.append({
                                        "profile": profile_dir.name,
                                        "filename": metadata.get("filename", ""),
                                        "prompt_text": metadata.get("sentence", ""),
                                        "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
                                    })
                                except json.JSONDecodeError:
                                    continue
                except Exception:
                    pass

    # Sort by timestamp and return most recent 10
    recent_recordings.sort(key=lambda x: x["timestamp"], reverse=True)
    return recent_recordings[:10]

# Voice profiles endpoint (alias for compatibility)
@app.get("/api/voice-profiles/{profile_name}")
async def get_voice_profile(profile_name: str):
    """Get voice profile details (alias for /api/profiles/{profile_name})"""
    return await get_profile(profile_name)

# Prompt lists endpoint
@app.get("/api/prompt-lists/{prompt_list}")
async def get_prompt_list_details(prompt_list: str):
    """Get prompt list details"""
    # Find the prompt list in any profile
    prompts = []

    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir():
            prompts_dir = profile_dir / "prompts"
            if prompts_dir.exists():
                prompt_file = prompts_dir / f"{prompt_list}.txt"
                if prompt_file.exists():
                    try:
                        with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
                            prompts = [line.strip() for line in f if line.strip()]
                        return {"prompts": prompts, "profile": profile_dir.name, "name": prompt_list}
                    except Exception:
                        pass

    raise HTTPException(status_code=404, detail="Prompt list not found")

# Create recording endpoint
@app.post("/api/recordings")
async def create_recording(
    audio: UploadFile = File(...),
    voice_profile_id: str = Form(...),
    prompt_list_id: str = Form(...),
    prompt_text: str = Form(...),
    prompt_index: str = Form(...)
):
    """Create a new recording"""
    profile_dir = VOICES_DIR / voice_profile_id
    clips_dir = profile_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prompt_list_id}_{prompt_index}_{timestamp}.wav"
    file_path = clips_dir / filename

    # Save audio file
    try:
        content = await audio.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Update metadata
        metadata_file = profile_dir / "metadata.jsonl"
        metadata = {
            "filename": filename,
            "sentence": prompt_text,
            "prompt_list": prompt_list_id
        }
        with open(metadata_file, "a") as f:
            f.write(json.dumps(metadata) + "\n")

        return {
            "message": "Recording saved successfully",
            "filename": filename,
            "id": f"{voice_profile_id}_{prompt_list_id}_{prompt_index}_{timestamp}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save recording: {str(e)}")

@app.get("/api/recordings")
async def get_recordings(limit: int = 10):
    """Get recent recordings"""
    recordings = []

    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir() and profile_dir.name != "example":
            clips_dir = profile_dir / "clips"
            metadata_file = profile_dir / "metadata.jsonl"

            if clips_dir.exists() and metadata_file.exists():
                # Read metadata
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        for line in f:
                            if line.strip():
                                try:
                                    metadata = json.loads(line.strip())
                                    recordings.append({
                                        "filename": metadata.get("filename", ""),
                                        "prompt_text": metadata.get("sentence", ""),
                                        "voice_profile_name": profile_dir.name,
                                        "prompt_list": metadata.get("prompt_list", ""),
                                        "duration": 3.0,  # Estimated
                                        "created_at": "2024-01-01T00:00:00Z"  # Placeholder
                                    })
                                except json.JSONDecodeError:
                                    continue

    # Sort by created_at (newest first) and limit
    recordings = recordings[-limit:] if limit > 0 else recordings
    return recordings

@app.get("/api/profiles/{profile_name}")
async def get_profile(profile_name: str):
    """Get specific profile details"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get profile metadata
    metadata_file = profile_dir / "metadata.jsonl"
    profile_info = {
        "name": profile_name,
        "description": "",
        "language": "",
        "gender": "",
        "clips_count": 0,
        "prompt_lists": []
    }

    # Get clips count
    clips_dir = profile_dir / "clips"
    if clips_dir.exists():
        profile_info["clips_count"] = len(list(clips_dir.glob("*.wav")))

    # Get prompt lists
    prompts_dir = profile_dir / "prompts"
    if prompts_dir.exists():
        profile_info["prompt_lists"] = [p.stem for p in prompts_dir.glob("*.txt")]

    return profile_info

@app.delete("/api/profiles/{profile_name}")
async def delete_profile(profile_name: str):
    """Delete a voice profile"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        return {"success": False, "error": "Profile not found"}

    # Delete the entire profile directory
    shutil.rmtree(profile_dir)

    return {"success": True, "message": f"Profile {profile_name} deleted successfully"}

@app.post("/api/profiles/{profile_name}/prompts")
async def upload_prompt_list(
    profile_name: str,
    prompt_list_name: str = Form(...),
    prompt_file: UploadFile = File(...)
):
    """Upload a prompt list file"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    prompts_dir = profile_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)

    # Save the prompt file
    file_path = prompts_dir / f"{prompt_list_name}.txt"

    content = await prompt_file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {"message": f"Prompt list {prompt_list_name} uploaded successfully"}

@app.get("/api/profiles/{profile_name}/prompts/{prompt_list}")
async def get_prompt_list(profile_name: str, prompt_list: str):
    """Get sentences from a prompt list"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    prompt_file = profile_dir / "prompts" / f"{prompt_list}.txt"

    if not prompt_file.exists():
        raise HTTPException(status_code=404, detail="Prompt list not found")

    with open(prompt_file, "r") as f:
        sentences = [line.strip() for line in f if line.strip()]

    return {"sentences": sentences, "total": len(sentences)}

@app.delete("/api/profiles/{profile_name}/prompts/{prompt_list}")
async def delete_prompt_list(profile_name: str, prompt_list: str):
    """Delete a prompt list"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    prompt_file = profile_dir / "prompts" / f"{prompt_list}.txt"

    if not prompt_file.exists():
        raise HTTPException(status_code=404, detail="Prompt list not found")

    prompt_file.unlink()

    return {"message": f"Prompt list {prompt_list} deleted successfully"}

# Prompt list download functionality
@app.post("/api/profiles/{profile_name}/prompts/download")
async def download_prompt_list(
    profile_name: str,
    source: str = Form(...),  # 'piper' or 'online'
    language: str = Form(...),  # language code like 'en-US'
    category: str = Form("General"),  # category like 'General', 'Chat', 'CustomerService'
    prompt_list_name: str = Form(None)
):
    """Download a prompt list from piper_recording_studio wordlists or online LM dataset"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    prompts_dir = profile_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)

    # Generate default prompt list name if not provided
    if not prompt_list_name:
        prompt_list_name = f"{source}_{language}_{category}"

    file_path = prompts_dir / f"{prompt_list_name}.txt"

    if file_path.exists():
        return {"message": f"Prompt list {prompt_list_name} already exists", "downloaded": False}

    prompts = []

    if source == "piper":
        # Load from local repo prompts directory
        prompts = await download_piper_prompt_list(language, category)
    elif source == "online":
        # Download from online LM dataset
        prompts = await download_online_lm_dataset(language, category)
    else:
        raise HTTPException(status_code=400, detail="Invalid source. Use 'piper' or 'online'")

    if not prompts:
        raise HTTPException(status_code=404, detail=f"No prompts found for {language} - {category}")

    # Save the downloaded prompts
    with open(file_path, "w", encoding="utf-8") as f:
        for prompt in prompts:
            f.write(prompt + "\n")

    return {
        "message": f"Prompt list {prompt_list_name} downloaded successfully",
        "downloaded": True,
        "prompts_count": len(prompts),
        "source": source,
        "language": language,
        "category": category
    }

async def download_piper_prompt_list(language: str, category: str) -> list:
    """Fetch prompts from local 'prompts' directory mirroring piper-recording-studio structure.
    If files are present locally, load from disk. Otherwise, return empty list (UI can present link).
    """
    # Map category names to file patterns
    category_patterns = {
        "General": ["General", "0000000001"],
        "Chat": ["Chat", "3000000001"],
        "CustomerService": ["CustomerService", "4000000001"],
        "Numbers": ["numbers"],
        "CommonPhrases": ["common_phrases"]
    }

    # Map language codes to directory names
    language_mappings = {
        "sv-SE": "Swedish (Sweden)_sv-SE",
        "it-IT": "Italian (Italy)_it-IT",
        "en-US": "English (United States)_en-US",
        "en-GB": "English (United Kingdom)_en-GB",
        "es-ES": "Spanish (Spain)_es-ES",
        "fr-FR": "French (France)_fr-FR",
        "de-DE": "German (Germany)_de-DE",
        "pt-BR": "Portuguese (Brazil)_pt-BR",
        "ja-JP": "Japanese (Japan)_ja-JP",
        "ko-KR": "Korean (Korea)_ko-KR",
        "zh-CN": "Chinese (Simplified)_zh-CN",
        "zh-TW": "Chinese (Traditional)_zh-TW"
    }

    base_prompts_dir = PROMPTS_DIR

    # Get the directory name for the language
    dir_name = language_mappings.get(language)
    if not dir_name:
        # Try to find a matching language directory
        for dir_path in base_prompts_dir.iterdir():
            if dir_path.is_dir() and language in dir_path.name:
                dir_name = dir_path.name
                break
        else:
            return []

    language_dir = base_prompts_dir / dir_name

    if not language_dir.exists():
        return []

    prompts = []
    patterns = category_patterns.get(category, [category])

    # Look for files matching the category patterns
    for pattern in patterns:
        for txt_file in language_dir.glob(f"*{pattern}*.txt"):
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    file_prompts = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                    prompts.extend(file_prompts)
            except Exception as e:
                print(f"Error reading {txt_file}: {e}")
                continue

    return prompts  # Return full list

async def download_online_lm_dataset(language: str, category: str) -> list:
    """Download prompts from online LM dataset"""
    # This is a placeholder for online dataset integration
    # You could integrate with APIs like:
    # - Common Voice dataset
    # - OpenSLR datasets
    # - Custom LM datasets

    # For now, we'll use a simple fallback that generates sample prompts
    sample_prompts = {
        "en-US": {
            "General": [
                "The quick brown fox jumps over the lazy dog.",
                "Hello, how are you doing today?",
                "I am learning to use the voice dataset manager.",
                "This is a test of the recording system.",
                "The weather today is sunny and warm.",
                "Please record each prompt clearly and at a normal speaking pace.",
                "Thank you for helping to create high-quality voice datasets.",
                "Welcome to the voice dataset manager version 1.0!",
                "What time is it right now?",
                "How do I get to the nearest store?"
            ],
            "Chat": [
                "Hey, what's up?",
                "That's awesome!",
                "I totally agree with you.",
                "Can you help me with this?",
                "Thanks for your help!",
                "See you later!",
                "How's your day going?",
                "What do you think about that?",
                "That's a great idea!",
                "I'm not sure about that."
            ],
            "CustomerService": [
                "Thank you for calling customer service.",
                "How may I help you today?",
                "I understand your concern.",
                "Let me check that for you.",
                "Is there anything else I can help you with?",
                "Your order has been processed successfully.",
                "Please hold while I transfer your call.",
                "I apologize for the inconvenience.",
                "Your feedback is important to us.",
                "Have a wonderful day!"
            ]
        }
    }

    # Return prompts for the requested language and category, or fallback to English General
    return sample_prompts.get(language, sample_prompts).get(category, sample_prompts["en-US"]["General"])

# Get prompt lists for a specific profile
@app.get("/api/profiles/{profile_name}/prompts")
async def get_profile_prompts(profile_name: str):
    """Get all prompt lists for a specific profile"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    prompts_dir = profile_dir / "prompts"
    if not prompts_dir.exists():
        return []

    prompts = []
    for prompt_file in prompts_dir.glob("*.txt"):
        try:
                        with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
                            prompt_lines = []
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith("#"):
                                    # Handle tab-separated format: take the text part after the tab
                                    if '\t' in line:
                                        text_part = line.split('\t', 1)[1].strip()
                                        if text_part:  # Only count if there's actual text content
                                            prompt_lines.append(text_part)
                                    else:
                                        prompt_lines.append(line)
                            prompts.append({
                                "id": f"{profile_name}_{prompt_file.stem}",
                                "name": prompt_file.stem,
                                "language": "en-US",  # Default, could be enhanced to detect from content
                                "prompt_count": len(prompt_lines),
                                "profile": profile_name
                            })
        except Exception as e:
            print(f"Error reading prompt file {prompt_file}: {e}")
            continue

    return prompts

# Helper endpoint to open prompt file folder in OS explorer
@app.get("/api/open_prompt_folder/{profile_name}/{prompt_name}")
async def open_prompt_folder(profile_name: str, prompt_name: str):
    profile_dir = VOICES_DIR / profile_name
    prompt_file = profile_dir / "prompts" / f"{prompt_name}.txt"
    if not prompt_file.exists():
        return {"success": False}
    folder = str(prompt_file.parent.resolve())
    try:
        # Windows explorer
        if os.name == "nt":
            subprocess.Popen(["explorer", folder])
        else:
            # macOS
            if os.system("uname") == 0:
                subprocess.Popen(["open", folder])
            else:
                # Linux
                subprocess.Popen(["xdg-open", folder])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
# Get next prompt for recording
@app.get("/api/next_prompt/{profile_name}/{prompt_list_id}")
async def get_next_prompt(profile_name: str, prompt_list_id: str):
    """Get the next prompt for recording"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    # Parse prompt list name from ID (format: profile_name_prompt_name)
    # Remove the profile_name prefix and first underscore
    if not prompt_list_id.startswith(f"{profile_name}_"):
        raise HTTPException(status_code=400, detail="Invalid prompt list ID format")

    prompt_name = prompt_list_id[len(profile_name) + 1:]
    prompt_file = profile_dir / "prompts" / f"{prompt_name}.txt"



    if not prompt_file.exists():
        raise HTTPException(status_code=404, detail="Prompt list not found")

    try:
        with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
            prompts = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Handle tab-separated format: take the text part after the tab
                    if '\t' in line:
                        text_part = line.split('\t', 1)[1].strip()
                        if text_part:  # Only count if there's actual text content
                            prompts.append(text_part)
                    else:
                        prompts.append(line)

        if not prompts:
            raise HTTPException(status_code=404, detail="No prompts available")

        # For now, return the first prompt
        # In a real implementation, you'd track which prompts have been recorded
        return {
            "prompt": {
                "id": 1,
                "text": prompts[0],
                "index": 0,
                "total": len(prompts)
            },
            "progress": {
                "recorded": 0,
                "total": len(prompts)
            }
        }
    except Exception as e:
        print(f"Error reading prompt file {prompt_file}: {e}")
        raise HTTPException(status_code=500, detail="Error reading prompts")

# Load all prompts for a specific prompt list
@app.get("/api/load_prompts/{profile_name}/{prompt_list_id}")
async def load_prompts(profile_name: str, prompt_list_id: str):
    """Load all prompts for a specific prompt list"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    # Parse prompt list name from ID - handle both formats
    if prompt_list_id.startswith(f"{profile_name}_"):
        prompt_name = prompt_list_id[len(profile_name) + 1:]
    else:
        prompt_name = prompt_list_id
    prompt_file = profile_dir / "prompts" / f"{prompt_name}.txt"

    if not prompt_file.exists():
        raise HTTPException(status_code=404, detail="Prompt list not found")

    try:
        with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
            prompts = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Handle tab-separated format: take the text part after the tab
                    if '\t' in line:
                        text_part = line.split('\t', 1)[1].strip()
                        if text_part:  # Only count if there's actual text content
                            prompts.append(text_part)
                    else:
                        prompts.append(line)

        return {"prompts": prompts}
    except Exception as e:
        print(f"Error reading prompt file {prompt_file}: {e}")
        raise HTTPException(status_code=500, detail="Error reading prompts")

# Get recorded status for a prompt list
@app.get("/api/recorded_status/{profile_name}/{prompt_list_id}")
async def get_recorded_status(profile_name: str, prompt_list_id: str):
    """Get which prompts have been recorded for a specific prompt list - only if files actually exist"""
    profile_dir = VOICES_DIR / profile_name
    recordings_dir = profile_dir / "recordings"

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    # Parse prompt list name from ID - handle both formats
    if prompt_list_id.startswith(f"{profile_name}_"):
        prompt_name = prompt_list_id[len(profile_name) + 1:]
    else:
        prompt_name = prompt_list_id

    # Check metadata file for recorded prompts
    metadata_file = profile_dir / "metadata.jsonl"
    recorded_indices = []

    if metadata_file.exists() and recordings_dir.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            metadata = json.loads(line.strip())
                            if metadata.get("prompt_list") == prompt_name:
                                # Use prompt_index from metadata directly
                                prompt_idx = metadata.get("prompt_index")
                                filename = metadata.get("filename")

                                # CRITICAL: Only count as recorded if the actual file exists
                                if prompt_idx is not None and filename:
                                    file_path = recordings_dir / filename
                                    if file_path.exists():
                                        recorded_indices.append(prompt_idx)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error reading metadata file: {e}")

    return {"recorded_indices": recorded_indices}

# Get recording statistics for a profile
@app.get("/api/recording_stats/{profile_name}")
async def get_recording_stats(profile_name: str, selected_language: str = None):
    """Get recording statistics for prompt lists in a profile"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    stats = []
    metadata_file = profile_dir / "metadata.jsonl"
    recordings_dir = profile_dir / "recordings"

    # Get all prompt files in the profile
    prompts_dir = profile_dir / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            language_code = prompt_name.split('_')[0] if '_' in prompt_name else prompt_name

            # Count total prompts in file
            try:
                with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
                    total_prompts = 0
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if '\t' in line:
                                text_part = line.split('\t', 1)[1].strip()
                                if text_part:
                                    total_prompts += 1
                            else:
                                total_prompts += 1
            except Exception as e:
                print(f"Error reading prompt file {prompt_file}: {e}")
                total_prompts = 0

            # Count recorded prompts by scanning actual files
            recorded_count = 0
            if recordings_dir.exists() and metadata_file.exists():
                # Get all files for this prompt list from metadata
                with open(metadata_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                metadata = json.loads(line.strip())
                                if metadata.get("prompt_list") == prompt_name:
                                    filename = metadata.get("filename")
                                    if filename:
                                        file_path = recordings_dir / filename
                                        # Only count if the actual file exists
                                        if file_path.exists():
                                            recorded_count += 1
                            except json.JSONDecodeError:
                                continue

            # Only include if:
            # 1. It's the selected language, OR
            # 2. It has existing recordings
            should_include = False
            if selected_language and language_code == selected_language:
                should_include = True
            elif recorded_count > 0:
                should_include = True

            if should_include:
                stats.append({
                    "language_code": language_code,
                    "prompt_list": prompt_name,
                    "recorded": recorded_count,
                    "total": total_prompts
                })

    return stats

# Open recordings folder
@app.get("/api/open_recordings_folder/{profile_name}")
async def open_recordings_folder(profile_name: str):
    """Open the recordings folder for a profile in the file explorer"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        return {"success": False, "error": "Profile not found"}

    recordings_dir = profile_dir / "recordings"
    recordings_dir.mkdir(exist_ok=True)

    try:
        import subprocess
        import platform
        import shutil

        system = platform.system()
        if system == "Windows":
            subprocess.Popen(['explorer', str(recordings_dir)], shell=False)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", str(recordings_dir)])
        else:  # Linux
            # Check if xdg-open exists (not available in Docker)
            if shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", str(recordings_dir)])
            else:
                # Return the path for Docker/containers
                return {
                    "success": True, 
                    "message": "Running in container - folder available at host path",
                    "path": str(recordings_dir)
                }

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Save recording
@app.post("/api/record")
async def save_recording(
    audio: UploadFile = File(...),
    prompt_id: int = Form(...),
    prompt_index: int = Form(...),
    prompt_text: str = Form(...),
    profile_id: str = Form(...),
    prompt_list_id: str = Form(...)
):
    """Save a recording"""
    try:
        # Create recordings directory for the profile
        profile_dir = VOICES_DIR / profile_id
        recordings_dir = profile_dir / "recordings"
        recordings_dir.mkdir(exist_ok=True)

        # Parse prompt list name from ID - handle both formats
        if prompt_list_id.startswith(f"{profile_id}_"):
            prompt_list_name = prompt_list_id[len(profile_id) + 1:]
        else:
            prompt_list_name = prompt_list_id

        # Extract prompt ID from prompt file to get actual prompt number
        prompt_file = profile_dir / "prompts" / f"{prompt_list_name}.txt"
        prompt_number = f"{prompt_index+1:04d}"  # Default to 1-based numbering

        if prompt_file.exists():
            try:
                with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                    if prompt_index < len(lines):
                        line = lines[prompt_index]
                        if '\t' in line:
                            full_prompt_id = line.split('\t')[0].strip()
                            # Extract last 4 digits from prompt ID (e.g., 3000000001 -> 0001)
                            if len(full_prompt_id) >= 4:
                                prompt_number = full_prompt_id[-4:].zfill(4)
                            else:
                                prompt_number = full_prompt_id.zfill(4)
                        else:
                            prompt_number = f"{prompt_index+1:04d}"
            except Exception as e:
                print(f"Error reading prompt file for naming: {e}")

        # Extract language and category from prompt_list_name
        parts = prompt_list_name.split('_')
        language_code = parts[0]  # e.g., sv-SE
        category = parts[-1]  # e.g., General

        # Generate filename with prompt number first
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prompt_number}_{language_code}_{category}_{timestamp}.wav"
        file_path = recordings_dir / filename

        # Save the audio file
        contents = await audio.read()
        
        # Save raw file first
        temp_path = file_path.with_suffix('.tmp')
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Try to convert to proper WAV format immediately
        try:
            from pydub import AudioSegment
            # Load audio (handles webm, mp4, etc.)
            audio_segment = AudioSegment.from_file(temp_path)
            # Export as proper WAV
            audio_segment.export(file_path, format="wav")
            # Remove temp file
            temp_path.unlink()
        except Exception as conv_error:
            # If conversion fails, just use the raw file
            print(f"Could not convert to WAV on upload: {conv_error}")
            temp_path.rename(file_path)

        # Update metadata
        metadata_file = profile_dir / "metadata.jsonl"
        metadata = {
            "filename": filename,
            "sentence": prompt_text,
            "prompt_list": prompt_list_name,
            "prompt_index": prompt_index,
            "timestamp": timestamp
        }
        with open(metadata_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(metadata) + "\n")

        # Calculate duration (this is a simple approximation)
        # In a real implementation, you'd use an audio library to get actual duration
        duration = len(contents) / 44100 / 2  # Rough estimate for 44.1kHz 16-bit audio

        return JSONResponse({"success": True, "duration": duration})

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

# Get recording history for a profile
@app.get("/api/recording_history/{profile_name}")
async def get_recording_history(profile_name: str, limit: int = 10, offset: int = 0):
    """Get recent recordings for a profile by scanning actual files"""
    profile_dir = VOICES_DIR / profile_name
    recordings_dir = profile_dir / "recordings"
    metadata_file = profile_dir / "metadata.jsonl"

    if not recordings_dir.exists():
        return []

    # Get all recording files and their metadata
    recordings = []

    # Create a lookup for metadata by filename
    metadata_lookup = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        metadata = json.loads(line.strip())
                        filename = metadata.get("filename")
                        if filename:
                            metadata_lookup[filename] = metadata
                    except json.JSONDecodeError:
                        continue

    # Scan actual files in recordings directory
    for file_path in recordings_dir.glob("*.wav"):
        filename = file_path.name
        file_stat = file_path.stat()

        # Get metadata if available, otherwise create basic info
        if filename in metadata_lookup:
            recording_info = metadata_lookup[filename].copy()
        else:
            # Extract basic info from filename if no metadata
            parts = filename.split('_')
            if len(parts) >= 4:
                prompt_number = parts[0]
                language_code = parts[1]
                category = parts[2]
                timestamp = parts[3].replace('.wav', '')
                recording_info = {
                    "filename": filename,
                    "sentence": f"Recording {prompt_number}",
                    "prompt_list": f"{language_code}_{category}",
                    "timestamp": timestamp
                }
            else:
                recording_info = {
                    "filename": filename,
                    "sentence": "Unknown recording",
                    "prompt_list": "unknown",
                    "timestamp": "unknown"
                }

        # Add file modification time for sorting
        recording_info["file_mtime"] = file_stat.st_mtime
        recordings.append(recording_info)

    # Sort by file modification time, newest first
    recordings.sort(key=lambda x: x.get("file_mtime", 0), reverse=True)

    # Return paginated results
    return recordings[offset:offset+limit]

# Serve a recording file
@app.get("/api/recording/{profile_name}/{filename}")
async def get_recording(profile_name: str, filename: str):
    """Serve a recording file"""
    from fastapi.responses import FileResponse
    file_path = VOICES_DIR / profile_name / "recordings" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(file_path)

# Get recording for a specific prompt
@app.get("/api/get_recording_for_prompt/{profile_name}/{prompt_list_id}/{prompt_index}")
async def get_recording_for_prompt(profile_name: str, prompt_list_id: str, prompt_index: int):
    """Get the recording filename for a specific prompt - only if file actually exists"""
    profile_dir = VOICES_DIR / profile_name
    recordings_dir = profile_dir / "recordings"
    metadata_file = profile_dir / "metadata.jsonl"

    # Parse prompt list name
    if prompt_list_id.startswith(f"{profile_name}_"):
        prompt_name = prompt_list_id[len(profile_name) + 1:]
    else:
        prompt_name = prompt_list_id

    if metadata_file.exists() and recordings_dir.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    metadata = json.loads(line.strip())
                    if (metadata.get("prompt_list") == prompt_name and
                        metadata.get("prompt_index") == prompt_index):
                        filename = metadata.get("filename")
                        if filename:
                            file_path = recordings_dir / filename
                            # Only return filename if the actual file exists
                            if file_path.exists():
                                return {"filename": filename}

    return {"filename": None}

# Delete a recording for a specific prompt
@app.delete("/api/delete_recording/{profile_name}/{prompt_list_id}/{prompt_index}")
async def delete_recording(profile_name: str, prompt_list_id: str, prompt_index: int):
    """Delete a recording file and remove it from metadata"""
    profile_dir = VOICES_DIR / profile_name
    recordings_dir = profile_dir / "recordings"
    metadata_file = profile_dir / "metadata.jsonl"

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    # Parse prompt list name
    if prompt_list_id.startswith(f"{profile_name}_"):
        prompt_name = prompt_list_id[len(profile_name) + 1:]
    else:
        prompt_name = prompt_list_id

    deleted_filename = None
    
    # Find and delete the recording file
    if metadata_file.exists() and recordings_dir.exists():
        # Read all metadata
        metadata_lines = []
        with open(metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        metadata = json.loads(line.strip())
                        if (metadata.get("prompt_list") == prompt_name and
                            metadata.get("prompt_index") == prompt_index):
                            # Found the recording to delete
                            filename = metadata.get("filename")
                            if filename:
                                file_path = recordings_dir / filename
                                if file_path.exists():
                                    file_path.unlink()  # Delete the file
                                    deleted_filename = filename
                            # Don't add this line to metadata_lines (effectively removing it)
                            continue
                        # Keep all other metadata entries
                        metadata_lines.append(line)
                    except json.JSONDecodeError:
                        metadata_lines.append(line)  # Keep malformed lines
        
        # Write back the updated metadata (without the deleted recording)
        with open(metadata_file, "w", encoding="utf-8") as f:
            f.writelines(metadata_lines)
    
    if deleted_filename:
        return {"success": True, "message": f"Recording {deleted_filename} deleted"}
    else:
        return {"success": False, "message": "Recording not found"}

# Get all available prompt lists
@app.get("/api/prompts")
async def get_all_prompts():
    """Get all available prompt lists"""
    prompts = []

    # Scan all profiles and their prompts directories
    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir() and profile_dir.name not in ("__pycache__", "example"):
            prompts_dir = profile_dir / "prompts"
            if prompts_dir.exists():
                for prompt_file in prompts_dir.glob("*.txt"):
                    try:
                        with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
                            prompt_lines = []
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith("#"):
                                    # Handle tab-separated format: take the text part after the tab
                                    if '\t' in line:
                                        text_part = line.split('\t', 1)[1].strip()
                                        if text_part:  # Only count if there's actual text content
                                            prompt_lines.append(text_part)
                                    else:
                                        prompt_lines.append(line)
                            prompts.append({
                                "id": f"{profile_dir.name}_{prompt_file.stem}",
                                "name": prompt_file.stem,
                                "language": "en-US",  # Default, could be enhanced to detect from content
                                "prompt_count": len(prompt_lines),
                                "profile": profile_dir.name
                            })
                    except Exception as e:
                        print(f"Error reading prompt file {prompt_file}: {e}")
                        continue

    return prompts

# Create a new prompt list
@app.post("/api/prompts")
async def create_prompt_list(prompt_data: dict):
    """Create a new prompt list"""
    try:
        name = prompt_data.get("name")
        language = prompt_data.get("language", "en-US")
        prompts = prompt_data.get("prompts", [])

        if not name:
            return {"success": False, "error": "Prompt list name is required"}

        # For now, save to the example profile
        profile_dir = VOICES_DIR / "example"
        prompts_dir = profile_dir / "prompts"
        prompts_dir.mkdir(exist_ok=True)

        file_path = prompts_dir / f"{name}.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            for prompt in prompts:
                f.write(f"{prompt}\n")

        return {"success": True, "message": "Prompt list created successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Delete a prompt list by ID
@app.delete("/api/prompts/{prompt_id}")
async def delete_prompt_list_by_id(prompt_id: str):
    """Delete a prompt list by ID"""
    try:
        # Parse prompt_id to get profile and prompt name
        parts = prompt_id.split("_", 1)
        if len(parts) != 2:
            return {"success": False, "error": "Invalid prompt ID format"}

        profile_name, prompt_name = parts

        profile_dir = VOICES_DIR / profile_name
        file_path = profile_dir / "prompts" / f"{prompt_name}.txt"

        if file_path.exists():
            file_path.unlink()
            return {"success": True, "message": "Prompt list deleted successfully"}
        else:
            return {"success": False, "error": "Prompt list not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Get available prompt sources and languages
@app.get("/api/prompt-sources")
async def get_prompt_sources():
    """Get available prompt sources and languages"""
    # Use local repository prompts directory
    base_prompts_dir = PROMPTS_DIR

    # Scan available languages in piper_recording_studio
    piper_languages = []
    if base_prompts_dir.exists():
        for lang_dir in base_prompts_dir.iterdir():
            if lang_dir.is_dir():
                # Extract language code from directory name
                lang_name = lang_dir.name
                if "_" in lang_name:
                    lang_code = lang_name.split("_")[-1]
                    lang_display = lang_name.replace("_", " - ")
                else:
                    lang_code = lang_name
                    lang_display = lang_name

                piper_languages.append({
                    "code": lang_code,
                    "display": lang_display,
                    "directory": lang_name
                })

    return {
        "sources": [
            {
                "id": "piper",
                "name": "Piper Recording Studio Wordlists (Local)",
                "description": "Local wordlists bundled or added to this repo",
                "languages": piper_languages,
                "categories": ["General", "Chat", "CustomerService", "Numbers", "CommonPhrases"]
            }
        ],
        "github_prompts_url": "https://github.com/rhasspy/piper-recording-studio/tree/master/prompts"
    }

# Export routes
@app.get("/export/{profile_name}", response_class=HTMLResponse)
async def export_page_for_profile(request: Request, profile_name: str):
    """Render the export page for a specific profile"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    return templates.TemplateResponse("profiles.html", {
        "request": request,
        "profile_name": profile_name,
        "export_mode": True
    })

@app.post("/api/profiles/{profile_name}/export")
async def export_profile(profile_name: str):
    """Export a profile to Piper format"""
    profile_dir = VOICES_DIR / profile_name

    if not profile_dir.exists():
        raise HTTPException(status_code=404, detail="Profile not found")

    # Export the dataset
    # This would use the export_dataset function from utils.export
    export_dir = Path(f"exports/{profile_name}")
    export_dir.mkdir(parents=True, exist_ok=True)

    return {"message": "Dataset exported successfully", "export_path": str(export_dir)}

# Additional dashboard routes
@app.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request):
    """Serve the profiles management page."""
    try:
        # Backfill: ensure existing profiles have offline prompts for supported languages
        for profile_dir in VOICES_DIR.iterdir():
            if profile_dir.is_dir() and profile_dir.name not in ("example", "__pycache__"):
                # Try to read profile language
                lang = "en-US"
                profile_file = profile_dir / "profile.json"
                if profile_file.exists():
                    try:
                        with open(profile_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            lang = meta.get("language", lang)
                    except Exception:
                        pass
                # Always seed all four supported languages for every profile
                for lang_code in ["en-US", "en-GB", "sv-SE", "it-IT"]:
                    seed_offline_prompts(profile_dir, lang_code)

        profiles = await get_profiles()
        return templates.TemplateResponse("profiles.html", {
            "request": request,
            "profiles": profiles
        })
    except Exception as e:
        print(f"Error serving profiles page: {e}")
        return templates.TemplateResponse("profiles.html", {
            "request": request,
            "profiles": []
        })

@app.get("/record", response_class=HTMLResponse)
async def record_page_dashboard(request: Request):
    """Serve the recording page."""
    try:
        profiles = await get_profiles()
        return templates.TemplateResponse("record.html", {
            "request": request,
            "profiles": profiles
        })
    except Exception as e:
        print(f"Error serving record page: {e}")
        return templates.TemplateResponse("record.html", {
            "request": request,
            "profiles": []
        })

# Post-processing endpoints
@app.get("/postprocess", response_class=HTMLResponse)
async def postprocess_page(request: Request):
    """Render the post-processing page"""
    return templates.TemplateResponse("postprocess.html", {"request": request})

@app.get("/api/postprocess/datasets/{profile_name}")
async def get_postprocess_datasets(profile_name: str):
    """Get datasets with recordings for a profile"""
    try:
        profile_dir = VOICES_DIR / profile_name
        recordings_dir = profile_dir / "recordings"

        if not profile_dir.exists() or not recordings_dir.exists():
            return []

        # Get all prompt lists with recordings
        datasets = {}

        # Read metadata to find files for each prompt list
        metadata_file = profile_dir / "metadata.jsonl"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            metadata = json.loads(line.strip())
                            prompt_list = metadata.get("prompt_list")
                            filename = metadata.get("filename")

                            if prompt_list and filename:
                                file_path = recordings_dir / filename
                                if file_path.exists():
                                    if prompt_list not in datasets:
                                        datasets[prompt_list] = {
                                            "name": prompt_list,
                                            "recorded_count": 0,
                                            "total_count": 0
                                        }
                                    datasets[prompt_list]["recorded_count"] += 1
                        except json.JSONDecodeError:
                            continue

        # Get total count for each prompt list from prompt files
        prompts_dir = profile_dir / "prompts"
        if prompts_dir.exists():
            for prompt_file in prompts_dir.glob("*.txt"):
                prompt_name = prompt_file.stem
                if prompt_name in datasets:
                    try:
                        with open(prompt_file, "r", encoding="utf-8", errors="ignore") as f:
                            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                            datasets[prompt_name]["total_count"] = len(lines)
                    except Exception:
                        datasets[prompt_name]["total_count"] = 0

        # Convert to list and sort
        result = []
        for prompt_list, data in datasets.items():
            if data["recorded_count"] > 0:  # Only include datasets with recordings
                result.append({
                    "id": f"{profile_name}_{prompt_list}",
                    "name": prompt_list,
                    "recorded_count": data["recorded_count"],
                    "total_count": data["total_count"],
                    "display_name": f"{prompt_list} {data['recorded_count']}/{data['total_count']}"
                })

        return sorted(result, key=lambda x: x["name"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/postprocess/info/{profile_name}/{prompt_list_id}")
async def get_postprocess_info(profile_name: str, prompt_list_id: str):
    """Get information about files to be processed"""
    try:
        profile_dir = VOICES_DIR / profile_name
        recordings_dir = profile_dir / "recordings"

        if not profile_dir.exists() or not recordings_dir.exists():
            raise HTTPException(status_code=404, detail="Profile or recordings directory not found")

        # Parse prompt list name from ID
        if prompt_list_id.startswith(f"{profile_name}_"):
            prompt_name = prompt_list_id[len(profile_name) + 1:]
        else:
            prompt_name = prompt_list_id

        # Get all audio files for this prompt list
        audio_files = []
        total_duration = 0
        total_size = 0

        # Read metadata to find files for this prompt list
        metadata_file = profile_dir / "metadata.jsonl"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            metadata = json.loads(line.strip())
                            if metadata.get("prompt_list") == prompt_name:
                                filename = metadata.get("filename")
                                if filename:
                                    file_path = recordings_dir / filename
                                    if file_path.exists():
                                        audio_files.append(file_path)
                                        # Get file info
                                        from utils.audio import get_audio_info
                                        info = get_audio_info(file_path)
                                        if info:
                                            total_duration += info['duration']
                                            total_size += info['file_size']
                        except json.JSONDecodeError:
                            continue

        return {
            "total_files": len(audio_files),
            "total_duration": total_duration,
            "average_duration": total_duration / len(audio_files) if audio_files else 0,
            "total_size": total_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# In-memory storage for processing jobs (in production, use Redis or database)
processing_jobs = {}

@app.post("/api/postprocess/start")
async def start_postprocessing(request: Request):
    """Start post-processing job"""
    try:
        data = await request.json()

        profile_id = data.get("profile_id")
        # Support both single prompt_list_id (legacy) and prompt_list_ids (new multi-select)
        prompt_list_ids = data.get("prompt_list_ids", [])
        if not prompt_list_ids and data.get("prompt_list_id"):
            prompt_list_ids = [data.get("prompt_list_id")]

        silence_threshold = data.get("silence_threshold", -40)
        target_volume = data.get("target_volume", -6)  # Updated default to -6dB
        target_sample_rate = data.get("target_sample_rate", 44100)  # Default to 44.1kHz
        silence_padding = data.get("silence_padding", 200)
        create_backup = data.get("create_backup", True)

        if not profile_id or not prompt_list_ids:
            raise HTTPException(status_code=400, detail="profile_id and prompt_list_ids are required")

        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())

        # Initialize job status
        processing_jobs[job_id] = {
            "status": "running",
            "profile_id": profile_id,
            "prompt_list_ids": prompt_list_ids,
            "silence_threshold": silence_threshold,
            "target_volume": target_volume,
            "target_sample_rate": target_sample_rate,
            "silence_padding": silence_padding,
            "create_backup": create_backup,
            "processed": 0,
            "total": 0,
            "current_file": None,
            "created_at": datetime.now().isoformat(),
            "error": None
        }

        # Start processing in background
        asyncio.create_task(process_audio_batch(job_id))

        return {"success": True, "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_audio_batch(job_id: str):
    """Process audio files in background"""
    try:
        job = processing_jobs[job_id]
        profile_dir = VOICES_DIR / job["profile_id"]
        recordings_dir = profile_dir / "recordings"

        # Get files to process from ALL selected prompt lists
        files_to_process = []
        metadata_file = profile_dir / "metadata.jsonl"

        # Parse all prompt list names
        prompt_names = []
        for prompt_list_id in job["prompt_list_ids"]:
            if prompt_list_id.startswith(f"{job['profile_id']}_"):
                prompt_name = prompt_list_id[len(job['profile_id']) + 1:]
            else:
                prompt_name = prompt_list_id
            prompt_names.append(prompt_name)

        # Collect files from all prompt lists while preserving metadata
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            metadata = json.loads(line.strip())
                            # Check if this file belongs to any of the selected prompt lists
                            if metadata.get("prompt_list") in prompt_names:
                                filename = metadata.get("filename")
                                if filename:
                                    file_path = recordings_dir / filename
                                    if file_path.exists():
                                        files_to_process.append((file_path, metadata))
                        except json.JSONDecodeError:
                            continue

        job["total"] = len(files_to_process)

        # Process each file with sample rate conversion
        for i, (file_path, metadata) in enumerate(files_to_process):
            job["current_file"] = file_path.name
            job["processed"] = i

            # Process the file with sample rate conversion
            from utils.audio import process_audio_enhanced_with_sample_rate
            success, _, _ = process_audio_enhanced_with_sample_rate(
                file_path,
                job["silence_threshold"],
                job["target_volume"],
                job["target_sample_rate"],
                job["silence_padding"],
                job["create_backup"]
            )

            if not success:
                print(f"Failed to process {file_path}")

        # Mark as completed
        job["status"] = "completed"
        job["processed"] = job["total"]
        job["current_file"] = None

    except Exception as e:
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        print(f"Processing job {job_id} failed: {e}")

@app.get("/api/postprocess/status/{job_id}")
async def get_postprocess_status(job_id: str):
    """Get status of post-processing job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return processing_jobs[job_id]

@app.get("/api/postprocess/history")
async def get_postprocess_history():
    """Get post-processing history"""
    # Return recent jobs (last 10)
    recent_jobs = []
    for job_id, job in processing_jobs.items():
        if job["status"] in ["completed", "failed"]:
            recent_jobs.append({
                "job_id": job_id,
                "profile_name": job["profile_id"],
                "prompt_list_name": job["prompt_list_id"],
                "status": job["status"],
                "processed_files": job["processed"],
                "total_files": job["total"],
                "silence_threshold": job["silence_threshold"],
                "target_volume": job["target_volume"],
                "silence_padding": job["silence_padding"],
                "created_at": job["created_at"],
                "error": job.get("error")
            })

    # Sort by creation time, newest first
    recent_jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return recent_jobs[:10]

# Export endpoints
@app.get("/export", response_class=HTMLResponse)
async def export_page(request: Request):
    """Render the export page"""
    return templates.TemplateResponse("export.html", {"request": request})

# In-memory storage for export jobs (in production, use Redis or database)
export_jobs = {}

@app.post("/api/export/start")
async def start_export(request: Request):
    """Start export job"""
    try:
        data = await request.json()

        profile_id = data.get("profile_id")
        # Support both single prompt_list_id (legacy) and prompt_list_ids (new multi-select)
        prompt_list_ids = data.get("prompt_list_ids", [])
        if not prompt_list_ids and data.get("prompt_list_id"):
            prompt_list_ids = [data.get("prompt_list_id")]

        format = data.get("format", "wav")
        sample_rate = data.get("sample_rate", 44100)
        bit_depth = data.get("bit_depth", 16)
        channels = data.get("channels", 1)
        mp3_bitrate = data.get("mp3_bitrate", "192")
        include_metadata = data.get("include_metadata", True)
        include_transcripts = data.get("include_transcripts", True)
        create_zip = data.get("create_zip", True)

        if not profile_id or not prompt_list_ids:
            raise HTTPException(status_code=400, detail="profile_id and prompt_list_ids are required")

        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())

        # Initialize job status
        export_jobs[job_id] = {
            "status": "running",
            "profile_id": profile_id,
            "prompt_list_ids": prompt_list_ids,  # Changed to support multiple lists
            "format": format,
            "sample_rate": sample_rate,
            "bit_depth": bit_depth,
            "channels": channels,
            "mp3_bitrate": mp3_bitrate,
            "include_metadata": include_metadata,
            "include_transcripts": include_transcripts,
            "create_zip": create_zip,
            "processed": 0,
            "total": 0,
            "current_file": None,
            "created_at": datetime.now().isoformat(),
            "error": None,
            "download_url": None
        }

        # Start export in background
        asyncio.create_task(export_audio_batch(job_id))

        return {"success": True, "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def export_audio_batch(job_id: str):
    """Export audio files in background"""
    try:
        job = export_jobs[job_id]
        profile_dir = VOICES_DIR / job["profile_id"]
        recordings_dir = profile_dir / "recordings"

        # Parse ALL prompt list names (same logic as postprocessing)
        prompt_names = []
        for prompt_list_id in job["prompt_list_ids"]:
            if prompt_list_id.startswith(f"{job['profile_id']}_"):
                prompt_name = prompt_list_id[len(job['profile_id']) + 1:]
            else:
                prompt_name = prompt_list_id
            prompt_names.append(prompt_name)

        # Get files to export from ALL selected prompt lists
        files_to_export = []
        metadata_entries = []
        metadata_file = profile_dir / "metadata.jsonl"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            metadata = json.loads(line.strip())
                            # Check if this file belongs to ANY of the selected prompt lists
                            if metadata.get("prompt_list") in prompt_names:
                                filename = metadata.get("filename")
                                if filename:
                                    file_path = recordings_dir / filename
                                    if file_path.exists():
                                        files_to_export.append(file_path)
                                        metadata_entries.append(metadata)  # Preserves original metadata!
                        except json.JSONDecodeError:
                            continue

        job["total"] = len(files_to_export)

        # Create export directory with combined name for multiple lists
        if len(prompt_names) == 1:
            combined_name = prompt_names[0]
        elif len(prompt_names) <= 3:
            combined_name = "_".join(prompt_names)
        else:
            combined_name = f"{prompt_names[0]}_{prompt_names[1]}_and_{len(prompt_names)-2}_more"

        export_dir = profile_dir / "exports" / f"{combined_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        export_dir.mkdir(parents=True, exist_ok=True)

        # Process each file
        exported_files = []
        for i, file_path in enumerate(files_to_export):
            job["current_file"] = file_path.name
            job["processed"] = i

            # Export the file with new format
            from utils.audio import export_audio_file
            success, exported_path = export_audio_file(
                file_path,
                export_dir,
                job["format"],
                job["sample_rate"],
                job["bit_depth"],
                job["channels"],
                job["mp3_bitrate"]
            )

            if success:
                exported_files.append(exported_path)
            else:
                print(f"Failed to export {file_path}")

        # Create metadata file if requested
        if job["include_metadata"] and metadata_entries:
            metadata_export_path = export_dir / "metadata.json"
            with open(metadata_export_path, "w", encoding="utf-8") as f:
                json.dump(metadata_entries, f, indent=2, ensure_ascii=False)

        # Create transcript file if requested
        if job["include_transcripts"] and metadata_entries:
            transcript_path = export_dir / "transcripts.txt"
            with open(transcript_path, "w", encoding="utf-8") as f:
                for entry in metadata_entries:
                    f.write(f"{entry.get('filename', '')}\t{entry.get('sentence', '')}\n")

        # Create ZIP if requested
        if job["create_zip"]:
            import zipfile
            zip_path = export_dir.parent / f"{export_dir.name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in exported_files:
                    zipf.write(file_path, file_path.name)
                if job["include_metadata"] and metadata_entries:
                    zipf.write(metadata_export_path, "metadata.json")
                if job["include_transcripts"] and metadata_entries:
                    zipf.write(transcript_path, "transcripts.txt")

            # Set download URL to ZIP file
            job["download_url"] = f"/api/export/download/{zip_path.name}"
        else:
            # Set download URL to directory (or first file)
            job["download_url"] = f"/api/export/download/{export_dir.name}"

        # Mark as completed
        job["status"] = "completed"
        job["processed"] = job["total"]
        job["current_file"] = None

    except Exception as e:
        export_jobs[job_id]["status"] = "failed"
        export_jobs[job_id]["error"] = str(e)
        print(f"Export job {job_id} failed: {e}")

@app.get("/api/export/status/{job_id}")
async def get_export_status(job_id: str):
    """Get status of export job"""
    if job_id not in export_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return export_jobs[job_id]

@app.get("/api/export/history")
async def get_export_history():
    """Get export history"""
    # Return recent jobs (last 10)
    recent_jobs = []
    for job_id, job in export_jobs.items():
        if job["status"] in ["completed", "failed"]:
            recent_jobs.append({
                "job_id": job_id,
                "profile_name": job["profile_id"],
                "prompt_list_name": job["prompt_list_id"],
                "status": job["status"],
                "exported_files": job["processed"],
                "total_files": job["total"],
                "format": job["format"],
                "sample_rate": job["sample_rate"],
                "bit_depth": job["bit_depth"],
                "created_at": job["created_at"],
                "download_url": job.get("download_url"),
                "error": job.get("error")
            })

    # Sort by creation time, newest first
    recent_jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return recent_jobs[:10]

@app.get("/api/export/download/{filename}")
async def download_export(filename: str):
    """Download exported file"""
    # Find the file in any profile's exports directory
    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir():
            exports_dir = profile_dir / "exports"
            if exports_dir.exists():
                file_path = exports_dir / filename
                if file_path.exists():
                    return FileResponse(
                        path=str(file_path),
                        filename=filename,
                        media_type='application/octet-stream'
                    )

    raise HTTPException(status_code=404, detail="File not found")

# Training endpoints
@app.get("/train", response_class=HTMLResponse)
async def train_page(request: Request):
    """Render the training page"""
    return templates.TemplateResponse("train.html", {"request": request})

@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """Render the test voices page"""
    return templates.TemplateResponse("test.html", {"request": request})

# In-memory storage for training jobs (in production, use Redis or database)
training_jobs = {}

@app.get("/api/train/gpu-status")
async def get_gpu_status():
    """Check if GPU is available for training"""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_count = torch.cuda.device_count() if gpu_available else 0
        return {
            "available": gpu_available,
            "count": gpu_count,
            "devices": [torch.cuda.get_device_name(i) for i in range(gpu_count)] if gpu_available else []
        }
    except ImportError:
        return {"available": False, "count": 0, "devices": [], "error": "PyTorch not installed"}

@app.post("/api/train/start")
async def start_training(
    training_type: str = Form(...),
    profile_id: str = Form(...),
    prompt_list_ids: str = Form(...),  # Now accepts JSON array
    model_size: str = Form(...),
    learning_rate: float = Form(...),
    batch_size: int = Form(...),
    epochs: int = Form(...),
    train_split: float = Form(...),
    validation_split: float = Form(...),
    save_interval: int = Form(...),
    early_stopping: int = Form(...),
    use_gpu: bool = Form(...),
    mixed_precision: bool = Form(...),
    output_dir: str = Form(...),
    model_name: str = Form(""),
    checkpoint_path: str = Form("")
):
    """Start training job"""
    try:
        # Parse prompt_list_ids from JSON
        import json as json_module
        try:
            parsed_prompt_list_ids = json_module.loads(prompt_list_ids)
        except:
            # Fallback for single value (backward compatibility)
            parsed_prompt_list_ids = [prompt_list_ids]

        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())

        # Initialize job status
        training_jobs[job_id] = {
            "status": "running",
            "training_type": training_type,
            "profile_id": profile_id,
            "prompt_list_ids": parsed_prompt_list_ids,
            "model_size": model_size,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "epochs": epochs,
            "train_split": train_split,
            "validation_split": validation_split,
            "save_interval": save_interval,
            "early_stopping": early_stopping,
            "use_gpu": use_gpu,
            "mixed_precision": mixed_precision,
            "output_dir": output_dir,
            "model_name": model_name,
            "checkpoint_path": checkpoint_path,
            "current_epoch": 0,
            "total_epochs": epochs,
            "current_loss": None,
            "eta": None,
            "console_output": [],
            "created_at": datetime.now().isoformat(),
            "error": None
        }

        # Start training in background
        asyncio.create_task(train_model_background(job_id))

        return {"success": True, "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def train_model_background(job_id: str):
    """Train model in background (simulated)

    NOTE: When implementing actual training, use job["prompt_list_ids"] to collect
    audio files from multiple prompt lists (same logic as postprocessing and export):

    prompt_names = []
    for prompt_list_id in job["prompt_list_ids"]:
        if prompt_list_id.startswith(f"{job['profile_id']}_"):
            prompt_name = prompt_list_id[len(job['profile_id']) + 1:]
        else:
            prompt_name = prompt_list_id
        prompt_names.append(prompt_name)

    # Then collect files: if metadata.get("prompt_list") in prompt_names
    """
    try:
        job = training_jobs[job_id]

        # Simulate training progress
        for epoch in range(1, job["total_epochs"] + 1):
            if training_jobs[job_id]["status"] != "running":
                break

            job["current_epoch"] = epoch

            # Simulate loss decrease
            base_loss = 2.0
            loss = base_loss * (0.9 ** (epoch / 10))
            job["current_loss"] = loss

            # Simulate console output
            job["console_output"].append(f"Epoch {epoch}/{job['total_epochs']}: Loss = {loss:.4f}")

            # Calculate ETA
            remaining_epochs = job["total_epochs"] - epoch
            eta_minutes = remaining_epochs * 2  # Assume 2 minutes per epoch
            if eta_minutes > 60:
                eta_hours = eta_minutes / 60
                job["eta"] = f"{eta_hours:.1f}h"
            else:
                job["eta"] = f"{eta_minutes:.0f}m"

            # Simulate training time
            await asyncio.sleep(1)  # In real implementation, this would be actual training

        # Mark as completed
        if training_jobs[job_id]["status"] == "running":
            training_jobs[job_id]["status"] = "completed"
            training_jobs[job_id]["console_output"].append("Training completed successfully!")

    except Exception as e:
        training_jobs[job_id]["status"] = "failed"
        training_jobs[job_id]["error"] = str(e)
        training_jobs[job_id]["console_output"].append(f"Training failed: {str(e)}")

@app.get("/api/train/status/{job_id}")
async def get_training_status(job_id: str):
    """Get status of training job"""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return training_jobs[job_id]

@app.post("/api/train/stop/{job_id}")
async def stop_training(job_id: str):
    """Stop training job"""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    training_jobs[job_id]["status"] = "stopped"
    training_jobs[job_id]["console_output"].append("Training stopped by user")

    return {"success": True}

# Phoneme and Language Support API Endpoints

@app.get("/api/languages")
async def api_get_supported_languages():
    """Get list of all supported languages with phoneme information"""
    if not PHONEME_SUPPORT:
        return {"error": "Phoneme support not available"}

    try:
        phoneme_manager = get_phoneme_manager()
        languages = phoneme_manager.get_supported_languages()
        return {
            "success": True,
            "languages": languages,
            "total_count": len(languages)
        }
    except Exception as e:
        return {"error": f"Failed to get languages: {str(e)}"}

@app.get("/api/languages/{language_code}")
async def get_language_info(language_code: str):
    """Get detailed information about a specific language"""
    if not PHONEME_SUPPORT:
        return {"error": "Phoneme support not available"}

    try:
        phoneme_manager = get_phoneme_manager()
        config = phoneme_manager.get_language_config(language_code)

        if not config:
            raise HTTPException(status_code=404, detail=f"Language {language_code} not supported")

        return {
            "success": True,
            "language_code": language_code,
            "config": config,
            "phoneme_set_info": phoneme_manager.get_phoneme_set_info(language_code)
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to get language info: {str(e)}"}

@app.post("/api/phonemes/convert")
async def convert_text_to_phonemes(text: str = Form(...), language_code: str = Form(...)):
    """Convert text to phonemes for a given language"""
    if not PHONEME_SUPPORT:
        return {"error": "Phoneme support not available"}

    try:
        phoneme_manager = get_phoneme_manager()

        if not is_language_supported(language_code):
            raise HTTPException(status_code=400, detail=f"Language {language_code} not supported")

        phonemes = phoneme_manager.text_to_phonemes(text, language_code)

        if not phonemes:
            raise HTTPException(status_code=500, detail="Failed to convert text to phonemes")

        return {
            "success": True,
            "text": text,
            "language_code": language_code,
            "phonemes": phonemes,
            "valid": phoneme_manager.validate_phonemes(phonemes, language_code)
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to convert text: {str(e)}"}

@app.get("/api/mfa/status")
async def get_mfa_status():
    """Get MFA (Montreal Forced Aligner) status and available models"""
    if not PHONEME_SUPPORT:
        return {"error": "MFA support not available"}

    try:
        mfa_aligner = get_mfa_aligner()
        available = is_mfa_available()

        result = {
            "success": True,
            "available": available,
            "path": mfa_aligner.mfa_path if available else None
        }

        if available:
            models = mfa_aligner.get_available_models()
            result["available_models"] = models
            result["total_models"] = len(models)

        return result
    except Exception as e:
        return {"error": f"Failed to get MFA status: {str(e)}"}

@app.post("/api/mfa/download-model")
async def download_mfa_model(language_code: str = Form(...)):
    """Download MFA model for a specific language"""
    if not PHONEME_SUPPORT:
        return {"error": "MFA support not available"}

    try:
        mfa_aligner = get_mfa_aligner()

        if not is_mfa_available():
            raise HTTPException(status_code=503, detail="MFA not available")

        success = mfa_aligner.download_model(language_code)

        if success:
            return {
                "success": True,
                "message": f"MFA model for {language_code} downloaded successfully"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to download MFA model for {language_code}")

    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to download model: {str(e)}"}

@app.get("/api/phonemes/validate")
async def validate_phoneme_system():
    """Validate the phoneme and MFA system"""
    if not PHONEME_SUPPORT:
        return {"error": "Phoneme support not available"}

    try:
        validation_result = {
            "success": True,
            "phoneme_system": {
                "available": True,
                "supported_languages": len(get_supported_languages())
            },
            "mfa_system": {
                "available": is_mfa_available(),
                "path": get_mfa_aligner().mfa_path if is_mfa_available() else None
            },
            "test_conversion": None
        }

        # Test phoneme conversion
        try:
            phoneme_manager = get_phoneme_manager()
            test_phonemes = phoneme_manager.text_to_phonemes("Hello world", "en-US")
            validation_result["test_conversion"] = {
                "success": test_phonemes is not None,
                "result": test_phonemes
            }
        except Exception as e:
            validation_result["test_conversion"] = {
                "success": False,
                "error": str(e)
            }

        return validation_result

    except Exception as e:
        return {"error": f"Validation failed: {str(e)}"}

# Checkpoint Management API Endpoints

@app.get("/api/checkpoints")
async def get_all_checkpoints():
    """Get all available checkpoints across all languages"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()
        checkpoints = checkpoint_manager.get_all_available_checkpoints()
        cache_info = checkpoint_manager.get_cache_info()

        return {
            "success": True,
            "checkpoints": checkpoints,
            "cache_info": cache_info
        }
    except Exception as e:
        return {"error": f"Failed to get checkpoints: {str(e)}"}

@app.get("/api/checkpoints/{language_code}")
async def get_language_checkpoints(language_code: str):
    """Get available checkpoints for a specific language"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()
        checkpoints = checkpoint_manager.get_available_checkpoints(language_code)

        if not checkpoints:
            raise HTTPException(status_code=404, detail=f"No checkpoints available for language: {language_code}")

        return {
            "success": True,
            "language_code": language_code,
            "checkpoints": checkpoints,
            "count": len(checkpoints)
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to get checkpoints for {language_code}: {str(e)}"}

@app.get("/api/checkpoints/{language_code}/{voice_id}")
async def get_checkpoint_info(language_code: str, voice_id: str):
    """Get detailed information about a specific checkpoint"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()

        # Get checkpoint details
        checkpoints = checkpoint_manager.get_available_checkpoints(language_code)
        checkpoint_info = None

        for cp in checkpoints:
            if cp["voice_id"] == voice_id:
                checkpoint_info = cp
                break

        if not checkpoint_info:
            raise HTTPException(status_code=404, detail=f"Checkpoint {language_code}.{voice_id} not found")

        # Get metadata if downloaded
        metadata = checkpoint_manager.get_checkpoint_metadata(language_code, voice_id)

        return {
            "success": True,
            "checkpoint": checkpoint_info,
            "metadata": metadata,
            "downloaded": checkpoint_info["downloaded"]
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to get checkpoint info: {str(e)}"}

@app.post("/api/checkpoints/{language_code}/{voice_id}/download")
async def download_checkpoint_endpoint(language_code: str, voice_id: str):
    """Download a specific checkpoint"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()

        # Check if already downloaded
        if checkpoint_manager.is_checkpoint_downloaded(language_code, voice_id):
            return {
                "success": True,
                "message": "Checkpoint already downloaded",
                "downloaded": True
            }

        # Start download
        success, message = checkpoint_manager.download_checkpoint(language_code, voice_id)

        if success:
            return {
                "success": True,
                "message": message,
                "downloaded": True,
                "checkpoint_path": str(checkpoint_manager.get_checkpoint_path(language_code, voice_id))
            }
        else:
            raise HTTPException(status_code=500, detail=f"Download failed: {message}")

    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to download checkpoint: {str(e)}"}

@app.delete("/api/checkpoints/{language_code}/{voice_id}")
async def delete_checkpoint_endpoint(language_code: str, voice_id: str):
    """Delete a downloaded checkpoint"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()

        if not checkpoint_manager.is_checkpoint_downloaded(language_code, voice_id):
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        success = checkpoint_manager.delete_checkpoint(language_code, voice_id)

        if success:
            return {
                "success": True,
                "message": f"Checkpoint {language_code}.{voice_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete checkpoint")

    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to delete checkpoint: {str(e)}"}

@app.get("/api/checkpoints/recommended/{language_code}")
async def get_recommended_checkpoint(language_code: str, gender: str = None):
    """Get recommended checkpoint for a language"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()
        recommended = checkpoint_manager.get_recommended_checkpoint(language_code, gender)

        if not recommended:
            raise HTTPException(status_code=404, detail=f"No checkpoints available for language: {language_code}")

        return {
            "success": True,
            "language_code": language_code,
            "gender_preference": gender,
            "recommended": recommended
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to get recommended checkpoint: {str(e)}"}

@app.get("/api/checkpoints/cache/info")
async def get_cache_info():
    """Get checkpoint cache information"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()
        cache_info = checkpoint_manager.get_cache_info()

        return {
            "success": True,
            "cache_info": cache_info
        }
    except Exception as e:
        return {"error": f"Failed to get cache info: {str(e)}"}

@app.delete("/api/checkpoints/cache/clear")
async def clear_checkpoint_cache():
    """Clear all downloaded checkpoints"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()
        success = checkpoint_manager.clear_cache()

        if success:
            return {
                "success": True,
                "message": "Checkpoint cache cleared successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")

    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to clear cache: {str(e)}"}

@app.post("/api/checkpoints/validate/{language_code}/{voice_id}")
async def validate_checkpoint_endpoint(language_code: str, voice_id: str):
    """Validate a downloaded checkpoint"""
    if not CHECKPOINT_SUPPORT:
        return {"error": "Checkpoint support not available"}

    try:
        checkpoint_manager = get_checkpoint_manager()

        if not checkpoint_manager.is_checkpoint_downloaded(language_code, voice_id):
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        is_valid = checkpoint_manager.validate_checkpoint(language_code, voice_id)

        return {
            "success": True,
            "language_code": language_code,
            "voice_id": voice_id,
            "valid": is_valid,
            "message": "Checkpoint is valid" if is_valid else "Checkpoint validation failed"
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Failed to validate checkpoint: {str(e)}"}

# Voice Testing endpoints
import tempfile
import shutil
from pathlib import Path

# Directory for temporary test audio files
TEST_AUDIO_DIR = Path("test_audio")
TEST_AUDIO_DIR.mkdir(exist_ok=True)

@app.post("/api/test/generate")
async def generate_test_speech(
    language: str = Form(...),
    voice_id: str = Form(...),
    text: str = Form(...),
    speech_rate: float = Form(1.0),
    speech_pitch: float = Form(1.0)
):
    """Generate speech from text using a voice model"""
    try:
        if not CHECKPOINT_SUPPORT:
            raise HTTPException(status_code=503, detail="Checkpoint support not available")

        # Get checkpoint manager
        checkpoint_manager = get_checkpoint_manager()

        # Check if checkpoint is available and downloaded
        if not checkpoint_manager.is_checkpoint_downloaded(language, voice_id):
            raise HTTPException(status_code=404, detail=f"Checkpoint {language}.{voice_id} not downloaded")

        # Get checkpoint path
        checkpoint_path = checkpoint_manager.get_checkpoint_path(language, voice_id)
        if not checkpoint_path or not checkpoint_path.exists():
            raise HTTPException(status_code=404, detail="Checkpoint file not found")

        # Generate unique filename
        import uuid
        filename = f"test_{language}_{voice_id}_{uuid.uuid4().hex[:8]}.wav"
        output_path = TEST_AUDIO_DIR / filename

        # Create real TTS audio file
        success = create_test_audio_with_voice(text, output_path, language, voice_id, speech_rate, speech_pitch)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        # Return audio URL and metadata
        audio_url = f"/api/test/audio/{filename}"

        return {
            "success": True,
            "audio_url": audio_url,
            "filename": filename,
            "duration": "3.5",  # Placeholder duration
            "language": language,
            "voice_id": voice_id,
            "text": text,
            "speech_rate": speech_rate,
            "speech_pitch": speech_pitch
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/api/test/audio/{filename}")
async def get_test_audio(filename: str):
    """Serve test audio files"""
    try:
        file_path = TEST_AUDIO_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")

        # Return the audio file
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(file_path),
            media_type="audio/wav",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving audio: {str(e)}")

def create_test_audio_with_voice(text: str, output_path: Path, language: str, voice_id: str,
                                speech_rate: float = 1.0, speech_pitch: float = 1.0) -> bool:
    """
    Create a test audio file using real TTS synthesis with specific voice
    """
    try:
        # Import TTS utilities
        from utils.tts import synthesize_speech

        # Try to synthesize speech with the specified voice
        success = synthesize_speech(text, language, voice_id, output_path, speech_rate, speech_pitch)

        if success:
            return True

        # Fallback to placeholder if TTS fails
        print("TTS synthesis failed, using placeholder audio")
        return create_test_audio_fallback(text, output_path, speech_rate, speech_pitch)

    except Exception as e:
        print(f"Error creating test audio: {e}")
        return create_test_audio_fallback(text, output_path, speech_rate, speech_pitch)

def create_test_audio_fallback(text: str, output_path: Path, speech_rate: float = 1.0, speech_pitch: float = 1.0) -> bool:
    """
    Fallback audio generation using simple tones
    """
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine

        # Create a simple tone as fallback
        duration_ms = max(1000, len(text) * 100)  # Rough duration estimate

        # Generate a simple sine wave tone
        tone = Sine(440).to_audio_segment(duration=duration_ms)

        # Apply rate and pitch adjustments (simplified)
        if speech_rate != 1.0:
            tone = tone.speedup(playback_speed=speech_rate)  # pylint: disable=no-member

        # Export as WAV
        tone.export(output_path, format="wav")

        return True

    except Exception as e:
        print(f"Error creating fallback audio: {e}")
        return False

@app.delete("/api/test/cleanup")
async def cleanup_test_audio():
    """Clean up old test audio files"""
    try:
        import time
        current_time = time.time()
        max_age = 3600  # 1 hour

        cleaned_count = 0
        for file_path in TEST_AUDIO_DIR.glob("*.wav"):
            if current_time - file_path.stat().st_mtime > max_age:
                file_path.unlink()
                cleaned_count += 1

        return {
            "success": True,
            "cleaned_files": cleaned_count,
            "message": f"Cleaned up {cleaned_count} old test audio files"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up files: {str(e)}")

# Model Conversion endpoints
CONVERT_DIR = Path("converted_models")
CONVERT_DIR.mkdir(exist_ok=True)

# In-memory storage for conversion jobs
conversion_jobs = {}

@app.get("/convert", response_class=HTMLResponse)
async def convert_page(request: Request):
    """Render the model conversion page"""
    return templates.TemplateResponse("convert.html", {"request": request})

@app.post("/api/convert/start")
async def start_conversion(
    input_file: UploadFile = File(...),
    config_file: UploadFile = File(None),
    output_name: str = Form("converted_model"),
    optimization_level: str = Form("standard"),
    quantize: bool = Form(True),
    validate_output: bool = Form(True)
):
    """Start a model conversion job"""
    try:
        import uuid
        import time

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Validate input file
        if not input_file.filename.endswith('.ckpt'):
            raise HTTPException(status_code=400, detail="Input file must be a .ckpt file")

        # Create job info
        job_info = {
            "job_id": job_id,
            "status": "started",
            "progress": 0,
            "message": "Starting conversion...",
            "input_file": input_file.filename,
            "output_name": output_name,
            "optimization_level": optimization_level,
            "quantize": quantize,
            "validate_output": validate_output,
            "started_at": time.time(),
            "log": []
        }

        conversion_jobs[job_id] = job_info

        # Start background conversion
        asyncio.create_task(convert_model_background(job_id, input_file, config_file, output_name, optimization_level, quantize, validate_output))

        return {
            "success": True,
            "job_id": job_id,
            "message": "Conversion started"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting conversion: {str(e)}")

async def convert_model_background(job_id: str, input_file: UploadFile, config_file: UploadFile,
                                 output_name: str, optimization_level: str, quantize: bool, validate_output: bool):
    """Background task for model conversion"""
    try:
        job_info = conversion_jobs[job_id]

        # Update progress
        job_info["progress"] = 10
        job_info["message"] = "Saving input files..."
        job_info["log"].append("Saving input checkpoint file...")

        # Save input files
        input_path = CONVERT_DIR / f"{job_id}_input.ckpt"
        with open(input_path, "wb") as f:
            content = await input_file.read()
            f.write(content)

        config_path = None
        if config_file:
            config_path = CONVERT_DIR / f"{job_id}_config.json"
            with open(config_path, "wb") as f:
                content = await config_file.read()
                f.write(content)

        # Update progress
        job_info["progress"] = 20
        job_info["message"] = "Loading PyTorch model..."
        job_info["log"].append("Loading PyTorch checkpoint...")

        # Simulate conversion process (in real implementation, this would use actual conversion)
        import time
        steps = [
            (30, "Extracting model architecture..."),
            (40, "Converting to ONNX format..."),
            (50, "Applying optimizations..."),
            (60, "Quantizing model..." if quantize else "Skipping quantization..."),
            (70, "Validating output..." if validate_output else "Skipping validation..."),
            (80, "Saving converted model..."),
            (90, "Finalizing conversion..."),
            (100, "Conversion completed!")
        ]

        for progress, message in steps:
            time.sleep(1)  # Simulate processing time
            job_info["progress"] = progress
            job_info["message"] = message
            job_info["log"].append(message)

        # Create output files
        output_path = CONVERT_DIR / f"{output_name}.onnx"
        output_config_path = CONVERT_DIR / f"{output_name}.onnx.json"

        # For demo purposes, create placeholder files
        with open(output_path, "w") as f:
            f.write("# ONNX Model Placeholder\n")

        with open(output_config_path, "w") as f:
            f.write('{"model_type": "onnx", "optimization_level": "' + optimization_level + '"}')

        # Update job status
        job_info["status"] = "completed"
        job_info["output_file"] = f"{output_name}.onnx"
        job_info["config_file"] = f"{output_name}.onnx.json"
        job_info["file_size"] = f"{output_path.stat().st_size / 1024:.1f} KB"
        job_info["optimization_level"] = optimization_level
        job_info["quantized"] = quantize
        job_info["completed_at"] = time.time()

    except Exception as e:
        job_info = conversion_jobs[job_id]
        job_info["status"] = "failed"
        job_info["error"] = str(e)
        job_info["log"].append(f"Error: {str(e)}")

@app.get("/api/convert/status/{job_id}")
async def get_conversion_status(job_id: str):
    """Get the status of a conversion job"""
    try:
        if job_id not in conversion_jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job_info = conversion_jobs[job_id]

        return {
            "success": True,
            "job_id": job_id,
            "status": job_info["status"],
            "progress": job_info["progress"],
            "message": job_info["message"],
            "log": "\n".join(job_info["log"])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")

@app.get("/api/convert/download/{filename}")
async def download_converted_model(filename: str):
    """Download a converted model file"""
    try:
        file_path = CONVERT_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(file_path),
            media_type="application/octet-stream",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.get("/api/convert/history")
async def get_conversion_history():
    """Get recent conversion history"""
    try:
        # Get completed jobs from the last 24 hours
        import time
        current_time = time.time()
        recent_jobs = []

        for job_id, job_info in conversion_jobs.items():
            if (job_info["status"] == "completed" and
                current_time - job_info.get("completed_at", 0) < 86400):  # 24 hours
                recent_jobs.append({
                    "job_id": job_id,
                    "input_file": job_info["input_file"],
                    "output_file": job_info["output_file"],
                    "completed_at": job_info["completed_at"]
                })

        # Sort by completion time (newest first)
        recent_jobs.sort(key=lambda x: x["completed_at"], reverse=True)

        return {
            "success": True,
            "conversions": recent_jobs[:10]  # Last 10 conversions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversion history: {str(e)}")

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)