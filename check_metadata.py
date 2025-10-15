import json
from pathlib import Path

metadata_file = Path("voices/latestPetter ny svenska pc/metadata.jsonl")

with open(metadata_file, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

print(f"Total entries: {len(data)}")
print("\nUnique prompt lists:")
for pl in sorted(set(d['prompt_list'] for d in data)):
    count = sum(1 for d in data if d['prompt_list'] == pl)
    print(f"  {pl}: {count} clips")

