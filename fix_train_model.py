#!/usr/bin/env python3
"""Fix train_model.py to use all clips when prompt_list_id is 'all'"""

# Read the file
with open('/app/train_model.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the filtering line
old_line = '                        if metadata.get("prompt_list") == prompt_list_id or metadata.get("prompt_list") == actual_prompt_list_id:'
new_line = '                        if prompt_list_id == "all" or metadata.get("prompt_list") == prompt_list_id or metadata.get("prompt_list") == actual_prompt_list_id:'

if old_line in content:
    content = content.replace(old_line, new_line)
    print("✓ Found and replaced the line")
else:
    print("✗ Could not find the line to replace")
    print("Looking for:", old_line[:50] + "...")

# Write the file back
with open('/app/train_model.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ File updated successfully")

