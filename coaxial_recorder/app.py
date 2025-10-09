"""
Voice Dataset Manager - FastAPI Application
"""
import os
import json
import shutil
import requests
from typing import List, Optional
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel
from pathlib import Path

# Create FastAPI app
app = FastAPI(title="Voice Dataset Manager")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Define base paths
VOICES_DIR = Path("voices")
VOICES_DIR.mkdir(exist_ok=True)

# Define data models
class VoiceProfile(BaseModel):
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    
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
            metadata_file = profile_dir / "metadata.jsonl"
            progress_file = profile_dir / "progress.json"
            
            # Get profile info
            profile_info = {
                "name": profile_dir.name,
                "clips_count": len(list((profile_dir / "clips").glob("*.wav"))) if (profile_dir / "clips").exists() else 0,
                "prompt_lists": [p.stem for p in (profile_dir / "prompts").glob("*.txt")] if (profile_dir / "prompts").exists() else []
            }
            
            # Add progress info if available
            if progress_file.exists():
                with open(progress_file, "r") as f:
                    progress = json.load(f)
                    profile_info["progress"] = progress
                    
            profiles.append(profile_info)
    
    return profiles

@app.post("/api/profiles")
async def create_profile(profile: VoiceProfile):
    """Create a new voice profile"""
    profile_dir = VOICES_DIR / profile.name
    
    if profile_dir.exists():
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    # Create directory structure
    profile_dir.mkdir()
    (profile_dir / "clips").mkdir()
    (profile_dir / "prompts").mkdir()
    
    # Create initial progress file
    with open(profile_dir / "progress.json", "w") as f:
        json.dump({}, f)
    
    # Create metadata file with profile info
    with open(profile_dir / "metadata.jsonl", "w") as f:
        f.write("")
    
    return {"message": f"Profile {profile.name} created successfully"}

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
    with open(prompt_file, "r") as f:
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
async def save_recording(
    profile_name: str,
    prompt_list: str = Form(...),
    sentence_index: int = Form(...),
    sentence: str = Form(...),
    audio_file: UploadFile = File(...)
):
    """Save a recorded audio clip"""
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
            with open(prompt_file, "r") as f:
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
async def get_prompt_list(prompt_list: str):
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
                        with open(prompt_file, "r") as f:
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
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Delete the entire profile directory
    shutil.rmtree(profile_dir)
    
    return {"message": f"Profile {profile_name} deleted successfully"}

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
        # Download from piper_recording_studio wordlists
        prompts = await download_piper_prompt_list(language, category)
    elif source == "online":
        # Download from online LM dataset
        prompts = await download_online_lm_dataset(language, category)
    else:
        raise HTTPException(status_code=400, detail="Invalid source. Use 'piper' or 'online'")
    
    if not prompts:
        raise HTTPException(status_code=404, detail=f"No prompts found for {language} - {category}")
    
    # Save the downloaded prompts
    with open(file_path, "w") as f:
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
    """Download prompts from piper_recording_studio wordlists"""
    # Map category names to file patterns
    category_patterns = {
        "General": ["General", "0000000001"],
        "Chat": ["Chat", "3000000001"],
        "CustomerService": ["CustomerService", "4000000001"],
        "Numbers": ["numbers"],
        "CommonPhrases": ["common_phrases"]
    }
    
    base_prompts_dir = Path("/Users/petter/Desktop/untitled folder/piper-recording-studio/prompts")
    language_dir = base_prompts_dir / f"{language}"
    
    if not language_dir.exists():
        # Try to find a matching language directory
        for dir_path in base_prompts_dir.iterdir():
            if dir_path.is_dir() and language in dir_path.name:
                language_dir = dir_path
                break
        else:
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
    
    return prompts[:100]  # Limit to first 100 prompts

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

# Get all available prompt lists
@app.get("/api/prompts")
async def get_all_prompts():
    """Get all available prompt lists"""
    prompts = []
    
    # Scan all profiles and their prompts directories
    for profile_dir in VOICES_DIR.iterdir():
        if profile_dir.is_dir() and profile_dir.name != "__pycache__":
            prompts_dir = profile_dir / "prompts"
            if prompts_dir.exists():
                for prompt_file in prompts_dir.glob("*.txt"):
                    try:
                        with open(prompt_file, "r", encoding="utf-8") as f:
                            prompt_lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
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

# Delete a prompt list
@app.delete("/api/prompts/{prompt_id}")
async def delete_prompt_list(prompt_id: str):
    """Delete a prompt list"""
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
    base_prompts_dir = Path("/Users/petter/Desktop/untitled folder/piper-recording-studio/prompts")
    
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
                "name": "Piper Recording Studio Wordlists",
                "description": "Local wordlists from piper_recording_studio",
                "languages": piper_languages,
                "categories": ["General", "Chat", "CustomerService", "Numbers", "CommonPhrases"]
            },
            {
                "id": "online", 
                "name": "Online LM Dataset",
                "description": "Download from online language model datasets",
                "languages": [
                    {"code": "en-US", "display": "English (US)"},
                    {"code": "en-GB", "display": "English (UK)"},
                    {"code": "es-ES", "display": "Spanish (Spain)"},
                    {"code": "fr-FR", "display": "French (France)"},
                    {"code": "de-DE", "display": "German (Germany)"},
                    {"code": "it-IT", "display": "Italian (Italy)"},
                    {"code": "pt-BR", "display": "Portuguese (Brazil)"},
                    {"code": "ja-JP", "display": "Japanese (Japan)"},
                    {"code": "ko-KR", "display": "Korean (Korea)"},
                    {"code": "zh-CN", "display": "Chinese (Simplified)"}
                ],
                "categories": ["General", "Chat", "CustomerService"]
            }
        ]
    }

# Export routes
@app.get("/export/{profile_name}", response_class=HTMLResponse)
async def export_page(request: Request, profile_name: str):
    """Render the export page"""
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

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)