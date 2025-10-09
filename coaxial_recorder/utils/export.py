"""
Export utilities for Voice Dataset Manager
"""
import os
import json
import shutil
from pathlib import Path
import pandas as pd

def export_dataset(profile_dir: Path):
    """
    Export a voice profile to a Piper-compatible dataset format
    
    Args:
        profile_dir: Path to the voice profile directory
        
    Returns:
        Path to the exported dataset
    """
    # Create export directory
    profile_name = profile_dir.name
    export_dir = Path(f"exports/{profile_name}")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dataset structure
    dataset_dir = export_dir / "dataset"
    dataset_dir.mkdir(exist_ok=True)
    
    # Copy audio files
    clips_dir = profile_dir / "clips"
    if clips_dir.exists():
        for clip_file in clips_dir.glob("*.wav"):
            shutil.copy(clip_file, dataset_dir)
    
    # Create metadata file
    metadata_file = profile_dir / "metadata.jsonl"
    if metadata_file.exists():
        # Read metadata
        metadata_entries = []
        with open(metadata_file, "r") as f:
            for line in f:
                if line.strip():
                    metadata_entries.append(json.loads(line))
        
        # Create list.txt file
        with open(dataset_dir / "list.txt", "w") as f:
            for entry in metadata_entries:
                f.write(f"{entry['filename']}|{entry['sentence']}\n")
                
        # Create metadata.csv file
        df = pd.DataFrame(metadata_entries)
        df.to_csv(dataset_dir / "metadata.csv", index=False)
    
    return export_dir

def import_dataset(dataset_path: Path, profile_name: str):
    """
    Import a dataset into a voice profile
    
    Args:
        dataset_path: Path to the dataset directory
        profile_name: Name of the profile to create
        
    Returns:
        Path to the created profile
    """
    # Create profile directory
    profile_dir = Path(f"voices/{profile_name}")
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    # Create clips directory
    clips_dir = profile_dir / "clips"
    clips_dir.mkdir(exist_ok=True)
    
    # Create prompts directory
    prompts_dir = profile_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    
    # Import audio files
    for audio_file in dataset_path.glob("*.wav"):
        shutil.copy(audio_file, clips_dir)
    
    # Import metadata
    metadata_file = dataset_path / "metadata.csv"
    if metadata_file.exists():
        df = pd.read_csv(metadata_file)
        
        # Create metadata.jsonl
        with open(profile_dir / "metadata.jsonl", "w") as f:
            for _, row in df.iterrows():
                entry = row.to_dict()
                f.write(json.dumps(entry) + "\n")
        
        # Create prompt list
        sentences = df["sentence"].unique().tolist()
        with open(prompts_dir / "imported.txt", "w") as f:
            for sentence in sentences:
                f.write(f"{sentence}\n")
        
        # Create progress file
        progress = {
            "imported": {
                "total": len(sentences),
                "recorded": len(df),
                "last_index": len(sentences) - 1
            }
        }
        with open(profile_dir / "progress.json", "w") as f:
            json.dump(progress, f)
    
    return profile_dir