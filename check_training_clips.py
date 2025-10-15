#!/usr/bin/env python3
"""Check how many clips the training is using"""

import json
from pathlib import Path

# Check metadata
metadata_file = Path("voices/latestPetter ny svenska pc/metadata.jsonl")
with open(metadata_file, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print(f"Total clips in metadata: {len(data)}")
print(f"\nClips by prompt list:")
for pl in sorted(set(d['prompt_list'] for d in data)):
    count = sum(1 for d in data if d['prompt_list'] == pl)
    print(f"  {pl}: {count} clips")

# Simulate what the training script would do with "all"
print(f"\nWith prompt_list_id='all':")
print(f"  Would use: {len(data)} clips")

# Check what it would do with the old prompt_list_id
old_prompt_list_id = "latestPetter ny svenska pc_sv-SE_0000000001_0300000050_General"
actual_prompt_list_id = old_prompt_list_id.split("_", 1)[1] if "_" in old_prompt_list_id else old_prompt_list_id
print(f"\nWith prompt_list_id='{old_prompt_list_id}':")
matching = [d for d in data if d.get("prompt_list") == old_prompt_list_id or d.get("prompt_list") == actual_prompt_list_id]
print(f"  Would use: {len(matching)} clips")

